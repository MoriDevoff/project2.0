from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from .forms import RegistrationForm, CarForm, UserProfileForm
from .models import User, Car, CarPhoto
from django.utils import timezone

def car_list(request):
    cars = Car.objects.filter(is_sold=False)
    return render(request, 'car_list.html', {'cars': cars})

def car_detail(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    return render(request, 'car_detail.html', {'car': car, 'author': car.user})

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.date_joined = timezone.now()
            user.avatar_url = 'https://via.placeholder.com/150'
            user.save()
            messages.success(request, 'Регистрация успешна!')
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
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            request.session['user_id'] = user.id
            messages.success(request, 'Вы успешно вошли!')
            return redirect('car_list')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')
    return render(request, 'login.html')

def logout_view(request):
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

            photo_urls = form.cleaned_data['photo_urls_list']
            print("Saving photo URLs:", photo_urls)
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

@login_required
def profile(request):
    user_cars = Car.objects.filter(user=request.user, is_sold=False)
    return render(request, 'profile.html', {'user': request.user, 'user_cars': user_cars})

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            if not user.date_joined:
                user.date_joined = timezone.now()
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Профиль успешно обновлён!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'edit_profile.html', {'form': form})

@login_required
def edit_car(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    if request.user != car.user:
        messages.error(request, 'У вас нет прав для редактирования этого объявления.')
        return redirect('car_detail', car_id=car_id)

    if request.method == 'POST':
        form = CarForm(request.POST, instance=car)
        if form.is_valid():
            car = form.save(commit=False)
            car.user = request.user
            car.save()

            existing_photos = CarPhoto.objects.filter(car=car)
            photo_urls = form.cleaned_data['photo_urls_list']
            existing_photo_urls = set(existing_photos.values_list('photo_url', flat=True))
            new_photo_urls = set(photo_urls) - existing_photo_urls

            for url in existing_photo_urls - set(photo_urls):
                CarPhoto.objects.filter(car=car, photo_url=url).delete()
            for url in new_photo_urls:
                try:
                    CarPhoto.objects.create(car=car, photo_url=url)
                except Exception as e:
                    print(f"Error saving photo URL {url}: {e}")
                    messages.error(request, f'Ошибка при сохранении фото: {url}')
                    continue

            messages.success(request, 'Объявление успешно обновлено!')
            return redirect('car_detail', car_id=car_id)
    else:
        initial_photo_urls = list(car.carphoto_set.values_list('photo_url', flat=True))
        if car.main_photo_url and car.main_photo_url not in initial_photo_urls:
            initial_photo_urls.append(car.main_photo_url)
        form = CarForm(instance=car, initial={'photo_urls_list': initial_photo_urls})

    return render(request, 'edit_car.html', {'form': form, 'car': car})