from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Car, CarSpecification, Favorite, User
from .forms import LoginForm, CarForm, CarSpecificationForm
from django.contrib.auth.hashers import make_password, check_password

def car_list(request):
    cars = Car.objects.filter(is_sold=False)
    return render(request, 'car_list.html', {'cars': cars})

def car_detail(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    specs = get_object_or_404(CarSpecification, car=car)
    return render(request, 'car_detail.html', {'car': car, 'specs': specs})

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            try:
                user = User.objects.get(username=username)
                if check_password(password, user.password_hash):
                    request.session['user_id'] = user.id
                    messages.success(request, 'Вы успешно вошли!')
                    return redirect('car_list')
                else:
                    messages.error(request, 'Неверный пароль.')
            except User.DoesNotExist:
                messages.error(request, 'Пользователь не найден.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def user_logout(request):
    if 'user_id' in request.session:
        del request.session['user_id']
    messages.success(request, 'Вы успешно вышли!')
    return redirect('car_list')

@login_required(login_url='/login/')
def add_to_favorites(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    user_id = request.session.get('user_id')
    user = get_object_or_404(User, id=user_id)
    Favorite.objects.get_or_create(user=user, car=car)
    messages.success(request, 'Автомобиль добавлен в избранное!')
    return redirect('car_list')

@login_required(login_url='/login/')
def view_favorites(request):
    user_id = request.session.get('user_id')
    user = get_object_or_404(User, id=user_id)
    favorites = Favorite.objects.filter(user=user)
    return render(request, 'favorites.html', {'favorites': favorites})

@login_required(login_url='/login/')
def create_car(request):
    if request.method == 'POST':
        car_form = CarForm(request.POST)
        spec_form = CarSpecificationForm(request.POST)
        if car_form.is_valid() and spec_form.is_valid():
            user_id = request.session.get('user_id')
            user = get_object_or_404(User, id=user_id)
            car = car_form.save(commit=False)
            car.user = user
            car.save()
            spec = spec_form.save(commit=False)
            spec.car = car
            spec.save()
            messages.success(request, 'Объявление успешно опубликовано!')
            return redirect('car_list')
    else:
        car_form = CarForm()
        spec_form = CarSpecificationForm()
    return render(request, 'create_car.html', {'car_form': car_form, 'spec_form': spec_form})
