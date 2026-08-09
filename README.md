# EasyRide - Plataforma Web Institucional

Plataforma web integrada para apresentação institucional da EasyRide
e gestão de leads do Programa Piloto.

> **Sobre este repositório**
>
> Projeto desenvolvido em equipe no Desafio Tecnológico da Fase 3 do Programa
> Bolsa Futuro Digital (Capacita 04 - Conecta e Capacita | CEPEDI).
>
> Este é um repositório pessoal, mantido para fins de portfólio com autorização
> da administração do programa. O repositório oficial da entrega é
> [easyride-g1lag/easyride-web](https://github.com/easyride-g1lag/easyride-web).
>
> O histórico de commits da equipe foi preservado integralmente, com a autoria
> original de cada pessoa. A tag
> [`entrega-fase3`](../../releases/tag/entrega-fase3) marca o encerramento do
> trabalho coletivo — commits posteriores a ela são de desenvolvimento
> individual.

## Tecnologias

- **Front-end:** React, Vite, HTML5, CSS3
- **Back-end:** Python, Django, Django REST Framework

## Onde está o código da entrega

O repositório guarda as versões intermediárias do projeto. **A entrega da
Fase 3 é composta por estas duas pastas:**

| Camada | Pasta da entrega |
|---|---|
| Back-end (API Django/DRF) | [`backend/entrega-backend/`](backend/entrega-backend/) |
| Front-end (landing page React) | [`frontend/entrega_front/`](frontend/entrega_front/) |

As demais pastas são etapas anteriores, mantidas apenas como registro do
percurso e **não fazem parte da versão final**:

- `backend/prototipo-bd-api/` - protótipo de banco de dados da Fase 2
- `backend/prototipo_backend/` - protótipo funcional da API, anterior ao RBAC do Admin
- `frontend/experimento_front/` - experimento de front-end anterior ao ajuste final

## Como rodar o projeto

O projeto tem duas partes que precisam rodar ao mesmo tempo: o back-end (a API que guarda os dados) e o front-end (o site que a pessoa visitante vê).

### 1. Ligar o back-end

```bash
cd backend/entrega-backend
python -m venv .venv
source .venv/bin/activate      # no Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed          # preenche o banco com dados de exemplo
python manage.py runserver
```

A API fica disponível em `http://127.0.0.1:8000/`, com documentação navegável
(Swagger UI) em `http://127.0.0.1:8000/api/docs/` e o painel administrativo em
`http://127.0.0.1:8000/admin/`. Instruções mais detalhadas estão em
[`backend/entrega-backend/README.md`](backend/entrega-backend/README.md).

Para rodar a suíte de testes automatizados:

```bash
python manage.py test
```

O roteiro completo de testes está em
[`backend/entrega-backend/TESTING.md`](backend/entrega-backend/TESTING.md).

### 2. Ligar o front-end

Em outro terminal, com o back-end já rodando:

```bash
cd frontend/entrega_front
npm install
cp .env.example .env
npm run dev
```

O site fica disponível em `http://localhost:3000/`. Mais detalhes em [`frontend/entrega_front/README.md`](frontend/entrega_front/README.md).

## Documentação

Os documentos do projeto estão em [`docs/`](docs/):

| Documento | Conteúdo |
|---|---|
| `Atualizacao_Contrato_API_v4.0.pdf` | **Contrato da API vigente** |
| `Especificacao_Contrato_API_v3.0_deprecated.pdf` | Contrato anterior, formalmente depreciado |
| `Arquitetura_Componentes_React_v3.0.pdf` | Árvore de componentes, props e estados do front-end |
| `Especificacao_Painel_Admnistrativo_e_Dados_Teste.pdf` | Especificação do painel administrativo |
| `Conformidade_Painel_Administrativo.pdf` | Registro de conformidade do painel com a especificação |
| `der/` | Diagrama Entidade-Relacionamento (completo e simplificado) |
| `dicionario-dados/` | Dicionário de dados do back-end (CSV e XLSX) |
| `wireframe/` | Guia de estilos e regras de acessibilidade WCAG |

## Equipe da Fase 3

- **André Luís** - Desenvolvedor Back-End - [GitHub](https://github.com/andretanuki) | [LinkedIn](https://www.linkedin.com/in/andretanuki/)
- **Flávia Rocha** - Desenvolvedora Front-End - [GitHub](https://github.com/flaviaa666) | [LinkedIn](https://www.linkedin.com/in/flaviarochassls/)
- **Flávia Sena** - Desenvolvedora Back-End - [GitHub](https://github.com/Flavia-Sena) | [LinkedIn](https://www.linkedin.com/in/fl%C3%A1via-sena-a462592b7/)
- **Dafne Santos** - Desenvolvedora Front-End - [GitHub](https://github.com/Dafnev5f)

O projeto foi construído de forma colaborativa pela equipe acima. Este
repositório é mantido por **André Luís**, que contribuiu em back-end e
front-end ao longo de toda a entrega.
