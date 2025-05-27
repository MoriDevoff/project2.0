from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.core.cache import cache
from .forms import RegistrationForm, CarForm, UserProfileForm, PurchaseForm, PasswordResetForm, SetPasswordForm, ManageBalanceForm, ManageUserForm, CarSpecificationForm
from .models import User, Car, CarPhoto, PurchaseRequest, EmailVerification, PriceHistory, Favorite, CarSpecification
from datetime import timedelta
import json
import logging
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

logger = logging.getLogger(__name__)

def get_unread_deals_count(user):
    """Вспомогательная функция для подсчёта непрочитанных уведомлений."""
    if not user.is_authenticated:
        return 0
    buyer_requests = PurchaseRequest.objects.filter(buyer=user).order_by('-request_date')
    seller_requests = PurchaseRequest.objects.filter(seller=user).order_by('-request_date')
    unread_purchases_count = buyer_requests.filter(is_read=False, status__in=['Одобрено', 'Отклонено']).count()
    unread_sales_count = seller_requests.filter(is_read=False, status='В ожидании').count()
    return unread_purchases_count + unread_sales_count

def car_list(request):
    cars = Car.objects.filter(is_sold=False).annotate(favorite_count=Count('favorites'))
    if request.user.is_authenticated:
        for car in cars:
            car.is_favorited = Favorite.objects.filter(car=car, user=request.user).exists()
    else:
        for car in cars:
            car.is_favorited = False
    unread_deals_count = get_unread_deals_count(request.user) if request.user.is_authenticated else 0
    return render(request, 'car_list.html', {
        'cars': cars,
        'unread_deals_count': unread_deals_count
    })

def car_search(request):
    cars = Car.objects.filter(is_sold=False).annotate(favorite_count=Count('favorites'))
    query = request.GET.get('q', '').strip()
    year = request.GET.get('year')
    condition = request.GET.get('condition')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    mileage_min = request.GET.get('mileage_min')
    mileage_max = request.GET.get('mileage_max')
    fuel_type = request.GET.get('fuel_type')
    transmission = request.GET.get('transmission')
    color = request.GET.get('color')
    engine_capacity_min = request.GET.get('engine_capacity_min')
    engine_capacity_max = request.GET.get('engine_capacity_max')
    body_type = request.GET.get('body_type')
    power_min = request.GET.get('power_min')
    power_max = request.GET.get('power_max')
    drive_type = request.GET.get('drive_type')
    weight_min = request.GET.get('weight_min')
    weight_max = request.GET.get('weight_max')
    country_of_origin = request.GET.get('country_of_origin')
    vin = request.GET.get('vin')

    if query:
        search_terms = query.split()
        query_conditions = Q()
        for term in search_terms:
            query_conditions |= Q(brand__icontains=term) | Q(model__icontains=term)
        cars = cars.filter(query_conditions)

    if year:
        cars = cars.filter(year__icontains=year)
    if condition and condition != "":
        cars = cars.filter(condition=condition)
    if price_min:
        try:
            cars = cars.filter(price__gte=float(price_min))
        except (ValueError, TypeError):
            pass
    if price_max:
        try:
            cars = cars.filter(price__lte=float(price_max))
        except (ValueError, TypeError):
            pass
    if mileage_min:
        try:
            cars = cars.filter(mileage__gte=int(mileage_min))
        except (ValueError, TypeError):
            pass
    if mileage_max:
        try:
            cars = cars.filter(mileage__lte=int(mileage_max))
        except (ValueError, TypeError):
            pass
    if fuel_type and fuel_type != "":
        cars = cars.filter(fuel_type=fuel_type)
    if transmission and transmission != "":
        cars = cars.filter(transmission=transmission)
    if color and color != "":
        cars = cars.filter(color__icontains=color)
    if engine_capacity_min:
        try:
            cars = cars.filter(engine_capacity__gte=float(engine_capacity_min))
        except (ValueError, TypeError):
            pass
    if engine_capacity_max:
        try:
            cars = cars.filter(engine_capacity__lte=float(engine_capacity_max))
        except (ValueError, TypeError):
            pass
    # CarSpecification фильтры
    if body_type and body_type != "":
        cars = cars.filter(carspecification__body_type=body_type)
    if power_min:
        try:
            cars = cars.filter(carspecification__power__gte=int(power_min))
        except (ValueError, TypeError):
            pass
    if power_max:
        try:
            cars = cars.filter(carspecification__power__lte=int(power_max))
        except (ValueError, TypeError):
            pass
    if drive_type and drive_type != "":
        cars = cars.filter(carspecification__drive_type=drive_type)
    if weight_min:
        try:
            cars = cars.filter(carspecification__weight__gte=int(weight_min))
        except (ValueError, TypeError):
            pass
    if weight_max:
        try:
            cars = cars.filter(carspecification__weight__lte=int(weight_max))
        except (ValueError, TypeError):
            pass
    if country_of_origin and country_of_origin != "":
        cars = cars.filter(carspecification__country_of_origin__icontains=country_of_origin)
    if vin and vin != "":
        cars = cars.filter(carspecification__vin__icontains=vin)

    unread_deals_count = get_unread_deals_count(request.user)

    for car in cars:
        car.is_favorited = request.user.is_authenticated and Favorite.objects.filter(car=car, user=request.user).exists()

    return render(request, 'car_list.html', {
        'cars': cars,
        'unread_deals_count': unread_deals_count
    })

