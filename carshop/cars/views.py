from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login
from .forms import RegistrationForm, CarForm
from .models import User, Car, CarPhoto
from django.utils import timezone

def car_list(request):
    cars = Car.objects.filter(is_sold=False)
    return render(request, 'car_list.html', {'cars': cars})

def car_detail(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    return render(request, 'car_detail.html', {'car': car})

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

def create_car(request):
    if 'user_id' not in request.session:
        messages.error(request, 'Пожалуйста, войдите, чтобы добавить автомобиль.')
        return redirect('login')

    user = get_object_or_404(User, id=request.session['user_id'])

    if request.method == 'POST':
        form = CarForm(request.POST)
        if form.is_valid():
            car = form.save(commit=False)
            car.user = user
            car.save()

            # Сохранение дополнительных URL
            photo_urls = form.cleaned_data['photo_urls_list']
            print("Saving photo URLs:", photo_urls)  # Отладка
            for url in photo_urls:
                try:
                    CarPhoto.objects.create(car=car, photo_url=url)
                except Exception as e:
                    print(f"Error saving photo URL {url}: {e}")
                    messages.error(request, f'Ошибка при сохранении фото: {url}')
                    continue

            messages.success(request, 'Автомобиль успешно добавлен!')
            return redirect('car_list')
        else:
            messages.error(request, 'Ошибка при создании объявления. Проверьте введенные данные.')
    else:
        form = CarForm()

    return render(request, 'create_car.html', {'form': form})