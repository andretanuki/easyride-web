"""Reaplica a matriz RBAC do painel administrativo aos grupos do Django.

Item 5 da Especificação Técnica. A migration 0007 já cria os grupos, mas em
banco novo ela pode rodar antes de o Django ter criado as permissões padrão
dos models (que nascem num sinal post_migrate). Este comando fecha essa
lacuna e serve para reaplicar a matriz depois de qualquer ajuste manual:

    python manage.py sincronizar_grupos
"""

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from EasyRide.permissoes import MATRIZ_GRUPOS


class Command(BaseCommand):
    help = 'Sincroniza os grupos de acesso do painel com a matriz RBAC.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Sincronizando grupos RBAC...\n'))

        for nome_grupo, permissoes in MATRIZ_GRUPOS.items():
            grupo, criado = Group.objects.get_or_create(name=nome_grupo)

            objetos, ausentes = [], []
            for app_label, codename in permissoes:
                try:
                    objetos.append(
                        Permission.objects.get(
                            codename=codename,
                            content_type__app_label=app_label,
                        )
                    )
                except Permission.DoesNotExist:
                    ausentes.append(f'{app_label}.{codename}')

            grupo.permissions.set(objetos)

            label = 'Criado' if criado else 'Atualizado'
            self.stdout.write(
                f'  [{label}] {nome_grupo}: {len(objetos)} permissão(ões)'
            )
            for codename in ausentes:
                self.stdout.write(
                    self.style.WARNING(f'      permissão inexistente: {codename}')
                )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ Grupos sincronizados.'))
