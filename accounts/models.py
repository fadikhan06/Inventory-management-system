"""
Accounts models: UserProfile with role mapping and shop association.
"""
from django.db import models
from django.contrib.auth.models import User
from inventory.models import Shop


class UserProfile(models.Model):
    """Extended user profile with role and shop association."""

    ROLE_ADMIN = 'admin'
    ROLE_STAFF = 'staff'
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_STAFF, 'Staff'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_STAFF)
    shop = models.ForeignKey(
        Shop, on_delete=models.SET_NULL, null=True, blank=True, related_name='users'
    )
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_staff_role(self):
        return self.role == self.ROLE_STAFF
