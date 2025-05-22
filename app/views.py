from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect

from app.forms import LoginForm


def index(request):
    return render(request, 'layouts/base.html')


@login_required
def profile_edit(request):
    return render(request, 'profile/edit.html')


def logout(request):
    auth.logout(request)
    return redirect(reverse('login'))


@csrf_protect
def login(request):
    if request.method == "POST":

        form = LoginForm(request.POST)
        if form.is_valid():
            user = auth.authenticate(request, **form.cleaned_data)
            if user:
                auth.login(request, user)
                return redirect(reverse('profile.edit'))

    return render(request, 'login.html', context={'form': LoginForm()})