def car_detail(request, car_id):
    car = get_object_or_404(
        Car.objects.annotate(favorite_count=Count('favorites')),
        id=car_id
    )
    if request.user.is_authenticated:
        car.is_favorited = Favorite.objects.filter(car=car, user=request.user).exists()
    else:
        car.is_favorited = False

    # Кэширование фото
    cache_key_photos = f'car_photos_{car_id}'
    cached_photos = cache.get(cache_key_photos)
    if cached_photos is None:
        photos = list(car.carphoto_set.all())
        cache.set(cache_key_photos, photos, timeout=3600)  # Кэш на 1 час
    else:
        photos = cached_photos

    # Кэширование характеристик
    cache_key_spec = f'car_specification_{car_id}'
    cached_spec = cache.get(cache_key_spec)
    if cached_spec is None:
        try:
            spec = car.carspecification
            cache.set(cache_key_spec, spec, timeout=3600)  # Кэш на 1 час
        except CarSpecification.DoesNotExist:
            spec = None
    else:
        spec = cached_spec

    price_history = PriceHistory.objects.filter(car=car).order_by('change_date')
    price_data = [
        {
            'date': entry.change_date.isoformat(),
            'old_price': float(entry.old_price),
            'new_price': float(entry.new_price),
        }
        for entry in price_history
    ]
    if price_history.exists():
        initial_price = {
            'date': car.created_at.isoformat(),
            'old_price': None,
            'new_price': float(price_history.first().old_price),
        }
        price_data.insert(0, initial_price)
    else:
        price_data = [{
            'date': car.created_at.isoformat(),
            'old_price': None,
            'new_price': float(car.price),
        }]
    price_data_json = json.dumps(price_data)

    unread_deals_count = get_unread_deals_count(request.user) if request.user.is_authenticated else 0
    current_timestamp = int(timezone.now().timestamp())

    return render(request, 'car_detail.html', {
        'car': car,
        'author': car.user,
        'photos': photos,
        'spec': spec,
        'price_data_json': price_data_json,
        'unread_deals_count': unread_deals_count,
        'current_timestamp': current_timestamp
    })

@never_cache
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.date_joined = timezone.now()
            user.avatar_url = 'https://avatars.mds.yandex.net/i?id=e54ae3f787cf29aa21be07d6762ecc0dfaa02fa2-5014002-images-thumbs&n=13'
            user.save()
            if not user.is_superuser:
                expiration_date = timezone.now() + timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS)
                verification = EmailVerification.objects.create(
                    user=user,
                    expiration_date=expiration_date
                )
                verification_link = request.build_absolute_uri(reverse('verify_email', args=[str(verification.token)]))
                subject = 'Подтверждение регистрации'
                message = f'Спасибо за регистрацию! Пожалуйста, подтвердите ваш email, перейдя по ссылке: {verification_link}'
                from_email = settings.DEFAULT_FROM_EMAIL
                try:
                    send_mail(subject, message, from_email, [user.email], fail_silently=False)
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': True, 'message': 'Регистрация успешна! Проверьте вашу почту для подтверждения email.', 'redirect': reverse('login') + '?verify_email=1'})
                    messages.success(request, 'Регистрация успешна! Проверьте вашу почту для подтверждения email.')
                except Exception as e:
                    user.delete()
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': 'Ошибка при отправке email. Пожалуйста, попробуйте снова.'}, status=500)
                    messages.error(request, 'Ошибка при отправке email. Пожалуйста, попробуйте снова.')
                    return render(request, 'register.html', {'form': form})
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': 'Регистрация суперюзера успешна! Вы можете войти.', 'redirect': reverse('login')})
                messages.success(request, 'Регистрация суперюзера успешна! Вы можете войти.')

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'redirect': reverse('login')})
            return redirect(reverse('login') + '?verify_email=1')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': form.errors.as_json()}, status=400)
            return render(request, 'register.html', {'form': form})
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

