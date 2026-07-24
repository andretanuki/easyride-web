"""Configuração do Django Admin para o app EasyRide.

Permite que a equipe EasyRide visualize, filtre e gerencie
os contatos/leads captados pelo site institucional.
"""

from django.contrib import admin
from .models import Pessoa, PessoaFisica, PessoaJuridica, Modelo, Interesse


class PessoaFisicaInline(admin.StackedInline):
    """Inline para dados de Pessoa Física na tela de Pessoa."""
    model = PessoaFisica
    can_delete = False
    verbose_name = 'Dados de Pessoa Física'
    verbose_name_plural = 'Dados de Pessoa Física'
    extra = 0


class PessoaJuridicaInline(admin.StackedInline):
    """Inline para dados de Pessoa Jurídica na tela de Pessoa."""
    model = PessoaJuridica
    can_delete = False
    verbose_name = 'Dados de Pessoa Jurídica'
    verbose_name_plural = 'Dados de Pessoa Jurídica'
    extra = 0


class InteresseInline(admin.TabularInline):
    """Inline para exibir os interesses/leads vinculados a uma Pessoa."""
    model = Interesse
    extra = 0
    readonly_fields = ['data_hora', 'modelo', 'origem', 'status_lead']
    fields = ['modelo', 'quantidade_estimada', 'origem', 'status_lead', 'data_hora']
    show_change_link = True


@admin.register(Pessoa)
class PessoaAdmin(admin.ModelAdmin):
    """Admin para a entidade Pessoa com inlines de especialização."""

    list_display = ['nome', 'email', 'telefone', 'cidade', 'estado', 'tipo_pessoa', 'criado_em']
    list_filter = ['estado', 'criado_em']
    search_fields = ['nome', 'email', 'telefone', 'cidade']
    readonly_fields = ['criado_em', 'atualizado_em']
    inlines = [PessoaFisicaInline, PessoaJuridicaInline, InteresseInline]

    @admin.display(description='Tipo')
    def tipo_pessoa(self, obj):
        tipos = []
        try:
            if obj.pessoa_fisica:
                tipos.append('PF')
        except PessoaFisica.DoesNotExist:
            pass
        try:
            if obj.pessoa_juridica:
                tipos.append('PJ')
        except PessoaJuridica.DoesNotExist:
            pass
        return ' / '.join(tipos) if tipos else '—'


@admin.register(PessoaFisica)
class PessoaFisicaAdmin(admin.ModelAdmin):
    """Admin para Pessoa Física."""

    list_display = ['get_nome', 'cpf', 'perfil', 'tipo_deficiencia', 'comunicacao_verbal_preservada']
    list_filter = ['perfil', 'comunicacao_verbal_preservada']
    search_fields = ['pessoa__nome', 'cpf']

    @admin.display(description='Nome', ordering='pessoa__nome')
    def get_nome(self, obj):
        return obj.pessoa.nome


@admin.register(PessoaJuridica)
class PessoaJuridicaAdmin(admin.ModelAdmin):
    """Admin para Pessoa Jurídica."""

    list_display = ['get_nome', 'cnpj', 'tipo_instituicao', 'contato_responsavel', 'cargo_responsavel']
    list_filter = ['tipo_instituicao']
    search_fields = ['pessoa__nome', 'cnpj', 'contato_responsavel']

    @admin.display(description='Instituição', ordering='pessoa__nome')
    def get_nome(self, obj):
        return obj.pessoa.nome


@admin.register(Modelo)
class ModeloAdmin(admin.ModelAdmin):
    """Admin para Modelos de cadeiras de rodas."""

    list_display = ['nome_modelo', 'marca', 'motorizada', 'criado_em']
    list_filter = ['motorizada', 'marca']
    search_fields = ['nome_modelo', 'marca']


@admin.register(Interesse)
class InteresseAdmin(admin.ModelAdmin):
    """Admin para Interesses/Leads com filtros avançados.
    
    Este é o painel principal para a equipe comercial da EasyRide
    gerenciar os contatos captados pelo site.
    """

    list_display = [
        'id', 'get_pessoa_nome', 'get_pessoa_email', 'modelo',
        'origem', 'status_lead', 'quantidade_estimada',
        'aceite_termos', 'possui_cadeira', 'data_hora',
    ]
    list_filter = ['status_lead', 'origem', 'aceite_termos', 'possui_cadeira', 'data_hora']
    search_fields = ['pessoa__nome', 'pessoa__email', 'mensagem']
    list_editable = ['status_lead']
    readonly_fields = ['data_hora']
    date_hierarchy = 'data_hora'
    list_per_page = 25

    actions = ['marcar_como_contatado', 'marcar_como_qualificado']

    @admin.display(description='Nome', ordering='pessoa__nome')
    def get_pessoa_nome(self, obj):
        return obj.pessoa.nome

    @admin.display(description='E-mail', ordering='pessoa__email')
    def get_pessoa_email(self, obj):
        return obj.pessoa.email

    @admin.action(description='Marcar selecionados como "Contatado"')
    def marcar_como_contatado(self, request, queryset):
        updated = queryset.update(status_lead='contatado')
        self.message_user(request, f'{updated} lead(s) marcado(s) como contatado(s).')

    @admin.action(description='Marcar selecionados como "Qualificado"')
    def marcar_como_qualificado(self, request, queryset):
        updated = queryset.update(status_lead='qualificado')
        self.message_user(request, f'{updated} lead(s) marcado(s) como qualificado(s).')


# Customização do cabeçalho do Admin
admin.site.site_header = 'EasyRide — Painel de Gestão de Leads'
admin.site.site_title = 'EasyRide Admin'
admin.site.index_title = 'Gestão de Leads e Contatos'
