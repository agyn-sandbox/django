from django.urls import include, path

from . import views

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path(
        "en/account/<slug:slug>/",
        views.index_page,
        {"section": None},
        name="i18n_account_optional",
    ),
    path(
        "en/account/<slug:slug>/section/<slug:section>/",
        views.index_page,
        name="i18n_account_optional",
    ),
    path(
        "nl/account/<slug:slug>/",
        views.index_page,
        name="i18n_account_optional",
    ),
    path(
        "nl/account/<slug:slug>/section/<slug:section>/",
        views.index_page,
        name="i18n_account_optional",
    ),
]
