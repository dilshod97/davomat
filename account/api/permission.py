from rest_framework.permissions import BasePermission
import requests
from account.models import User
from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework import exceptions


class CONSTANTS:
    AUTH_ENDPOINT = 'https://hpauth.masofaviyaudit.uz/auth/verify'
    DETAIL_ENDPOINT = 'https://hpauth.masofaviyaudit.uz/auth/detail'


class HasPermissionToAPI(BasePermission):
    def has_permission(self, request, view):
        return True


class AuthRemoteChecking(BaseAuthentication):

    def authenticate(self, request):
        try:
            auth = get_authorization_header(request).split()

            if not auth:
                raise exceptions.AuthenticationFailed("Authorization header topilmadi")

            if len(auth) > 2:
                raise exceptions.AuthenticationFailed("Token noto'g'ri kiritildi")

            token = auth[0].decode("utf-8")

            prepared_headers = {
                "Authorization": token
            }

            response = requests.get(
                CONSTANTS.AUTH_ENDPOINT,
                headers=prepared_headers,
                verify=False
            )

            data = response.json()

            if response.status_code == 200 and data.get("response") is True:
                res = requests.get(
                    CONSTANTS.DETAIL_ENDPOINT,
                    headers=prepared_headers,
                    verify=False
                )
                user = User.objects.get(username=res.json()['results']['user_pinfl'])
                return (user, token)

            raise exceptions.AuthenticationFailed("Not allowed")

        except requests.RequestException:
            raise exceptions.AuthenticationFailed("Auth service unavailable")

        except Exception:
            raise exceptions.AuthenticationFailed("Not allowed")