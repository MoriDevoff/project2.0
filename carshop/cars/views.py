from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from .forms import RegistrationForm, CarForm, UserProfileForm, PurchaseForm
from .models import User, Car, CarPhoto, PurchaseRequest
from django.utils import timezone

def car_list(request):
    cars = Car.objects.filter(is_sold=False)
    # Подсчет непрочитанных заявок для отображения в хедере
    unread_deals_count = 0
    if request.user.is_authenticated:
        # Для покупателя: учитываем изменения статуса (Одобрено/Отклонено)
        buyer_requests = PurchaseRequest.objects.filter(buyer=request.user).order_by('-request_date')
        # Для продавца: учитываем новые заявки (В ожидании)
        seller_requests = PurchaseRequest.objects.filter(seller=request.user).order_by('-request_date')
        unread_purchases_count = buyer_requests.filter(is_read=False, status__in=['Одобрено', 'Отклонено']).count()
        unread_sales_count = seller_requests.filter(is_read=False, status='В ожидании').count()
        unread_deals_count = unread_purchases_count + unread_sales_count
    return render(request, 'car_list.html', {'cars': cars, 'unread_deals_count': unread_deals_count})

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
            for url in photo_urls:
                if url:
                    CarPhoto.objects.create(car=car, photo_url=url)

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
    buyer_requests = PurchaseRequest.objects.filter(buyer=request.user).order_by('-request_date')
    seller_requests = PurchaseRequest.objects.filter(seller=request.user).order_by('-request_date')
    unread_purchases_count = buyer_requests.filter(is_read=False, status__in=['Одобрено', 'Отклонено']).count()
    unread_sales_count = seller_requests.filter(is_read=False, status='В ожидании').count()
    has_new_notifications = (unread_purchases_count > 0 or unread_sales_count > 0)
    unread_deals_count = unread_purchases_count + unread_sales_count
    print(f"Debug - profile: unread_purchases_count={unread_purchases_count}, unread_sales_count={unread_sales_count}, has_new_notifications={has_new_notifications}")
    return render(request, 'profile.html', {
        'user': request.user,
        'user_cars': user_cars,
        'buyer_requests': buyer_requests,
        'seller_requests': seller_requests,
        'unread_deals_count': unread_deals_count,
        'unread_purchases_count': unread_purchases_count,
        'unread_sales_count': unread_sales_count,
        'has_new_notifications': has_new_notifications,
    })

@login_required
def purchases(request):
    buyer_requests = PurchaseRequest.objects.filter(buyer=request.user).order_by('-request_date')
    seller_requests = PurchaseRequest.objects.filter(seller=request.user).order_by('-request_date')

    # Пометить все заявки как прочитанные при просмотре страницы покупок
    buyer_requests.filter(is_read=False, status__in=['Одобрено', 'Отклонено']).update(is_read=True)
    seller_requests.filter(is_read=False, status='В ожидании').update(is_read=True)

    # Пересчитываем счетчики после обновления
    unread_purchases_count = buyer_requests.filter(is_read=False, status__in=['Одобрено', 'Отклонено']).count()
    unread_sales_count = seller_requests.filter(is_read=False, status='В ожидании').count()
    has_new_notifications = (unread_purchases_count > 0 or unread_sales_count > 0)
    unread_deals_count = unread_purchases_count + unread_sales_count

    print(f"Debug - purchases: unread_purchases_count={unread_purchases_count}, unread_sales_count={unread_sales_count}, has_new_notifications={has_new_notifications}")

    return render(request, 'profile.html', {
        'user': request.user,
        'user_cars': Car.objects.filter(user=request.user, is_sold=False),
        'buyer_requests': buyer_requests,
        'seller_requests': seller_requests,
        'unread_deals_count': unread_deals_count,
        'unread_purchases_count': unread_purchases_count,
        'unread_sales_count': unread_sales_count,
        'has_new_notifications': has_new_notifications,
    })

