"""Signals de invalidação de cache do conteúdo dinâmico da landing page.

As rotas GET /api/beneficios, /api/depoimentos e /api/faq são servidas a
partir de cache (Contrato v3.0 §5). Sempre que um registro de Beneficio,
Depoimento ou Faq é criado, alterado ou removido — via Admin ou ORM — o
cache é limpo, para que a mudança apareça imediatamente sem esperar o TTL.
"""

from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Beneficio, Depoimento, Faq


@receiver(post_save, sender=Beneficio)
@receiver(post_delete, sender=Beneficio)
@receiver(post_save, sender=Depoimento)
@receiver(post_delete, sender=Depoimento)
@receiver(post_save, sender=Faq)
@receiver(post_delete, sender=Faq)
def invalidar_cache_conteudo_landing(sender, **kwargs):
    """Limpa o cache ao salvar/excluir Beneficio, Depoimento ou Faq."""
    cache.clear()
