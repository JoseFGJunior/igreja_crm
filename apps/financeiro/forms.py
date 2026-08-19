from django import forms

from apps.financeiro.models import CategoriaFinanceira
from apps.financeiro.models import LancamentoFinanceiro
from apps.membros.models import Membro


class CategoriaEntradaForm(forms.ModelForm):

    class Meta:
        model = CategoriaFinanceira
        fields = (
            'nome',
            'ativa',
        )
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'ativa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CategoriaSaidaForm(forms.ModelForm):

    class Meta:
        model = CategoriaFinanceira
        fields = (
            'nome',
            'ativa',
        )
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'ativa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EntradaFinanceiraForm(forms.ModelForm):

    class Meta:
        model = LancamentoFinanceiro
        fields = (
            'data',
            'categoria',
            'membro',
            'descricao',
            'valor',
            'forma_pagamento',
            'observacao',
        )
        widgets = {
            'data': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                }
            ),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'membro': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.01',
                    'min': '0',
                }
            ),
            'forma_pagamento': forms.Select(attrs={'class': 'form-select'}),
            'observacao': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                }
            ),
        }

    def __init__(self, *args, igreja=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['categoria'].queryset = CategoriaFinanceira.objects.filter(
            igreja=igreja,
            tipo=CategoriaFinanceira.TIPO_ENTRADA,
            ativa=True
        ).order_by(
            'nome'
        )
        self.fields['membro'].queryset = Membro.objects.filter(
            igreja=igreja
        ).order_by(
            'nome'
        )
        self.fields['membro'].required = False


class ContaPagarForm(forms.ModelForm):

    class Meta:
        model = LancamentoFinanceiro
        fields = (
            'data',
            'categoria',
            'descricao',
            'valor',
            'forma_pagamento',
            'observacao',
        )
        widgets = {
            'data': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                }
            ),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.01',
                    'min': '0',
                }
            ),
            'forma_pagamento': forms.Select(attrs={'class': 'form-select'}),
            'observacao': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                }
            ),
        }

    def __init__(self, *args, igreja=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['categoria'].queryset = CategoriaFinanceira.objects.filter(
            igreja=igreja,
            tipo=CategoriaFinanceira.TIPO_SAIDA,
            ativa=True
        ).order_by(
            'nome'
        )


class DespesaRecorrenteForm(forms.Form):

    TIPO_RECORRENTE = 'RECORRENTE'
    TIPO_PARCELADA = 'PARCELADA'

    TIPO_CHOICES = [
        (TIPO_RECORRENTE, 'Despesa recorrente'),
        (TIPO_PARCELADA, 'Compra parcelada'),
    ]

    tipo_geracao = forms.ChoiceField(
        choices=TIPO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    data_primeiro_vencimento = forms.DateField(
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={
                'class': 'form-control',
                'type': 'date',
            }
        )
    )
    categoria = forms.ModelChoiceField(
        queryset=CategoriaFinanceira.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    descricao = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    valor_parcela = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
            }
        )
    )
    quantidade = forms.IntegerField(
        min_value=2,
        max_value=120,
        help_text='Informe por quantos meses a despesa deve ser criada.',
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
                'min': '2',
                'max': '120',
            }
        )
    )
    forma_pagamento = forms.ChoiceField(
        choices=LancamentoFinanceiro.FORMA_PAGAMENTO_CHOICES,
        initial=LancamentoFinanceiro.FORMA_PIX,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    observacao = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 3,
            }
        )
    )

    def __init__(self, *args, igreja=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['categoria'].queryset = CategoriaFinanceira.objects.filter(
            igreja=igreja,
            tipo=CategoriaFinanceira.TIPO_SAIDA,
            ativa=True
        ).order_by('nome')
