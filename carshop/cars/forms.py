from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError
from .models import Car, User, PurchaseRequest, CarPhoto

User = get_user_model()

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Подтверждение пароля')

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password']
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

    def clean_password(self):
        password = self.cleaned_data.get('password')
        try:
            password_validation.validate_password(password, self.instance)
        except ValidationError as error:
            raise ValidationError(error)
        return password

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
    photo_url_1 = forms.URLField(label='URL фото 1', required=False)
    photo_url_2 = forms.URLField(label='URL фото 2', required=False)
    photo_url_3 = forms.URLField(label='URL фото 3', required=False)
    photo_url_4 = forms.URLField(label='URL фото 4', required=False)
    photo_url_5 = forms.URLField(label='URL фото 5', required=False)
    photo_url_6 = forms.URLField(label='URL фото 6', required=False)
    photo_url_7 = forms.URLField(label='URL фото 7', required=False)
    photo_url_8 = forms.URLField(label='URL фото 8', required=False)
    photo_url_9 = forms.URLField(label='URL фото 9', required=False)
    photo_url_10 = forms.URLField(label='URL фото 10', required=False)
    photo_file_1 = forms.ImageField(label='Фото 1', required=False)
    photo_file_2 = forms.ImageField(label='Фото 2', required=False)
    photo_file_3 = forms.ImageField(label='Фото 3', required=False)
    photo_file_4 = forms.ImageField(label='Фото 4', required=False)
    photo_file_5 = forms.ImageField(label='Фото 5', required=False)
    photo_file_6 = forms.ImageField(label='Фото 6', required=False)
    photo_file_7 = forms.ImageField(label='Фото 7', required=False)
    photo_file_8 = forms.ImageField(label='Фото 8', required=False)
    photo_file_9 = forms.ImageField(label='Фото 9', required=False)
    photo_file_10 = forms.ImageField(label='Фото 10', required=False)

    class Meta:
        model = Car
        fields = [
            'brand', 'model', 'year', 'price', 'mileage', 'engine_capacity',
            'fuel_type', 'transmission', 'color', 'description'
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
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'fuel_type': forms.Select(),
            'transmission': forms.Select(),
        }

    def clean(self):
        cleaned_data = super().clean()
        photo_urls = [
            cleaned_data.get(f'photo_url_{i}') for i in range(1, 11)
        ]
        photo_files = [
            cleaned_data.get(f'photo_file_{i}') for i in range(1, 11)
        ]

        has_photos = any(url for url in photo_urls if url) or any(file for file in photo_files if file)

        if not has_photos:
            raise forms.ValidationError('Пожалуйста, добавьте хотя бы одно фото через URL-адрес или загрузку.')

        cleaned_data['photo_urls_list'] = [url for url in photo_urls if url]
        cleaned_data['photo_files_list'] = [file for file in photo_files if file]
        return cleaned_data

class UserProfileForm(forms.ModelForm):
    avatar_file = forms.ImageField(
        label='Загрузить аватар',
        required=False,
        widget=forms.ClearableFileInput()
    )
    password = forms.CharField(widget=forms.PasswordInput, label='Новый пароль', required=False)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Подтверждение пароля', required=False)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone', 'avatar_url', 'avatar_file')
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'phone': 'Телефон',
            'avatar_url': 'URL аватара',
        }

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            try:
                password_validation.validate_password(password, self.instance)
            except ValidationError as error:
                raise ValidationError(error)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Пароли не совпадают.')
        return cleaned_data

class PurchaseForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequest
        fields = ['offered_price', 'message']
        labels = {
            'offered_price': 'Предложенная цена (₽)',
            'message': 'Сообщение продавцу',
        }
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Напишите сообщение продавцу (опционально)'}),
        }

    def clean_offered_price(self):
        offered_price = self.cleaned_data.get('offered_price')
        if offered_price is not None and offered_price <= 0:
            raise ValidationError('Цена должна быть больше 0.')
        return offered_price

    def clean(self):
        cleaned_data = super().clean()
        if 'buyer' in self.instance.__dict__ and 'seller' in self.instance.__dict__:
            if self.instance.buyer == self.instance.seller:
                raise ValidationError('Покупатель и продавец не могут быть одним и тем же пользователем.')
        return cleaned_data

class PasswordResetForm(forms.Form):
    email = forms.EmailField(label='Электронная почта')

class SetPasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput, label='Новый пароль')
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Подтверждение пароля')

    def clean_password(self):
        password = self.cleaned_data.get('password')
        try:
            password_validation.validate_password(password)
        except ValidationError as error:
            raise ValidationError(error)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Пароли не совпадают.')
        return cleaned_data