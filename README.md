# EasyRide — Plataforma Web Institucional

Desafio Tecnológico da Fase 2 do Programa Bolsa Futuro Digital
Capacita 04 – Conecta e Capacita | CEPEDI

## Sobre o projeto
Plataforma web integrada para apresentação institucional da EasyRide
e gestão de leads do Programa Piloto.

## Tecnologias
- **Frontend:** React, HTML5, CSS3
- **Backend:** Python, Django, Django REST Framework

## Como rodar o projeto

O projeto tem duas partes que precisam rodar ao mesmo tempo: o back-end (a API que guarda os dados) e o front-end (o site que a pessoa visitante vê).

### 1. Ligar o back-end

```bash
cd backend/prototipo_backend
python -m venv .venv
source .venv/bin/activate      # no Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed          # preenche o banco com dados de exemplo
python manage.py runserver
```

A API fica disponível em `http://127.0.0.1:8000/`. Instruções mais detalhadas estão em [`backend/prototipo_backend/README.md`](backend/prototipo_backend/README.md).

### 2. Ligar o front-end

Em outro terminal, com o back-end já rodando:

```bash
cd frontend/experimento_front
npm install
cp .env.example .env
npm run dev
```

O site fica disponível em `http://localhost:3000/`. Mais detalhes em [`frontend/experimento_front/README.md`](frontend/experimento_front/README.md).

## Equipe
- **André Luís** - Desenvolvedor Back-End - [GitHub](https://github.com/andretanuki) | [LinkedIn](https://www.linkedin.com/in/andretanuki/)
- **Flávia Rocha** - Desenvolvedora Front-End - [GitHub](https://github.com/flaviaa666 ) | [LinkedIn](a ser preenchido pela equipe)
- **Flávia Sena** - Desenvolvedora Back-End - [GitHub]( a ser preenchido pela equipe) | [LinkedIn](a ser preenchido pela equipe)
- **Dafne Santos** - Desenvolvedora Front-End - [GitHub]( a ser preenchido pela equipe) | [LinkedIn](a ser preenchido pela equipe)
