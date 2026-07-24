"""Testes automatizados do app EasyRide.

Cobertura: models, services, selectors e endpoints da API.
Todos os testes de lead usam o novo payload aninhado (LeadSerializer).
"""

import itertools

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Pessoa, PessoaFisica, PessoaJuridica, Modelo, Interesse, Beneficio, Depoimento, Faq
from .validators import validar_cpf, validar_cnpj
from . import services, selectors


# ──────────────────────────────────────────────────────────────
# Testes dos Validadores de CPF e CNPJ
# ──────────────────────────────────────────────────────────────

class ValidadorCpfTest(TestCase):
    """Testes unitários para validar_cpf (dígito verificador)."""

    def test_cpf_valido_sem_formatacao(self):
        validar_cpf('12345678909')  # não deve levantar

    def test_cpf_valido_com_formatacao(self):
        validar_cpf('123.456.789-09')  # não deve levantar

    def test_cpf_vazio_e_aceito(self):
        validar_cpf('')  # não deve levantar
        validar_cpf(None)  # não deve levantar

    def test_cpf_tamanho_incorreto(self):
        with self.assertRaises(ValidationError):
            validar_cpf('123')

    def test_cpf_sequencia_repetida_invalida(self):
        for d in '0123456789':
            with self.assertRaises(ValidationError):
                validar_cpf(d * 11)

    def test_cpf_digito_verificador_errado(self):
        with self.assertRaises(ValidationError):
            validar_cpf('12345678900')


class ValidadorCnpjTest(TestCase):
    """Testes unitários para validar_cnpj (dígito verificador)."""

    def test_cnpj_valido_sem_formatacao(self):
        validar_cnpj('12345678000195')

    def test_cnpj_valido_com_formatacao(self):
        validar_cnpj('12.345.678/0001-95')

    def test_cnpj_vazio_e_aceito(self):
        validar_cnpj('')
        validar_cnpj(None)

    def test_cnpj_tamanho_incorreto(self):
        with self.assertRaises(ValidationError):
            validar_cnpj('123')

    def test_cnpj_sequencia_repetida_invalida(self):
        with self.assertRaises(ValidationError):
            validar_cnpj('11111111111111')

    def test_cnpj_digito_verificador_errado(self):
        with self.assertRaises(ValidationError):
            validar_cnpj('12345678000100')


# ──────────────────────────────────────────────────────────────
# Testes de Models
# ──────────────────────────────────────────────────────────────

class PessoaModelTest(TestCase):
    """Testes para o model Pessoa."""

    def setUp(self):
        self.pessoa = Pessoa.objects.create(
            nome='João Silva',
            email='joao@email.com',
            telefone='11999999999',
            estado='SP',
            cidade='São Paulo',
        )

    def test_str_representation(self):
        self.assertEqual(str(self.pessoa), 'João Silva (joao@email.com)')

    def test_email_unique(self):
        with self.assertRaises(Exception):
            Pessoa.objects.create(nome='Outro', email='joao@email.com')

    def test_criado_em_auto(self):
        self.assertIsNotNone(self.pessoa.criado_em)


class PessoaFisicaModelTest(TestCase):
    """Testes para o model PessoaFisica."""

    def setUp(self):
        self.pessoa = Pessoa.objects.create(
            nome='Maria Souza', email='maria@email.com'
        )
        self.pf = PessoaFisica.objects.create(
            pessoa=self.pessoa,
            cpf='12345678909',
            perfil='paciente',
            comunicacao_verbal_preservada=True,
        )

    def test_str_representation(self):
        self.assertEqual(str(self.pf), 'Maria Souza - PF')

    def test_one_to_one_relationship(self):
        self.assertEqual(self.pessoa.pessoa_fisica, self.pf)


class ModeloModelTest(TestCase):
    """Testes para o model Modelo."""

    def setUp(self):
        self.modelo = Modelo.objects.create(
            nome_modelo='Freedom One',
            marca='Freedom',
            motorizada=True,
        )

    def test_str_motorizada(self):
        self.assertIn('Motorizada', str(self.modelo))

    def test_str_manual(self):
        modelo_manual = Modelo.objects.create(
            nome_modelo='Compacta', marca='Ortobras', motorizada=False
        )
        self.assertIn('Manual', str(modelo_manual))


# ──────────────────────────────────────────────────────────────
# Helpers compartilhados nos testes de service e API
# ──────────────────────────────────────────────────────────────

_contador_cpf = itertools.count()


def _gerar_cpf_valido():
    """Gera um CPF com dígito verificador correto e único por chamada.

    PessoaFisica.cpf tem unique=True (e strings vazias também colidem no
    UNIQUE do SQLite), então testes que criam vários leads físicos em loop
    precisam de um CPF novo a cada iteração.
    """
    n = next(_contador_cpf)
    base = [int(d) for d in f'{100000000 + n:09d}']

    def _dv(digitos, pesos):
        resto = sum(d * p for d, p in zip(digitos, pesos)) % 11
        return 0 if resto < 2 else 11 - resto

    dv1 = _dv(base, list(range(10, 1, -1)))
    dv2 = _dv(base + [dv1], list(range(11, 1, -1)))
    return ''.join(map(str, base + [dv1, dv2]))


