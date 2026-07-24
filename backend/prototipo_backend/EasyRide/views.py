"""Views (camada de requisição) do app EasyRide.

Responsabilidade: receber a request HTTP, delegar a lógica para
services/selectors e retornar a response formatada conforme o
Contrato de Integração da API v3.0.
"""

import logging

from django.conf import settings
from django.db import IntegrityError
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.cache import cache_control
from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Pessoa, Modelo, Interesse
from .serializers import (
    PessoaReadSerializer,
    ModeloSerializer,
    LeadListSerializer,
    LeadSerializer,
    AtualizarStatusLeadSerializer,
    BeneficioSerializer,
    DepoimentoSerializer,
    FaqSerializer,
)
from . import services, selectors

logger = logging.getLogger(__name__)


# ViewSets de Consulta (Pessoas e Modelos)

class PessoaViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint para consulta de Pessoas cadastradas.

    Restrito a administradores: expõe dados sensíveis (CPF, CNPJ,
    tipo_deficiencia) sob LGPD, mesmo padrão de proteção de /api/leads/.
    Suporta busca por nome/email e ordenação por nome ou data de criação.
    """

    serializer_class = PessoaReadSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['nome', 'email', 'cidade']
    ordering_fields = ['nome', 'criado_em']
    ordering = ['-criado_em']

    def get_queryset(self):
        tipo = self.request.query_params.get('tipo')
        return selectors.listar_pessoas(tipo=tipo)


class ModeloViewSet(viewsets.ModelViewSet):
    """API endpoint para CRUD de Modelos de cadeiras de rodas.

    Leitura pública (o LeadForm precisa listar modelos sem autenticação);
    escrita (POST/PUT/PATCH/DELETE) restrita a usuários staff.
    """

    serializer_class = ModeloSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['motorizada']
    search_fields = ['nome_modelo', 'marca']
    ordering_fields = ['marca', 'nome_modelo']

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    def get_queryset(self):
        motorizada = self.request.query_params.get('motorizada')
        if motorizada is not None:
            motorizada = motorizada.lower() in ('true', '1', 'sim')
            return selectors.listar_modelos(apenas_motorizadas=motorizada)
        return selectors.listar_modelos()


# LeadViewSet — endpoint central de leads (/api/leads/)

class LeadViewSet(viewsets.GenericViewSet,
                  viewsets.mixins.ListModelMixin,
                  viewsets.mixins.RetrieveModelMixin):
    """Endpoint central para captação e consulta de leads.

    GET  /api/leads/        → lista todos os leads (interesses) com dados expandidos.
    GET  /api/leads/{id}/   → detalha um lead específico.
    POST /api/leads/        → cria um novo lead (Pessoa Física ou Jurídica).
    PATCH /api/leads/{id}/status/ → atualiza o status de acompanhamento do lead.
    """

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status_lead', 'origem', 'pessoa']
    search_fields = ['pessoa__nome', 'pessoa__email', 'mensagem']
    ordering_fields = ['data_hora', 'status_lead']
    ordering = ['-data_hora']

    # ScopedRateThrottle lê o scope deste atributo da VIEW (não de um
    # atributo `scope` na classe do throttle). Taxa configurada em
    # settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['leads'] (5/minuto
    # por IP), para prevenir spam e abuso no formulário público.
    throttle_scope = 'leads'

    def get_throttles(self):
        """Aplica throttle apenas na ação de criação."""
        if self.action == 'create':
            return [ScopedRateThrottle()]
        return []

    def get_permissions(self):
        """POST (create) é público; list/retrieve/atualizar_status exigem staff
        (os leads expõem CPF, e-mail, telefone e tipo_deficiencia — dado sensível
        de saúde sob a LGPD — e não podem ficar acessíveis anonimamente)."""
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    def get_serializer_class(self):
        """Retorna serializer de escrita (POST) ou de leitura (GET)."""
        if self.action == 'create':
            return LeadSerializer
        return LeadListSerializer

    def get_queryset(self):
        return selectors.listar_interesses(
            status=self.request.query_params.get('status'),
            origem=self.request.query_params.get('origem'),
            pessoa_id=self.request.query_params.get('pessoa_id'),
        )

    @extend_schema(
        examples=[
            OpenApiExample(
                'Pessoa Física',
                summary='Lead de Pessoa Física (B2C)',
                description='Payload com tipo_pessoa=FISICA e o sub-objeto dados_fisica.',
                value={
                    'tipo_pessoa': 'FISICA',
                    'nome': 'João da Silva',
                    'email': 'joao.silva@email.com',
                    'telefone': '11999999999',
                    'estado': 'SP',
                    'cidade': 'São Paulo',
                    'dados_fisica': {
                        'cpf': '123.456.789-00',
                        'data_nascimento': '1990-05-20',
                        'tipo_deficiencia': 'Motora',
                        'perfil': 'paciente',
                        'comunicacao_verbal_preservada': True,
                    },
                    'interesse': {
                        'modelo_id': 2,
                        'quantidade_estimada': 1,
                        'mensagem': 'Gostaria de mais detalhes sobre as dimensões da cadeira.',
                        'origem': 'outro',
                        'aceite_termos': True,
                        'possui_cadeira': False,
                    },
                },
                request_only=True,
            ),
            OpenApiExample(
                'Pessoa Jurídica',
                summary='Lead de Pessoa Jurídica (B2B)',
                description='Payload com tipo_pessoa=JURIDICA e o sub-objeto dados_juridica.',
                value={
                    'tipo_pessoa': 'JURIDICA',
                    'nome': 'Clínica de Reabilitação Esperança',
                    'email': 'contato@clinicaesperanca.com.br',
                    'telefone': '1132221111',
                    'estado': 'SP',
                    'cidade': 'Campinas',
                    'dados_juridica': {
                        'cnpj': '12.345.678/0001-90',
                        'tipo_instituicao': 'clinica',
                        'contato_responsavel': 'Maria Souza',
                        'cargo_responsavel': 'Diretora Médica',
                    },
                    'interesse': {
                        'modelo_id': 5,
                        'quantidade_estimada': 10,
                        'mensagem': 'Cotação para renovação da frota da clínica.',
                        'origem': 'google',
                        'aceite_termos': True,
                        'possui_cadeira': True,
                    },
                },
                request_only=True,
            ),
        ],
    )
    def create(self, request, *args, **kwargs):
        """POST /api/leads/

        Recebe o payload aninhado, valida, persiste e retorna a resposta
        no formato definido pelo Contrato da API.
        """
        serializer = LeadSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            interesse = services.criar_lead(serializer.validated_data)
            logger.info(
                'Lead criado: #%s | tipo=%s | email=%s | IP=%s',
                interesse.pk,
                serializer.validated_data.get('tipo_pessoa'),
                serializer.validated_data.get('email'),
                request.META.get('REMOTE_ADDR', 'IP desconhecido'),
            )
            return Response(
                {
                    'status': 'success',
                    'mensagem': 'Lead cadastrado com sucesso',
                    'dados': {
                        'id': interesse.pk,
                        'tipo_pessoa': serializer.validated_data.get('tipo_pessoa'),
                        'nome': serializer.validated_data.get('nome'),
                        'email': serializer.validated_data.get('email'),
                    },
                },
                status=status.HTTP_201_CREATED
            )

        except IntegrityError:
            # E-mail já cadastrado com conflito de unicidade em outro campo
            logger.warning(
                'Conflito de dados ao criar lead: email=%s',
                serializer.validated_data.get('email'),
            )
            return Response(
                {
                    'status': 'error',
                    'mensagem': 'Lead já cadastrado',
                },
                status=status.HTTP_409_CONFLICT
            )

        except Exception as e:
            logger.exception('Erro interno ao criar lead: %s', e)
            return Response(
                {
                    'status': 'error',
                    'mensagem': 'Erro interno no servidor',
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['patch'], url_path='status')
    def atualizar_status(self, request, pk=None):
        """PATCH /api/leads/{id}/status/  {"status_lead": "contatado"}

        Atualiza o status de acompanhamento de um lead existente.
        """
        serializer = AtualizarStatusLeadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        novo_status = serializer.validated_data['status_lead']

        try:
            interesse = services.atualizar_status_lead(pk, novo_status)
            logger.info('Lead #%s atualizado para status "%s"', pk, novo_status)
            return Response(LeadListSerializer(interesse).data)
        except Interesse.DoesNotExist:
            return Response(
                {
                    'status': 'error',
                    'mensagem': 'Lead não encontrado',
                },
                status=status.HTTP_404_NOT_FOUND
            )


# View de Estatísticas

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def estatisticas_leads(request):
    """GET /api/leads/estatisticas/

    Retorna estatísticas consolidadas dos leads para o painel administrativo.
    Restrito a usuários staff (mesma justificativa de LGPD do LeadViewSet).
    """
    stats = selectors.obter_estatisticas_leads()
    return Response(stats)


# ViewSets de Conteúdo Dinâmico da Landing Page FAQ|Depoimentos|Benefícios (Contrato v3.0)
#
# Rotas "estáticas (cacheadas)": o list() de cada ViewSet é servido a
# partir do cache configurado em settings.CACHES, com TTL definido por
# settings.CACHE_TTL_CONTEUDO. O cache é invalidado nos signals
# post_save/post_delete registrados em signals.py.

class BeneficioViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint somente leitura para Benefícios da landing page."""

    serializer_class = BeneficioSerializer

    def get_queryset(self):
        return selectors.listar_beneficios_ativos()

    @method_decorator(cache_control(public=True, max_age=settings.CACHE_TTL_CONTEUDO))
    @method_decorator(cache_page(settings.CACHE_TTL_CONTEUDO))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_control(public=True, max_age=settings.CACHE_TTL_CONTEUDO))
    @method_decorator(cache_page(settings.CACHE_TTL_CONTEUDO))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class DepoimentoViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint somente leitura para Depoimentos da landing page."""

    serializer_class = DepoimentoSerializer

    def get_queryset(self):
        return selectors.listar_depoimentos_ativos()

    @method_decorator(cache_control(public=True, max_age=settings.CACHE_TTL_CONTEUDO))
    @method_decorator(cache_page(settings.CACHE_TTL_CONTEUDO))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_control(public=True, max_age=settings.CACHE_TTL_CONTEUDO))
    @method_decorator(cache_page(settings.CACHE_TTL_CONTEUDO))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class FaqViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint somente leitura para Perguntas Frequentes da landing page."""

    serializer_class = FaqSerializer

    def get_queryset(self):
        return selectors.listar_faqs_ativos()

    @method_decorator(cache_control(public=True, max_age=settings.CACHE_TTL_CONTEUDO))
    @method_decorator(cache_page(settings.CACHE_TTL_CONTEUDO))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_control(public=True, max_age=settings.CACHE_TTL_CONTEUDO))
    @method_decorator(cache_page(settings.CACHE_TTL_CONTEUDO))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
