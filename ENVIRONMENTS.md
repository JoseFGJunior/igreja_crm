# Ambientes e banco de dados

O projeto usa Django e PostgreSQL em ambos os ambientes. Não há
sincronização automática entre os bancos.

## Selecionar o ambiente

O arquivo `.env` contém somente o seletor central:

```text
ENVIRONMENT=development
```

Use `development` para o banco PostgreSQL local e `production` somente
na VPS. O Django carrega, respectivamente, `.env.development` ou
`.env.production`.

Os arquivos reais com credenciais são ignorados pelo Git. Use os
arquivos `.example` como modelo ao configurar outra máquina ou a VPS.

## Desenvolvimento local

```powershell
.\venv\Scripts\Activate.ps1
python manage.py runserver
python manage.py makemigrations
python manage.py migrate
python manage.py test
```

O sistema exibe `Ambiente: DESENVOLVIMENTO` em todas as páginas.

## Aplicação manual em produção

1. Crie e teste a migration localmente.
2. Revise o SQL com `python manage.py sqlmigrate <app> <migration>`.
3. Faça o deploy do código e da migration revisada na VPS.
4. Altere o seletor da VPS para `ENVIRONMENT=production`.
5. Execute somente a migration aprovada:

```powershell
$env:ALLOW_PRODUCTION_MIGRATIONS='true'
python manage.py migrate
Remove-Item Env:ALLOW_PRODUCTION_MIGRATIONS
```

Em produção, `test`, `makemigrations`, `runserver` e `flush` são
bloqueados. `migrate` exige a variável de aprovação explícita acima.
O sistema exibe `Ambiente: PRODUÇÃO` em vermelho.
