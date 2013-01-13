from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase

from emailusernames import settings
from emailusernames.models import unmonkeypatch_user, monkeypatch_user
from emailusernames.utils import create_user, migrate_usernames


class CreateUserTests(TestCase):
    """
    Tests which create users.
    """
    def setUp(self):
        self.email = 'user@example.com'
        self.password = 'password'

    def test_can_create_user(self):
        user = create_user(self.email, self.password)
        self.assertEquals(list(User.objects.all()), [user])

    def test_can_create_user_with_long_email(self):
        padding = 'a' * 30
        create_user(padding + self.email, self.password)

    def test_created_user_has_correct_details(self):
        user = create_user(self.email, self.password)
        self.assertEquals(user.email, self.email)


class ExistingUserTests(TestCase):
    """
    Tests which require an existing user.
    """

    def setUp(self):
        self.email = 'user@example.com'
        self.password = 'password'
        self.user = create_user(self.email, self.password)

    def test_user_can_authenticate(self):
        auth = authenticate(email=self.email, password=self.password)
        self.assertEquals(self.user, auth)

    def test_user_can_authenticate_with_case_insensitive_match(self):
        auth = authenticate(email=self.email.upper(), password=self.password)
        self.assertEquals(self.user, auth)

    def test_user_emails_are_unique(self):
        with self.assertRaises(IntegrityError) as ctx:
            create_user(self.email, self.password)
        self.assertEquals(ctx.exception.message, 'user email is not unique')

    def test_user_emails_are_case_insensitive_unique(self):
        with self.assertRaises(IntegrityError) as ctx:
            create_user(self.email.upper(), self.password)
        self.assertEquals(ctx.exception.message, 'user email is not unique')

    def test_user_unicode(self):
        self.assertEquals(unicode(self.user), self.email)


class EmptyEmailTests(TestCase):
    def setUp(self):
        self.ALLOW_EMPTY = settings.ALLOW_EMPTY
        
    def tearDown(self):
        settings.ALLOW_EMPTY = self.ALLOW_EMPTY
        
    def test_cant_create_users_without_email(self):
        settings.ALLOW_EMPTY = False
        with self.assertRaises(IntegrityError) as ctx:
            create_user('', '')
        self.assertEquals(ctx.exception.message, 'user email is empty')
        
    def test_can_create_user_without_email(self):
        settings.ALLOW_EMPTY = True
        # Test creating one user
        try:
            user = create_user('', '')
        except Exception, e:
            self.fail('Could not create users without email: %s' % e.message)
        else:
            # User created, check the username is now unique
            self.assertEquals(
                user.username, '%s%s' % (settings.EMPTY_PREFIX, user.pk)
            )


class UserMigrationTests(TestCase):
    def setUp(self):
        self.ALLOW_EMPTY = settings.ALLOW_EMPTY
        self.username = 'example_user'
        self.email = 'user@example.com'
        self.password = 'password'
        
    def tearDown(self):
        settings.ALLOW_EMPTY = self.ALLOW_EMPTY
        
    def test_empty_disabled_can_migrate_with_email(self):
        # Default setting
        settings.ALLOW_EMPTY = False
        self._test_can_migrate_with_email()
        
    def test_empty_enabled_can_migrate_with_email(self):
        # Default setting
        settings.ALLOW_EMPTY = True
        self._test_can_migrate_with_email()
        
    def _test_can_migrate_with_email(self):
        """
        Same outcome required when ALLOW_EMPTY is disabled and enabled
        """
        # Create a user to migrate, with username and email
        user = self.create_src_user(self.username, self.email)
        
        # Migration succeeds
        migrate_usernames(quiet=True)
        
        # User has email hashed as username
        user = User.objects.get(pk=user.pk)
        self.assertEqual(user.username, self.email)
        
    def test_empty_disabled_cant_migrate_without_email(self):
        # Default setting
        settings.ALLOW_EMPTY = False
        
        # Create a user to migrate, with username and no email
        self.create_src_user(self.username, '')
        
        # Migration fails due to missing e-mail
        try:
            migrate_usernames(quiet=True)
        except Exception, e:
            self.assertEqual(
                e.message, 'django-email-as-username migration failed.'
            )
        else:
            self.fail('Migration succeeded unexpectedly')
            
    def test_empty_enabled_can_migrate_without_email(self):
        # Default setting
        settings.ALLOW_EMPTY = True
        
        # Create a user to migrate, with username and no email
        user = self.create_src_user(self.username, '')
        
        # Migration succeeds
        migrate_usernames(quiet=True)
        
        # User has original username and no email
        user = User.objects.get(pk=user.pk)
        self.assertEqual(user.username, self.username)
        self.assertEqual(user.email, '')
        
    def create_src_user(self, username, email):
        """
        Create a user without interference from emailusernames
        """
        unmonkeypatch_user()
        user = User.objects.create_user(username, email, self.password)
        monkeypatch_user()
        return user
