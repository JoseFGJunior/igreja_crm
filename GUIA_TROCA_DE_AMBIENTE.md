# Guia para alternar entre teste e produção

O projeto não sincroniza bancos automaticamente. A escolha do banco é
controlada pelo parâmetro `ENVIRONMENT` no arquivo `.env` de cada máquina.

## 1. Desenvolvimento e testes no computador local

No computador local, confirme que o arquivo `.env` contém:

```text
ENVIRONMENT=development
```

O arquivo `.env.development` deve apontar somente para o PostgreSQL local:

```text
DEBUG=True
POSTGRES_DB=igreja_crm
POSTGRES_USER=igreja_crm
POSTGRES_PASSWORD=<senha-local>
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

Inicie o sistema:

```powershell
cd C:\dev\igreja_crm
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

Confirme na tela o aviso amarelo: **Ambiente: DESENVOLVIMENTO**.

## 2. Criar e testar uma alteração no banco local

Depois de alterar um model Django, execute somente no computador local:

```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py test
```

Antes de enviar a alteração, revise o SQL da migration criada:

```powershell
python manage.py showmigrations
python manage.py sqlmigrate <app> <numero_da_migration>
```

Exemplo:

```powershell
python manage.py sqlmigrate financeiro 0003
```

## 3. Preparar a VPS uma única vez

Na VPS, no diretório do projeto, crie `.env.production` a partir de
`.env.production.example`. Preencha os dados reais do PostgreSQL da VPS:

```text
SECRET_KEY=<chave-secreta-de-producao>
DEBUG=False
ALLOWED_HOSTS=<dominio-e-ip-da-vps-separados-por-virgula>
POSTGRES_DB=igreja_crm
POSTGRES_USER=igreja_crm
POSTGRES_PASSWORD=<senha-de-producao>
POSTGRES_HOST=<host-do-postgresql-da-vps>
POSTGRES_PORT=5432
```

No arquivo `.env` da **VPS**, defina:

```text
ENVIRONMENT=production
```

Depois, reinicie o processo da aplicação configurado na VPS.

> Não copie o arquivo `.env.production` da VPS para o computador local e
> não deixe `ENVIRONMENT=production` no arquivo `.env` local.

## 4. Aplicar uma migration revisada em produção

1. Faça backup do banco da VPS.
2. Envie o código, incluindo o arquivo de migration já revisado.
3. Confirme o aviso vermelho: **Ambiente: PRODUÇÃO**.
4. Execute exclusivamente a migration aprovada:

```powershell
$env:ALLOW_PRODUCTION_MIGRATIONS='true'
python manage.py migrate
Remove-Item Env:ALLOW_PRODUCTION_MIGRATIONS
```

O projeto bloqueia, em produção, os comandos `test`, `makemigrations`,
`runserver` e `flush`. Também bloqueia `migrate` sem a variável de
aprovação acima.

## 5. Voltar ao banco de teste

No computador local, mantenha ou restaure:

```text
ENVIRONMENT=development
```

No terminal, pare o servidor com `Ctrl+C` e inicie-o novamente. O banner
deve voltar a exibir **Ambiente: DESENVOLVIMENTO**.

## Checklist antes de qualquer migration em produção

- A migration foi criada e aplicada no banco local.
- Os testes locais passaram.
- O SQL de `sqlmigrate` foi revisado.
- Existe backup atual da VPS.
- O banner informa **PRODUÇÃO** somente na VPS.
- `ALLOW_PRODUCTION_MIGRATIONS=true` foi definido somente para a execução
  da migration e removido logo depois.
