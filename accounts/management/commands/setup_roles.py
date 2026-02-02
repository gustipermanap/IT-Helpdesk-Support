from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from tickets.models import Ticket, TicketComment, TicketAttachment, Department, SupportProfile
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = "Create default roles (Employee, Support, Manager) and assign permissions."

    def handle(self, *args, **options):
        employee_group, _ = Group.objects.get_or_create(name="Employee")
        support_group, _ = Group.objects.get_or_create(name="Support")
        manager_group, _ = Group.objects.get_or_create(name="Manager")

        # Ticket permissions
        ticket_ct = ContentType.objects.get_for_model(Ticket)
        comment_ct = ContentType.objects.get_for_model(TicketComment)
        attach_ct = ContentType.objects.get_for_model(TicketAttachment)
        dept_ct = ContentType.objects.get_for_model(Department)
        support_ct = ContentType.objects.get_for_model(SupportProfile)

        def perms(ct):
            return Permission.objects.filter(content_type=ct)

        # Employee: can add ticket, add comment, add attachment, view own via code (not perms)
        employee_group.permissions.set(
            list(Permission.objects.filter(codename__in=[
                "add_ticket", "add_ticketcomment", "add_ticketattachment",
                "view_ticket", "view_ticketcomment", "view_ticketattachment"
            ]))
        )

        # Support: view/change tickets + comments/attachments (access limited by code)
        support_group.permissions.set(
            list(Permission.objects.filter(codename__in=[
                "view_ticket", "change_ticket",
                "view_ticketcomment", "add_ticketcomment",
                "view_ticketattachment", "add_ticketattachment"
            ]))
        )

        # Manager: full control of ticket system (+ user changes)
        manager_group.permissions.set(
            list(Permission.objects.filter(codename__in=[
                "add_ticket", "view_ticket", "change_ticket", "delete_ticket",
                "add_ticketcomment", "view_ticketcomment", "change_ticketcomment", "delete_ticketcomment",
                "add_ticketattachment", "view_ticketattachment", "delete_ticketattachment",
                "add_department", "view_department", "change_department", "delete_department",
                "add_supportprofile", "view_supportprofile", "change_supportprofile", "delete_supportprofile",
                "change_user", "view_user"
            ]))
        )

        self.stdout.write(self.style.SUCCESS("Roles + permissions created/updated."))
