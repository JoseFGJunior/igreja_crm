# Retomar desenvolvimento do app mobile

Data: 28/09/2026

## Estado atual

- Projeto React Native/Expo em `mobile-app/`.
- Backend mobile integrado em `apps/mobile/`.
- Tenant configurado: `pibcruz`.
- Configuração mobile da PIB Cruz criada e ativa no banco.
- API Home funcionando: `GET /api/mobile/v1/home/` retorna HTTP 200.
- Pedido de oração implementado de ponta a ponta.
- Endpoint: `POST /api/mobile/v1/pedidos-oracao/`.
- Campos: nome, telefone e pedido.
- Migração aplicada: `apps/mobile/migrations/0002_pedidooracao.py`.
- CORS/preflight corrigido: `OPTIONS` retorna 204.
- POST validado: retorna HTTP 201 e grava em `mobile_pedidooracao`.
- Admin registra `PedidoOracao` em `apps/mobile/admin.py`.

## Como iniciar depois do reinício

Terminal 1 — Django:

```powershell
cd C:\dev\igreja_crm
.\venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```

Terminal 2 — Expo:

```powershell
cd C:\dev\igreja_crm\mobile-app
npx expo start --clear
```

Admin Django:

```text
http://127.0.0.1:8000/admin/
```

Pedidos de oração:

```text
http://127.0.0.1:8000/admin/mobile/pedidooracao/
```

Expo Web:

```text
http://localhost:8081/
```

## Último ponto pendente

O usuário informou que não está vendo `Pedidos de oração` no Admin, apesar de estar entrando com o superusuário `crm`. O modelo está registrado e existem registros no banco. Ao retomar, confirmar se o Admin aberto é realmente o Django em `127.0.0.1:8000`, e não o Expo em `localhost:8081`, além de verificar se não há outro processo/instância Django rodando.

## Próximas funcionalidades

1. Confirmar visualização dos pedidos no Admin.
2. Implementar mensagens/séries reais.
3. Implementar detalhes de eventos.
4. Integrar Pix real e contatos.
5. Substituir dados fallback do React Native pelos contratos definitivos da API.