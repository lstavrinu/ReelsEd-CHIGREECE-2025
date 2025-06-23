from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from django.contrib.auth import authenticate
from .models import Reel


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'role']


class CustomAuthenticationForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        required=True
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        required=True
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise forms.ValidationError("Invalid username or password")
        return cleaned_data

    def get_user(self):
        username = self.cleaned_data.get('username')
        return authenticate(username=username, password=self.cleaned_data.get('password'))


class VideoForm(forms.Form):
    url = forms.URLField(
        label="YouTube Video URL",
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter a YouTube video URL',
        })
    )


class ReelUploadForm(forms.ModelForm):
    class Meta:
        model = Reel
        fields = ['start_time', 'end_time', 'label', 'summary', 'file_path']
