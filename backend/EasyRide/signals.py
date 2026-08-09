"""Signals do app EasyRide.

Reúne dois receivers:

1. Invalidação de cache do conteúdo dinâmico da landing page. As rotas
   GET /api/beneficios, /api/depoimentos e /api/faq são servidas a partir
   de cache (Contrato v3.0 §5). Sempre que um registro de Beneficio,
   Depoimento ou Faq é criado, alterado ou removido — via Admin ou ORM — o
   cache é limpo, para que a mudança apareça imediatamente sem esperar o TTL.

2. Aplicação da matriz RBAC do painel administrativo (item 5 da
   Especificação Técnica), no post_migrate.
"""

from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .models import Beneficio, Depoimento, Faq
from .permissoes import MATRIZ_GRUPOS


@receiver(post_save, sender=Beneficio)
@receiver(post_delete, sender=Beneficio)
@receiver(post_save, sender=Depoimento)
@receiver(post_delete, sender=Depoimento)
@receiver(post_save, sender=Faq)
@receiver(post_delete, sender=Faq)
def invalidar_cache_conteudo_landing(sender, **kwargs):
    """Limpa o cache ao salvar/excluir Beneficio, Depoimento ou Faq."""
    cache.clear()


@receiver(post_migrate)
def aplicar_matriz_rbac(sender, **kwargs):
    """Garante que os grupos do painel tenham as permissões da matriz.

    A migration 0007 cria os grupos, mas em banco novo ela roda *antes* de
    o Django ter criado as permissões padrão dos models — que nascem neste
    mesmo post_migrate. Resultado: os grupos existiriam vazios, e todo
    operador não-superusuário levaria 403 no painel.

    Reaplicar aqui fecha essa janela e mantém a matriz como fonte única:
    o receiver é idempotente (`set`), então também corrige um grupo que
    tenha sido editado à mão pela tela de grupos do admin.
    """
    if getattr(sender, 'name', None) != 'EasyRide':
        return

    from django.contrib.auth.models import Group, Permission

    for nome_grupo, permissoes in MATRIZ_GRUPOS.items():
        grupo, _ = Group.objects.get_or_create(name=nome_grupo)
        objetos = Permission.objects.filter(
            content_type__app_label='EasyRide',
            codename__in=[codename for _, codename in permissoes],
        )
        grupo.permissions.set(objetos)
