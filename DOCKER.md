# Executar com Docker

## Primeira execução

Instale e inicie o Docker Desktop. Depois, na raiz do projeto:

```powershell
Copy-Item .env.docker.example .env.docker
docker compose up --build
```

Acesse `http://localhost:8000`. O container `web` aguarda o PostgreSQL
ficar saudável e executa `python manage.py migrate --noinput` antes de
iniciar o Django.

## Comandos úteis

```powershell
docker compose up -d
docker compose logs -f web
docker compose exec web python manage.py createsuperuser
docker compose down
```

`docker compose down` preserva o volume do PostgreSQL. Use
`docker compose down -v` somente para remover também os dados do banco.

O arquivo `.env.docker` é local e não deve ser versionado. Para produção,
continue usando `.env.production` e o procedimento de migrations aprovado
em `ENVIRONMENTS.md`; esta composição é destinada ao desenvolvimento.
