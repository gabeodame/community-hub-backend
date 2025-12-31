from rest_framework.throttling import SimpleRateThrottle

# Custom throttles for user-related actions
class LoginThrottle(SimpleRateThrottle):
    scope = "auth_login"

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class RegisterThrottle(SimpleRateThrottle):
    scope = "auth_register"

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class UserWriteThrottle(SimpleRateThrottle):
    scope = "user_write"

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = f"user:{request.user.pk}"
        else:
            ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}
