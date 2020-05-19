from django import forms
from django.contrib.auth.forms import UserCreationForm

from app import models


class BootstrapClassForm:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'


class SignUpForm(BootstrapClassForm, UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label='Имя')
    last_name = forms.CharField(max_length=30, required=True, label='Фамилия')
    middle_name = forms.CharField(max_length=30, required=False, label='Отчество')
    is_staff = forms.BooleanField(initial=True, widget=forms.HiddenInput())

    class Meta:
        model = models.User
        fields = (
            'username',
            'first_name',
            'last_name',
            'middle_name',
            'password1',
            'password2',
            'is_staff'
        )


class StudentTestForm(BootstrapClassForm, forms.ModelForm):

    class Meta:
        model = models.StudentTest
        exclude = (
            'created_time',
            'modified_time',
            'points',
            'checked',
            'student',
            'group'
        )


class StudentAnswerForm(BootstrapClassForm, forms.ModelForm):
    question = forms.ModelChoiceField(
        queryset=models.StudentTestQuestion.objects.all(),
        widget=forms.HiddenInput()
    )
    answers = forms.ModelMultipleChoiceField(queryset=models.Answer.objects.all(), required=False)

    class Meta:
        model = models.StudentAnswer
        fields = ['question', 'answers', 'text']
