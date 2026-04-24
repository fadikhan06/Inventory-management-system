"""Accounts views: login, logout, user management (admin only)."""
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import HttpResponseForbidden

from .forms import LoginForm, UserCreateForm, UserEditForm
from .models import UserProfile


def admin_required(view_func):
    """Decorator that requires the user to have admin role."""
    def wrapper(request, *args, **kwargs):
        try:
            if request.user.profile.role != UserProfile.ROLE_ADMIN:
                return HttpResponseForbidden('Admin access required.')
        except Exception:
            return HttpResponseForbidden('Admin access required.')
        return view_func(request, *args, **kwargs)
    return wrapper


class AdminRequiredMixin:
    """Mixin to restrict access to admin-role users."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        try:
            if request.user.profile.role != UserProfile.ROLE_ADMIN:
                messages.error(request, 'Admin access required.')
                return redirect('core:dashboard')
        except Exception:
            messages.error(request, 'Admin access required.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)


class LoginView(View):
    """Custom login view."""

    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('core:dashboard')
        form = LoginForm(request)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next', '/')
            return redirect(next_url)
        return render(request, self.template_name, {'form': form})


class LogoutView(LoginRequiredMixin, View):
    """Log out the current user."""

    def post(self, request):
        logout(request)
        return redirect('accounts:login')

    def get(self, request):
        logout(request)
        return redirect('accounts:login')


class UserListView(AdminRequiredMixin, LoginRequiredMixin, ListView):
    """Admin: list all users."""

    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'

    def get_queryset(self):
        return User.objects.select_related('profile', 'profile__shop').order_by('username')


class UserCreateView(AdminRequiredMixin, LoginRequiredMixin, View):
    """Admin: create a new user."""

    template_name = 'accounts/user_form.html'

    def get(self, request):
        form = UserCreateForm()
        return render(request, self.template_name, {'form': form, 'action': 'Create'})

    def post(self, request):
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'User created successfully.')
            return redirect('accounts:user_list')
        return render(request, self.template_name, {'form': form, 'action': 'Create'})


class UserEditView(AdminRequiredMixin, LoginRequiredMixin, View):
    """Admin: edit an existing user."""

    template_name = 'accounts/user_form.html'

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        form = UserEditForm(instance=user)
        return render(request, self.template_name, {'form': form, 'action': 'Edit', 'edit_user': user})

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated successfully.')
            return redirect('accounts:user_list')
        return render(request, self.template_name, {'form': form, 'action': 'Edit', 'edit_user': user})


class UserDeleteView(AdminRequiredMixin, LoginRequiredMixin, View):
    """Admin: deactivate (soft-delete) a user."""

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user == request.user:
            messages.error(request, 'You cannot delete your own account.')
        else:
            user.is_active = False
            user.save()
            messages.success(request, f'User "{user.username}" has been deactivated.')
        return redirect('accounts:user_list')