def _dados_lead_fisica(modelo_pk, **overrides):
    """Retorna um dicionário aninhado válido para lead de Pessoa Física."""
    dados = {
        'tipo_pessoa': 'FISICA',
        'nome': 'Carlos Lima',
        'email': 'carlos@email.com',
        'telefone': '71988887777',
        'estado': 'BA',
        'cidade': 'Salvador',
        'dados_fisica': {
            'cpf': '98765432100',
            'perfil': 'familiar',
            'comunicacao_verbal_preservada': False,
            'tipo_deficiencia': 'Motora',
        },
        'interesse': {
            'modelo_id': modelo_pk,
            'quantidade_estimada': 1,
            'mensagem': 'Tenho interesse no kit.',
            'origem': 'google',
            'aceite_termos': True,
            'possui_cadeira': True,
        },
    }
    dados.update(overrides)
    return dados


def _dados_lead_juridica(modelo_pk, **overrides):
    """Retorna um dicionário aninhado válido para lead de Pessoa Jurídica."""
    dados = {
        'tipo_pessoa': 'JURIDICA',
        'nome': 'Clínica Esperança',
        'email': 'contato@clinica.com',
        'telefone': '7133334444',
        'estado': 'BA',
        'cidade': 'Feira de Santana',
        'dados_juridica': {
            'cnpj': '12345678000195',
            'tipo_instituicao': 'clinica',
            'contato_responsavel': 'Dr. Pedro',
            'cargo_responsavel': 'Diretor Clínico',
        },
        'interesse': {
            'modelo_id': modelo_pk,
            'quantidade_estimada': 5,
            'mensagem': 'Para nosso setor de reabilitação.',
            'origem': 'indicacao',
            'aceite_termos': True,
            'possui_cadeira': False,
        },
    }
    dados.update(overrides)
    return dados


def _criar_usuario_staff(username='staff_test'):
    """Cria (ou reaproveita) um usuário staff para testes de rotas protegidas
    por IsAdminUser (leads, estatísticas, escrita de modelos)."""
    user, _ = User.objects.get_or_create(
        username=username, defaults={'is_staff': True}
    )
    if not user.is_staff:
        user.is_staff = True
        user.save(update_fields=['is_staff'])
    return user


# ──────────────────────────────────────────────────────────────
# Testes do Service criar_lead
# ──────────────────────────────────────────────────────────────

class CriarLeadFisicaServiceTest(TestCase):
    """Testes para o serviço criar_lead com Pessoa Física."""

    def setUp(self):
        self.modelo = Modelo.objects.create(
            nome_modelo='Power Lite', marca='Quickie', motorizada=True
        )

    def test_criar_lead_fisica_completo(self):
        dados = _dados_lead_fisica(self.modelo.pk)
        interesse = services.criar_lead(dados)

        self.assertEqual(interesse.pessoa.nome, 'Carlos Lima')
        self.assertEqual(interesse.pessoa.email, 'carlos@email.com')
        self.assertEqual(interesse.pessoa.pessoa_fisica.perfil, 'familiar')
        self.assertFalse(interesse.pessoa.pessoa_fisica.comunicacao_verbal_preservada)
        self.assertEqual(interesse.origem, 'google')
        self.assertEqual(interesse.status_lead, 'novo')
        self.assertTrue(interesse.possui_cadeira)

    def test_criar_lead_fisica_pessoa_existente_retorna_erro(self):
        """De acordo com o contrato atualizado, e-mail já cadastrado deve gerar conflito."""
        Pessoa.objects.create(nome='Existente', email='carlos@email.com')
        dados = _dados_lead_fisica(self.modelo.pk)
        from django.db.utils import IntegrityError
        with self.assertRaises(IntegrityError):
            services.criar_lead(dados)

    def test_criar_lead_fisica_sem_dados_opcionais(self):
        """Deve criar lead sem campos opcionais de PessoaFisica."""
        dados = {
            'tipo_pessoa': 'FISICA',
            'nome': 'Simples',
            'email': 'simples@email.com',
            'dados_fisica': {'perfil': 'paciente'},
            'interesse': {
                'modelo_id': self.modelo.pk,
                'aceite_termos': True,
            },
        }
        interesse = services.criar_lead(dados)
        self.assertIsNotNone(interesse.pk)
        self.assertEqual(interesse.pessoa.pessoa_fisica.perfil, 'paciente')


