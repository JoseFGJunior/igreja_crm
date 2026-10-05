from django import forms

from apps.eventos.models import Evento


class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = (
            'titulo', 'descricao', 'data', 'hora_inicio', 'hora_fim',
            'local', 'categoria', 'observacoes',
        )
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'data': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'hora_inicio': forms.TimeInput(format='%H:%M', attrs={'class': 'form-control', 'type': 'time'}),
            'hora_fim': forms.TimeInput(format='%H:%M', attrs={'class': 'form-control', 'type': 'time'}),
            'local': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        inicio = cleaned_data.get('hora_inicio')
        fim = cleaned_data.get('hora_fim')
        if inicio and fim and fim < inicio:
            self.add_error('hora_fim', 'O horário final deve ser posterior ao horário inicial.')
        return cleaned_data

class EventoImportForm(forms.Form):
    arquivo = forms.FileField(
        label='Planilha Excel',
        help_text='Use um arquivo .xlsx com as colunas EVENTO, HORA, DATA, DIRIGENTE e PREGADOR.',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.xlsx'}),
    )

    def clean_arquivo(self):
        arquivo = self.cleaned_data['arquivo']
        if not arquivo.name.lower().endswith('.xlsx'):
            raise forms.ValidationError('Envie uma planilha Excel no formato .xlsx.')
        if arquivo.size > 10 * 1024 * 1024:
            raise forms.ValidationError('A planilha deve ter no máximo 10 MB.')
        return arquivo