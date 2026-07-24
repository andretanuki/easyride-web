# Guia de Testes — EasyRide Backend

Este documento descreve como executar e estender a suíte de testes automatizados do backend EasyRide.

---

## Pré-requisitos

Antes de rodar os testes, certifique-se de que o ambiente está preparado conforme o `README.md` principal:

1. Ambiente virtual ativado (`.venv`)
2. Dependências instaladas (`pip install -r requirements.txt`)

**Não é necessário rodar `migrate` ou `seed`** — o Django cria um banco de dados isolado em memória para cada execução de teste.

---

## Executando os Testes

### Rodar toda a suíte

A partir da pasta `backend/prototipo-bd-api/`, execute:

```bash
python manage.py test
```

Saída esperada (resumo):

```
Ran 56 tests in 0.196s

OK
```

### Rodar com saída detalhada

```bash
python manage.py test -v 2
```

A flag `-v 2` (verbosity 2) mostra o nome de cada teste à medida que ele é executado, útil para identificar falhas pontuais.

### Rodar apenas um arquivo, classe ou teste específico

```bash
# Apenas os testes do app EasyRide
python manage.py test EasyRide

# Apenas a classe de testes do endpoint de leads
python manage.py test EasyRide.tests.LeadAPITest

# Apenas um teste específico
python manage.py test EasyRide.tests.LeadAPITest.test_criar_lead_fisica_sucesso_retorna_201

# Apenas os testes dos validadores de CPF/CNPJ
python manage.py test EasyRide.tests.ValidadorCpfTest EasyRide.tests.ValidadorCnpjTest
```

### Parar na primeira falha

Útil em ciclos rápidos de TDD:

```bash
python manage.py test --failfast
```

### Manter o banco de testes entre execuções

Acelera execuções repetidas (o Django pula a criação/destruição do schema):

```bash
python manage.py test --keepdb
```

---

## Estrutura da Suíte

Todos os testes vivem em `EasyRide/tests.py` e estão organizados em classes por responsabilidade:

| Classe | Responsabilidade | Tipo |
|--------|------------------|------|
| `ValidadorCpfTest` | Algoritmo de DV do CPF | Unitário |
| `ValidadorCnpjTest` | Algoritmo de DV do CNPJ | Unitário |
| `PessoaModelTest` | Model `Pessoa` (criação, unicidade, `__str__`) | Model |
| `PessoaFisicaModelTest` | Model `PessoaFisica` (relação 1:1) | Model |
| `ModeloModelTest` | Model `Modelo` (representação textual) | Model |
| `CriarLeadFisicaServiceTest` | Service `criar_lead` para Pessoa Física | Service |
| `CriarLeadJuridicaServiceTest` | Service `criar_lead` para Pessoa Jurídica | Service |
| `AtualizarStatusLeadTest` | Service `atualizar_status_lead` | Service |
| `LeadAPITest` | Endpoints `GET`/`POST /api/leads/` | Integração HTTP |
| `AtualizarStatusLeadAPITest` | Endpoint `PATCH /api/leads/{id}/status/` | Integração HTTP |
| `ModeloAPITest` | Endpoints de Modelos (CRUD) | Integração HTTP |
| `EstatisticasAPITest` | Endpoint `GET /api/leads/estatisticas/` | Integração HTTP |

### Cobertura por área

- **Validação de dígito verificador** (CPF e CNPJ): formato sem máscara, com máscara, vazio, tamanho incorreto, sequências repetidas, DV errado
- **Códigos HTTP do contrato da API**: 200 (consulta), 201 (criação), 400 (validação), 404 (não encontrado), 409 (conflito de e-mail)
- **Validações de payload**: aceite de termos obrigatório, `modelo_id` existente, `tipo_pessoa` exige sub-objeto correto, `choices` (perfil, tipo_instituicao, origem) respeitados
- **Persistência**: lead criado realmente aparece em `Pessoa`, `PessoaFisica`/`PessoaJuridica` e `Interesse`
- **Formato de resposta**: estrutura aninhada com `pessoa`/`modelo`, formato de erro `{ "campo": ..., "mensagem": ... }`

---

## Padrões de Escrita

### Helpers reutilizáveis

Os arquivos de teste compartilham dois helpers para evitar duplicação:

```python
_dados_lead_fisica(modelo_pk, **overrides)   # payload válido para PF
_dados_lead_juridica(modelo_pk, **overrides) # payload válido para PJ
```

Use-os ao escrever novos testes e sobrescreva apenas os campos relevantes:

```python
def test_meu_caso(self):
    payload = _dados_lead_fisica(self.modelo.pk)
    payload['dados_fisica']['cpf'] = '11111111111'  # caso específico
    response = self.client.post(self.url, payload, format='json')
    self.assertEqual(response.status_code, 400)
```

### Convenção de nomes

Os testes seguem o padrão `test_<acao>_<condicao>_<resultado_esperado>`:

- `test_criar_lead_fisica_sucesso_retorna_201`
- `test_criar_lead_sem_aceite_retorna_400`
- `test_atualizar_status_lead_inexistente_retorna_404`

### Dados de teste

CPFs e CNPJs usados nos testes **precisam ter dígito verificador válido** (a validação é aplicada). Para gerar valores corretos, consulte `EasyRide/validators.py` ou use os exemplos já presentes em `tests.py` como referência.

---

## Resolvendo Problemas Comuns

### `django.db.utils.OperationalError: no such table`

O banco de testes não foi criado. Isso normalmente acontece quando se usa `--keepdb` após mudanças em migrations. Solução: rode sem a flag uma vez.

### Teste de API recebe 404 em URL conhecida

Verifique se o `reverse('nome-da-rota')` está usando o `basename` correto definido em `EasyRide/urls.py`.

### Teste falha por causa de throttling

Os testes de criação de lead usam `LeadThrottle` (5 req/min). Se você criar muitos leads em uma classe de teste, pode encontrar `429 Too Many Requests`. Solução: use `APITestCase` (já em uso), que isola o cache de throttle entre testes.

---

## Adicionando Novos Testes

1. Identifique a classe certa em `tests.py` (ou crie uma nova seguindo o padrão de cabeçalhos `# ──────`)
2. Escreva o teste com nome descritivo (`test_<acao>_<condicao>_<resultado>`)
3. Reutilize os helpers `_dados_lead_fisica` / `_dados_lead_juridica` quando possível
4. Rode o teste isoladamente primeiro: `python manage.py test EasyRide.tests.MinhaClasse.test_meu_caso -v 2`
5. Rode a suíte completa antes de fazer commit: `python manage.py test`

---

## Métricas Atuais

- **Total de testes:** 56
- **Tempo de execução:** ~0,2 s
- **Última execução verificada:** todos passando (`OK`)