class CriarLeadJuridicaServiceTest(TestCase):
    """Testes para o serviço criar_lead com Pessoa Jurídica."""

    def setUp(self):
        self.modelo = Modelo.objects.create(
            nome_modelo='Freedom CGR', marca='Freedom', motorizada=True
        )

    def test_criar_lead_juridica_completo(self):
        dados = _dados_lead_juridica(self.modelo.pk)
        interesse = services.criar_lead(dados)

        self.assertEqual(interesse.pessoa.nome, 'Clínica Esperança')
        self.assertEqual(interesse.pessoa.pessoa_juridica.tipo_instituicao, 'clinica')
        self.assertEqual(interesse.pessoa.pessoa_juridica.contato_responsavel, 'Dr. Pedro')
        self.assertEqual(interesse.quantidade_estimada, 5)
        self.assertEqual(interesse.origem, 'indicacao')

    def test_criar_lead_juridica_sem_cnpj(self):
        """Deve criar lead jurídico mesmo sem CNPJ (campo opcional)."""
        dados = {
            'tipo_pessoa': 'JURIDICA',
            'nome': 'ONG Sorrir',
            'email': 'ong@sorrir.org',
            'dados_juridica': {'tipo_instituicao': 'ong'},
            'interesse': {
                'modelo_id': self.modelo.pk,
                'aceite_termos': True,
            },
        }
        interesse = services.criar_lead(dados)
        self.assertEqual(interesse.pessoa.pessoa_juridica.tipo_instituicao, 'ong')


class AtualizarStatusLeadTest(TestCase):
    """Testes para o serviço atualizar_status_lead."""

    def setUp(self):
        self.pessoa = Pessoa.objects.create(nome='Test', email='test@email.com')
        self.modelo = Modelo.objects.create(
            nome_modelo='Teste', marca='Marca', motorizada=True
        )
        self.interesse = Interesse.objects.create(
            pessoa=self.pessoa, modelo=self.modelo,
            aceite_termos=True, status_lead='novo'
        )

    def test_atualizar_status_valido(self):
        resultado = services.atualizar_status_lead(self.interesse.pk, 'contatado')
        self.assertEqual(resultado.status_lead, 'contatado')

    def test_atualizar_status_invalido(self):
        with self.assertRaises(ValueError):
            services.atualizar_status_lead(self.interesse.pk, 'invalido')

    def test_atualizar_status_nao_encontrado(self):
        with self.assertRaises(Interesse.DoesNotExist):
            services.atualizar_status_lead(99999, 'contatado')


# ──────────────────────────────────────────────────────────────
# Testes de API (Endpoints)
# ──────────────────────────────────────────────────────────────

