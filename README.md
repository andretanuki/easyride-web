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

## Estrutura do repositório

```
easyride-web/
├── backend/     # API Django/DRF (projeto core + app EasyRide)
├── frontend/    # Landing page React + Vite
└── docs/        # Contratos de API, arquitetura, DER e guia de acessibilidade
```

| Pasta | Conteúdo |
|---|---|
| [`backend/`](backend/) | API Django/DRF: captação de leads, conteúdo da landing e painel administrativo com RBAC |
| [`frontend/`](frontend/) | Landing page React + Vite que consome a API |
| [`docs/`](docs/) | Documentação do projeto (ver [Documentação](#documentação)) |

> As versões intermediárias do projeto (protótipo de banco da Fase 2, protótipo
> da API anterior ao RBAC e o experimento de front-end) foram consolidadas nesta
> estrutura. Elas continuam acessíveis pelo histórico, na tag
> [`entrega-fase3`](../../releases/tag/entrega-fase3).

## Como rodar o projeto

O projeto tem duas partes que precisam rodar ao mesmo tempo: o back-end (a API que guarda os dados) e o front-end (o site que a pessoa visitante vê).

### 1. Ligar o back-end

```bash
cd backend
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
[`backend/README.md`](backend/README.md).

Para rodar a suíte de testes automatizados:

```bash
python manage.py test
```

O roteiro completo de testes está em
[`backend/TESTING.md`](backend/TESTING.md).

### 2. Ligar o front-end

Em outro terminal, com o back-end já rodando:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

O site fica disponível em `http://localhost:3000/`. Mais detalhes em [`frontend/README.md`](frontend/README.md).

## Documentação

Os documentos do projeto estão em [`docs/`](docs/):

| Documento | Conteúdo |
|---|---|
| `Atualizacao_Contrato_API_v4.0.pdf` | **Contrato da API vigente** |
| `Arquitetura_Componentes_React_v3.0.pdf` | Árvore de componentes, props e estados do front-end |
| `Especificacao_Painel_Admnistrativo_e_Dados_Teste.pdf` | Especificação do painel administrativo |
| `Conformidade_Painel_Administrativo.pdf` | Registro de conformidade do painel com a especificação |
| `Guia_de_Estilos_e_Regras_de_Acessibilidade_WCAG.pdf` | Guia de estilos e regras de acessibilidade WCAG |
| `banco-dados/` | DER (completo e simplificado) e dicionário de dados do back-end (CSV e XLSX) |

O contrato de API v3.0, formalmente depreciado pelo v4.0, foi removido da pasta
e permanece disponível no histórico, na tag
[`entrega-fase3`](../../releases/tag/entrega-fase3).

## Equipe da Fase 3

- **André Luís** - Desenvolvedor Back-End - [GitHub](https://github.com/andretanuki) | [LinkedIn](https://www.linkedin.com/in/andretanuki/)
- **Flávia Rocha** - Desenvolvedora Front-End - [GitHub](https://github.com/flaviaa666) | [LinkedIn](https://www.linkedin.com/in/flaviarochassls/)
- **Flávia Sena** - Desenvolvedora Back-End - [GitHub](https://github.com/Flavia-Sena) | [LinkedIn](https://www.linkedin.com/in/fl%C3%A1via-sena-a462592b7/)
- **Dafne Santos** - Desenvolvedora Front-End - [GitHub](https://github.com/Dafnev5f)

O projeto foi construído de forma colaborativa pela equipe acima. Este
repositório é mantido por **André Luís**, que contribuiu em back-end e
front-end ao longo de toda a entrega.
