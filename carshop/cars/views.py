from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q
from .forms import RegistrationForm, CarForm, UserProfileForm, PurchaseForm, PasswordResetForm, SetPasswordForm
from .models import User, Car, CarPhoto, PurchaseRequest, EmailVerification, PriceHistory
from datetime import timedelta
import json
from django.core.serializers.json import DjangoJSONEncoder

def car_list(request):
    cars = Car.objects.filter(is_sold=False)
    unread_deals_count = 0
    if request.user.is_authenticated:
        buyer_requests = PurchaseRequest.objects.filter(buyer=request.user).order_by('-request_date')
        seller_requests = PurchaseRequest.objects.filter(seller=request.user).order_by('-request_date')
        unread_purchases_count = buyer_requests.filter(is_read=False, status__in=['Одобрено', 'Отклонено']).count()
        unread_sales_count = seller_requests.filter(is_read=False, status='В ожидании').count()
        unread_deals_count = unread_purchases_count + unread_sales_count
    return render(request, 'car_list.html', {'cars': cars, 'unread_deals_count': unread_deals_count})

def car_search(request):
    cars = Car.objects.filter(is_sold=False)
    query = request.GET.get('q', '').strip()
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

    if query:
        search_terms = query.split()
        query_conditions = Q()
        for term in search_terms:
            query_conditions |= Q(brand__icontains=term) | Q(model__icontains=term)
        cars = cars.filter(query_conditions)

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
        cars = cars.filter(color=color)

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

    unread_deals_count = 0
    if request.user.is_authenticated:
        buyer_requests = PurchaseRequest.objects.filter(buyer=request.user).order_by('-request_date')
        seller_requests = PurchaseRequest.objects.filter(seller=request.user).order_by('-request_date')
        unread_purchases_count = buyer_requests.filter(is_read=False, status__in=['Одобрено', 'Отклонено']).count()
        unread_sales_count = seller_requests.filter(is_read=False, status='В ожидании').count()
        unread_deals_count = unread_purchases_count + unread_sales_count

    return render(request, 'car_list.html', {'cars': cars, 'unread_deals_count': unread_deals_count})

def car_detail(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    price_history = PriceHistory.objects.filter(car=car).order_by('change_date')
    price_data = [
        {
            'date': entry.change_date,
            'old_price': float(entry.old_price),
            'new_price': float(entry.new_price),
        }
        for entry in price_history
    ]
    if price_history.exists():
        initial_price = {
            'date': car.created_at,
            'old_price': None,
            'new_price': float(price_history.first().old_price),
        }
        price_data.insert(0, initial_price)
    else:
        price_data = [{
            'date': car.created_at,
            'old_price': None,
            'new_price': float(car.price),
        }]
    price_data_json = json.dumps(price_data, cls=DjangoJSONEncoder)
    return render(request, 'car_detail.html', {
        'car': car,
        'author': car.user,
        'price_data_json': price_data_json,
    })

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
                    messages.success(request, 'Регистрация успешна! Проверьте вашу почту для подтверждения email.')
                except Exception as e:
                    user.delete()
                    messages.error(request, 'Ошибка при отправке email. Пожалуйста, попробуйте снова.')
                    return render(request, 'register.html', {'form': form})
            else:
                messages.success(request, 'Регистрация суперюзера успешна! Вы можете войти.')

            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def verify_email(request, token):
    try:
        verification = EmailVerification.objects.get(token=token, is_used=False, expiration_date__gt=timezone.now())
        user = verification.user
        user.is_verified = True
        user.save()
        verification.is_used = True
        verification.save()
        messages.success(request, 'Ваш email успешно подтвержден! Теперь вы можете войти.')
        return redirect('login')
    except EmailVerification.DoesNotExist:
        messages.error(request, 'Неверный или просроченный токен подтверждения.')
        return redirect('register')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and (user.is_verified or user.is_superuser):
            login(request, user)
            messages.success(request, 'Вы успешно вошли!')
            return redirect('car_list')
        elif user is not None and not user.is_verified:
            messages.error(request, 'Ваш email не подтвержден. Проверьте почту.')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'Вы успешно вышли из аккаунта.')
    return redirect('login')

@login_required
def create_car(request):
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES)
        if form.is_valid():
            car = form.save(commit=False)
            car.user = request.user
            car.save()
            photo_urls = form.cleaned_data['photo_urls_list']
            photo_files = form.cleaned_data['photo_files_list']
            for url in photo_urls:
                if url:
                    CarPhoto.objects.create(car=car, photo_url=url)
            for photo_file in photo_files:
                if photo_file:
                    CarPhoto.objects.create(car=car, photo_file=photo_file)
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
    buyer_requests.filter(is_read=False, status__in=['Одобрено', 'Отклонено']).update(is_read=True)
    seller_requests.filter(is_read=False, status='В ожидании').update(is_read=True)
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
def reset_notifications(request):
    if request.method == 'POST':
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
            purchase_request.is_read = False
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
        purchase.is_read = False
        purchase.save()
        messages.success(request, f'Заявка одобрена. Автомобиль продан за {purchase.final_price} ₽.')
    elif action == 'reject':
        purchase.status = 'Отклонено'
        purchase.is_read = False
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
            password = form.cleaned_data.get('password')
            if password:
                user.set_password(password)
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
        old_price = car.price
        form = CarForm(request.POST, request.FILES, instance=car)
        if form.is_valid():
            car = form.save(commit=False)
            new_price = car.price
            car.user = request.user
            car.save()
            if old_price != new_price:
                PriceHistory.objects.create(
                    car=car,
                    old_price=old_price,
                    new_price=new_price,
                    changed_by_user=request.user
                )
            # Обработка удаления фотографий
            delete_photo_ids = request.POST.getlist('delete_photos')
            if delete_photo_ids:
                CarPhoto.objects.filter(id__in=delete_photo_ids).delete()
            # Сохранение существующих и новых фото
            existing_photos = car.carphoto_set.all()
            photo_urls = form.cleaned_data['photo_urls_list']
            photo_files = form.cleaned_data['photo_files_list']
            for url in photo_urls:
                if url and not existing_photos.filter(photo_url=url).exists():
                    CarPhoto.objects.create(car=car, photo_url=url)
            for photo_file in photo_files:
                if photo_file and not existing_photos.filter(photo_file=photo_file).exists():
                    CarPhoto.objects.create(car=car, photo_file=photo_file)
            messages.success(request, 'Объявление успешно обновлено!')
            return redirect('car_detail', car_id=car_id)
    else:
        initial_data = {}
        existing_photos = car.carphoto_set.all()
        for i, photo in enumerate(existing_photos[:10], 1):
            if photo.photo_url:
                initial_data[f'photo_url_{i}'] = photo.photo_url
            # Для ImageField начальные значения не устанавливаются напрямую
        form = CarForm(instance=car, initial=initial_data)
    return render(request, 'edit_car.html', {'form': form, 'car': car, 'existing_photos': existing_photos})

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
                messages.success(request, 'Пароль успешно изменен. Теперь вы можете войти.')
                return redirect('login')
        else:
            form = SetPasswordForm()
        return render(request, 'password_reset_confirm.html', {'form': form})
    except EmailVerification.DoesNotExist:
        messages.error(request, 'Неверный или просроченный токен.')
        return redirect('password_reset_request')