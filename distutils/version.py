import re


class LooseVersion:
    """Lightweight replacement for distutils.version.LooseVersion.

    Only implements what's needed by Django's tests: the ``version`` attribute
    listing parsed components so callers can read leading integer parts.
    """

    def __init__(self, vstring):
        self.vstring = str(vstring)
        # Split on common separators and keep numeric vs non-numeric tokens.
        parts = re.split(r"[._-]", self.vstring)
        version = []
        for p in parts:
            try:
                version.append(int(p))
            except ValueError:
                # Keep non-integer tokens as-is, matching LooseVersion behavior.
                version.append(p)
        self.version = version

