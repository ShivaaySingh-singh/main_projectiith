from .utils import set_current_user

class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user if request.user.is_authenticated else None
        set_current_user(user)

        response = self.get_response(request)

        set_current_user(None)
        return response