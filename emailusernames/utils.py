import base64
import hashlib
import os
import sys

from django.contrib.auth.models import User
from django.db import IntegrityError

from emailusernames import settings


# We need to convert emails to hashed versions when we store them in the
# username field.  We can't just store them directly, or we'd be limited
# to Django's username <= 30 chars limit, which is really too small for
# arbitrary emails.
def _email_to_username(email):
    # Emails should be case-insensitive unique
    email = email.lower()
    # Deal with internationalized email addresses
    converted = email.encode('utf8', 'ignore')
    return base64.urlsafe_b64encode(hashlib.sha256(converted).digest())[:30]


def get_user(email, queryset=None):
    """
    Return the user with given email address.
    Note that email address matches are case-insensitive.
    """
    # Can't guarantee a unique match without email
    if settings.ALLOW_EMPTY and not email:
        return User.DoesNotExist('User cannot be matched without email')
    
    if queryset is None:
        queryset = User.objects
    return queryset.get(username=_email_to_username(email))


def user_exists(email, queryset=None):
    """
    Return True if a user with given email address exists.
    Note that email address matches are case-insensitive.
    """
    if settings.ALLOW_EMPTY and not email:
        return False
    
    try:
        get_user(email, queryset)
    except User.DoesNotExist:
        return False
    return True


def create_user(email, password=None, is_staff=None, is_active=None):
    """
    Create a new user with the given email.
    Use this instead of `User.objects.create_user`.
    """
    if not email:
        if settings.ALLOW_EMPTY:
            # Create with temporary username if no e-mail address
            try:
                user = User.objects.create_user(
                    settings.EMPTY_PREFIX, email, password
                )
            except IntegrityError, err:
                if err.message == 'column username is not unique':
                    raise IntegrityError('temporary username already in use')
                raise
                
            # Make username unique if no e-mail
            user.save()
        else:
            raise IntegrityError('user email is empty')
        
    else:
        # Create with hashed e-mail as username
        try:
            user = User.objects.create_user(email, email, password)
        except IntegrityError, err:
            if err.message == 'column username is not unique':
                raise IntegrityError('user email is not unique')
            raise
        
    if is_active is not None or is_staff is not None:
        if is_active is not None:
            user.is_active = is_active
        if is_staff is not None:
            user.is_staff = is_staff
        user.save()
    return user


def create_superuser(email, password):
    """
    Create a new superuser with the given email.
    Use this instead of `User.objects.create_superuser`.
    """
    return User.objects.create_superuser(email, email, password)


def migrate_usernames(stream=None, quiet=False):
    """
    Migrate all existing users to django-email-as-username hashed usernames.
    If any users cannot be migrated an exception will be raised and the
    migration will not run.
    """
    stream = stream or (quiet and open(os.devnull, 'w') or sys.stdout)

    # Check all users can be migrated before applying migration
    emails = set()
    errors = []
    for user in User.objects.all():
        if not user.email:
            if settings.ALLOW_EMPTY:
                # Empty e-mail address ok - username will be updated by save
                pass
            else:
                errors.append("Cannot convert user '%s' because email is not "
                          "set." % (user._username, ))
        elif user.email.lower() in emails:
            errors.append("Cannot convert user '%s' because email '%s' "
                          "already exists." % (user._username, user.email))
        else:
            emails.add(user.email.lower())

    # Cannot migrate.
    if errors:
        [stream.write(error + '\n') for error in errors]
        raise Exception('django-email-as-username migration failed.')

    # Can migrate just fine.
    total = User.objects.count()
    for user in User.objects.all():
        user.save()

    stream.write("Successfully migrated usernames for all %d users\n"
                 % (total, ))