@never_cache
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if not user.is_active:
                return redirect('blocked', block_reason=user.block_reason or "Не указана")
            if not user.is_verified and not user.is_superuser:
                messages.error(request, 'Ваш email не подтвержден. Проверьте почту.')
                return render(request, 'login.html')
            login(request, user)
            messages.success(request, 'Вы успешно вошли!')
            return redirect(reverse('car_list'))
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')
    return render(request, 'login.html')

@never_cache
def blocked(request, block_reason=None):
    if not request.user.is_authenticated or request.user.is_active:
        return redirect('car_list')
    return render(request, 'blocked.html', {'block_reason': block_reason})

@never_cache
def logout_view(request):
    if request.user.is_authenticated:
        logger.info(f"Logging out user: {request.user.username}")
        logout(request)
        request.session.flush()  # Очищает сессию
        response = redirect('car_list')
        response.delete_cookie('sessionid')  # Удаляем куку сессии
        messages.success(request, 'Вы успешно вышли из системы!')
        return response
    else:
        logger.info("No user authenticated during logout")
        return redirect('car_list')

@login_required
@never_cache
def create_car(request):
    photo_range = range(1, 11)
    photo_url_fields = [f'photo_url_{i}' for i in photo_range]
    photo_file_fields = [f'photo_file_{i}' for i in photo_range]
    form = CarForm()
    spec_form = CarSpecificationForm()
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES)
        spec_form = CarSpecificationForm(request.POST)
        if form.is_valid() and spec_form.is_valid():
            with transaction.atomic():
                car = form.save(commit=False)
                car.user = request.user
                car.save()

                spec = spec_form.save(commit=False)
                spec.car = car
                spec.clean()  # Проверка VIN
                spec.save()

                photo_files = form.cleaned_data.get('photo_files_list', [])
                for photo in photo_files:
                    CarPhoto.objects.create(car=car, photo_file=photo)

                photo_urls = form.cleaned_data.get('photo_urls_list', [])
                for url in photo_urls:
                    CarPhoto.objects.create(car=car, photo_url=url)

            # Инвалидация кэша фото и характеристик после создания
            cache.delete(f'car_photos_{car.id}')
            cache.delete(f'car_specification_{car.id}')

            messages.success(request, 'Автомобиль успешно добавлен!')
            return redirect('car_list')
        else:
            messages.error(request, 'Ошибка при создании объявления. Проверьте введенные данные.')
            for error in form.errors.values():
                messages.error(request, error)
            for error in spec_form.errors.values():
                messages.error(request, error)
    else:
        form = CarForm()
        spec_form = CarSpecificationForm()

    delete_photo_fields = [name for name in form.fields if name.startswith('delete_photo_')]
    main_fields = [
        name for name in form.fields
        if name not in photo_url_fields + photo_file_fields + delete_photo_fields + ['photo_files_list', 'photo_urls_list']
    ]

    unread_deals_count = get_unread_deals_count(request.user)

    return render(request, 'create_car.html', {
        'form': form,
        'spec_form': spec_form,
        'main_fields': main_fields,
        'photo_url_fields': photo_url_fields,
        'photo_file_fields': photo_file_fields,
        'unread_deals_count': unread_deals_count
    })

