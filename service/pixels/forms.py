from distutils.command.build_scripts import first_line_re
from xml.etree.ElementTree import Comment
from django import forms
from pixels.models import ShopListing, ShopItem, Profile, Gift, Comment
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import password_validation
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.validators import UnicodeUsernameValidator
from .validators import ContentTypeRestrictedFileField, TextFileExtensionValidator, ImageFileExtensionValidator


class ShopItemForm(forms.ModelForm):
    name = forms.CharField(
        max_length=100,
        min_length=5,
        required=True,
        help_text="Enter the name of your item",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Inser item name...',
        }))

    cert_license = forms.FileField(
        allow_empty_file=False,
        required=True,
        validators=[TextFileExtensionValidator]
        )
    
    data = forms.ImageField(
        allow_empty_file=False,
        required=True,
        validators=[ImageFileExtensionValidator]
        )

    class Meta:
        model = ShopItem
        fields = ['name','cert_license','data']

class ShopListingForm(forms.ModelForm):
    class Meta:
        model = ShopListing
        fields = ['price','description']

class SignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=20, min_length=4, required=True, help_text='Required: First Name',
                                widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=20, min_length=4, required=True, help_text='Required: Last Name',
                               widget=(forms.TextInput(attrs={'class': 'form-control'})))
    email = forms.EmailField(max_length=100, help_text='Required. Inform a valid email address.',
                             widget=(forms.TextInput(attrs={'class': 'form-control'})))
    password1 = forms.CharField(
        label=_('Password'),
        widget=(forms.PasswordInput(attrs={'class': 'form-control'})),
        help_text=password_validation.password_validators_help_text_html())
    password2 = forms.CharField(
        label=_('Password Confirmation'),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text=_('Just Enter the same password, for confirmation'))
    username = forms.CharField(
        label=_('Username'),
        max_length=150,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[UnicodeUsernameValidator()],
        error_messages={'unique': _("A user with that username already exists.")},
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    cryptographic_key = forms.CharField(max_length=1000, help_text='Required. Inform a valid email address.',required=False,
                             widget=(forms.TextInput(attrs={'class': 'form-control'})))

    def __init__(self,*args,**kwargs):
        super(SignupForm, self).__init__(*args,**kwargs)      

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2','cryptographic_key',)

class NoteForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['notes']

class GiftReceiveForm(forms.ModelForm):
    class Meta:
        model = Gift
        fields = ['code']

class GiftCreationForm(forms.ModelForm):
    class Meta:
        model = Gift
        fields = ['code','value']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['stars','content']