@login_required
def reset_notifications(request):
    if request.method == 'POST':
        # Пометить все заявки пользователя как прочитанные
        PurchaseRequest.objects.filter(buyer=request.user, is_read=False, status__in=['Одобрено', 'Отклонено']).update(is_read=True)
        PurchaseRequest.objects.filter(seller=request.user, is_read=False, status='В ожидании').update(is_read=True)
        messages.success(request, 'Все уведомления сброшены.')
        return redirect('profile')
    return redirect('profile')

@login_required
def purchase_car(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    if request.user == car.user:
        messages.error(request, 'Вы не можете купить свой собственный автомобиль.')
        return redirect('car_detail', car_id=car.id)

    if car.is_sold:
        messages.error(request, 'Этот автомобиль уже продан.')
        return redirect('car_detail', car_id=car.id)

    if PurchaseRequest.objects.filter(car=car, buyer=request.user, status='В ожидании').exists():
        messages.error(request, 'Вы уже подали заявку на покупку этого автомобиля.')
        return redirect('car_detail', car_id=car.id)

    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        if form.is_valid():
            offered_price = form.cleaned_data.get('offered_price') or car.price
            if request.user.balance < offered_price:
                messages.error(request, 'Недостаточно средств на балансе для покупки.')
                return render(request, 'purchase_car.html', {'form': form, 'car': car})

            purchase_request = form.save(commit=False)
            purchase_request.car = car
            purchase_request.buyer = request.user
            purchase_request.seller = car.user
            purchase_request.is_read = False  # Новая заявка помечена как непрочитанная для продавца
            purchase_request.save()

            messages.success(request, 'Заявка на покупку отправлена продавцу!')
            return redirect('car_detail', car_id=car.id)
    else:
        form = PurchaseForm(initial={'offered_price': car.price})
    return render(request, 'purchase_car.html', {'form': form, 'car': car})

@login_required
def respond_purchase(request, purchase_id, action):
    purchase = get_object_or_404(PurchaseRequest, id=purchase_id)
    if request.user != purchase.seller:
        messages.error(request, 'У вас нет прав для обработки этой заявки.')
        return redirect('profile')

    if purchase.status != 'В ожидании':
        messages.error(request, 'Эта заявка уже обработана.')
        return redirect('profile')

    if action == 'accept':
        purchase.status = 'Одобрено'
        purchase.final_price = purchase.offered_price if purchase.offered_price else purchase.car.price
        purchase.car.is_sold = True
        purchase.car.save()
        purchase.is_read = False  # Пометить как непрочитанную для покупателя
        purchase.save()
        messages.success(request, f'Заявка одобрена. Автомобиль продан за {purchase.final_price} ₽.')
    elif action == 'reject':
        purchase.status = 'Отклонено'
        purchase.is_read = False  # Пометить как непрочитанную для покупателя
        purchase.save()
        messages.success(request, 'Заявка отклонена.')
    else:
        messages.error(request, 'Недопустимое действие.')
        return redirect('profile')

    return redirect('profile')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
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

            # Удаляем все существующие URL-адреса фотографий
            CarPhoto.objects.filter(car=car).delete()

            # Сохраняем новые URL-адреса
            photo_urls = form.cleaned_data['photo_urls_list']
            for url in photo_urls:
                if url:
                    CarPhoto.objects.create(car=car, photo_url=url)

            messages.success(request, 'Объявление успешно обновлено!')
            return redirect('car_detail', car_id=car_id)
    else:
        # Заполняем поля формы существующими URL-адресаами
        initial_data = {}
        existing_photos = list(car.carphoto_set.values_list('photo_url', flat=True))
        for i, url in enumerate(existing_photos[:10], 1):
            initial_data[f'photo_url_{i}'] = url
        form = CarForm(instance=car, initial=initial_data)

    return render(request, 'edit_car.html', {'form': form, 'car': car})

@login_required
def delete_car(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    if request.user != car.user:
        messages.error(request, 'У вас нет прав для удаления этого объявления.')
        return redirect('car_detail', car_id=car_id)

    if request.method == 'POST':
        car.delete()
        messages.success(request, 'Объявление успешно удалено!')
        return redirect('profile')

    return render(request, 'edit_car.html', {'car': car})