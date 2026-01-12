"""Deprecated markup helpers from :mod:`django.contrib`."""

import warnings

from django.utils.deprecation import RemovedInNextVersionWarning


warnings.warn(
    "django.contrib.markup is deprecated and will be removed in Django 1.6. "
    "Install the markup libraries you rely on directly and update any "
    "template tags to use those packages or third-party Django helpers.",
    RemovedInNextVersionWarning,
    stacklevel=2,
)

__all__ = []
