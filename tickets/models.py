import uuid
from django.db import models
from django.contrib.auth.models import User

class Department(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"

class EmployeeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return f"{self.user.username}"

    class Meta:
        verbose_name = "Employee Profile"
        verbose_name_plural = "Employee Profiles"

class SupportProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.user.username} ({self.department})"

    class Meta:
        verbose_name = "Support Profile"
        verbose_name_plural = "Support Profiles"

class Ticket(models.Model):
    class Status(models.TextChoices):
        NEW = "NEW", "New"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        WAITING_EMPLOYEE = "WAITING_EMPLOYEE", "Waiting for Employee"
        RESOLVED = "RESOLVED", "Resolved"
        CLOSED = "CLOSED", "Closed"

    ticket_id = models.CharField(max_length=20, unique=True, editable=False)
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tickets_created")
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    assigned_support = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="tickets_assigned"
    )

    subject = models.CharField(max_length=200)
    description = models.TextField()

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    internal_notes = models.TextField(blank=True)  # Manager-only notes

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.ticket_id:
            # Short readable ID (you can change format)
            self.ticket_id = "TCK" + uuid.uuid4().hex[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_id} - {self.subject}"

    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"

def ticket_attachment_path(instance, filename):
    return f"tickets/{instance.ticket.ticket_id}/{filename}"

class TicketAttachment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to=ticket_attachment_path)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ticket Attachment"
        verbose_name_plural = "Ticket Attachments"

class TicketComment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    is_internal = models.BooleanField(default=False)  # internal manager/support notes
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Ticket Comment"
        verbose_name_plural = "Ticket Comments"