@login_required
@never_cache
def profile(request):
    user_cars = Car.objects.filter(user=request.user, is_sold=False)
    buyer_requests = PurchaseRequest.objects.filter(buyer=request.user).order_by('-request_date')
    seller_requests = PurchaseRequest.objects.filter(seller=request.user).order_by('-request_date')
    unread_purchases_count = buyer_requests.filter(is_read=False, status__in=['Одобрено', 'Отклонено']).count()
    unread_sales_count = seller_requests.filter(is_read=False, status='В ожидании').count()
    has_new_notifications = (unread_purchases_count > 0 or unread_sales_count > 0)
    unread_deals_count = unread_purchases_count + unread_sales_count

    # Кэширование данных профиля
    cache_key_profile = f'profile_{request.user.id}'
    cached_data = cache.get(cache_key_profile)
    if cached_data is None:
        profile_data = {
            'user_cars': user_cars,
            'buyer_requests': buyer_requests,
            'seller_requests': seller_requests,
            'unread_deals_count': unread_deals_count,
            'has_new_notifications': has_new_notifications,
        }
        cache.set(cache_key_profile, profile_data, timeout=3600)  # Кэш на 1 час
    else:
        profile_data = cached_data

    return render(request, 'profile.html', {
        'user': request.user,
        'user_cars': profile_data['user_cars'],
        'buyer_requests': profile_data['buyer_requests'],
        'seller_requests': profile_data['seller_requests'],
        'unread_deals_count': profile_data['unread_deals_count'],
        'unread_purchases_count': unread_purchases_count,
        'unread_sales_count': unread_sales_count,
        'has_new_notifications': profile_data['has_new_notifications'],
    })

@login_required
@never_cache
def purchases(request):
    buyer_requests = PurchaseRequest.objects.filter(buyer=request.user).order_by('-request_date')
    seller_requests = PurchaseRequest.objects.filter(seller=request.user).order_by('-request_date')
    buyer_requests.filter(is_read=False, status__in=['Одобрено', 'Отклонено']).update(is_read=True)
    seller_requests.filter(is_read=False, status='В ожидании').update(is_read=True)
    # Инвалидация кэша профиля после обновления уведомлений
    cache.delete(f'profile_{request.user.id}')

    unread_purchases_count = buyer_requests.filter(is_read=False, status__in=['Одобрено', 'Отклонено']).count()
    unread_sales_count = seller_requests.filter(is_read=False, status='В ожидании').count()
    has_new_notifications = (unread_purchases_count > 0 or unread_sales_count > 0)
    unread_deals_count = unread_purchases_count + unread_sales_count
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
@never_cache
def reset_notifications(request):
    if request.method == 'POST':
        PurchaseRequest.objects.filter(buyer=request.user, is_read=False, status__in=['Одобрено', 'Отклонено']).update(is_read=True)
        PurchaseRequest.objects.filter(seller=request.user, is_read=False, status='В ожидании').update(is_read=True)
        # Инвалидация кэша профиля после сброса уведомлений
        cache.delete(f'profile_{request.user.id}')
        messages.success(request, 'Все уведомления сброшены.')
        return redirect('profile')
    return redirect('profile')

@login_required
@never_cache
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
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        form = PurchaseForm(request.POST)
        if form.is_valid():
            offered_price = form.cleaned_data.get('offered_price') or car.price
            if request.user.balance < offered_price:
                return JsonResponse({'status': 'error', 'message': 'Недостаточно средств на балансе для покупки.'}, status=400)
            purchase_request = form.save(commit=False)
            purchase_request.car = car
            purchase_request.buyer = request.user
            purchase_request.seller = car.user
            purchase_request.is_read = False
            purchase_request.save()
            # Сброс кэша профиля для покупателя и продавца
            cache.delete(f'profile_{request.user.id}')
            cache.delete(f'profile_{car.user.id}')
            messages.success(request, 'Заявка на покупку отправлена продавцу!')
            return JsonResponse({'status': 'success', 'message': 'Заявка на покупку отправлена!'})
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    else:
        form = PurchaseForm(initial={'offered_price': car.price})

    unread_deals_count = get_unread_deals_count(request.user)

    return render(request, 'purchase_car.html', {
        'form': form,
        'car': car,
        'unread_deals_count': unread_deals_count
    })

