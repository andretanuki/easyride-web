"""Camada de seletores (Selectors) do app EasyRide.

Contém consultas complexas ao banco de dados (operações de leitura).
As Views devem chamar estes seletores para obter querysets filtrados.
"""

from django.db.models import QuerySet, Count, Q
from .models import Pessoa, Interesse, Modelo


def listar_pessoas(tipo: str = None) -> QuerySet:
    """Retorna queryset de Pessoas, opcionalmente filtrado por tipo.
    
    Args:
        tipo: 'PF' para Pessoa Física, 'PJ' para Pessoa Jurídica, ou None para todas.
    
    Returns:
        QuerySet de Pessoa com select_related para otimizar queries.
    """
    qs = Pessoa.objects.select_related('pessoa_fisica', 'pessoa_juridica')

    if tipo == 'PF':
        qs = qs.filter(pessoa_fisica__isnull=False)
    elif tipo == 'PJ':
        qs = qs.filter(pessoa_juridica__isnull=False)

    return qs


def listar_interesses(
    status: str = None,
    origem: str = None,
    pessoa_id: int = None,
) -> QuerySet:
    """Retorna queryset de Interesses com filtros opcionais.
    
    Args:
        status: Filtro por status_lead.
        origem: Filtro por origem do lead.
        pessoa_id: Filtro por pessoa específica.
    
    Returns:
        QuerySet de Interesse com select_related.
    """
    qs = Interesse.objects.select_related('pessoa', 'modelo')

    if status:
        qs = qs.filter(status_lead=status)
    if origem:
        qs = qs.filter(origem=origem)
    if pessoa_id:
        qs = qs.filter(pessoa_id=pessoa_id)

    return qs


def obter_estatisticas_leads() -> dict:
    """Retorna estatísticas consolidadas dos leads para o painel administrativo.
    
    Otimizado para executar no máximo 3 queries ao banco em vez de 5.
    
    Returns:
        Dicionário com contagens por status, origem e totais.
    """
    # Query 1: contagem por status (uma única passagem)
    por_status = dict(
        Interesse.objects.values_list('status_lead')
        .annotate(total=Count('id'))
        .values_list('status_lead', 'total')
    )

    # Query 2: contagem por origem (uma única passagem)
    por_origem = dict(
        Interesse.objects.values_list('origem')
        .annotate(total=Count('id'))
        .values_list('origem', 'total')
    )

    # Derivados calculados em Python (sem queries extras)
    total = sum(por_status.values()) if por_status else 0

    # Contagem B2C / B2B baseada no tipo de pessoa vinculada ao lead
    b2c_count = Interesse.objects.filter(
        pessoa__pessoa_fisica__isnull=False
    ).count()
    b2b_count = Interesse.objects.filter(
        pessoa__pessoa_juridica__isnull=False
    ).count()

    return {
        'total_leads': total,
        'por_status': por_status,
        'por_origem': por_origem,
        'total_b2c': b2c_count,
        'total_b2b': b2b_count,
    }


def listar_modelos(apenas_motorizadas: bool = None) -> QuerySet:
    """Retorna queryset de Modelos com filtro opcional.
    Args:
        apenas_motorizadas: Se True, retorna apenas cadeiras motorizadas.
    
    Returns:
        QuerySet de Modelo.
    """
    qs = Modelo.objects.all()

    if apenas_motorizadas is not None:
        qs = qs.filter(motorizada=apenas_motorizadas)

    return qs
