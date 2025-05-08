from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Car, CarSpecification

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )

class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        max_length=254,
        required=True,
        help_text='Введите действительный адрес электронной почты.',
        widget=forms.EmailInput(attrs={'class': 'w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
        self.fields['email'].widget.attrs.update({
            'class': 'w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
        })

class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ['brand', 'model', 'year', 'price', 'mileage', 'engine_capacity', 'fuel_type', 'transmission', 'color', 'description', 'main_photo_url']

    def __init__(self, *args, **kwargs):
        super(CarForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            })

class CarSpecificationForm(forms.ModelForm):
    class Meta:
        model = CarSpecification
        fields = ['body_type', 'doors', 'seats', 'power', 'drive_type', 'vin', 'weight', 'country_of_origin']

    def __init__(self, *args, **kwargs):
        super(CarSpecificationForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            })