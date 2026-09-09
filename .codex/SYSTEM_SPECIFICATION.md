# Especificação do sistema — Igreja CRM

Este documento é a referência obrigatória para qualquer nova funcionalidade do projeto. Antes de alterar código, o agente deve ler este arquivo, verificar as regras aplicáveis e confirmar ao final que a implementação atende ao checklist.

## 1. Objetivo e limites

O sistema é um CRM para igrejas. Cada igreja possui seus próprios dados e usuários podem estar vinculados a uma ou mais igrejas.

Uma funcionalidade nova deve ser implementada somente dentro do escopo solicitado. Não refatorar, renomear ou alterar autenticação, layout, financeiro, membros ou outro módulo sem necessidade direta e explícita.

## 2. Arquitetura atual

- Framework: Django.
- Usuário: `apps.accounts.models.Usuario`, baseado em `AbstractUser`.
- Igreja: `apps.igrejas.models.Igreja`.
- Vínculo usuário/igreja: `apps.accounts.models.UsuarioIgreja`.
- Igreja ativa: `request.session['igreja_id']`, validada pela relação `UsuarioIgreja` do usuário, com `ativo=True` e `igreja__ativa=True`.
- Modelo multi-tenant: `apps.core.models.TenantModel`.
- `TenantModel` já fornece `igreja`, `created_at` e `updated_at`.
- Layout: `templates/base/base.html`, com navbar e sidebar compartilhadas.
- Banco: PostgreSQL em todos os ambientes.

Atualmente não existe middleware que defina `request.igreja`. Até que isso seja alterado de forma planejada, as views devem resolver a igreja pela sessão e pela relação do usuário, como fazem os módulos existentes.

## 3. Regra obrigatória de acesso e multi-tenant

Toda requisição autenticada que manipule dados de igreja deve:

1. resolver a igreja ativa usando o padrão de `get_igreja_selecionada(request)`;
2. validar que o usuário está vinculado à igreja, que o vínculo está ativo e que a igreja está ativa;
3. redirecionar para `dashboard` quando não houver igreja válida;
4. filtrar todas as consultas pela igreja resolvida;
5. nunca confiar em `igreja_id` enviado por formulário, query string ou URL;
6. atribuir `objeto.igreja = igreja` no servidor durante a criação;
7. buscar objetos individuais com filtro de igreja, por exemplo:

```python
get_object_or_404(Evento, pk=pk, igreja=igreja)
```

É proibido usar uma consulta de dados de tenant equivalente a `Modelo.objects.all()` sem filtro por igreja. Também é proibido aceitar a igreja como campo editável no formulário.

Testes de toda nova entidade multi-tenant devem provar que dados da Igreja A não aparecem, não podem ser editados e não podem ser excluídos por uma sessão ativa na Igreja B.

## 4. Autenticação e autorização

- Views internas devem usar `@login_required`.
- A política de autorização deve ser definida antes da implementação: permissões Django, grupo, superusuário ou acesso a todo usuário com igreja ativa.
- O menu nunca deve exibir um link para uma view que retorna 403 para o mesmo usuário por falta de permissão. Se uma funcionalidade usa permissões, o menu deve usar as mesmas permissões para decidir a visibilidade.
- Ao criar novas permissões, deve ser definido como usuários e grupos existentes receberão essas permissões. Não presumir que a criação automática de `auth.Permission` concede acesso.
- Se o requisito não pedir controle de permissões, a política adotada deve ser documentada e as views devem exigir, no mínimo, login e igreja ativa.
- Nunca remover uma checagem de permissão existente de outro módulo para corrigir um erro local.
- Acesso a objeto de outra igreja deve resultar em 404 (ou resposta equivalente segura), sem revelar se o objeto existe.

### Checklist específico para evitar 403 inesperado

Antes de adicionar `permission_required`:

- confirmar que o requisito realmente exige autorização distinta;
- verificar como o menu ficará para usuários sem a permissão;
- criar atribuição inicial por migration, grupo, comando de gestão ou instrução operacional, quando aplicável;
- criar teste para usuário sem e com a permissão;
- validar manualmente o fluxo com usuário real não-superusuário.

## 5. Modelos e banco

