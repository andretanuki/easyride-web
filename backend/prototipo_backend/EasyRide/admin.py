"""Configuração do Django Admin para o app EasyRide.

Permite que a equipe EasyRide visualize, filtre e gerencie
os contatos/leads captados pelo site institucional.
"""

import csv

from django.contrib import admin
from django.http import HttpResponse

from .models import (
    Pessoa, PessoaFisica, PessoaJuridica, Modelo, Interesse,
    Beneficio, Depoimento, Faq,
)


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

    def get_inline_instances(self, request, obj=None):
        """Oculta o inline da especialização incompatível com a que já existe.

        PF e PJ são OneToOne independentes de Pessoa: o banco não impede que
        as duas coexistam. Sem este filtro, abrir uma Pessoa já cadastrada
        como Jurídica exibe o bloco de Pessoa Física em branco, convidando a
        criar um registro híbrido (que o CSV e o serializer não sabem
        representar). Aqui só escondemos o formulário — a garantia real
        depende de constraint no modelo/banco.
        """
        instances = super().get_inline_instances(request, obj)

        if obj is None:
            return instances

        tem_fisica = PessoaFisica.objects.filter(pessoa=obj).exists()
        tem_juridica = PessoaJuridica.objects.filter(pessoa=obj).exists()

        if not (tem_fisica or tem_juridica):
            return instances

        ocultar = PessoaJuridicaInline if tem_fisica else PessoaFisicaInline
        return [i for i in instances if not isinstance(i, ocultar)]

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

    actions = ['marcar_como_contatado', 'marcar_como_qualificado', 'exportar_csv']

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

    @admin.action(description='Exportar selecionados para CSV')
    def exportar_csv(self, request, queryset):
        """RF04: permite à equipe exportar os leads filtrados/selecionados.

        Usa select_related explícito (não coberto pelo get_queryset padrão
        do Admin) para evitar N+1 ao acessar pessoa_fisica/pessoa_juridica
        e modelo de cada linha.
        """
        queryset = queryset.select_related(
            'pessoa', 'pessoa__pessoa_fisica', 'pessoa__pessoa_juridica', 'modelo',
        )

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="leads_easyride.csv"'
        response.write('﻿')  # BOM UTF-8, para acentuação correta no Excel

        writer = csv.writer(response)
        writer.writerow([
            'id', 'data_hora', 'status_lead', 'origem', 'quantidade_estimada',
            'possui_cadeira', 'aceite_termos', 'nome', 'email', 'telefone',
            'cidade', 'estado', 'tipo_pessoa', 'documento', 'modelo',
        ])

        for interesse in queryset:
            pessoa = interesse.pessoa
            try:
                tipo_pessoa = 'Física'
                documento = pessoa.pessoa_fisica.cpf
            except PessoaFisica.DoesNotExist:
                try:
                    tipo_pessoa = 'Jurídica'
                    documento = pessoa.pessoa_juridica.cnpj
                except PessoaJuridica.DoesNotExist:
                    tipo_pessoa = '—'
                    documento = ''

            writer.writerow([
                interesse.pk,
                interesse.data_hora.isoformat(),
                interesse.status_lead,
                interesse.origem,
                interesse.quantidade_estimada,
                interesse.possui_cadeira,
                interesse.aceite_termos,
                pessoa.nome,
                pessoa.email,
                pessoa.telefone,
                pessoa.cidade,
                pessoa.estado,
                tipo_pessoa,
                documento,
                f'{interesse.modelo.marca} {interesse.modelo.nome_modelo}',
            ])

        return response


@admin.register(Beneficio)
class BeneficioAdmin(admin.ModelAdmin):
    """Admin para Benefícios da landing page (conteúdo dinâmico, Contrato v3.0)."""

    list_display = ['titulo', 'icone', 'ordem', 'ativo']
    list_filter = ['ativo']
    list_editable = ['ordem', 'ativo']
    search_fields = ['titulo', 'descricao']


@admin.register(Depoimento)
class DepoimentoAdmin(admin.ModelAdmin):
    """Admin para Depoimentos da landing page (conteúdo dinâmico, Contrato v3.0)."""

    list_display = ['nome', 'avaliacao', 'ordem', 'ativo']
    list_filter = ['ativo', 'avaliacao']
    list_editable = ['ordem', 'ativo']
    search_fields = ['nome', 'texto']


@admin.register(Faq)
class FaqAdmin(admin.ModelAdmin):
    """Admin para Perguntas Frequentes da landing page (conteúdo dinâmico, Contrato v3.0)."""

    list_display = ['pergunta', 'ordem', 'ativo']
    list_filter = ['ativo']
    list_editable = ['ordem', 'ativo']
    search_fields = ['pergunta', 'resposta']


# Customização do cabeçalho do Admin
admin.site.site_header = 'EasyRide — Painel de Gestão de Leads'
admin.site.site_title = 'EasyRide Admin'
admin.site.index_title = 'Gestão de Leads e Contatos'
