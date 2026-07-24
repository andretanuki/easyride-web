"""Serializers do app EasyRide.

Estratégia de serialização:
- Leitura (GET): PessoaSerializer, ModeloSerializer, LeadListSerializer expandem dados relacionados.
- Escrita (POST): LeadSerializer aceita um único payload aninhado com tipo_pessoa ("FISICA"|"JURIDICA"),
  dados_fisica/dados_juridica e interesse, validando condicionalmente cada sub-estrutura.
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import (
    Pessoa, PessoaFisica, PessoaJuridica, Modelo, Interesse,
    Beneficio, Depoimento, Faq,
)
from .validators import validar_cpf, validar_cnpj


# Serializers de Leitura (GET)

class PessoaFisicaReadSerializer(serializers.ModelSerializer):
    """Serializer de leitura para dados específicos de Pessoa Física."""

    class Meta:
        model = PessoaFisica
        fields = [
            'cpf', 'data_nascimento', 'tipo_deficiencia',
            'perfil', 'comunicacao_verbal_preservada',
        ]


class PessoaJuridicaReadSerializer(serializers.ModelSerializer):
    """Serializer de leitura para dados específicos de Pessoa Jurídica."""

    class Meta:
        model = PessoaJuridica
        fields = [
            'cnpj', 'tipo_instituicao',
            'contato_responsavel', 'cargo_responsavel',
        ]


class PessoaReadSerializer(serializers.ModelSerializer):
    """Serializer de leitura completo de Pessoa com especialização aninhada."""

    tipo_pessoa = serializers.SerializerMethodField()
    dados_fisica = PessoaFisicaReadSerializer(source='pessoa_fisica', read_only=True)
    dados_juridica = PessoaJuridicaReadSerializer(source='pessoa_juridica', read_only=True)

    class Meta:
        model = Pessoa
        fields = [
            'id', 'tipo_pessoa', 'nome', 'email', 'telefone',
            'estado', 'cidade', 'dados_fisica', 'dados_juridica',
        ]
        read_only_fields = ['id']

    @extend_schema_field(serializers.ChoiceField(choices=['FISICA', 'JURIDICA']))
    def get_tipo_pessoa(self, obj):
        """Determina se a Pessoa é Física ou Jurídica consultando as relações."""
        try:
            if obj.pessoa_fisica is not None:
                return 'FISICA'
        except PessoaFisica.DoesNotExist:
            pass
        try:
            if obj.pessoa_juridica is not None:
                return 'JURIDICA'
        except PessoaJuridica.DoesNotExist:
            pass
        return None


class ModeloReadSerializer(serializers.ModelSerializer):
    """Serializer de leitura para Modelos de cadeiras de rodas."""

    class Meta:
        model = Modelo
        fields = ['id', 'nome_modelo', 'marca', 'motorizada']
        read_only_fields = ['id']


class LeadListSerializer(serializers.ModelSerializer):
    """Serializer de leitura de Interesses/Leads com dados expandidos.

    Retorna a estrutura aninhada definida no Contrato da API:
    interesse > pessoa (com dados_fisica|dados_juridica) + modelo.
    """

    pessoa = PessoaReadSerializer(read_only=True)
    modelo = ModeloReadSerializer(read_only=True)

    class Meta:
        model = Interesse
        fields = [
            'id', 'data_hora', 'status_lead', 'quantidade_estimada',
            'mensagem', 'origem', 'possui_cadeira', 'aceite_termos',
            'pessoa', 'modelo',
        ]
        read_only_fields = ['id', 'data_hora']


# ──────────────────────────────────────────────────────────────
# Sub-serializers de Escrita (POST — payload aninhado)
# ──────────────────────────────────────────────────────────────

class DadosFisicaSerializer(serializers.Serializer):
    """Sub-serializer para os dados específicos de Pessoa Física.

    Valida o dicionário enviado na chave 'dados_fisica' do payload de criação.
    """

    cpf = serializers.CharField(max_length=14, required=False, allow_blank=True)
    data_nascimento = serializers.DateField(required=False, allow_null=True)
    tipo_deficiencia = serializers.CharField(max_length=100, required=False, allow_blank=True)
    perfil = serializers.ChoiceField(
        choices=PessoaFisica.PERFIL_CHOICES,
        default='paciente',
    )
    comunicacao_verbal_preservada = serializers.BooleanField(default=True)

    def validate_cpf(self, value):
        if not value:
            return value
        try:
            validar_cpf(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages[0])
        return value


class DadosJuridicaSerializer(serializers.Serializer):
    """Sub-serializer para os dados específicos de Pessoa Jurídica.

    Valida o dicionário enviado na chave 'dados_juridica' do payload de criação.
    """

    cnpj = serializers.CharField(max_length=18, required=False, allow_blank=True)
    tipo_instituicao = serializers.ChoiceField(
        choices=PessoaJuridica.TIPO_INSTITUICAO_CHOICES,
        default='clinica',
    )
    contato_responsavel = serializers.CharField(max_length=200, required=False, allow_blank=True)
    cargo_responsavel = serializers.CharField(max_length=100, required=False, allow_blank=True)

    def validate_cnpj(self, value):
        if not value:
            return value
        try:
            validar_cnpj(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages[0])
        return value


class InteressePayloadSerializer(serializers.Serializer):
    """Sub-serializer para os dados do Interesse enviados no payload de criação.

    Valida o dicionário enviado na chave 'interesse' do payload principal.
    """

    modelo_id = serializers.IntegerField()
    quantidade_estimada = serializers.IntegerField(default=1, min_value=1)
    mensagem = serializers.CharField(required=False, allow_blank=True)
    origem = serializers.ChoiceField(
        choices=Interesse.ORIGEM_CHOICES,
        default='outro',
    )
    aceite_termos = serializers.BooleanField()
    possui_cadeira = serializers.BooleanField(default=False)

    def validate_modelo_id(self, value):
        """Verifica se o Modelo referenciado existe no banco de dados."""
        if not Modelo.objects.filter(pk=value).exists():
            raise serializers.ValidationError('Modelo de cadeira não encontrado.')
        return value

    def validate_aceite_termos(self, value):
        """Garante que o aceite dos termos de uso foi explicitado."""
        if not value:
            raise serializers.ValidationError(
                'É necessário aceitar os termos para prosseguir.'
            )
        return value


# ──────────────────────────────────────────────────────────────
# Serializer Principal de Criação de Lead (POST /api/leads/)
# ──────────────────────────────────────────────────────────────

class LeadSerializer(serializers.Serializer):
    """Serializer para criação de Lead (POST /api/leads/).

    Aceita um único endpoint com o discriminador 'tipo_pessoa' para determinar
    se é pessoa física ou jurídica

    Estrutura esperada (Pessoa Física):
    {
        "tipo_pessoa": "FISICA",
        "nome": "...", "email": "...", ...campos raiz da Pessoa...,
        "dados_fisica": { "cpf": "...", "perfil": "...", ... },
        "interesse": { "modelo_id": 1, "aceite_termos": true, ... }
    }

    Estrutura esperada (Pessoa Jurídica):
    {
        "tipo_pessoa": "JURIDICA",
        "nome": "...", "email": "...", ...campos raiz da Pessoa...,
        "dados_juridica": { "cnpj": "...", "tipo_instituicao": "...", ... },
        "interesse": { "modelo_id": 5, "aceite_termos": true, ... }
    }
    """

    TIPO_CHOICES = [('FISICA', 'Pessoa Física'), ('JURIDICA', 'Pessoa Jurídica')]

    # Campos raiz (entidade Pessoa)
    tipo_pessoa = serializers.ChoiceField(choices=TIPO_CHOICES)
    nome = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    telefone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    estado = serializers.CharField(max_length=2, required=False, allow_blank=True)
    cidade = serializers.CharField(max_length=100, required=False, allow_blank=True)

    # Sub-objetos aninhados — cada um é opcional em si; a obrigatoriedade
    # condicional é aplicada no validate() abaixo.
    dados_fisica = DadosFisicaSerializer(required=False)
    dados_juridica = DadosJuridicaSerializer(required=False)
    interesse = InteressePayloadSerializer()

    def validate_email(self, value):
        """Normaliza o e-mail para minúsculas: capitalizações diferentes do
        mesmo endereço devem colidir no unique de Pessoa.email (409), e não
        gerar leads duplicados."""
        return value.strip().lower()

    def validate(self, attrs):
        """Validação cruzada: exige o sub-objeto correto para cada tipo_pessoa."""
        tipo = attrs.get('tipo_pessoa')

        if tipo == 'FISICA':
            if not attrs.get('dados_fisica'):
                raise serializers.ValidationError({
                    'dados_fisica': 'Este campo é obrigatório para tipo_pessoa "FISICA".'
                })
            # Remove o bloco jurídico se vier junto por engano
            attrs.pop('dados_juridica', None)

        elif tipo == 'JURIDICA':
            if not attrs.get('dados_juridica'):
                raise serializers.ValidationError({
                    'dados_juridica': 'Este campo é obrigatório para tipo_pessoa "JURIDICA".'
                })
            attrs.pop('dados_fisica', None)

        return attrs


# Serializer de Atualização de Status (PATCH /api/leads/{id}/status/)

class AtualizarStatusLeadSerializer(serializers.Serializer):
    """Serializer para validação do PATCH de status de um lead.

    Centraliza a validação do campo status_lead usando ChoiceField,
    garantindo que apenas valores definidos em Interesse.STATUS_CHOICES
    sejam aceitos e que os erros retornem no formato padrão do DRF.
    """

    status_lead = serializers.ChoiceField(
        choices=Interesse.STATUS_CHOICES,
        error_messages={
            'required': 'Campo "status_lead" é obrigatório.',
            'invalid_choice': 'Status inválido. Valores permitidos: {input}.',
        }
    )


# Aliases mantidos por compatibilidade com views existentes

# ModeloSerializer mantido para o ModeloViewSet (CRUD completo de modelos)
class ModeloSerializer(serializers.ModelSerializer):
    """Serializer completo para CRUD de Modelos de cadeiras de rodas."""

    display_name = serializers.SerializerMethodField()

    class Meta:
        model = Modelo
        fields = ['id', 'nome_modelo', 'marca', 'motorizada', 'display_name', 'criado_em']
        read_only_fields = ['id', 'criado_em']

    @extend_schema_field(serializers.CharField())
    def get_display_name(self, obj):
        return str(obj)


# Serializers de Conteúdo Dinâmico da Landing Page (GET /api/beneficios,
# /api/depoimentos, /api/faq — Contrato de Integração v3.0)

class BeneficioSerializer(serializers.ModelSerializer):
    """Serializer de leitura para Benefícios da landing page."""

    class Meta:
        model = Beneficio
        fields = ['titulo', 'descricao', 'icone']


class DepoimentoSerializer(serializers.ModelSerializer):
    """Serializer de leitura para Depoimentos da landing page."""

    class Meta:
        model = Depoimento
        fields = ['nome', 'foto', 'texto', 'avaliacao']


class FaqSerializer(serializers.ModelSerializer):
    """Serializer de leitura para Perguntas Frequentes da landing page."""

    class Meta:
        model = Faq
        fields = ['pergunta', 'resposta']
