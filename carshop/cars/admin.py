from django.contrib import admin
from .models import User, Car, CarSpecification, Favorite, PurchaseRequest, PriceHistory

admin.site.register(User)
admin.site.register(Car)
admin.site.register(CarSpecification)
admin.site.register(Favorite)
admin.site.register(PurchaseRequest)
admin.site.register(PriceHistory)