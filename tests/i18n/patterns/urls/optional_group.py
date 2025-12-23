from django.urls import path
from django.views.generic import TemplateView

view = TemplateView.as_view(template_name="dummy.html")

urlpatterns = [
    path(
        "en/account/<slug:slug>/",
        view,
        {"section": None},
        name="account-optional",
    ),
    path(
        "en/account/<slug:slug>/section/<slug:section>/",
        view,
        name="account-optional",
    ),
    path(
        "nl/account/<slug:slug>/",
        view,
        name="account-optional",
    ),
    path(
        "nl/account/<slug:slug>/section/<slug:section>/",
        view,
        name="account-optional",
    ),
]
