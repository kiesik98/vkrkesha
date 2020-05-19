from django import forms
from django.contrib.auth import authenticate

from app import models


class BootstrapClassForm:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'


class UserLoginForm(BootstrapClassForm, forms.Form):
    username = forms.CharField(max_length=30, required=True, label='Логин')
    password = forms.CharField(widget=forms.PasswordInput, max_length=30, required=True, label='Пароль')

    def clean(self, *args, **kwargs):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise forms.ValidationError('Такого пользователя не существует!')
            if not user.check_password(password):
                raise forms.ValidationError('Неверный пароль!')
            if not user.is_active:
                raise forms.ValidationError('Пользователь неактивен!')
        return super(UserLoginForm, self).clean(*args, **kwargs)

    class Meta:
        model = models.User
        fields = (
            'username',
            'password',
        )
