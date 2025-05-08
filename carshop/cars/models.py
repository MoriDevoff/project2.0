from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.hashers import make_password

# Определение вариантов для полей с ограничениями
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

class User(models.Model):
    """Модель для пользователей."""
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    registration_date = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)  # Добавляем поле last_login
    is_dealer = models.BooleanField(default=False)
    company_name = models.CharField(max_length=100, blank=True)
    avatar_url = models.URLField(blank=True)

    def set_password(self, raw_password):
        """Хеширование пароля перед сохранением."""
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        """Проверка пароля."""
        from django.contrib.auth.hashers import check_password
        return check_password(raw_password, self.password_hash)

    class Meta:
        db_table = 'Users'

class Car(models.Model):
    """Модель для автомобилей."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.IntegerField(
        validators=[
            MinValueValidator(1901),
            MaxValueValidator(timezone.now().year + 1)
        ]
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    mileage = models.IntegerField(validators=[MinValueValidator(0)])
    engine_capacity = models.FloatField(validators=[MinValueValidator(0.1)])
    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPE_CHOICES)
    transmission = models.CharField(max_length=20, choices=TRANSMISSION_CHOICES)
    color = models.CharField(max_length=30)
    description = models.TextField(blank=True)
    main_photo_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_sold = models.BooleanField(default=False)

    class Meta:
        db_table = 'Cars'

class CarSpecification(models.Model):
    """Модель для спецификаций автомобилей."""
    car = models.OneToOneField(Car, on_delete=models.CASCADE)
    body_type = models.CharField(max_length=20, choices=BODY_TYPE_CHOICES)
    doors = models.IntegerField(validators=[MinValueValidator(2), MaxValueValidator(6)])
    seats = models.IntegerField(validators=[MinValueValidator(2), MaxValueValidator(9)])
    power = models.IntegerField(validators=[MinValueValidator(1)])  # л.с.
    drive_type = models.CharField(max_length=10, choices=DRIVE_TYPE_CHOICES)
    vin = models.CharField(max_length=17, unique=True)
    weight = models.IntegerField(validators=[MinValueValidator(1)])  # кг
    country_of_origin = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = 'CarSpecifications'

    def clean(self):
        """Проверка длины VIN."""
        if self.vin and len(self.vin) != 17:
            raise ValidationError({'vin': 'VIN должен содержать ровно 17 символов.'})

class Favorite(models.Model):
    """Модель для избранных автомобилей."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    added_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Favorites'
        unique_together = ('user', 'car')

class PurchaseRequest(models.Model):
    """Модель для заявок на покупку."""
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buyer_requests')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_requests')
    message = models.TextField(blank=True)
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='В ожидании', choices=STATUS_CHOICES)

    class Meta:
        db_table = 'PurchaseRequests'

    def clean(self):
        """Проверка, что покупатель и продавец не совпадают."""
        if self.buyer == self.seller:
            raise ValidationError('Покупатель и продавец не могут быть одним и тем же пользователем.')

class PriceHistory(models.Model):
    """Модель для истории цен."""
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    old_price = models.DecimalField(max_digits=12, decimal_places=2)
    new_price = models.DecimalField(max_digits=12, decimal_places=2)
    change_date = models.DateTimeField(auto_now_add=True)
    changed_by_user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = 'PriceHistory'