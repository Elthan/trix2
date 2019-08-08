from allauth.account.models import EmailAddress
from django.shortcuts import redirect
from django.contrib import messages
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from trix.trix_core.models import User


class TrixAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Allows for connecting existing local accounts to Dataporten accounts.
        """
        # Ignore existing accounts.
        if sociallogin.is_existing:
            return

        try:
            email = sociallogin.user
            user = User.objects.get(email__iexact=email)
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            return
