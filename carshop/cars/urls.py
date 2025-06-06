from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.car_list, name='car_list'),
    path('search/', views.car_search, name='car_search'),
    path('car/<int:car_id>/', views.car_detail, name='car_detail'),
    path('register/', views.register, name='register'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('login/', views.login_view, name='login'),
    path('blocked/', views.blocked, name='blocked'),
    path('logout/', views.logout_view, name='logout'),
    path('create/', views.create_car, name='create_car'),
    path('edit_car/<int:car_id>/', views.edit_car, name='edit_car'),
    path('car/<int:car_id>/delete/', views.delete_car, name='delete_car'),
    path('profile/', views.profile, name='profile'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('purchases/', views.purchases, name='purchases'),
    path('reset-notifications/', views.reset_notifications, name='reset_notifications'),
    path('purchase/<int:car_id>/', views.purchase_car, name='purchase_car'),
    path('purchase/<int:purchase_id>/<str:action>/', views.respond_purchase, name='respond_purchase'),
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/<str:token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('toggle-favorite/<int:car_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('favorites/', views.favorite_list, name='favorite_list'),
    path('manage/users/', views.manage_users, name='manage_users'),
    path('manage/ads/', views.manage_ads, name='manage_ads'),
    path('manage/balances/', views.manage_balances, name='manage_balances'),
    path('check-email/', views.check_email_availability, name='check_email_availability'),
]

# Добавление маршрутов для медиафайлов в режиме отладки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)