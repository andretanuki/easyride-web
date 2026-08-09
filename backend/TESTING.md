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

A partir da pasta `backend/`, execute:

```bash
python manage.py test
```

Saída esperada (resumo):

```
Ran 98 tests in 1.9s

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
| `LeadThrottleAPITest` | Rate limit do `POST /api/leads/` (5/min → 429) | Integração HTTP |
| `AtualizarStatusLeadAPITest` | Endpoint `PATCH /api/leads/{id}/status/` | Integração HTTP |
| `PessoaAPITest` | Endpoint `GET /api/pessoas/` (restrito a staff) | Integração HTTP |
| `ModeloAPITest` | Endpoints de Modelos (CRUD) | Integração HTTP |
| `EstatisticasAPITest` | Endpoint `GET /api/leads/estatisticas/` | Integração HTTP |
| `BeneficioAPITest` | Endpoint `GET /api/beneficios/` + cache | Integração HTTP |
| `DepoimentoAPITest` | Endpoint `GET /api/depoimentos/` + cache | Integração HTTP |
| `FaqAPITest` | Endpoint `GET /api/faq/` + cache | Integração HTTP |
| `InteresseAdminExportTest` | Ação de exportação CSV no Django Admin | Admin |
| `InteresseAdminTriagemTest` | Filtro B2C/B2B, busca por documento, colunas da listagem | Admin |
| `PessoaAdminEmailTest` | Duplicidade de e-mail na tela de Pessoa (regressão de 500) | Admin |
| `MatrizRbacTest` | Grupos de acesso e restrições por função (item 5 da Especificação) | Admin |
| `SeedMassaDocumentoTest` | Massa nomeada do item 8 da Especificação (15 registros) | Seed |
| `SeedVolumeTest` | Geração de volume para o CT02 (`seed --bulk N`) | Seed |
| `Ct02PaginacaoTest` | Paginação profunda e ordenação estável ao mudar de página | Admin |

### Cobertura por área

- **Validação de dígito verificador** (CPF e CNPJ): formato sem máscara, com máscara, vazio, tamanho incorreto, sequências repetidas, DV errado
- **Códigos HTTP do contrato da API**: 200 (consulta), 201 (criação), 400 (validação), 401 (rotas restritas a staff), 404 (não encontrado), 409 (conflito de e-mail, inclusive com capitalização diferente), 429 (throttle de 5/min no POST de leads)
- **Validações de payload**: aceite de termos obrigatório, `modelo_id` existente, `tipo_pessoa` exige sub-objeto correto, `choices` (perfil, tipo_instituicao, origem) respeitados
- **Persistência**: lead criado realmente aparece em `Pessoa`, `PessoaFisica`/`PessoaJuridica` e `Interesse`
- **Formato de resposta**: estrutura aninhada com `pessoa`/`modelo`, erro 400 no formato hierárquico nativo do DRF (Contrato v3.0 §6)
- **Painel administrativo**: filtros laterais, busca por CPF/CNPJ/telefone, exportação CSV (header, delimitador, BOM), paginação de 25, matriz RBAC dos 3 grupos e massa de teste do item 8 — ver [`docs/Conformidade_Painel_Administrativo.pdf`](../docs/Conformidade_Painel_Administrativo.pdf)

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

Pelo mesmo motivo, os documentos da massa do item 8 da Especificação (`111.222.333-44` e afins) não são usados literalmente: o seed preserva o prefixo e recalcula o DV. Os helpers `_cpf_valido` / `_cnpj_valido` em `seed.py` fazem isso para a massa sintética do CT02.

---

## Resolvendo Problemas Comuns

### `django.db.utils.OperationalError: no such table`

O banco de testes não foi criado. Isso normalmente acontece quando se usa `--keepdb` após mudanças em migrations. Solução: rode sem a flag uma vez.

### Teste de API recebe 404 em URL conhecida

Verifique se o `reverse('nome-da-rota')` está usando o `basename` correto definido em `EasyRide/urls.py`.

### Teste falha por causa de throttling

O `POST /api/leads/` tem rate limit real de 5 req/min por IP (`throttle_scope = 'leads'` na `LeadViewSet`). O histórico do throttle vive no cache, que o Django **não** limpa entre testes — qualquer classe que crie leads via API precisa de `cache.clear()` no `setUp` (padrão já adotado em `LeadAPITest` e `LeadThrottleAPITest`), e um único método de teste não pode fazer mais de 5 POSTs de lead.

---

## Adicionando Novos Testes

1. Identifique a classe certa em `tests.py` (ou crie uma nova seguindo o padrão de cabeçalhos `# ──────`)
2. Escreva o teste com nome descritivo (`test_<acao>_<condicao>_<resultado>`)
3. Reutilize os helpers `_dados_lead_fisica` / `_dados_lead_juridica` quando possível
4. Rode o teste isoladamente primeiro: `python manage.py test EasyRide.tests.MinhaClasse.test_meu_caso -v 2`
5. Rode a suíte completa antes de fazer commit: `python manage.py test`

---

## Métricas Atuais

- **Total de testes:** 146
- **Tempo de execução:** ~52 s (os testes de seed com volume dominam o tempo)
- **Última execução verificada:** todos passando (`OK`)
