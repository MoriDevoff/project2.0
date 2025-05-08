from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from .forms import RegistrationForm
from .models import User, Car
from django.utils import timezone

def car_list(request):
    cars = Car.objects.filter(is_sold=False)
    return render(request, 'car_list.html', {'cars': cars})

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Добавляем начальные данные
            user.avatar_url = 'https://via.placeholder.com/150'  # Аватар по умолчанию
            user.save()
            messages.success(request, 'Регистрация успешна! Вы можете войти.')
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Обновляем last_login вручную
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            # Сохраняем ID пользователя в сессии
            request.session['user_id'] = user.id
            messages.success(request, 'Вы успешно вошли!')
            return redirect('car_list')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')
    return render(request, 'login.html')

def logout_view(request):
    # Удаляем user_id из сессии
    if 'user_id' in request.session:
        del request.session['user_id']
    messages.success(request, 'Вы вышли из аккаунта.')
    return redirect('login')