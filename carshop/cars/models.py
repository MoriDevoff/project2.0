from django.db import models

class User(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField()
    password_hash = models.CharField(max_length=128)
    phone = models.CharField(max_length=15)
    registration_date = models.DateTimeField(auto_now_add=True)
    is_dealer = models.BooleanField(default=False)
    company_name = models.CharField(max_length=100, blank=True)
    avatar_url = models.URLField(blank=True)

class Car(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    mileage = models.IntegerField()
    engine_capacity = models.FloatField()
    fuel_type = models.CharField(max_length=50)
    transmission = models.CharField(max_length=50)
    color = models.CharField(max_length=50)
    description = models.TextField()
    main_photo_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_sold = models.BooleanField(default=False)

class CarSpecification(models.Model):
    car = models.OneToOneField(Car, on_delete=models.CASCADE)
    body_type = models.CharField(max_length=50)
    doors = models.IntegerField()
    seats = models.IntegerField()
    power = models.IntegerField()
    drive_type = models.CharField(max_length=50)
    vin = models.CharField(max_length=17)
    weight = models.IntegerField()
    country_of_origin = models.CharField(max_length=100)

class PurchaseRequest(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buyer_requests')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_requests')
    message = models.TextField()
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='pending')

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    added_date = models.DateTimeField(auto_now_add=True)