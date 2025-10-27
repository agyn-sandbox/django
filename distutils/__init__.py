"""Minimal distutils shim for Django tests.

This repository version of Django imports distutils.version.LooseVersion,
which is no longer available in Python 3.12+. Provide a minimal package so
tests can run in modern environments.
"""

