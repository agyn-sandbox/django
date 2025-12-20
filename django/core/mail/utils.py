"""
Email message and email sending related helper functions.
"""

import socket


# Cache the hostname, but do it lazily: socket.getfqdn() can take a couple of
# seconds, which slows down the restart of the server.
class CachedDnsName:
    def __str__(self):
        return self.get_fqdn()

    def get_fqdn(self):
        if not hasattr(self, '_fqdn'):
            fqdn = socket.getfqdn()
            try:
                fqdn.encode('ascii')
            except UnicodeEncodeError:
                fqdn = fqdn.encode('idna').decode('ascii')
            self._fqdn = fqdn
        return self._fqdn


DNS_NAME = CachedDnsName()
