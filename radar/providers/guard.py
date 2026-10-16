"""Process-wide deny rule, independent of provider configuration."""
import sys
import urllib.parse

from .errors import ProviderError

_installed = False


def blocked(host):
    value=str(host or '').lower().rstrip('.')
    return value == 'aisa.one' or value.endswith('.aisa.one')


def install():
    global _installed
    if _installed:return
    def audit(event, args):
        host=None
        if event=='urllib.Request':host=urllib.parse.urlsplit(args[0]).hostname
        elif event=='socket.getaddrinfo':host=args[0]
        if blocked(host):raise ProviderError('Legacy gateway network access is forbidden')
    sys.addaudithook(audit)
    _installed=True
