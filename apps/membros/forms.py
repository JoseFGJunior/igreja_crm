from django import forms

from apps.membros.models import Membro


class MembroForm(forms.ModelForm):

    tipo_cuidado_especial = forms.MultipleChoiceField(
        choices=Membro.TIPO_CUIDADO_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(
            attrs={'class': 'form-check-input'}
        )
    )

    class Meta:
        model = Membro
        fields = (
            'nome',
            'email',
            'telefone',
            'data_nascimento',
            'endereco',
            'bairro',
            'cidade',
            'status',
            'cargo',
            'batizado',
            'data_batismo',
            'necessita_cuidado_especial',
            'tipo_cuidado_especial',
            'prioridade_cuidado',
            'responsavel_cuidado',
            'observacao_cuidado_especial',
        )
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'data_nascimento': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                }
            ),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'batizado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'data_batismo': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                }
            ),
            'necessita_cuidado_especial': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
            'prioridade_cuidado': forms.Select(attrs={'class': 'form-select'}),
            'responsavel_cuidado': forms.TextInput(attrs={'class': 'form-control'}),
            'observacao_cuidado_especial': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.tipo_cuidado_especial:
            self.initial['tipo_cuidado_especial'] = [
                tipo.strip()
                for tipo in self.instance.tipo_cuidado_especial.split(',')
                if tipo.strip()
            ]

        self.fields['prioridade_cuidado'].required = False

    def clean_tipo_cuidado_especial(self):
        tipos = self.cleaned_data.get('tipo_cuidado_especial') or []

        return ','.join(tipos)
