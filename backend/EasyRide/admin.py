"""Configuração do Django Admin para o app EasyRide.

Permite que a equipe EasyRide visualize, filtre e gerencie
os contatos/leads captados pelo site institucional.
"""

import csv

from django import forms
from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html

from .models import (
    Pessoa, PessoaFisica, PessoaJuridica, Modelo, Interesse,
    Beneficio, Depoimento, Faq,
)
from .permissoes import GRUPO_VENDAS


class PessoaAdminForm(forms.ModelForm):
    """Form de Pessoa que normaliza o e-mail antes da checagem de unicidade.

    `Pessoa.save()` baixa o e-mail para minúsculas, mas isso roda depois do
    `validate_unique()` do ModelForm — que compara a string como digitada.
    Sem normalizar aqui, cadastrar "DUP@Email.com" quando já existe
    "dup@email.com" passa pela validação do form e só quebra no INSERT,
    entregando um IntegrityError (HTTP 500) ao operador em vez do erro de
    campo. Normalizando em `clean_email`, o unique é conferido sobre o
    mesmo valor que será gravado e o admin exibe a mensagem padrão.
    """

    class Meta:
        model = Pessoa
        fields = '__all__'

    def clean_email(self):
        email = self.cleaned_data.get('email', '')
        return email.strip().lower() if email else email


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


