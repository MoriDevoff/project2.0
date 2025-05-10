from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password, phone=None, **extra_fields):
        if not username:
            raise ValueError(_('The username must be set'))
        if not email:
            raise ValueError(_('The email must be set'))
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save()
        return user

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
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    is_dealer = models.BooleanField(default=False)
    company_name = models.CharField(max_length=100, blank=True)
    avatar_url = models.URLField(blank=True)
    is_staff = models.BooleanField(default=False)  # Добавлено
    is_active = models.BooleanField(default=True)  # Добавлено

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'Users'

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

STATUS_CHOICES = [
    ('В ожидании', 'В ожидании'),
    ('Принято', 'Принято'),
    ('Отклонено', 'Отклонено'),
    ('Завершено', 'Завершено'),
]

class Car(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    mileage = models.PositiveIntegerField()
    engine_capacity = models.DecimalField(max_digits=4, decimal_places=1)
    fuel_type = models.CharField(max_length=50, choices=FUEL_TYPE_CHOICES)
    transmission = models.CharField(max_length=50, choices=TRANSMISSION_CHOICES)
    color = models.CharField(max_length=50)
    description = models.TextField()
    main_photo_url = models.URLField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_sold = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.brand} {self.model} ({self.year})"

    def get_first_photo(self):
        return self.carphoto_set.first().photo_url if self.carphoto_set.exists() else None

class CarPhoto(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='carphoto_set')
    photo_url = models.URLField(max_length=200, null=True, blank=True)

    def __str__(self):
        return f"Photo for {self.car}"

class CarSpecification(models.Model):
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
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    added_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Favorites'
        unique_together = ('user', 'car')

class PurchaseRequest(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buyer_requests')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_requests')
    message = models.TextField(blank=True)
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='В ожидании', choices=STATUS_CHOICES)

    class Meta:
        db_table = 'PurchaseRequests'

    def clean(self):
        if self.buyer == self.seller:
            raise ValidationError('Покупатель и продавец не могут быть одним и тем же пользователем.')

class PriceHistory(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    old_price = models.DecimalField(max_digits=12, decimal_places=2)
    new_price = models.DecimalField(max_digits=12, decimal_places=2)
    change_date = models.DateTimeField(auto_now_add=True)
    changed_by_user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = 'PriceHistory'