@login_required
@never_cache
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
        purchase.is_read = False
        purchase.save()
        # Инвалидация кэша фото и характеристик после продажи
        cache.delete(f'car_photos_{purchase.car.id}')
        cache.delete(f'car_specification_{purchase.car.id}')
        # Сброс кэша профиля для покупателя и продавца
        cache.delete(f'profile_{purchase.buyer.id}')
        cache.delete(f'profile_{purchase.seller.id}')
        messages.success(request, f'Заявка одобрена. Автомобиль продан за {purchase.final_price} ₽.')
    elif action == 'reject':
        purchase.status = 'Отклонено'
        purchase.is_read = False
        purchase.save()
        # Сброс кэша профиля для покупателя и продавца
        cache.delete(f'profile_{purchase.buyer.id}')
        cache.delete(f'profile_{purchase.seller.id}')
        messages.success(request, 'Заявка отклонена.')
    else:
        messages.error(request, 'Недопустимое действие.')
        return redirect('profile')
    return redirect('profile')

@login_required
@never_cache
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            if not user.date_joined:
                user.date_joined = timezone.now()
            password = form.cleaned_data.get('password')
            if password:
                user.set_password(password)
            user.save()
            update_session_auth_hash(request, user)
            # Инвалидация кэша профиля после редактирования
            cache.delete(f'profile_{request.user.id}')
            messages.success(request, 'Профиль успешно обновлён!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)

    unread_deals_count = get_unread_deals_count(request.user)

    return render(request, 'edit_profile.html', {
        'form': form,
        'unread_deals_count': unread_deals_count
    })

@login_required
@never_cache
def edit_car(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    if car.user != request.user:
        return redirect('car_detail', car_id=car.id)

    try:
        spec = car.carspecification
    except CarSpecification.DoesNotExist:
        spec = None

    photo_range = range(1, 11)
    photo_url_fields = [f'photo_url_{i}' for i in photo_range]
    photo_file_fields = [f'photo_file_{i}' for i in photo_range]

    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES, instance=car)
        spec_form = CarSpecificationForm(request.POST, instance=spec)
        if form.is_valid() and spec_form.is_valid():
            with transaction.atomic():
                old_price = car.price
                car = form.save()
                if old_price != car.price:
                    PriceHistory.objects.create(
                        car=car,
                        old_price=old_price,
                        new_price=car.price,
                        change_date=timezone.now(),
                        changed_by_user=request.user
                    )
                spec = spec_form.save(commit=False)
                spec.car = car
                spec.clean()  # Проверка VIN
                spec.save()

                for key in form.cleaned_data:
                    if key.startswith('delete_photo_') and form.cleaned_data[key]:
                        photo_id = key.replace('delete_photo_', '')
                        CarPhoto.objects.filter(id=photo_id, car=car).delete()

                existing_photos = CarPhoto.objects.filter(car=car, photo_url__isnull=False)
                existing_urls = set(photo.photo_url for photo in existing_photos)
                photo_urls = form.cleaned_data.get('photo_urls_list', [])
                for url in photo_urls:
                    if url and url not in existing_urls:
                        CarPhoto.objects.create(car=car, photo_url=url)
                        existing_urls.add(url)

                photo_files = form.cleaned_data.get('photo_files_list', [])
                for photo_file in photo_files:
                    CarPhoto.objects.create(car=car, photo_file=photo_file)

            # Инвалидация кэша фото и характеристик после редактирования
            cache.delete(f'car_photos_{car.id}')
            cache.delete(f'car_specification_{car.id}')

            messages.success(request, 'Объявление успешно обновлено!')
            return redirect('car_detail', car_id=car.id)
        else:
            messages.error(request, 'Ошибка при редактировании объявления. Проверьте введенные данные.')
    else:
        initial_data = {}
        existing_photos = CarPhoto.objects.filter(car=car, photo_url__isnull=False)
        for i, photo in enumerate(existing_photos, 1):
            if i <= 10:
                initial_data[f'photo_url_{i}'] = photo.photo_url

        form = CarForm(instance=car, initial=initial_data)
        spec_form = CarSpecificationForm(instance=spec)

    unread_deals_count = get_unread_deals_count(request.user)

    return render(request, 'edit_car.html', {
        'form': form,
        'spec_form': spec_form,
        'car': car,
        'photo_url_fields': photo_url_fields,
        'photo_file_fields': photo_file_fields,
        'unread_deals_count': unread_deals_count
    })

@csrf_exempt
@login_required
@never_cache
def delete_car(request, car_id):
    if request.method != 'POST' and not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Метод не разрешён'}, status=405)
    try:
        logger.info(f"Попытка удаления объявления {car_id} пользователем {request.user}")
        car = get_object_or_404(Car, id=car_id)
        if request.user != car.user:
            logger.warning(f"Пользователь {request.user} попытался удалить чужое объявление {car_id}")
            return JsonResponse({'success': False, 'error': 'У вас нет прав для удаления этого объявления'}, status=403)

        car.delete()
        # Инвалидация кэша фото и характеристик после удаления
        cache.delete(f'car_photos_{car_id}')
        cache.delete(f'car_specification_{car_id}')
        logger.info(f"Объявление {car_id} успешно удалено пользователем {request.user}")
        return JsonResponse({'success': True})

    except Car.DoesNotExist:
        logger.error(f"Объявление с id {car_id} не найдено")
        return JsonResponse({'success': False, 'error': 'Объявление не найдено'}, status=404)
    except Exception as e:
        logger.error(f"Ошибка при удалении объявления {car_id}: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Внутренняя ошибка сервера'}, status=500)

@never_cache
def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                expiration_date = timezone.now() + timedelta(hours=1)
                verification = EmailVerification.objects.create(
                    user=user,
                    expiration_date=expiration_date,
                    is_used=False
                )
                reset_link = request.build_absolute_uri(reverse('password_reset_confirm', args=[str(verification.token)]))
                subject = 'Сброс пароля'
                message = f'Перейдите по ссылке для сброса пароля: {reset_link}'
                from_email = settings.DEFAULT_FROM_EMAIL
                try:
                    send_mail(subject, message, from_email, [user.email], fail_silently=False)
                    messages.success(request, 'Ссылка для сброса пароля отправлена на ваш email.')
                    return redirect('login')
                except Exception as e:
                    messages.error(request, 'Ошибка при отправке email. Пожалуйста, попробуйте снова.')
                    return render(request, 'password_reset_request.html', {'form': form})
            except User.DoesNotExist:
                messages.error(request, 'Пользователь с таким email не найден.')
    else:
        form = PasswordResetForm()
    return render(request, 'password_reset_request.html', {'form': form})

@never_cache
def password_reset_confirm(request, token):
    try:
        verification = EmailVerification.objects.get(token=token, is_used=False, expiration_date__gt=timezone.now())
        if request.method == 'POST':
            form = SetPasswordForm(request.POST)
            if form.is_valid():
                user = verification.user
                user.set_password(form.cleaned_data['password'])
                user.save()
                verification.is_used = True
                verification.save()
                # Инвалидация кэша профиля после смены пароля
                cache.delete(f'profile_{user.id}')
                messages.success(request, 'Пароль успешно изменен. Теперь вы можете войти.')
                return redirect('login')
        else:
            form = SetPasswordForm()
        return render(request, 'password_reset_confirm.html', {'form': form})
    except EmailVerification.DoesNotExist:
        messages.error(request, 'Неверный или просроченный токен.')
        return redirect('password_reset_request')

@csrf_exempt
@login_required
@never_cache
def toggle_favorite(request, car_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Метод не разрешён'}, status=405)

    car = get_object_or_404(Car, id=car_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, car=car)

    if not created:
        favorite.delete()
        status = 'removed'
    else:
        status = 'added'

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': status, 'favorite_count': car.favorites.count()})
    else:
        messages.success(request, 'Объявление добавлено в избранное.' if created else 'Объявление удалено из избранного.')
        return redirect('car_detail', car_id=car.id)

@login_required
def favorite_list(request):
    favorites = Favorite.objects.filter(user=request.user).order_by('-added_date')
    unread_deals_count = get_unread_deals_count(request.user)
    return render(request, 'favorite_list.html', {
        'favorites': favorites,
        'unread_deals_count': unread_deals_count
    })

@login_required
@never_cache
def manage_users(request):
    if not request.user.is_superuser:
        messages.error(request, 'У вас нет прав для доступа к этой странице.')
        return redirect('car_list')
    users = User.objects.all()
    if request.method == 'POST':
        form = ManageUserForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            action = form.cleaned_data['action']
            if user == request.user:
                messages.error(request, 'Вы не можете выполнить это действие над самим собой.')
                return render(request, 'manage_users.html', {'users': users, 'form': form})
            if action == 'block':
                reason = form.cleaned_data['block_reason']
                if not reason:
                    messages.error(request, 'Укажите причину блокировки.')
                    return render(request, 'manage_users.html', {'users': users, 'form': form})
                user.is_active = False
                user.block_reason = reason
                user.save()
            elif action == 'unblock':
                user.is_active = True
                user.block_reason = ''
                user.save()
            elif action == 'delete':
                user_id = user.id
                user.delete()
                messages.success(request, f'Пользователь {user.username} удалён')
            return redirect('manage_users')
    else:
        form = ManageUserForm()

    unread_deals_count = get_unread_deals_count(request.user)

    return render(request, 'manage_users.html', {
        'users': users,
        'form': form,
        'unread_deals_count': unread_deals_count
    })

@login_required
@never_cache
def manage_ads(request):
    if not request.user.is_superuser:
        messages.error(request, 'У вас нет прав для доступа к этой странице.')
        return redirect('car_list')
    cars = Car.objects.all()
    if request.method == 'POST':
        author_filter = request.POST.get('author_filter', '')
        if author_filter:
            cars = cars.filter(user__username__icontains=author_filter)
        car_id = request.POST.get('car_id')
        action = request.POST.get('action')
        if car_id and action:
            car = get_object_or_404(Car, id=car_id)
            if action == 'edit':
                form = CarForm(request.POST, request.FILES, instance=car)
                if form.is_valid():
                    form.save()
                    # Инвалидация кэша фото и характеристик после редактирования
                    cache.delete(f'car_photos_{car.id}')
                    cache.delete(f'car_specification_{car.id}')
                    messages.success(request, f'Объявление {car.brand} {car.model} обновлено')
                    return redirect('manage_ads')
            elif action == 'delete':
                car_id = car.id
                car.delete()
                # Инвалидация кэша фото и характеристик после удаления
                cache.delete(f'car_photos_{car_id}')
                cache.delete(f'car_specification_{car_id}')
                messages.success(request, f'Объявление {car.brand} {car.model} удалено')
    unread_deals_count = get_unread_deals_count(request.user)
    return render(request, 'manage_ads.html', {
        'cars': cars,
        'unread_deals_count': unread_deals_count
    })

@login_required
@never_cache
def manage_balances(request):
    if not request.user.is_superuser:
        messages.error(request, 'У вас нет прав для доступа к этой странице.')
        return redirect('car_list')
    users = User.objects.all()
    if request.method == 'POST':
        form = ManageBalanceForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            amount = form.cleaned_data['amount']
            action = form.cleaned_data['action']
            if amount <= 0:
                messages.error(request, 'Сумма должна быть больше 0.')
                return render(request, 'manage_balances.html', {'users': users, 'form': form})
            if action == 'add':
                user.balance += amount
                messages.success(request, f'Баланс пользователя {user.username} увеличен на {amount} ₽')
            elif action == 'subtract':
                if user.balance >= amount:
                    user.balance -= amount
                    messages.success(request, f'Баланс пользователя {user.username} уменьшен на {amount} ₽')
                else:
                    messages.error(request, 'Недостаточно средств для списания')
                    return render(request, 'manage_balances.html', {'users': users, 'form': form})
            user.save()
            # Инвалидация кэша профиля после изменения баланса
            cache.delete(f'profile_{user.id}')
            return redirect('manage_balances')
    else:
        form = ManageBalanceForm()

    unread_deals_count = get_unread_deals_count(request.user)

    return render(request, 'manage_balances.html', {
        'users': users,
        'form': form,
        'unread_deals_count': unread_deals_count
    })

@require_POST
@never_cache
def check_email_availability(request):
    email = request.POST.get('email', '').strip()
    exists = User.objects.filter(email=email).exists()
    return JsonResponse({'exists': exists, 'email': email})

@never_cache
def verify_email(request, token):
    try:
        verification = EmailVerification.objects.get(token=token, is_used=False, expiration_date__gt=timezone.now())
        user = verification.user
        user.is_verified = True
        user.save()
        verification.is_used = True
        verification.save()
        # Инвалидация кэша профиля после подтверждения email
        cache.delete(f'profile_{user.id}')
        messages.success(request, 'Ваш email успешно подтвержден! Теперь вы можете войти.')
        return redirect('login')
    except EmailVerification.DoesNotExist:
        messages.error(request, 'Неверный или просроченный токен подтверждения.')
        return redirect('register')