class TipoPessoaFilter(admin.SimpleListFilter):
    """Filtro lateral de segmentação B2C (Física) x B2B (Jurídica).

    Pessoa não tem campo discriminador: o tipo é derivado da existência
    da especialização (CTI via OneToOne). Por isso o filtro não pode ser
    um simples `pessoa__tipo_pessoa` e é resolvido por `isnull` sobre as
    relações reais (`pessoa_fisica` / `pessoa_juridica`).
    """

    title = 'Tipo de pessoa'
    parameter_name = 'tipo_pessoa'

    def lookups(self, request, model_admin):
        return [('fisica', 'Física (B2C)'), ('juridica', 'Jurídica (B2B)')]

    def queryset(self, request, queryset):
        if self.value() == 'fisica':
            return queryset.filter(pessoa__pessoa_fisica__isnull=False)
        if self.value() == 'juridica':
            return queryset.filter(pessoa__pessoa_juridica__isnull=False)
        return queryset


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

    form = PessoaAdminForm
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
        'id', 'get_pessoa_nome', 'get_pessoa_email', 'get_tipo_pessoa', 'modelo',
        'origem', 'status_lead', 'quantidade_estimada',
        'aceite_termos', 'possui_cadeira', 'data_hora',
    ]
    list_filter = [
        'status_lead', TipoPessoaFilter, 'origem',
        'aceite_termos', 'possui_cadeira', 'data_hora',
    ]
    # Busca por documento e telefone: o operador costuma ter o CNPJ/CPF ou o
    # número da ligação em mãos, não o nome exato como foi cadastrado.
    search_fields = [
        'pessoa__nome', 'pessoa__email', 'pessoa__telefone', 'mensagem',
        'pessoa__pessoa_fisica__cpf', 'pessoa__pessoa_juridica__cnpj',
    ]
    list_editable = ['status_lead']
    readonly_fields = ['data_hora']
    date_hierarchy = 'data_hora'
    list_per_page = 25

    actions = ['marcar_como_contatado', 'marcar_como_qualificado', 'exportar_csv']

    def has_delete_permission(self, request, obj=None):
        """Vendas não deleta leads (item 5 da Especificação, matriz RBAC).

        A permissão `delete_interesse` simplesmente não é concedida ao grupo
        Equipe de Vendas, então o `super()` já bastaria. O override existe
        para que a regra continue valendo se alguém conceder a permissão pela
        tela de grupos do admin: um lead apagado é um registro de contato
        perdido, e a exclusão é reservada ao Administrador (TI).
        """
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name=GRUPO_VENDAS).exists():
            return False
        return super().has_delete_permission(request, obj)

    def get_readonly_fields(self, request, obj=None):
        """Vendas edita apenas `status_lead`; o resto do lead é imutável.

        A matriz do item 5 concede a Vendas "Visualizar e Editar (apenas o
        campo status_lead)". Como `change_interesse` é uma permissão de
        objeto inteiro no Django, a restrição por campo precisa ser feita
        aqui — caso contrário quem move o funil também poderia reescrever
        e-mail, telefone ou modelo do lead captado.
        """
        readonly = list(super().get_readonly_fields(request, obj))

        if request.user.is_superuser:
            return readonly

        if request.user.groups.filter(name=GRUPO_VENDAS).exists():
            editaveis = {'status_lead'}
            readonly = [
                f.name for f in self.model._meta.fields
                if f.name not in editaveis
            ]

        return readonly

    def get_queryset(self, request):
        """Carrega por JOIN as relações que a listagem e as ações percorrem.

        Item 3.4 da Especificação do Painel Administrativo. O ChangeList do
        admin já aplica um `select_related()` sem argumentos por conta própria
        (porque há FK no list_display), mas ele só percorre chaves
        estrangeiras: as especializações PF/PJ são OneToOne *reversos* e ficam
        de fora. Sem declará-las aqui, todo código que pergunta o tipo da
        pessoa — `tipo_pessoa` no CSV, por exemplo — paga uma consulta por
        lead. Medido em 11 queries para 10 leads, contra 1 com o JOIN.
        """
        return super().get_queryset(request).select_related(
            'pessoa', 'modelo', 'pessoa__pessoa_fisica', 'pessoa__pessoa_juridica',
        )

    @admin.display(description='Nome', ordering='pessoa__nome')
    def get_pessoa_nome(self, obj):
        return obj.pessoa.nome

    @admin.display(description='E-mail', ordering='pessoa__email')
    def get_pessoa_email(self, obj):
        return obj.pessoa.email

    @admin.display(description='Tipo')
    def get_tipo_pessoa(self, obj):
        """Tag visual FISICA/JURIDICA na listagem (item 3.1 da Especificação).

        O tipo é derivado da especialização, não de um campo discriminador
        (ver a decisão de modelagem em `Pessoa`). O custo é zero em queries:
        `get_queryset` já traz PF e PJ no mesmo JOIN, então o try/except
        resolve em memória.
        """
        try:
            obj.pessoa.pessoa_fisica
            rotulo, cor = 'FISICA', '#0b6b3a'
        except PessoaFisica.DoesNotExist:
            try:
                obj.pessoa.pessoa_juridica
                rotulo, cor = 'JURIDICA', '#1b4f8a'
            except PessoaJuridica.DoesNotExist:
                return '—'

        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:10px;font-size:11px;font-weight:600;">{}</span>',
            cor, rotulo,
        )

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

        O select_related é reafirmado aqui, embora `get_queryset` já o
        declare: uma action recebe o queryset que o admin lhe entrega, e
        mantê-lo explícito preserva a exportação em O(1) queries mesmo que
        alguém a chame com outro queryset. Repetir é inofensivo — o Django
        não duplica JOIN já presente no plano da consulta.
        """
        queryset = queryset.select_related(
            'pessoa', 'pessoa__pessoa_fisica', 'pessoa__pessoa_juridica', 'modelo',
        )

        # O charset declarado é utf-8, e não utf-8-sig, de propósito: o Django
        # codifica cada write() isoladamente, então o codec 'sig' emitiria um
        # BOM por linha e sujaria a primeira coluna de todas elas no Excel.
        # O BOM que a spec pede é escrito uma única vez, logo abaixo.
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="leads_easyride.csv"'
        response.write('﻿')  # BOM UTF-8: acentuação correta no Excel

        # Delimitador ';': o Excel em português abre CSV separado por vírgula
        # como coluna única. Cabeçalho e ordem seguem a Especificação Técnica
        # do painel administrativo (item 4).
        writer = csv.writer(response, delimiter=';')
        writer.writerow([
            'ID', 'Nome', 'Email', 'Telefone', 'Estado', 'Cidade',
            'Tipo Pessoa', 'Documento', 'Modelo Kit', 'Qtd Estimada',
            'Origem', 'Status', 'Data',
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
                pessoa.nome,
                pessoa.email,
                pessoa.telefone,
                pessoa.estado,
                pessoa.cidade,
                tipo_pessoa,
                documento,
                f'{interesse.modelo.marca} {interesse.modelo.nome_modelo}',
                interesse.quantidade_estimada,
                interesse.origem,
                interesse.status_lead,
                interesse.data_hora.isoformat(),
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
