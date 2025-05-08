from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Car, CarSpecification, Favorite, PurchaseRequest
from .forms import LoginForm, RegisterForm, CarForm, CarSpecificationForm

def car_list(request):
    cars = Car.objects.all()
    return render(request, 'car_list.html', {'cars': cars})

def car_detail(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    specs = CarSpecification.objects.filter(car=car).first()
    return render(request, 'car_detail.html', {'car': car, 'specs': specs})

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                request.session['user_id'] = user.id
                messages.success(request, 'Вы успешно вошли!')
                return redirect('car_list')
            else:
                messages.error(request, 'Неверное имя пользователя или пароль.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def user_register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Регистрация прошла успешно! Теперь вы можете войти.')
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def user_logout(request):
    logout(request)
    request.session.flush()
    messages.success(request, 'Вы успешно вышли!')
    return redirect('car_list')

@login_required
def add_to_favorites(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    user = request.user
    Favorite.objects.get_or_create(user=user, car=car)
    messages.success(request, 'Автомобиль добавлен в избранное!')
    return redirect('car_detail', car_id=car_id)

@login_required
@csrf_exempt
def remove_from_favorites(request, favorite_id):
    if request.method == 'POST':
        favorite = get_object_or_404(Favorite, id=favorite_id, user=request.user)
        favorite.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required
def send_purchase_request(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    user = request.user
    existing_request = PurchaseRequest.objects.filter(user=user, car=car).first()
    if existing_request:
        messages.warning(request, 'Вы уже отправили запрос на этот автомобиль.')
    else:
        PurchaseRequest.objects.create(user=user, car=car)
        messages.success(request, 'Запрос на покупку успешно отправлен!')
    return redirect('car_detail', car_id=car_id)

@login_required
def view_favorites(request):
    favorites = Favorite.objects.filter(user=request.user)
    return render(request, 'favorites.html', {'favorites': favorites})

@login_required
def view_purchase_requests(request):
    requests = PurchaseRequest.objects.filter(user=request.user)
    return render(request, 'requests.html', {'requests': requests})

@login_required
def create_car(request):
    if request.method == 'POST':
        car_form = CarForm(request.POST)
        spec_form = CarSpecificationForm(request.POST)
        if car_form.is_valid() and spec_form.is_valid():
            car = car_form.save()
            spec = spec_form.save(commit=False)
            spec.car = car
            spec.save()
            messages.success(request, 'Объявление успешно создано!')
            return redirect('car_list')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        car_form = CarForm()
        spec_form = CarSpecificationForm()
    return render(request, 'create_car.html', {'car_form': car_form, 'spec_form': spec_form})