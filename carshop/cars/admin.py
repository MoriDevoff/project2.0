from django.contrib import admin
from .models import User, Car, CarSpecification, PurchaseRequest, Favorite

admin.site.register(User)
admin.site.register(Car)
admin.site.register(CarSpecification)
admin.site.register(PurchaseRequest)
admin.site.register(Favorite)
