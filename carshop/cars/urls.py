from django.urls import path
from . import views

urlpatterns = [
    path('', views.car_list, name='car_list'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('create-car/', views.create_car, name='create_car'),
    path('car/<int:car_id>/', views.car_detail, name='car_detail'),
    path('profile/', views.profile, name='profile'),
    path('purchases/', views.purchases, name='purchases'),
    path('car/<int:car_id>/purchase/', views.purchase_car, name='purchase_car'),
    path('purchase/<int:purchase_id>/respond/<str:action>/', views.respond_purchase, name='respond_purchase'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('car/<int:car_id>/edit/', views.edit_car, name='edit_car'),
]