from django.db import migrations
from django.db.models.functions import Lower


def normalizar_emails(apps, schema_editor):
    """Aplica lowercase aos e-mails já cadastrados, alinhando os dados
    existentes à normalização feita em Pessoa.save()/LeadSerializer.

    Se dois registros pré-existentes colidirem após o lowercase (ex.:
    'E@mail.com' e 'e@mail.com'), o UNIQUE do banco fará a migração falhar —
    nesse caso a duplicidade deve ser resolvida manualmente antes de migrar.
    """
    Pessoa = apps.get_model('EasyRide', 'Pessoa')
    Pessoa.objects.exclude(email=Lower('email')).update(email=Lower('email'))


class Migration(migrations.Migration):

    dependencies = [
        ('EasyRide', '0005_adiciona_conteudo_landing'),
    ]

    operations = [
        migrations.RunPython(normalizar_emails, migrations.RunPython.noop),
    ]
