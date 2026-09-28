# Ponto de retomada — migração para Docker

Atualizado em 14/09/2026.

## Já concluído

- Criados `Dockerfile`, `docker-compose.yml` e `.dockerignore`.
- Criado `docker/entrypoint.sh`, que executa as migrations antes de iniciar o Django.
- Criado `.env.docker.example` com configuração para PostgreSQL no serviço `db`.
- Criado `DOCKER.md` com instruções de uso.
- Docker Desktop instalado; Docker CLI identificado na versão 29.8.0.
- `python manage.py check` passou sem erros.

## Bloqueio atual

O Docker Desktop está instalado, mas o engine Linux não inicia. O log
indica que o WSL 2 não encontrou o kernel e o Compose retorna
`Docker Desktop is unable to start`. O CLI e o Compose estão instalados;
os containers ainda não foram iniciados.

## Próximos passos

Depois de corrigir o WSL 2/Docker Desktop, abra o PowerShell e execute:

```powershell
cd C:\dev\igreja_crm
docker version
Copy-Item .env.docker.example .env.docker
docker compose up --build
```

Se `.env.docker` já existir, o `Copy-Item` pode ser ignorado. Quando o
container subir, acessar `http://localhost:8000` e confirmar login e banco.

O arquivo `media/portal/pastor/PRJR.png` já estava como alteração não
versionada antes deste trabalho e deve ser preservado.
