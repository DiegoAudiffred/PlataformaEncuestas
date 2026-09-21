from django import forms

from db.models import *


class crearEncuestaForm(forms.ModelForm):
    #categoria = forms.ModelChoiceField(
    #    queryset=Categoria.objects.none(),
    #    widget=forms.Select(attrs={'class': 'form-select border border-3 border-primary my-2'}),
    #    required=True
    #)

    class Meta:
        model = Encuesta
        fields = ['titulo', 'descripcion', 'creador', 'activa', 'fechaVencimiento', 'imagen', 'dirigido','maxIntentos']#,categoria]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control border border-3 border-primary my-2', 'placeholder': 'Título'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control border border-3 border-primary my-2', 'rows': 3}),
            'creador': forms.Select(attrs={'class': 'form-select border border-3 border-primary my-2'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input border border-3 border-primary my-1'}),
            'fechaVencimiento': forms.DateInput(attrs={'class': 'form-control border border-3 border-primary my-1', 'type': 'date'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control border border-3 border-primary my-1', 'onchange':"previewImage(event)"}),
            'dirigido': forms.SelectMultiple(attrs={'class': 'form-select border border-3 border-primary my-2'}),
            'maxIntentos': forms.NumberInput(attrs={'class': 'form-control border border-3 border-primary my-2','min': 1}),
        }

    def __init__(self, *args, **kwargs):
        super(crearEncuestaForm, self).__init__(*args, **kwargs)

        #self.fields['creador'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['dirigido'].queryset = User.objects.filter(is_active=True).order_by('username')

        #if user and user.is_staff:
        #    self.fields['categoria'].queryset = Categoria.objects.all()
        #else:
        #    self.fields['categoria'].queryset = Categoria.objects.filter(activa=True)
class PreguntaForm(forms.ModelForm):
    class Meta:
        model = Pregunta
        fields = ['texto_pregunta', 'tipo', 'imagen']
        widgets = {
            'texto_pregunta': forms.TextInput(attrs={
                'class': 'form-control border border-primary my-2',
                'placeholder': 'Escribe el texto de la pregunta'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select border border-primary my-2'
            }),
            'imagen': forms.FileInput(attrs={
                'class': 'form-control border border-primary my-2',
                'onchange': 'previewQuestionImage(event)'
            })
        }