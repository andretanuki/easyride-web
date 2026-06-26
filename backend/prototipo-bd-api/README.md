# EasyRide Backend (API)

Este é o back-end do sistema EasyRide, desenvolvido em **Python/Django** com **Django Rest Framework (DRF)**. Ele fornece a API para captação de leads e gerenciamento de contatos do Kit de Automação EasyRide.

## Pré-requisitos
Certifique-se de ter o [Python 3.10+](https://www.python.org/downloads/) instalado na sua máquina.

## Passo a Passo para Rodar Localmente

Siga estas instruções para configurar o back-end no seu computador. Isso é necessário para que o Front-end consiga testar as requisições na máquina local.

### 1. Criar o Ambiente Virtual (.venv)
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

Para a documentação completa dos formatos JSON aceitos, consulte o documento `Atualizacao_Contrato_API.md`.

* `POST /api/leads/` - Criação de novos leads (Requer payload com `tipo_pessoa` FISICA ou JURIDICA).
* `GET /api/modelos/` - Lista os modelos de cadeiras disponíveis.

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
