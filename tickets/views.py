from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth.models import User
from .models import Ticket, TicketAttachment, TicketComment, SupportProfile
from .forms import TicketCreateForm, TicketUpdateManagerForm, TicketUpdateSupportForm, CommentForm

def is_manager(user): return user.groups.filter(name="Manager").exists()
def is_support(user): return user.groups.filter(name="Support").exists()
def is_employee(user): return user.groups.filter(name="Employee").exists() or (not is_manager(user) and not is_support(user))

@login_required
def employee_ticket_list(request):
    tickets = Ticket.objects.filter(employee=request.user).order_by("-created_at")
    return render(request, "tickets/employee_ticket_list.html", {"tickets": tickets})

@login_required
def ticket_create(request):
    if request.method == "POST":
        form = TicketCreateForm(request.POST)
        files = request.FILES.getlist("attachments")
        if form.is_valid():
            # Validate attachments server-side
            allowed = {"application/pdf", "image/png", "image/jpeg", "image/jpg", "image/webp"}
            max_size = 10 * 1024 * 1024
            attachments_error = None
            for f in files:
                if getattr(f, "content_type", None) not in allowed:
                    attachments_error = "Only PDF and image files are allowed."
                    break
                if f.size > max_size:
                    attachments_error = "Each file must be <= 10MB."
                    break

            if attachments_error:
                return render(request, "tickets/ticket_create.html", {"form": form, "attachments_error": attachments_error})

            ticket = form.save(commit=False)
            ticket.employee = request.user
            ticket.save()

            for f in files:
                TicketAttachment.objects.create(ticket=ticket, file=f, uploaded_by=request.user)

            return redirect("ticket_detail", pk=ticket.pk)
    else:
        form = TicketCreateForm()
    return render(request, "tickets/ticket_create.html", {"form": form})

@login_required
def manager_ticket_list(request):
    if not is_manager(request.user):
        return HttpResponseForbidden("Managers only.")
    tickets = Ticket.objects.all().order_by("-created_at")
    return render(request, "tickets/manager_ticket_list.html", {"tickets": tickets})

@login_required
def support_ticket_list(request):
    if not is_support(request.user):
        return HttpResponseForbidden("Support staff only.")
    
    # Get support profile to find department
    try:
        profile = request.user.supportprofile
        dept = profile.department
    except SupportProfile.DoesNotExist:
        dept = None

    # Tickets assigned to me
    my_tickets = Ticket.objects.filter(assigned_support=request.user).order_by("-created_at")
    
    # Tickets unassigned in my department
    unassigned_tickets = Ticket.objects.none()
    if dept:
        unassigned_tickets = Ticket.objects.filter(
            department=dept,
            assigned_support__isnull=True
        ).order_by("-created_at")

    return render(request, "tickets/support_ticket_list.html", {
        "my_tickets": my_tickets,
        "unassigned_tickets": unassigned_tickets,
        "department": dept
    })

@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    # Access control:
    if is_manager(request.user):
        pass
    elif is_support(request.user):
        # Support can view if assigned OR if unassigned and in own department
        try:
            profile = request.user.supportprofile
            is_same_dept = (ticket.department == profile.department)
        except SupportProfile.DoesNotExist:
            is_same_dept = False

        if ticket.assigned_support != request.user and not (is_same_dept and ticket.assigned_support is None):
            return HttpResponseForbidden("You can only view your assigned tickets or unassigned tickets in your department.")
    else:
        # employee
        if ticket.employee != request.user:
            return HttpResponseForbidden("You can only view your own tickets.")

    # Update forms (manager vs support)
    manager_form = None
    support_form = None

    if is_manager(request.user):
        if request.method == "POST" and request.POST.get("form_type") == "manager_update":
            manager_form = TicketUpdateManagerForm(request.POST, instance=ticket)
            if manager_form.is_valid():
                manager_form.save()
                return redirect("ticket_detail", pk=ticket.pk)
        else:
            manager_form = TicketUpdateManagerForm(instance=ticket)

        # For assignment: show only support of same department (optional)
        # If you want strict department-wise assignment, filter here:
        support_staff = User.objects.filter(groups__name="Support")
        manager_form.fields["assigned_support"].queryset = support_staff

    elif is_support(request.user):
        if request.method == "POST" and request.POST.get("form_type") == "support_update":
            support_form = TicketUpdateSupportForm(request.POST, instance=ticket)
            if support_form.is_valid():
                support_form.save()
                return redirect("ticket_detail", pk=ticket.pk)
        else:
            support_form = TicketUpdateSupportForm(instance=ticket)

    return render(request, "tickets/ticket_detail.html", {
        "ticket": ticket,
        "manager_form": manager_form,
        "support_form": support_form,
    })

@login_required
def ticket_add_comment(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    # Access control same as detail
    if is_manager(request.user):
        pass
    elif is_support(request.user):
        if ticket.assigned_support != request.user:
            return HttpResponseForbidden("Not your ticket.")
    else:
        if ticket.employee != request.user:
            return HttpResponseForbidden("Not your ticket.")

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False)
            c.ticket = ticket
            c.author = request.user

            # Employees cannot create internal comments
            if is_employee(request.user):
                c.is_internal = False

            c.save()
    return redirect("ticket_detail", pk=ticket.pk)

@login_required
def manager_ticket_assign(request, pk):
    if not is_manager(request.user):
        return HttpResponseForbidden("Managers only.")

    ticket = get_object_or_404(Ticket, pk=pk)

    if request.method == "POST":
        support_id = request.POST.get("support_id")
        support = User.objects.get(id=support_id)
        ticket.assigned_support = support
        ticket.status = Ticket.Status.IN_PROGRESS
        ticket.save()
        return redirect("ticket_detail", pk=ticket.pk)

    support_staff = User.objects.filter(groups__name="Support")
    return render(request, "tickets/manager_assign.html", {"ticket": ticket, "support_staff": support_staff})

@login_required
def manager_ticket_duplicate(request, pk):
    if not is_manager(request.user):
        return HttpResponseForbidden("Managers only.")

    ticket = get_object_or_404(Ticket, pk=pk)
    new_ticket = Ticket.objects.create(
        employee=ticket.employee,
        department=ticket.department,
        subject=f"[Duplicate] {ticket.subject}",
        description=ticket.description,
        status=Ticket.Status.NEW,
    )
    # copy attachments (file copy is not performed, just references - for real copy, you’d need file duplication)
    for att in ticket.attachments.all():
        TicketAttachment.objects.create(ticket=new_ticket, file=att.file, uploaded_by=request.user)

    TicketComment.objects.create(
        ticket=new_ticket,
        author=request.user,
        message=f"Duplicated from {ticket.ticket_id}.",
        is_internal=True
    )

    return redirect("ticket_detail", pk=new_ticket.pk)
