from django.urls import path
from . import views

urlpatterns = [
    # employee
    path("employee/", views.employee_ticket_list, name="employee_ticket_list"),
    path("create/", views.ticket_create, name="ticket_create"),

    # manager
    path("manager/", views.manager_ticket_list, name="manager_ticket_list"),
    path("manager/<int:pk>/assign/", views.manager_ticket_assign, name="manager_ticket_assign"),
    path("manager/<int:pk>/duplicate/", views.manager_ticket_duplicate, name="manager_ticket_duplicate"),

    # support
    path("support/", views.support_ticket_list, name="support_ticket_list"),

    # shared
    path("<int:pk>/", views.ticket_detail, name="ticket_detail"),
    path("<int:pk>/comment/", views.ticket_add_comment, name="ticket_add_comment"),
]