class LeadAPITest(APITestCase):
    """Testes de integração para o endpoint unificado de leads (POST /api/leads/)."""

    def setUp(self):
        # O throttle de leads (5/min por IP) conta requisições no cache,
        # que o Django não limpa entre testes — sem isto, os POSTs se
        # acumulam entre métodos e a suíte passa a receber 429.
        cache.clear()
        self.modelo = Modelo.objects.create(
            nome_modelo='Power Lite', marca='Quickie', motorizada=True
        )
        self.url = reverse('lead-list')

    # ── Sucesso: Pessoa Física ────────────────────────────────

    def test_criar_lead_fisica_sucesso_retorna_201(self):
        payload = _dados_lead_fisica(self.modelo.pk)
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_criar_lead_fisica_retorna_formato_contrato(self):
        """Resposta deve seguir exatamente o formato definido no contrato da API."""
        payload = _dados_lead_fisica(self.modelo.pk)
        response = self.client.post(self.url, payload, format='json')
        data = response.data
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['mensagem'], 'Lead cadastrado com sucesso')
        self.assertIn('dados', data)
        self.assertIn('id', data['dados'])
        self.assertEqual(data['dados']['tipo_pessoa'], 'FISICA')
        self.assertEqual(data['dados']['email'], 'carlos@email.com')

    def test_criar_lead_fisica_persiste_no_banco(self):
        payload = _dados_lead_fisica(self.modelo.pk)
        self.client.post(self.url, payload, format='json')
        self.assertTrue(Pessoa.objects.filter(email='carlos@email.com').exists())
        self.assertTrue(PessoaFisica.objects.filter(pessoa__email='carlos@email.com').exists())
        self.assertTrue(Interesse.objects.filter(pessoa__email='carlos@email.com').exists())

    def test_criar_lead_fisica_email_existente_retorna_409(self):
        """Conflito (Email já Cadastrado) deve retornar HTTP 409 Conflict."""
        # Cria uma pessoa com o email
        Pessoa.objects.create(nome='Existente', email='carlos@email.com')
        
        payload = _dados_lead_fisica(self.modelo.pk)
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['mensagem'], 'Lead já cadastrado')

    # ── Sucesso: Pessoa Jurídica ──────────────────────────────

    def test_criar_lead_juridica_sucesso_retorna_201(self):
        payload = _dados_lead_juridica(self.modelo.pk)
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_criar_lead_juridica_retorna_formato_contrato(self):
        payload = _dados_lead_juridica(self.modelo.pk)
        response = self.client.post(self.url, payload, format='json')
        data = response.data
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['dados']['tipo_pessoa'], 'JURIDICA')

    def test_criar_lead_juridica_persiste_no_banco(self):
        payload = _dados_lead_juridica(self.modelo.pk)
        self.client.post(self.url, payload, format='json')
        self.assertTrue(PessoaJuridica.objects.filter(pessoa__email='contato@clinica.com').exists())

    # ── Validação: aceite_termos ──────────────────────────────

    def test_criar_lead_sem_aceite_retorna_400(self):
        payload = _dados_lead_fisica(self.modelo.pk)
        payload['interesse']['aceite_termos'] = False
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_lead_sem_aceite_retorna_formato_erro_contrato(self):
        """Erro de validação deve seguir o formato hierárquico nativo do DRF (Contrato v3.0)."""
        payload = _dados_lead_fisica(self.modelo.pk)
        payload['interesse']['aceite_termos'] = False
        response = self.client.post(self.url, payload, format='json')
        data = response.data
        self.assertIn('interesse', data)
        self.assertIn('aceite_termos', data['interesse'])
        self.assertIsInstance(data['interesse']['aceite_termos'], list)
        self.assertGreater(len(data['interesse']['aceite_termos']), 0)

    def test_criar_lead_email_ausente_e_cpf_invalido_retorna_erros_hierarquicos(self):
        """Reproduz o exemplo do Contrato v3.0 §6: email ausente + CPF inválido
        deve retornar um dict com 'email' na raiz e 'cpf' aninhado em 'dados_fisica',
        sem nenhum wrapper 'status'/'mensagem'/'erros'."""
        payload = _dados_lead_fisica(self.modelo.pk)
        del payload['email']
        payload['dados_fisica']['cpf'] = '111.111.111-11'
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.data
        self.assertNotIn('status', data)
        self.assertNotIn('erros', data)
        self.assertIn('email', data)
        self.assertIn('dados_fisica', data)
        self.assertIn('cpf', data['dados_fisica'])

    # ── Validação: modelo_id inexistente ──────────────────────

    def test_criar_lead_modelo_invalido_retorna_400(self):
        payload = _dados_lead_fisica(self.modelo.pk)
        payload['interesse']['modelo_id'] = 99999
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Validação: tipo_pessoa obriga sub-objeto ──────────────

    def test_criar_lead_fisica_sem_dados_fisica_retorna_400(self):
        """tipo_pessoa FISICA sem 'dados_fisica' deve retornar 400."""
        payload = {
            'tipo_pessoa': 'FISICA',
            'nome': 'Sem Dados',
            'email': 'semdados@email.com',
            'interesse': {
                'modelo_id': self.modelo.pk,
                'aceite_termos': True,
            },
        }
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_lead_juridica_sem_dados_juridica_retorna_400(self):
        """tipo_pessoa JURIDICA sem 'dados_juridica' deve retornar 400."""
        payload = {
            'tipo_pessoa': 'JURIDICA',
            'nome': 'Empresa Sem Dados',
            'email': 'empresa@email.com',
            'interesse': {
                'modelo_id': self.modelo.pk,
                'aceite_termos': True,
            },
        }
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Validação: perfil inválido (choices) ──────────────────

    def test_criar_lead_perfil_invalido_retorna_400(self):
        payload = _dados_lead_fisica(self.modelo.pk)
        payload['dados_fisica']['perfil'] = 'medico'  # valor fora dos choices
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Validação: tipo_instituicao inválido (choices) ────────

    def test_criar_lead_tipo_instituicao_invalido_retorna_400(self):
        payload = _dados_lead_juridica(self.modelo.pk)
        payload['dados_juridica']['tipo_instituicao'] = 'escola'  # fora dos choices
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Validação: origem inválida (choices) ──────────────────

    def test_criar_lead_origem_invalida_retorna_400(self):
        payload = _dados_lead_fisica(self.modelo.pk)
        payload['interesse']['origem'] = 'tiktok'  # fora dos choices
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Validação: CPF com dígito verificador inválido ────────

    def test_criar_lead_cpf_digito_invalido_retorna_400(self):
        """CPF com formato correto mas DV errado deve ser rejeitado."""
        payload = _dados_lead_fisica(self.modelo.pk)
        payload['dados_fisica']['cpf'] = '12345678900'  # DV inválido
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_lead_cpf_repetido_retorna_400(self):
        """CPF com todos os dígitos iguais deve ser rejeitado."""
        payload = _dados_lead_fisica(self.modelo.pk)
        payload['dados_fisica']['cpf'] = '11111111111'
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Validação: CNPJ com dígito verificador inválido ───────

    def test_criar_lead_cnpj_digito_invalido_retorna_400(self):
        """CNPJ com formato correto mas DV errado deve ser rejeitado."""
        payload = _dados_lead_juridica(self.modelo.pk)
        payload['dados_juridica']['cnpj'] = '12345678000100'  # DV inválido
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_lead_cnpj_repetido_retorna_400(self):
        """CNPJ com todos os dígitos iguais deve ser rejeitado."""
        payload = _dados_lead_juridica(self.modelo.pk)
        payload['dados_juridica']['cnpj'] = '00000000000000'
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Listagem de leads ─────────────────────────────────────

    def test_listar_leads_retorna_200(self):
        self.client.force_authenticate(user=_criar_usuario_staff())
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_listar_leads_anonimo_retorna_401(self):
        """list/retrieve de leads exigem staff (LGPD: CPF/e-mail/telefone/tipo_deficiencia)."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_listar_leads_retorna_estrutura_aninhada(self):
        """GET /api/leads/ deve retornar pessoa e modelo aninhados."""
        self.client.force_authenticate(user=_criar_usuario_staff())
        # Cria um lead direto no banco
        pessoa = Pessoa.objects.create(nome='Listado', email='listado@email.com')
        PessoaFisica.objects.create(pessoa=pessoa, perfil='paciente')
        Interesse.objects.create(
            pessoa=pessoa, modelo=self.modelo,
            aceite_termos=True, status_lead='novo'
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertGreater(len(results), 0)
        lead = results[0]
        self.assertIn('pessoa', lead)
        self.assertIn('modelo', lead)
        self.assertIn('tipo_pessoa', lead['pessoa'])

    # ── Detalhe de lead específico ────────────────────────────

    def test_detalhar_lead_retorna_200(self):
        self.client.force_authenticate(user=_criar_usuario_staff())
        pessoa = Pessoa.objects.create(nome='Detalhe', email='detalhe@email.com')
        PessoaFisica.objects.create(pessoa=pessoa, perfil='cuidador')
        interesse = Interesse.objects.create(
            pessoa=pessoa, modelo=self.modelo,
            aceite_termos=True, status_lead='novo'
        )
        url_detalhe = reverse('lead-detail', args=[interesse.pk])
        response = self.client.get(url_detalhe)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('pessoa', response.data)
        self.assertIn('modelo', response.data)

    def test_detalhar_lead_inexistente_retorna_404(self):
        self.client.force_authenticate(user=_criar_usuario_staff())
        url_detalhe = reverse('lead-detail', args=[99999])
        response = self.client.get(url_detalhe)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ── Normalização de e-mail ────────────────────────────────

    def test_criar_lead_email_capitalizacao_diferente_retorna_409(self):
        """E-mail é normalizado para minúsculas: capitalizações diferentes
        do mesmo endereço colidem como lead duplicado (409), em vez de
        criarem duas Pessoas distintas."""
        Pessoa.objects.create(nome='Existente', email='carlos@email.com')
        payload = _dados_lead_fisica(self.modelo.pk)
        payload['email'] = 'CARLOS@Email.com'
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(Pessoa.objects.filter(nome='Existente').count(), 1)

    def test_email_e_normalizado_para_minusculas_ao_persistir(self):
        payload = _dados_lead_fisica(self.modelo.pk)
        payload['email'] = 'MAIUSCULO@Email.com'
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Pessoa.objects.filter(email='maiusculo@email.com').exists())


# ──────────────────────────────────────────────────────────────
# Testes do Throttle de Criação de Leads (5/min por IP)
# ──────────────────────────────────────────────────────────────

class LeadThrottleAPITest(APITestCase):
    """Prova que o rate limit do POST /api/leads/ está ativo em execução.

    Regressão do item 6 da auditoria (testes/relatorio/): o throttle
    existia no código mas era inoperante, porque o scope estava na classe
    do throttle e não em LeadViewSet.throttle_scope, que é o atributo que
    ScopedRateThrottle realmente lê.
    """

    def setUp(self):
        cache.clear()
        self.modelo = Modelo.objects.create(
            nome_modelo='Throttle Model', marca='Marca', motorizada=True
        )
        self.url = reverse('lead-list')

    def test_sexta_requisicao_no_mesmo_minuto_retorna_429(self):
        for i in range(5):
            payload = _dados_lead_fisica(self.modelo.pk)
            payload['email'] = f'throttle-{i}@email.com'
            payload['dados_fisica']['cpf'] = _gerar_cpf_valido()
            response = self.client.post(self.url, payload, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        payload = _dados_lead_fisica(self.modelo.pk)
        payload['email'] = 'throttle-6@email.com'
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('detail', response.data)

    def test_throttle_nao_se_aplica_a_leitura_de_leads(self):
        """O throttle vale só para create; GETs de staff não são limitados
        pelo scope 'leads' (seguem os limites globais anon/user)."""
        self.client.force_authenticate(user=_criar_usuario_staff())
        for _ in range(7):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)


# ──────────────────────────────────────────────────────────────
# Testes de Atualização de Status (PATCH /api/leads/{id}/status/)
# ──────────────────────────────────────────────────────────────

class AtualizarStatusLeadAPITest(APITestCase):
    """Testes de integração para o endpoint de atualização de status."""

    def setUp(self):
        self.client.force_authenticate(user=_criar_usuario_staff())
        self.pessoa = Pessoa.objects.create(nome='Status Test', email='status@email.com')
        self.modelo = Modelo.objects.create(
            nome_modelo='Status Model', marca='Marca', motorizada=True
        )
        self.interesse = Interesse.objects.create(
            pessoa=self.pessoa, modelo=self.modelo,
            aceite_termos=True, status_lead='novo'
        )
        self.url = reverse('lead-atualizar-status', args=[self.interesse.pk])

    def test_atualizar_status_valido_retorna_200(self):
        response = self.client.patch(self.url, {'status_lead': 'contatado'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.interesse.refresh_from_db()
        self.assertEqual(self.interesse.status_lead, 'contatado')

    def test_atualizar_status_invalido_retorna_400(self):
        response = self.client.patch(self.url, {'status_lead': 'invalido'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_atualizar_status_lead_inexistente_retorna_404(self):
        url_inexistente = reverse('lead-atualizar-status', args=[99999])
        response = self.client.patch(url_inexistente, {'status_lead': 'contatado'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_atualizar_status_anonimo_retorna_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.patch(self.url, {'status_lead': 'contatado'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ──────────────────────────────────────────────────────────────
# Testes de Pessoas (consulta restrita a admin)
# ──────────────────────────────────────────────────────────────

class PessoaAPITest(APITestCase):
    """Testes para o endpoint de Pessoas.

    Dados sensíveis (CPF, CNPJ, tipo_deficiencia) exigem IsAdminUser,
    mesmo padrão de proteção aplicado a /api/leads/.
    """

    def test_listar_pessoas_autenticado(self):
        Pessoa.objects.create(nome='Ana', email='ana@email.com')
        self.client.force_authenticate(user=_criar_usuario_staff())
        url = reverse('pessoa-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_listar_pessoas_anonimo_retorna_401(self):
        Pessoa.objects.create(nome='Ana', email='ana@email.com')
        url = reverse('pessoa-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_detalhar_pessoa_anonimo_retorna_401(self):
        pessoa = Pessoa.objects.create(nome='Ana', email='ana@email.com')
        url = reverse('pessoa-detail', args=[pessoa.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ──────────────────────────────────────────────────────────────
# Testes de Modelos (CRUD)
# ──────────────────────────────────────────────────────────────

class ModeloAPITest(APITestCase):
    """Testes para o endpoint de Modelos."""

    def test_listar_modelos(self):
        Modelo.objects.create(nome_modelo='M1', marca='Marca1', motorizada=True)
        Modelo.objects.create(nome_modelo='M2', marca='Marca2', motorizada=False)
        url = reverse('modelo-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_criar_modelo(self):
        self.client.force_authenticate(user=_criar_usuario_staff())
        url = reverse('modelo-list')
        payload = {'nome_modelo': 'Novo', 'marca': 'NovaMarca', 'motorizada': True}
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_criar_modelo_anonimo_retorna_401(self):
        url = reverse('modelo-list')
        payload = {'nome_modelo': 'Vandalismo', 'marca': 'X', 'motorizada': True}
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_deletar_modelo_anonimo_retorna_401(self):
        modelo = Modelo.objects.create(nome_modelo='M3', marca='Marca3', motorizada=True)
        url = reverse('modelo-detail', args=[modelo.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Modelo.objects.filter(pk=modelo.pk).exists())


# ──────────────────────────────────────────────────────────────
# Testes de Estatísticas
# ──────────────────────────────────────────────────────────────

class EstatisticasAPITest(APITestCase):
    """Testes para o endpoint de estatísticas."""

    def test_obter_estatisticas(self):
        self.client.force_authenticate(user=_criar_usuario_staff())
        url = reverse('lead-estatisticas')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_leads', response.data)
        self.assertIn('por_status', response.data)

    def test_obter_estatisticas_anonimo_retorna_401(self):
        url = reverse('lead-estatisticas')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ──────────────────────────────────────────────────────────────
# Testes de Conteúdo Dinâmico da Landing Page (Contrato v3.0 §5)
#
# Cada classe usa um CACHES isolado (LOCATION única) via override_settings
# para não vazar estado de cache entre métodos de teste ou entre classes.
# ──────────────────────────────────────────────────────────────

@override_settings(CACHES={'default': {
    'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    'LOCATION': 'test-cache-beneficios',
}})
class BeneficioAPITest(APITestCase):
    """Testes para o endpoint de Benefícios (GET /api/beneficios/)."""

    def setUp(self):
        cache.clear()

    def test_listar_beneficios_retorna_200(self):
        Beneficio.objects.create(titulo='B1', descricao='D1', icone='i1', ordem=1)
        url = reverse('beneficio-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_listar_beneficios_retorna_apenas_ativos(self):
        Beneficio.objects.create(titulo='Ativo', descricao='D', icone='i', ordem=1, ativo=True)
        Beneficio.objects.create(titulo='Inativo', descricao='D', icone='i', ordem=2, ativo=False)
        url = reverse('beneficio-list')
        response = self.client.get(url)
        titulos = [item['titulo'] for item in response.data['results']]
        self.assertIn('Ativo', titulos)
        self.assertNotIn('Inativo', titulos)

    def test_listar_beneficios_respeita_ordenacao_por_ordem(self):
        Beneficio.objects.create(titulo='Segundo', descricao='D', icone='i', ordem=2)
        Beneficio.objects.create(titulo='Primeiro', descricao='D', icone='i', ordem=1)
        url = reverse('beneficio-list')
        response = self.client.get(url)
        titulos = [item['titulo'] for item in response.data['results']]
        self.assertEqual(titulos, ['Primeiro', 'Segundo'])

    def test_resposta_beneficios_contem_campos_do_contrato(self):
        Beneficio.objects.create(titulo='T', descricao='D', icone='i', ordem=1)
        url = reverse('beneficio-list')
        response = self.client.get(url)
        item = response.data['results'][0]
        self.assertEqual(set(item.keys()), {'titulo', 'descricao', 'icone'})

    def test_segunda_requisicao_beneficios_nao_consulta_banco(self):
        Beneficio.objects.create(titulo='B1', descricao='D1', icone='i1', ordem=1)
        url = reverse('beneficio-list')
        self.client.get(url)  # primeira chamada popula o cache
        with self.assertNumQueries(0):
            self.client.get(url)

    def test_criar_beneficio_invalida_cache(self):
        url = reverse('beneficio-list')
        self.client.get(url)  # popula o cache com a lista vazia
        Beneficio.objects.create(titulo='Novo', descricao='D', icone='i', ordem=1)
        response = self.client.get(url)
        titulos = [item['titulo'] for item in response.data['results']]
        self.assertIn('Novo', titulos)

    def test_resposta_beneficios_contem_header_cache_control(self):
        url = reverse('beneficio-list')
        response = self.client.get(url)
        self.assertIn('Cache-Control', response.headers)
        self.assertIn('max-age', response.headers['Cache-Control'])
        self.assertIn('public', response.headers['Cache-Control'])

    def test_detalhar_beneficio_retorna_200(self):
        beneficio = Beneficio.objects.create(titulo='T', descricao='D', icone='i', ordem=1)
        url = reverse('beneficio-detail', args=[beneficio.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data.keys()), {'titulo', 'descricao', 'icone'})

    def test_detalhar_beneficio_inexistente_retorna_404(self):
        url = reverse('beneficio-detail', args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detalhar_beneficio_inativo_retorna_404(self):
        beneficio = Beneficio.objects.create(titulo='T', descricao='D', icone='i', ordem=1, ativo=False)
        url = reverse('beneficio-detail', args=[beneficio.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@override_settings(CACHES={'default': {
    'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    'LOCATION': 'test-cache-depoimentos',
}})
class DepoimentoAPITest(APITestCase):
    """Testes para o endpoint de Depoimentos (GET /api/depoimentos/)."""

    def setUp(self):
        cache.clear()

    def test_listar_depoimentos_retorna_200(self):
        Depoimento.objects.create(nome='Cliente', texto='Ótimo', avaliacao=5, ordem=1)
        url = reverse('depoimento-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_listar_depoimentos_retorna_apenas_ativos(self):
        Depoimento.objects.create(nome='Ativo', texto='T', avaliacao=5, ordem=1, ativo=True)
        Depoimento.objects.create(nome='Inativo', texto='T', avaliacao=5, ordem=2, ativo=False)
        url = reverse('depoimento-list')
        response = self.client.get(url)
        nomes = [item['nome'] for item in response.data['results']]
        self.assertIn('Ativo', nomes)
        self.assertNotIn('Inativo', nomes)

    def test_listar_depoimentos_respeita_ordenacao_por_ordem(self):
        Depoimento.objects.create(nome='Segundo', texto='T', avaliacao=5, ordem=2)
        Depoimento.objects.create(nome='Primeiro', texto='T', avaliacao=5, ordem=1)
        url = reverse('depoimento-list')
        response = self.client.get(url)
        nomes = [item['nome'] for item in response.data['results']]
        self.assertEqual(nomes, ['Primeiro', 'Segundo'])

    def test_segunda_requisicao_depoimentos_nao_consulta_banco(self):
        Depoimento.objects.create(nome='Cliente', texto='T', avaliacao=5, ordem=1)
        url = reverse('depoimento-list')
        self.client.get(url)
        with self.assertNumQueries(0):
            self.client.get(url)

    def test_criar_depoimento_invalida_cache(self):
        url = reverse('depoimento-list')
        self.client.get(url)
        Depoimento.objects.create(nome='Novo', texto='T', avaliacao=5, ordem=1)
        response = self.client.get(url)
        nomes = [item['nome'] for item in response.data['results']]
        self.assertIn('Novo', nomes)

    def test_resposta_depoimentos_contem_header_cache_control(self):
        url = reverse('depoimento-list')
        response = self.client.get(url)
        self.assertIn('Cache-Control', response.headers)
        self.assertIn('max-age', response.headers['Cache-Control'])

    def test_detalhar_depoimento_retorna_200(self):
        depoimento = Depoimento.objects.create(nome='Cliente', texto='Ótimo', avaliacao=5, ordem=1)
        url = reverse('depoimento-detail', args=[depoimento.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data.keys()), {'nome', 'foto', 'texto', 'avaliacao'})

    def test_detalhar_depoimento_inexistente_retorna_404(self):
        url = reverse('depoimento-detail', args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detalhar_depoimento_inativo_retorna_404(self):
        depoimento = Depoimento.objects.create(nome='Cliente', texto='T', avaliacao=5, ordem=1, ativo=False)
        url = reverse('depoimento-detail', args=[depoimento.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@override_settings(CACHES={'default': {
    'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    'LOCATION': 'test-cache-faq',
}})
class FaqAPITest(APITestCase):
    """Testes para o endpoint de Perguntas Frequentes (GET /api/faq/)."""

    def setUp(self):
        cache.clear()

    def test_listar_faqs_retorna_200(self):
        Faq.objects.create(pergunta='P1', resposta='R1', ordem=1)
        url = reverse('faq-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_listar_faqs_retorna_apenas_ativos(self):
        Faq.objects.create(pergunta='Ativa', resposta='R', ordem=1, ativo=True)
        Faq.objects.create(pergunta='Inativa', resposta='R', ordem=2, ativo=False)
        url = reverse('faq-list')
        response = self.client.get(url)
        perguntas = [item['pergunta'] for item in response.data['results']]
        self.assertIn('Ativa', perguntas)
        self.assertNotIn('Inativa', perguntas)

    def test_listar_faqs_respeita_ordenacao_por_ordem(self):
        Faq.objects.create(pergunta='Segunda', resposta='R', ordem=2)
        Faq.objects.create(pergunta='Primeira', resposta='R', ordem=1)
        url = reverse('faq-list')
        response = self.client.get(url)
        perguntas = [item['pergunta'] for item in response.data['results']]
        self.assertEqual(perguntas, ['Primeira', 'Segunda'])

    def test_segunda_requisicao_faqs_nao_consulta_banco(self):
        Faq.objects.create(pergunta='P1', resposta='R1', ordem=1)
        url = reverse('faq-list')
        self.client.get(url)
        with self.assertNumQueries(0):
            self.client.get(url)

    def test_criar_faq_invalida_cache(self):
        url = reverse('faq-list')
        self.client.get(url)
        Faq.objects.create(pergunta='Nova', resposta='R', ordem=1)
        response = self.client.get(url)
        perguntas = [item['pergunta'] for item in response.data['results']]
        self.assertIn('Nova', perguntas)

    def test_resposta_faqs_contem_header_cache_control(self):
        url = reverse('faq-list')
        response = self.client.get(url)
        self.assertIn('Cache-Control', response.headers)
        self.assertIn('max-age', response.headers['Cache-Control'])

    def test_detalhar_faq_retorna_200(self):
        faq = Faq.objects.create(pergunta='P1', resposta='R1', ordem=1)
        url = reverse('faq-detail', args=[faq.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data.keys()), {'pergunta', 'resposta'})

    def test_detalhar_faq_inexistente_retorna_404(self):
        url = reverse('faq-detail', args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detalhar_faq_inativo_retorna_404(self):
        faq = Faq.objects.create(pergunta='P1', resposta='R1', ordem=1, ativo=False)
        url = reverse('faq-detail', args=[faq.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ──────────────────────────────────────────────────────────────
# Teste da Action de Exportação CSV no Admin (RF04)
# ──────────────────────────────────────────────────────────────

class InteresseAdminExportTest(TestCase):
    """Testes para a action 'Exportar selecionados para CSV' do InteresseAdmin."""

    def setUp(self):
        self.staff = User.objects.create_superuser('admin_export_test', 'admin@test.com', 'senha123')
        self.client.login(username='admin_export_test', password='senha123')

        self.pessoa = Pessoa.objects.create(
            nome='Exportado Teste', email='exportado@email.com',
            telefone='71988887777', cidade='Salvador', estado='BA',
        )
        PessoaFisica.objects.create(pessoa=self.pessoa, cpf='11144477735', perfil='paciente')
        self.modelo = Modelo.objects.create(nome_modelo='Export Model', marca='ExportMarca', motorizada=True)
        self.interesse = Interesse.objects.create(
            pessoa=self.pessoa, modelo=self.modelo,
            aceite_termos=True, status_lead='novo', origem='google',
            quantidade_estimada=2, possui_cadeira=True,
        )

    def test_exportar_csv_retorna_cabecalho_e_linha_esperados(self):
        url = reverse('admin:EasyRide_interesse_changelist')
        response = self.client.post(url, {
            'action': 'exportar_csv',
            '_selected_action': [str(self.interesse.pk)],
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')

        conteudo = response.content.decode('utf-8-sig')
        linhas = conteudo.strip().split('\r\n')
        cabecalho = linhas[0].split(',')
        self.assertEqual(cabecalho, [
            'id', 'data_hora', 'status_lead', 'origem', 'quantidade_estimada',
            'possui_cadeira', 'aceite_termos', 'nome', 'email', 'telefone',
            'cidade', 'estado', 'tipo_pessoa', 'documento', 'modelo',
        ])

        linha_dados = linhas[1].split(',')
        self.assertEqual(linha_dados[0], str(self.interesse.pk))
        self.assertEqual(linha_dados[2], 'novo')
        self.assertEqual(linha_dados[7], 'Exportado Teste')
        self.assertEqual(linha_dados[8], 'exportado@email.com')
        self.assertEqual(linha_dados[12], 'Física')
        self.assertEqual(linha_dados[13], '11144477735')
        self.assertEqual(linha_dados[14], 'ExportMarca Export Model')
