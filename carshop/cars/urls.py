from django.urls import path
from . import views

urlpatterns = [
    path('', views.car_list, name='car_list'),
    path('car/<int:car_id>/', views.car_detail, name='car_detail'),
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('favorites/add/<int:car_id>/', views.add_to_favorites, name='add_to_favorites'),
    path('favorites/remove/<int:favorite_id>/', views.remove_from_favorites, name='remove_from_favorites'),
    path('favorites/', views.view_favorites, name='view_favorites'),
    path('create/', views.create_car, name='create_car'),
    path('request/<int:car_id>/', views.send_purchase_request, name='send_purchase_request'),
    path('requests/', views.view_purchase_requests, name='view_purchase_requests'),
]