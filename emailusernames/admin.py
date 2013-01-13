"""
Override the add- and change-form in the admin, to hide the username.
"""
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib import admin
from emailusernames.forms import EmailUserCreationForm, EmailUserChangeForm
from django.utils.translation import ugettext_lazy as _


class EmailUserAdmin(UserAdmin):
    add_form = EmailUserCreationForm
    form = EmailUserChangeForm

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')}
        ),
    )
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Groups'), {'fields': ('groups',)}),
    )
    list_display = ('_list_display_email', 'first_name', 'last_name', 'is_staff')
    ordering = ('email',)
    
    def _list_display_email(self, obj):
        return obj.email if obj.email else 'None (%s)' % obj.username
    _list_display_email.short_description = 'E-mail address'

admin.site.unregister(User)
admin.site.register(User, EmailUserAdmin)


def __email_unicode__(self):
    return self.email
