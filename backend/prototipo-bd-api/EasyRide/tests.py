"""Testes automatizados do app EasyRide.

Cobertura: models, services, selectors e endpoints da API.
Todos os testes de lead usam o novo payload aninhado (LeadSerializer).
"""

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Pessoa, PessoaFisica, PessoaJuridica, Modelo, Interesse
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
        """Erro de validação deve seguir o formato de array do contrato."""
        payload = _dados_lead_fisica(self.modelo.pk)
        payload['interesse']['aceite_termos'] = False
        response = self.client.post(self.url, payload, format='json')
        data = response.data
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['mensagem'], 'Erro de validação')
        self.assertIsInstance(data['erros'], list)
        self.assertGreater(len(data['erros']), 0)
        # Verifica que o campo de erro está prefixado corretamente
        campos_com_erro = [e['campo'] for e in data['erros']]
        self.assertIn('interesse.aceite_termos', campos_com_erro)

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
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_listar_leads_retorna_estrutura_aninhada(self):
        """GET /api/leads/ deve retornar pessoa e modelo aninhados."""
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
        url_detalhe = reverse('lead-detail', args=[99999])
        response = self.client.get(url_detalhe)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ──────────────────────────────────────────────────────────────
# Testes de Atualização de Status (PATCH /api/leads/{id}/status/)
# ──────────────────────────────────────────────────────────────

class AtualizarStatusLeadAPITest(APITestCase):
    """Testes de integração para o endpoint de atualização de status."""

    def setUp(self):
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
        url = reverse('modelo-list')
        payload = {'nome_modelo': 'Novo', 'marca': 'NovaMarca', 'motorizada': True}
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


# ──────────────────────────────────────────────────────────────
# Testes de Estatísticas
# ──────────────────────────────────────────────────────────────

class EstatisticasAPITest(APITestCase):
    """Testes para o endpoint de estatísticas."""

    def test_obter_estatisticas(self):
        url = reverse('lead-estatisticas')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_leads', response.data)
        self.assertIn('por_status', response.data)
        self.assertIn('por_origem', response.data)
