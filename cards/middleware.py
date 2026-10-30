from urllib.parse import urlsplit
from django.conf import settings


class LocalPreviewOriginMiddleware:
    """Normalize opaque IAB origins only for same-origin loopback development.

    Fetch Metadata is browser-controlled. No token/cookie check is skipped:
    Django's middleware and the admin view's csrf_protect both still run.
    This compatibility branch is unreachable in production.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (settings.DEVELOPMENT and settings.DEBUG
                and request.path.startswith('/manage/')
                and request.META.get('HTTP_ORIGIN') == 'null'
                and request.META.get('HTTP_SEC_FETCH_SITE') == 'same-origin'
                and request.META.get('REMOTE_ADDR') in {'127.0.0.1', '::1'}):
            origin = f'{request.scheme}://{request.get_host()}'
            if urlsplit(origin).hostname in {'127.0.0.1', 'localhost', '::1'}:
                request.META['HTTP_ORIGIN'] = origin
        return self.get_response(request)


class PrivacyHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-Robots-Tag'] = 'noindex, nofollow, noarchive'
        response['Cache-Control'] = 'private, no-store, max-age=0'
        response['Content-Security-Policy'] = (
            "default-src 'self'; img-src 'self' data:; font-src 'self'; "
            "style-src 'self'; script-src 'self'; connect-src 'self'; "
            "object-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
        return response
