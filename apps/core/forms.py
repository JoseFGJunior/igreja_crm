from django import forms

from apps.core.models import MensagemAniversario


class MensagemAniversarioForm(forms.ModelForm):

    class Meta:
        model = MensagemAniversario
        fields = ('texto', 'versiculo', 'ativa')
        labels = {
            'texto': 'Mensagem',
            'versiculo': 'Versículo bíblico',
            'ativa': 'Usar mensagem de aniversário',
        }
        widgets = {
            'texto': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'versiculo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ativa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_texto(self):
        texto = self.cleaned_data['texto'].strip()
        if '{nome}' not in texto:
            raise forms.ValidationError('Inclua a variável {nome} na mensagem.')
        return texto
