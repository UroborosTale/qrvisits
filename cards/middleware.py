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
