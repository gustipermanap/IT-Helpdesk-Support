from django.contrib import admin
from .models import Department, EmployeeProfile, SupportProfile, Ticket, TicketAttachment, TicketComment

admin.site.register(Department)
admin.site.register(EmployeeProfile)
admin.site.register(SupportProfile)
admin.site.register(Ticket)
admin.site.register(TicketAttachment)
admin.site.register(TicketComment)
