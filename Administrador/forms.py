from django import forms
from db.models import *
from django import forms
from django.contrib.auth.forms import UserChangeForm


class UserAdminForm(UserChangeForm):

    password = None 

    class Meta:
        model = User
        # Define los campos que el administrador PUEDE modificar
        fields = ('username', 'roles', 'is_active','email')
        
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control border border-3 border-primary my-2'}), 
            'roles': forms.Select(attrs={'class': 'form-control border border-3 border-primary my-2'}), 
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input border border-3 border-primary my-1'}),
            'email': forms.EmailInput(attrs={'class': 'form-control border border-3 border-primary my-1'}),
        }
    def __init__(self, *args, **kwargs):
            super(UserAdminForm, self).__init__(*args, **kwargs)
            self.fields['username'].required = True
            self.fields['email'].required = True
            #self.fields['roles'].required = True
            #self.fields['is_active'].required = True

class UserAdminPassForm(forms.ModelForm):
    nueva_contrasena = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control border border-3 border-primary my-2'}
        ),
        label="Contraseña",
        required=True
    )
    confirmar_contrasena = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control border border-3 border-primary my-2'}
        ),
        label="Confirmar Contraseña",
        required=True
    )
    
    class Meta:
        model = User
        fields = ('username', 'roles', 'is_active','email') 
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control border border-3 border-primary my-2'}), 
            'roles': forms.Select(attrs={'class': 'form-control border border-3 border-primary my-2'}), 
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input border border-3 border-primary my-1'}),
            'email': forms.EmailInput(attrs={'class': 'form-control  border border-3 border-primary my-1'}),
        }

    def __init__(self, *args, **kwargs):
        super(UserAdminPassForm, self).__init__(*args, **kwargs)
        self.fields['username'].required = True
        self.fields['roles'].required = True
        self.fields['is_active'].required = True

    def clean(self):
        cleaned_data = super().clean()
        nueva_contrasena = cleaned_data.get("nueva_contrasena")
        confirmar_contrasena = cleaned_data.get("confirmar_contrasena")

        if nueva_contrasena and confirmar_contrasena:
            if nueva_contrasena != confirmar_contrasena:
                raise forms.ValidationError("Las contraseñas no coinciden.")
        else:
            raise forms.ValidationError("Ambos campos de contraseña son requeridos.")
             
        return cleaned_data
        
    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("nueva_contrasena")
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user

class UserPasswordForm(forms.Form):
    nueva_contrasena = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control border border-3 border-primary my-2'}
        ),
        label="Nueva Contraseña"
    )
    confirmar_contrasena = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control border border-3 border-primary my-2'}
        ),
        label="Confirmar Contraseña"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        nueva_contrasena = cleaned_data.get("nueva_contrasena")
        confirmar_contrasena = cleaned_data.get("confirmar_contrasena")

        if nueva_contrasena and confirmar_contrasena and nueva_contrasena != confirmar_contrasena:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data    
    

class MensajeForm(forms.ModelForm):
    class Meta:
        model = Mensaje
        fields = ('asunto','cuerpo', 'numEnvio', 'medioContacto','encuesta') 
        widgets = {
            'asunto': forms.TextInput(attrs={'class': 'form-control border border-3 border-primary my-2'}), 
            'cuerpo': forms.TextInput(attrs={'class': 'form-control border border-3 border-primary my-2'}), 
            'medioContacto': forms.Select(attrs={'class': 'form-control border border-3 border-primary my-2'}), 
            'numEnvio': forms.NumberInput(attrs={'class': 'form-control border border-3 border-primary my-2'}), 
            'encuesta': forms.CheckboxInput(attrs={'class': 'form-check-input border border-3 border-primary my-auto check-pregunta' }),
        }


    def __init__(self, *args, **kwargs):
        super(MensajeForm, self).__init__(*args, **kwargs)
        self.fields['asunto'].required = True
        self.fields['cuerpo'].required = True
        self.fields['numEnvio'].required = True
        self.fields['medioContacto'].required = True

#SociosoFormSet = forms.modelformset_factory(Socio, form=EditarSocio, extra=1, can_delete=True)


#EstadoFormSet = forms.modelformset_factory(Estado, form=ModificarEstados, extra=1, can_delete=True)

