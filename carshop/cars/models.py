from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils.translation import gettext_lazy as _

import uuid

class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password, phone=None, **extra_fields):
        if not username:
            raise ValueError(_('The username must be set'))
        if not email:
            raise ValueError(_('The email must be set'))
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.balance = 0
        user.is_verified = extra_fields.get('is_superuser', False)
        user.save()
        return user
    pass

    def create_superuser(self, username, email, password, phone=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        if extra_fields.get('is_active') is not True:
            raise ValueError(_('Superuser must have is_active=True.'))

        return self.create_user(username, email, password, phone, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    company_name = models.CharField(max_length=100, blank=True)
    date_joined = models.DateTimeField(default=timezone.now)
    avatar_url = models.URLField(blank=True, null=True)
    avatar_file = models.ImageField(upload_to='avatars/', blank=True, null=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    block_reason = models.TextField(blank=True, null=True)  # New field for block reason

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

    def get_avatar(self):
        return self.avatar_file.url if self.avatar_file else (self.avatar_url or 'https://avatars.mds.yandex.net/i?id=e54ae3f787cf29aa21be07d6762ecc0dfaa02fa2-5014002-images-thumbs&n=13')

    class Meta:
        db_table = 'Users'

class Car(models.Model):
    FUEL_TYPE_CHOICES = [
        ('Бензин', 'Бензин'),
        ('Дизель', 'Дизель'),
        ('Электрическая', 'Электрическая'),
        ('Гибрид', 'Гибрид'),
        ('Газ', 'Газ'),
    ]

    TRANSMISSION_CHOICES = [
        ('Механическая', 'Механическая'),
        ('Автоматическая', 'Автоматическая'),
        ('Робот', 'Робот'),
        ('Вариатор', 'Вариатор'),
    ]

    CONDITION_CHOICES = [
        ('new', 'Новый'),
        ('used', 'Б/у'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    mileage = models.PositiveIntegerField()
    engine_capacity = models.DecimalField(max_digits=4, decimal_places=1)
    fuel_type = models.CharField(max_length=50, choices=FUEL_TYPE_CHOICES)
    transmission = models.CharField(max_length=50, choices=TRANSMISSION_CHOICES)
    color = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    is_sold = models.BooleanField(default=False)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='used')

    def __str__(self):
        return f"{self.brand} {self.model} ({self.year})"

    def get_first_photo(self):
        first_photo = self.carphoto_set.first()
        return first_photo.get_photo() if first_photo else '/media/car_photos/default-car.jpg'

class CarPhoto(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='carphoto_set')
    photo_url = models.URLField(max_length=200, blank=True, null=True)
    photo_file = models.ImageField(upload_to='car_photos/', blank=True, null=True)

    def __str__(self):
        return f"Photo for {self.car}"

    def get_photo(self):
        return self.photo_file.url if self.photo_file else (self.photo_url if self.photo_url else '/media/car_photos/default-car.jpg')

class CarSpecification(models.Model):
    BODY_TYPE_CHOICES = [
        ('Седан', 'Седан'),
        ('Хетчбек', 'Хетчбек'),
        ('SUV', 'SUV'),
        ('Купе', 'Купе'),
        ('Кабриолет', 'Кабриолет'),
        ('Минивэн', 'Минивэн'),
        ('Пикап', 'Пикап'),
    ]

    DRIVE_TYPE_CHOICES = [
        ('Передний', 'Передний'),
        ('Задний', 'Задний'),
        ('4WD', '4WD'),
        ('AWD', 'AWD'),
    ]

    car = models.OneToOneField(Car, on_delete=models.CASCADE)
    body_type = models.CharField(max_length=20, choices=BODY_TYPE_CHOICES)
    doors = models.IntegerField(validators=[MinValueValidator(2), MaxValueValidator(6)])
    seats = models.IntegerField(validators=[MinValueValidator(2), MaxValueValidator(9)])
    power = models.IntegerField(validators=[MinValueValidator(1)])
    drive_type = models.CharField(max_length=10, choices=DRIVE_TYPE_CHOICES)
    vin = models.CharField(max_length=17, unique=True)
    weight = models.IntegerField(validators=[MinValueValidator(1)])
    country_of_origin = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = 'CarSpecifications'

    def clean(self):
        if self.vin and len(self.vin) != 17:
            raise ValidationError({'vin': 'VIN должен содержать ровно 17 символов.'})

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='favorites')  # Добавляем related_name
    added_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Favorites'
        unique_together = ('user', 'car')

class PurchaseRequest(models.Model):
    STATUS_CHOICES = [
        ('В ожидании', 'В ожидании'),
        ('Одобрено', 'Одобрено'),
        ('Отклонено', 'Отклонено'),
    ]

    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buyer_requests')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_requests')
    offered_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    final_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    message = models.TextField(blank=True)
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='В ожидании', choices=STATUS_CHOICES)
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = 'PurchaseRequests'

    def save(self, *args, **kwargs):
        if self.status == 'Одобрено' and self.final_price:
            self.buyer.balance -= self.final_price
            self.seller.balance += self.final_price
            self.buyer.save()
            self.seller.save()
        super().save(*args, **kwargs)

class PriceHistory(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    old_price = models.DecimalField(max_digits=12, decimal_places=2)
    new_price = models.DecimalField(max_digits=12, decimal_places=2)
    change_date = models.DateTimeField(auto_now_add=True)
    changed_by_user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = 'PriceHistory'

class EmailVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"Verification for {self.user.username}"

class ChatRequest(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_chat_requests')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_chat_requests')
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('accepted', 'Accepted')], default='pending')
    timestamp = models.DateTimeField(auto_now_add=True)  # Убедитесь, что это поле существует

    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username} ({self.status})"

class Message(models.Model):
    chat_request = models.ForeignKey(ChatRequest, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Messages'

class Chat(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    car = models.ForeignKey('Car', on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.sender.username} to {self.receiver.username}: {self.message[:20]}'