- Modelos de dados de igreja devem herdar de `TenantModel`, salvo justificativa documentada.
- Não duplicar `igreja`, `created_at` ou `updated_at` já fornecidos pelo tenant.
- Usar `on_delete` conscientemente e considerar integridade entre igrejas em ForeignKeys.
- Definir `verbose_name`, `verbose_name_plural`, `ordering` e `__str__` quando fizer sentido.
- Criar migration versionada para cada alteração de modelo.
- Rodar `manage.py makemigrations`, `manage.py migrate` e `manage.py check`.
- Não editar migrations já aplicadas para corrigir comportamento; criar nova migration.
- Não alterar dados de produção sem autorização explícita e migration segura.

## 6. Views e CRUD

Para CRUD de uma entidade de igreja, seguir este padrão:

- listagem: queryset filtrado por igreja;
- criação: formulário sem campo de igreja; atribuição server-side;
- detalhe: `get_object_or_404` filtrado por igreja;
- edição: objeto carregado filtrado por igreja antes de salvar;
- exclusão: objeto carregado filtrado por igreja, confirmação via POST e CSRF;
- redirecionamentos usando nomes de URL, não caminhos hard-coded quando houver alternativa;
- mensagens e textos da interface em português, seguindo o padrão existente.

POSTs devem usar CSRF. Exclusões não devem ocorrer via GET. Entradas do usuário devem ser validadas por `ModelForm` ou validação equivalente.

## 7. Formulários

- Usar `ModelForm` quando o formulário representar um modelo.
- Declarar explicitamente `fields`; nunca expor `igreja`.
- Reutilizar classes CSS e widgets Bootstrap existentes.
- Filtrar querysets de ForeignKeys pela igreja ativa.
- Validar relações entre horários, datas, valores e campos obrigatórios no formulário/modelo.
- Ao abrir cadastro a partir de outro contexto, valores pré-preenchidos devem ser validados e nunca considerados confiáveis.

## 8. URLs e templates

- Seguir o padrão `/modulo/`, `/modulo/novo/`, `/modulo/<id>/`, `/modulo/<id>/editar/` e `/modulo/<id>/excluir/` quando aplicável.
- Usar nomes de URL claros e únicos.
- Registrar o app em `INSTALLED_APPS` e incluir suas URLs em `config/urls.py`.
- Estender `base/base.html`; não criar layout paralelo.
- Reutilizar navbar, sidebar, cards, botões, alertas e estilos existentes.
- Atualizar o menu existente somente para apontar para a funcionalidade, sem duplicar item.
- Recursos JavaScript externos devem ter versão fixada e fallback ou comportamento aceitável quando não carregarem.

## 9. APIs e JSON

Endpoints JSON devem aplicar exatamente as mesmas regras de autenticação, igreja ativa e filtro tenant das views HTML. Nunca retornar registros de todas as igrejas. Validar datas e parâmetros inválidos sem gerar erro 500.

## 10. Testes obrigatórios

Para uma nova funcionalidade, criar testes proporcionais ao risco cobrindo:

- usuário anônimo;
- usuário autenticado sem igreja ativa;
- fluxo principal de criação;
- listagem/detalhe/edição/exclusão;
- validações do formulário;
- isolamento entre pelo menos duas igrejas;
- tentativa de acessar, editar e excluir ID de outra igreja;
- permissões, quando forem usadas;
- endpoint JSON, quando existir.

Executar pelo menos:

```text
python manage.py check
python manage.py test
python manage.py showmigrations
```

## 11. Checklist obrigatório antes de entregar

- [ ] Li esta especificação e identifiquei as regras aplicáveis.
- [ ] Inspecionei o padrão equivalente já existente no projeto.
- [ ] Defini a política de autenticação/autorização e garanti que o menu não aponta para acesso proibido.
- [ ] Toda query de tenant está filtrada pela igreja ativa.
- [ ] Criação, detalhe, edição e exclusão não permitem atravessar igrejas.
- [ ] Nenhum formulário expõe ou aceita `igreja` do usuário.
- [ ] Templates usam o layout existente.
- [ ] URLs, app e menu foram integrados sem duplicação.
- [ ] Migration foi criada e aplicada/verificada.
- [ ] `manage.py check` passou.
- [ ] Testes relevantes passaram.
- [ ] Mudanças fora do escopo foram evitadas.

Se uma implementação precisar divergir desta especificação, a divergência deve ser explicada ao usuário antes da alteração e registrada neste documento ou em uma decisão técnica vinculada à mudança.
