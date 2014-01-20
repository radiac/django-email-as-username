from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from emailusernames.forms import EmailAdminAuthenticationForm
from emailusernames.utils import _email_to_username

from emailusernames import settings


# Horrible monkey patching.
# User.username always presents as the email, but saves as a hash of the email.
# It would be possible to avoid such a deep level of monkey-patching,
# but Django's admin displays the "Welcome, username" using user.username,
# and there's really no other way to get around it.
def user_init_patch(self, *args, **kwargs):
    super(User, self).__init__(*args, **kwargs)
    self._username = self.username
    # If no email, leave username field as loaded from the db
    if self.email:
        self.username = self.email


def user_save_patch(self, *args, **kwargs):
    # If no email, ensure username is a unique string
    if settings.ALLOW_EMPTY and not self.email:
        if not self.username or not self.username.startswith(settings.EMPTY_PREFIX):
            self.username = '%s%s' % (settings.EMPTY_PREFIX, self.pk or '')
        # If no email but has a username, leave for other auth backends
    else:
        self.username = _email_to_username(self.email)
    
    super(User, self).save_base(*args, **kwargs)
    
    if settings.ALLOW_EMPTY and not self.email:
        # Convert temporary to permanent
        if self.username == settings.EMPTY_PREFIX:
            self.username = '%s%s' % (settings.EMPTY_PREFIX, self.pk)
            super(User, self).save_base(*args, **kwargs)
            
    else:
        self.username = self.email


original_init = User.__init__
original_save_base = User.save_base


def monkeypatch_user():
    User.__init__ = user_init_patch
    User.save_base = user_save_patch


def unmonkeypatch_user():
    User.__init__ = original_init
    User.save_base = original_save_base


monkeypatch_user()


# Monkey-path the admin site to use a custom login form
AdminSite.login_form = EmailAdminAuthenticationForm
AdminSite.login_template = 'email_usernames/login.html'
