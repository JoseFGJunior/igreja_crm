from django import forms
from django.contrib.auth import get_user_model

from apps.membros.models import MensagemWhatsAppVisitante, Membro
from apps.membros.services import normalizar_whatsapp
from apps.accounts.models import UsuarioIgreja


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


class VisitanteForm(forms.ModelForm):

    class Meta:
        model = Membro
        fields = (
            'nome', 'whatsapp', 'telefone', 'data_primeira_visita',
            'origem_visitante', 'observacao_visitante',
            'responsavel_visitante',
        )
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'whatsapp': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'data_primeira_visita': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'origem_visitante': forms.TextInput(attrs={'class': 'form-control'}),
            'observacao_visitante': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            ),
            'responsavel_visitante': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, igreja=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.igreja = igreja
        self.fields['data_primeira_visita'].required = True
        usuario_ids = UsuarioIgreja.objects.filter(
            igreja=igreja,
            ativo=True,
        ).values_list('usuario_id', flat=True)
        self.fields['responsavel_visitante'].queryset = get_user_model().objects.filter(
            id__in=usuario_ids
        ).order_by('username')

    def clean_whatsapp(self):
        whatsapp = normalizar_whatsapp(self.cleaned_data['whatsapp'])
        if not whatsapp:
            raise forms.ValidationError('Informe o WhatsApp.')

        if self.igreja:
            existentes = Membro.objects.filter(
                igreja=self.igreja,
                status='VISITANTE',
                whatsapp=whatsapp,
            )
            if self.instance.pk:
                existentes = existentes.exclude(pk=self.instance.pk)
            if existentes.exists():
                raise forms.ValidationError(
                    'Já existe um visitante com este WhatsApp nesta igreja.'
                )

        return whatsapp

    def save(self, commit=True):
        visitante = super().save(commit=False)
        visitante.status = 'VISITANTE'
        if commit:
            visitante.save()
        return visitante


class MensagemWhatsAppVisitanteForm(forms.ModelForm):

    class Meta:
        model = MensagemWhatsAppVisitante
        fields = ('tipo', 'mensagem')
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'mensagem': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo'].disabled = True
