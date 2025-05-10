from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import Car, User

User = get_user_model()

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Подтверждение пароля')

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password']  # Вернули 'email'
        labels = {
            'username': 'Имя пользователя',
            'email': 'Электронная почта',
            'phone': 'Телефон',
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError('Профиль с таким именем пользователя уже существует.')
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Пароли не совпадают.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

class CarForm(forms.ModelForm):
    photo_urls = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Вставьте URL-адреса фотографий, по одному на строку'}),
        label='URL-адреса фотографий',
        required=False
    )

    class Meta:
        model = Car
        fields = [
            'brand', 'model', 'year', 'price', 'mileage', 'engine_capacity',
            'fuel_type', 'transmission', 'color', 'description', 'main_photo_url'
        ]
        labels = {
            'brand': 'Марка',
            'model': 'Модель',
            'year': 'Год выпуска',
            'price': 'Цена (₽)',
            'mileage': 'Пробег (км)',
            'engine_capacity': 'Объем двигателя (л)',
            'fuel_type': 'Тип топлива',
            'transmission': 'Трансмиссия',
            'color': 'Цвет',
            'description': 'Описание',
            'main_photo_url': 'Главное фото (URL)',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'fuel_type': forms.Select(),
            'transmission': forms.Select(),
        }

    def clean(self):
        cleaned_data = super().clean()
        main_photo_url = cleaned_data.get('main_photo_url')
        photo_urls = cleaned_data.get('photo_urls', '')

        photo_urls_list = [url.strip() for url in photo_urls.split('\n') if url.strip()]
        cleaned_data['photo_urls_list'] = photo_urls_list

        has_main_photo = bool(main_photo_url)
        has_additional_photos = bool(photo_urls_list)

        if not has_main_photo and not has_additional_photos:
            raise forms.ValidationError('Пожалуйста, добавьте хотя бы одно фото: либо главное фото (URL), либо дополнительные URL-адреса.')

        return cleaned_data

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone', 'avatar_url')
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'phone': 'Телефон',
            'avatar_url': 'URL аватара',
        }