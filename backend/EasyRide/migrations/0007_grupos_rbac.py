"""Cria os grupos de acesso do painel administrativo (RBAC).

Item 5 da Especificação Técnica. Ver `EasyRide/permissoes.py` para a matriz.
"""

from django.db import migrations

from EasyRide.permissoes import MATRIZ_GRUPOS


def criar_grupos(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    for nome_grupo, permissoes in MATRIZ_GRUPOS.items():
        grupo, _ = Group.objects.get_or_create(name=nome_grupo)

        objetos = []
        for app_label, codename in permissoes:
            try:
                objetos.append(
                    Permission.objects.get(
                        codename=codename,
                        content_type__app_label=app_label,
                    )
                )
            except Permission.DoesNotExist:
                # Migration executada antes de o Django ter criado as
                # permissões padrão dos models (elas nascem num post_migrate).
                # Em banco novo isso é esperado; `manage.py sincronizar_grupos`
                # reaplica a matriz depois que as permissões existem.
                continue

        # `set` em vez de `add`: torna a migration idempotente e faz com que
        # reexecutá-la corrija um grupo que tenha sido alterado à mão.
        grupo.permissions.set(objetos)


def remover_grupos(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=MATRIZ_GRUPOS.keys()).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('EasyRide', '0006_normaliza_email_minusculas'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(criar_grupos, remover_grupos),
    ]
