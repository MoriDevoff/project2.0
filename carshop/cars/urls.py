from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Проверка доступности email
    path('check-email/', views.check_email_availability, name='check_email_availability'),
    # Главная страница со списком автомобилей
    path('', views.car_list, name='car_list'),
    # Поиск автомобилей
    path('search/', views.car_search, name='car_search'),
    # Страница с деталями автомобиля
    path('car/<int:car_id>/', views.car_detail, name='car_detail'),
    # Регистрация пользователя
    path('register/', views.register, name='register'),
    # Вход в систему
    path('login/', views.login_view, name='login'),
    # Выход из системы
    path('logout/', views.logout_view, name='logout'),
    # Создание нового объявления
    path('create/', views.create_car, name='create_car'),
    # Профиль пользователя
    path('profile/', views.profile, name='profile'),
    # Список покупок/продаж
    path('purchases/', views.purchases, name='purchases'),
    # Сброс уведомлений
    path('reset-notifications/', views.reset_notifications, name='reset_notifications'),
    # Покупка автомобиля
    path('purchase/<int:car_id>/', views.purchase_car, name='purchase_car'),
    # Ответ на запрос покупки
    path('purchase/<int:purchase_id>/<str:action>/', views.respond_purchase, name='respond_purchase'),
    # Редактирование профиля
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    # Редактирование объявления
    path('edit_car/<int:car_id>/', views.edit_car, name='edit_car'),
    # Удаление объявления
    path('car/<int:car_id>/delete/', views.delete_car, name='delete_car'),
    # Подтверждение email
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    # Запрос сброса пароля
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    # Подтверждение сброса пароля
    path('password-reset/<str:token>/', views.password_reset_confirm, name='password_reset_confirm'),
    # Добавление/удаление в избранное
    path('toggle-favorite/<int:car_id>/', views.toggle_favorite, name='toggle_favorite'),
    # Список избранного
    path('favorites/', views.favorite_list, name='favorite_list'),
    # Управление пользователями (админ)
    path('manage/users/', views.manage_users, name='manage_users'),
    # Управление объявлениями (админ)
    path('manage/ads/', views.manage_ads, name='manage_ads'),
    # Управление балансами (админ)
    path('manage/balances/', views.manage_balances, name='manage_balances'),
    # Страница блокировки пользователя
    path('blocked/', views.blocked, name='blocked'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)