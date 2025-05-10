from django.urls import path
from . import views

urlpatterns = [
    path('', views.car_list, name='car_list'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('create-car/', views.create_car, name='create_car'),
    path('car/<int:car_id>/', views.car_detail, name='car_detail'),
]