# EasyRide Backend (API)

Este é o back-end do sistema EasyRide, desenvolvido em **Python/Django** com **Django Rest Framework (DRF)**. Ele fornece a API para captação de leads e gerenciamento de contatos do Kit de Automação EasyRide.

## Pré-requisitos
Certifique-se de ter o [Python 3.10+](https://www.python.org/downloads/) instalado na sua máquina.

## Passo a Passo para Rodar Localmente

Siga estas instruções para configurar o back-end no seu computador. Isso é necessário para que o Front-end consiga testar as requisições na máquina local.

### 1. Criar o Ambiente Virtual (.venv) — **obrigatório**
Um venv dedicado não é apenas recomendado: é **obrigatório**. Uma instalação
global de Python com versões diferentes das fixadas no `requirements.txt`
(ex.: Django 5.x global vs. Django 6.0.6 exigido) não gera nenhum erro visível
ao rodar o servidor, mas pode produzir diferenças sutis de comportamento —
sempre crie e ative o venv antes de instalar as dependências.

Abra o terminal na raiz deste projeto e rode:
```bash
# No Windows
python -m venv .venv

# No Linux/Mac
python3 -m venv .venv
```

### 2. Ativar o Ambiente Virtual
```bash
# No Windows
.venv\Scripts\activate

# No Linux/Mac
source .venv/bin/activate
```
*(Você saberá que deu certo se aparecer `(.venv)` no início da linha do terminal)*.

### 3. Instalar as Dependências
Com o ambiente ativado, instale as bibliotecas necessárias:
```bash
pip install -r requirements.txt
```

### 4. Criar o Banco de Dados (Migrations)
O projeto usa SQLite local para desenvolvimento. Para criar o banco e as tabelas, rode:
```bash
python manage.py migrate
```

### 5. Popular o Banco de Dados com Dados de Teste (Seed)
Nós criamos um script para preencher o seu banco de dados automaticamente com Modelos de cadeiras, Pessoas Físicas, Jurídicas e dezenas de leads. Assim, você não precisa cadastrar nada na mão para poder testar o Front-end!
```bash
python manage.py seed
```

### 6. Rodar o Servidor
Finalmente, ligue o servidor da API:
```bash
python manage.py runserver
```
O servidor estará rodando em `http://127.0.0.1:8000/`.

---

## Rotas Disponíveis

Para a documentação completa dos formatos JSON aceitos, consulte o documento `Atualizacao_Contrato_API.md` ou a documentação viva em `/api/docs/` (ver abaixo).

* `POST /api/leads/` - Criação de novos leads (Requer payload com `tipo_pessoa` FISICA ou JURIDICA). Público.
* `GET /api/leads/`, `GET /api/leads/{id}/`, `GET /api/leads/estatisticas/`, `PATCH /api/leads/{id}/status/` - Consulta e gestão de leads. Restrito a usuários staff.
* `GET /api/modelos/` - Lista os modelos de cadeiras disponíveis. Público.
* `POST/PUT/PATCH/DELETE /api/modelos/` - CRUD de modelos. Restrito a usuários staff.
* `GET /api/beneficios/`, `GET /api/depoimentos/`, `GET /api/faq/` - Conteúdo dinâmico da landing page (rotas cacheadas). Público.

## Documentação Viva da API (Swagger)

A API expõe documentação OpenAPI gerada automaticamente a partir do código via `drf-spectacular`:

* `GET /api/schema/` - Schema OpenAPI em YAML.
* `GET /api/docs/` - Interface Swagger UI navegável, com exemplos de payload FISICA e JURIDICA.

## Rodando os Testes

A suíte de testes automatizados cobre validadores, models, services e endpoints da API. Para executar:

```bash
python manage.py test
```

Para um guia completo (rodar testes específicos, padrões de escrita, helpers e troubleshooting), consulte o [`TESTING.md`](./TESTING.md).

---

## Acesso ao Painel Administrativo
O Django gera um painel de administração automaticamente. Após rodar o comando `seed`, um superusuário de teste é criado (se estiver configurado no script), ou você pode criar o seu próprio:
```bash
python manage.py createsuperuser
```
Acesse em: `http://127.0.0.1:8000/admin/`

---

## Deploy em Nuvem (Render, plano gratuito)

O projeto já está preparado para deploy no Render: `gunicorn` + `whitenoise` (arquivos estáticos do Admin) + `dj-database-url` + `psycopg[binary]` (Postgres) já estão em `requirements.txt`, e há um `build.sh` e um `render.yaml` na raiz do projeto.

### Variáveis de ambiente necessárias em produção

| Variável | Valor / Exemplo | Observação |
|---|---|---|
| `DJANGO_SECRET_KEY` | chave aleatória forte | Obrigatória quando `DJANGO_DEBUG=False` — o servidor não sobe sem ela. |
| `DJANGO_DEBUG` | `False` | Ativa HSTS, `SECURE_SSL_REDIRECT`, cookies seguros. |
| `DJANGO_ALLOWED_HOSTS` | `easyride-api.onrender.com` | Domínio real atribuído pelo Render. |
| `CORS_ALLOWED_ORIGINS` | `https://easyride.example.com` | URL do frontend publicado. |
| `CORS_ALLOW_ALL_ORIGINS` | `false` | Manter `false` em produção. |
| `DATABASE_URL` | injetada automaticamente pelo Render | Ao provisionar um banco Postgres gerenciado. |
| `CACHE_BACKEND` | `database` | Usa `DatabaseCache` (Render free não tem Redis). |
| `CACHE_TTL_CONTEUDO` | `900` | TTL em segundos das rotas de conteúdo dinâmico. |

### Passos

1. Rodar `python manage.py createcachetable` uma vez após o primeiro deploy (o `CACHE_BACKEND=database` exige a tabela existir).
2. Criar o superusuário em produção via shell do Render: `python manage.py createsuperuser`.
3. Rodar `python manage.py seed` em produção, se desejado, para popular dados de exemplo.
4. Validar `/admin/`, `/api/docs/` e um `POST /api/leads/` real após o deploy.

### Ponto em aberto

O `EasyRide/` (esta pasta) está sendo desenvolvido **fora do controle do git**, por decisão explícita da equipe. Como o Render normalmente faz deploy observando um repositório git remoto, falta decidir **como este código chega até o Render** antes do deploy real acontecer — por exemplo, portando o conteúdo de volta para dentro do repositório oficial `easyride-web/backend/prototipo-bd-api/`, ou outra estratégia a definir. A preparação de código acima (dependências, configurações, `build.sh`, `render.yaml`) não depende dessa decisão, mas o deploy em si sim.
