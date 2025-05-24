from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError
from .models import Car, User, PurchaseRequest, CarPhoto, CarSpecification

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
        widgets = {
            'phone': forms.TextInput(attrs={'required': False}),
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
    photo_file_1 = forms.ImageField(label='Фото 1', required=False, widget=forms.ClearableFileInput())
    photo_file_2 = forms.ImageField(label='Фото 2', required=False, widget=forms.ClearableFileInput())
    photo_file_3 = forms.ImageField(label='Фото 3', required=False, widget=forms.ClearableFileInput())
    photo_file_4 = forms.ImageField(label='Фото 4', required=False, widget=forms.ClearableFileInput())
    photo_file_5 = forms.ImageField(label='Фото 5', required=False, widget=forms.ClearableFileInput())
    photo_file_6 = forms.ImageField(label='Фото 6', required=False, widget=forms.ClearableFileInput())
    photo_file_7 = forms.ImageField(label='Фото 7', required=False, widget=forms.ClearableFileInput())
    photo_file_8 = forms.ImageField(label='Фото 8', required=False, widget=forms.ClearableFileInput())
    photo_file_9 = forms.ImageField(label='Фото 9', required=False, widget=forms.ClearableFileInput())
    photo_file_10 = forms.ImageField(label='Фото 10', required=False, widget=forms.ClearableFileInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not field_name.startswith('delete_photo_'):
                field.widget.attrs.update({'class': 'w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'})

        if self.instance and self.instance.pk:
            existing_photos = self.instance.carphoto_set.all()[:10]
            for i, photo in enumerate(existing_photos, 1):
                self.fields[f'delete_photo_{photo.id}'] = forms.BooleanField(
                    label=f'Удалить фото {i}',
                    required=False,
                    widget=forms.CheckboxInput(attrs={'class': 'mr-2'})
                )

    class Meta:
        model = Car
        fields = [
            'brand', 'model', 'year', 'price', 'mileage', 'engine_capacity',
            'fuel_type', 'transmission', 'color', 'description', 'condition'
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
            'condition': 'Состояние',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'fuel_type': forms.Select(choices=Car.FUEL_TYPE_CHOICES),
            'transmission': forms.Select(choices=Car.TRANSMISSION_CHOICES),
            'condition': forms.Select(choices=[('new', 'Новый'), ('used', 'Б/у')]),
        }

    def clean(self):
        cleaned_data = super().clean()
        photo_urls = [cleaned_data.get(f'photo_url_{i}') for i in range(1, 11)]
        photo_files = [cleaned_data.get(f'photo_file_{i}') for i in range(1, 11)]

        existing_photos = self.instance.carphoto_set.all() if self.instance and self.instance.pk else []
        photos_to_delete = [key for key in cleaned_data if key.startswith('delete_photo_') and cleaned_data[key]]
        remaining_photos = len(existing_photos) - len(photos_to_delete)
        new_photos = sum(1 for url in photo_urls if url) + sum(1 for file in photo_files if file)

        if remaining_photos + new_photos == 0:
            raise forms.ValidationError('Пожалуйста, оставьте или добавьте хотя бы одно фото.')

        cleaned_data['photo_urls_list'] = [url for url in photo_urls if url]
        cleaned_data['photo_files_list'] = [file for file in photo_files if file]
        return cleaned_data

# Остальные классы формы (UserProfileForm, PurchaseForm и т.д.) остаются без изменений
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

class ManageBalanceForm(forms.Form):
    user = forms.CharField(
        label='Пользователь',
        widget=forms.TextInput(attrs={'id': 'user-autocomplete', 'autocomplete': 'off'})
    )
    amount = forms.DecimalField(max_digits=12, decimal_places=2, label='Сумма')
    action = forms.ChoiceField(choices=[('add', 'Добавить'), ('subtract', 'Списать')], label='Действие')

    def clean_user(self):
        username = self.cleaned_data.get('user')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise ValidationError('Пользователь с таким именем не найден.')
        return user

class ManageUserForm(forms.Form):
    user = forms.CharField(
        label='Пользователь',
        widget=forms.TextInput(attrs={'id': 'user-autocomplete', 'autocomplete': 'off'})
    )
    action = forms.ChoiceField(choices=[('block', 'Заблокировать'), ('unblock', 'Разблокировать'), ('delete', 'Удалить')], label='Действие')
    block_reason = forms.CharField(max_length=255, label='Причина блокировки', required=False)

    def clean_user(self):
        username = self.cleaned_data.get('user')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise ValidationError('Пользователь с таким именем не найден.')
        return user

class CarSpecificationForm(forms.ModelForm):
    class Meta:
        model = CarSpecification
        fields = [
            'body_type', 'power', 'drive_type', 'vin', 'weight', 'country_of_origin'
        ]
        labels = {
            'body_type': 'Тип кузова',
            'power': 'Мощность (л.с.)',
            'drive_type': 'Тип привода',
            'vin': 'VIN',
            'weight': 'Масса (кг)',
            'country_of_origin': 'Страна производства',
        }
        widgets = {
            'body_type': forms.Select(choices=CarSpecification.BODY_TYPE_CHOICES),
            'drive_type': forms.Select(choices=CarSpecification.DRIVE_TYPE_CHOICES),
        }