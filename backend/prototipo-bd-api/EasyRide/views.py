"""Views (camada de requisição) do app EasyRide.

Responsabilidade: receber a request HTTP, delegar a lógica para
services/selectors e retornar a response formatada conforme o
Contrato de Integração da API (Atualização - Entrega 2).
"""

import logging

from django.db import IntegrityError
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, throttle_classes
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
)
from . import services, selectors

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Utilitários de formatação de resposta
# ──────────────────────────────────────────────────────────────

def _formatar_erros_validacao(erros_drf: dict, prefixo: str = '') -> list:
    """Converte o dicionário hierárquico de erros do DRF para o formato
    de array definido no contrato da API:
    [{"campo": "dados_fisica.cpf", "mensagem": "..."}, ...]

    Args:
        erros_drf: Dicionário de erros retornado pelo serializer.is_valid().
        prefixo: Prefixo acumulado para campos aninhados (ex: 'dados_fisica').

    Returns:
        Lista de dicionários com chaves 'campo' e 'mensagem'.
    """
    resultado = []
    for campo, valor in erros_drf.items():
        campo_completo = f'{prefixo}.{campo}' if prefixo else campo

        if isinstance(valor, dict):
            # Erro aninhado — recursão com prefixo acumulado
            resultado.extend(_formatar_erros_validacao(valor, campo_completo))
        elif isinstance(valor, list):
            for msg in valor:
                if isinstance(msg, dict):
                    # Lista de dicionários (sub-erros aninhados numa lista)
                    resultado.extend(_formatar_erros_validacao(msg, campo_completo))
                else:
                    resultado.append({
                        'campo': campo_completo,
                        'mensagem': str(msg),
                    })
        else:
            resultado.append({
                'campo': campo_completo,
                'mensagem': str(valor),
            })
    return resultado


# ──────────────────────────────────────────────────────────────
# ViewSets de Consulta (Pessoas e Modelos)
# ──────────────────────────────────────────────────────────────

class PessoaViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint para consulta de Pessoas cadastradas.

    Suporta busca por nome/email e ordenação por nome ou data de criação.
    """

    serializer_class = PessoaReadSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['nome', 'email', 'cidade']
    ordering_fields = ['nome', 'criado_em']
    ordering = ['-criado_em']

    def get_queryset(self):
        tipo = self.request.query_params.get('tipo')
        return selectors.listar_pessoas(tipo=tipo)


class ModeloViewSet(viewsets.ModelViewSet):
    """API endpoint para CRUD de Modelos de cadeiras de rodas."""

    serializer_class = ModeloSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['motorizada']
    search_fields = ['nome_modelo', 'marca']
    ordering_fields = ['marca', 'nome_modelo']

    def get_queryset(self):
        motorizada = self.request.query_params.get('motorizada')
        if motorizada is not None:
            motorizada = motorizada.lower() in ('true', '1', 'sim')
            return selectors.listar_modelos(apenas_motorizadas=motorizada)
        return selectors.listar_modelos()


# ──────────────────────────────────────────────────────────────
# Throttle de Leads
# ──────────────────────────────────────────────────────────────

class LeadThrottle(ScopedRateThrottle):
    """Throttle específico para endpoints de captação de leads.

    Limita a 5 requisições por minuto por IP para prevenir
    spam e abuso nos formulários públicos.
    """
    scope = 'leads'


# ──────────────────────────────────────────────────────────────
# LeadViewSet — endpoint central de leads (/api/leads/)
# ──────────────────────────────────────────────────────────────

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

    def get_throttles(self):
        """Aplica throttle apenas na ação de criação."""
        if self.action == 'create':
            return [LeadThrottle()]
        return []

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

    def create(self, request, *args, **kwargs):
        """POST /api/leads/

        Recebe o payload aninhado, valida, persiste e retorna a resposta
        no formato definido pelo Contrato da API.
        """
        serializer = LeadSerializer(data=request.data)

        if not serializer.is_valid():
            erros = _formatar_erros_validacao(serializer.errors)
            return Response(
                {
                    'status': 'error',
                    'mensagem': 'Erro de validação',
                    'erros': erros,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

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


# ──────────────────────────────────────────────────────────────
# View de Estatísticas
# ──────────────────────────────────────────────────────────────

@api_view(['GET'])
def estatisticas_leads(request):
    """GET /api/leads/estatisticas/

    Retorna estatísticas consolidadas dos leads para o painel administrativo.
    """
    stats = selectors.obter_estatisticas_leads()
    return Response(stats)
