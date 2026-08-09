from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator

from .validators import validar_cpf, validar_cnpj


class Pessoa(models.Model):
    """Entidade base que armazena dados comuns de todos os contatos/leads.

    DECISÃO DE MODELAGEM — não adicionar campo discriminador aqui.

    Um campo 'tipo_pessoa' (PF/PJ) nesta tabela foi proposto e descartado na
    revisão do DER: ele é redundante com a existência da subentidade e pode
    dessincronizar, ficando 'PF' sem que haja registro em PessoaFisica. O tipo
    é sempre derivado da especialização (`pessoa_fisica` / `pessoa_juridica`).

    A motivação original da proposta era evitar o N+1 de descobrir o tipo via
    try/except. Esse custo se resolve por `select_related` das especializações
    — como fazem `selectors.listar_pessoas` e `InteresseAdmin.get_queryset` —
    sem desnormalizar e sem risco de estado inconsistente.

    Nota: PessoaFisica e PessoaJuridica são OneToOne independentes, então o
    banco não impede uma Pessoa sem especialização nem com as duas. O DER
    declara a especialização total e exclusiva, mas essa garantia hoje é
    aplicada apenas na camada de aplicação (ver PessoaAdmin.get_inline_instances).
    """

    nome = models.CharField('Nome completo', max_length=200)
    email = models.EmailField('E-mail', unique=True)
    telefone = models.CharField(
        'Telefone',
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?\d{10,15}$',
                message='Informe um número de telefone válido (10 a 15 dígitos).'
            )
        ]
    )
    estado = models.CharField('Estado (UF)', max_length=2, blank=True)
    cidade = models.CharField('Cidade', max_length=100, blank=True)
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Pessoa'
        verbose_name_plural = 'Pessoas'
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['nome'], name='idx_pessoa_nome'),
            models.Index(fields=['estado'], name='idx_pessoa_estado'),
            models.Index(fields=['-criado_em'], name='idx_pessoa_criado'),
        ]

    def save(self, *args, **kwargs):
        # Normaliza o e-mail para minúsculas em qualquer via de escrita
        # (API, admin, shell): o unique é case-sensitive no banco, e sem
        # isso "E@mail.com" e "e@mail.com" gerariam dois leads distintos.
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.nome} ({self.email})'


class PessoaFisica(models.Model):
    """Especialização de Pessoa para pessoas físicas (B2C).

    Representa usuários finais: pacientes, familiares ou cuidadores
    interessados no Kit de Automação EasyRide.
    """

    PERFIL_CHOICES = [
        ('paciente', 'Paciente'),
        ('familiar', 'Familiar'),
        ('cuidador', 'Cuidador'),
    ]

    pessoa = models.OneToOneField(
        Pessoa,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='pessoa_fisica',
        verbose_name='Pessoa'
    )
    cpf = models.CharField(
        'CPF',
        max_length=14,
        unique=True,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\d{3}\.?\d{3}\.?\d{3}-?\d{2}$',
                message='Informe um CPF válido (ex: 000.000.000-00).'
            ),
            validar_cpf,
        ]
    )
    data_nascimento = models.DateField('Data de nascimento', null=True, blank=True)
    tipo_deficiencia = models.CharField(
        'Tipo de deficiência',
        max_length=100,
        blank=True,
        help_text='Descrição da deficiência motora do paciente.'
    )
    perfil = models.CharField(
        'Perfil',
        max_length=20,
        choices=PERFIL_CHOICES,
        default='paciente',
        help_text='Indica se o cadastro é do paciente, familiar ou cuidador.'
    )
    comunicacao_verbal_preservada = models.BooleanField(
        'Comunicação verbal preservada',
        default=True,
        help_text='Indica se o paciente mantém a capacidade de comunicação verbal '
                  '(relevante para o sistema de comandos de voz do kit).'
    )

    class Meta:
        verbose_name = 'Pessoa Física'
        verbose_name_plural = 'Pessoas Físicas'

    def __str__(self):
        return f'{self.pessoa.nome} - PF'


class PessoaJuridica(models.Model):
    """Especialização de Pessoa para pessoas jurídicas/instituições (B2B).

    Representa clínicas de reabilitação, hospitais e outras instituições
    de saúde interessadas no Programa Piloto.
    """

    TIPO_INSTITUICAO_CHOICES = [
        ('clinica', 'Clínica de Reabilitação'),
        ('hospital', 'Hospital'),
        ('ong', 'ONG / Instituição Social'),
        ('outro', 'Outro'),
    ]

    pessoa = models.OneToOneField(
        Pessoa,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='pessoa_juridica',
        verbose_name='Pessoa'
    )
    cnpj = models.CharField(
        'CNPJ',
        max_length=18,
        unique=True,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}$',
                message='Informe um CNPJ válido (ex: 00.000.000/0000-00).'
            ),
            validar_cnpj,
        ]
    )
    tipo_instituicao = models.CharField(
        'Tipo de instituição',
        max_length=30,
        choices=TIPO_INSTITUICAO_CHOICES,
        default='clinica'
    )
    contato_responsavel = models.CharField(
        'Nome do responsável',
        max_length=200,
        blank=True,
        help_text='Nome da pessoa de contato na instituição.'
    )
    cargo_responsavel = models.CharField(
        'Cargo do responsável',
        max_length=100,
        blank=True
    )

    class Meta:
        verbose_name = 'Pessoa Jurídica'
        verbose_name_plural = 'Pessoas Jurídicas'

    def __str__(self):
        return f'{self.pessoa.nome} - PJ'


class Modelo(models.Model):
    """Modelos de cadeiras de rodas e equipamentos de mobilidade.

    Catálogo de cadeiras compatíveis com o Kit de Automação EasyRide.
    """

    nome_modelo = models.CharField('Nome do modelo', max_length=100)
    marca = models.CharField('Marca', max_length=100)
    motorizada = models.BooleanField(
        'Motorizada',
        default=False,
        help_text='Indica se a cadeira é motorizada (requisito para o kit).'
    )
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Modelo de Cadeira'
        verbose_name_plural = 'Modelos de Cadeiras'
        ordering = ['marca', 'nome_modelo']
        unique_together = ['nome_modelo', 'marca']

    def __str__(self):
        tipo = 'Motorizada' if self.motorizada else 'Manual'
        return f'{self.marca} {self.nome_modelo} ({tipo})'


class Interesse(models.Model):
    """Registro de interesse (lead) de uma Pessoa por um Modelo.

    Entidade associativa que resolve o relacionamento N:N entre Pessoa e Modelo,
    armazenando os dados do lead captado pelo formulário do site.
    """

    STATUS_CHOICES = [
        ('novo', 'Novo'),
        ('contatado', 'Contatado'),
        ('qualificado', 'Qualificado'),
        ('negociacao', 'Em Negociação'),
        ('convertido', 'Convertido'),
        ('perdido', 'Perdido'),
    ]

    ORIGEM_CHOICES = [
        ('google', 'Google'),
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('indicacao', 'Indicação'),
        ('evento', 'Evento'),
        ('outro', 'Outro'),
    ]

    pessoa = models.ForeignKey(
        Pessoa,
        on_delete=models.CASCADE,
        related_name='interesses',
        verbose_name='Pessoa'
    )
    modelo = models.ForeignKey(
        Modelo,
        on_delete=models.CASCADE,
        related_name='interesses',
        verbose_name='Modelo'
    )
    data_hora = models.DateTimeField('Data/hora do registro', auto_now_add=True)
    quantidade_estimada = models.PositiveIntegerField(
        'Quantidade estimada',
        default=1,
        help_text='Quantidade de kits/cadeiras de interesse.'
    )
    mensagem = models.TextField(
        'Mensagem',
        blank=True,
        help_text='Mensagem ou observações adicionais do interessado.'
    )
    origem = models.CharField(
        'Como nos conheceu',
        max_length=20,
        choices=ORIGEM_CHOICES,
        default='outro',
        help_text='Canal pelo qual o interessado conheceu a EasyRide.'
    )
    status_lead = models.CharField(
        'Status do lead',
        max_length=20,
        choices=STATUS_CHOICES,
        default='novo'
    )
    aceite_termos = models.BooleanField(
        'Aceite dos termos',
        default=False,
        help_text='Indica se o interessado aceitou os termos de uso e política de privacidade.'
    )
    possui_cadeira = models.BooleanField(
        'Já possui cadeira motorizada',
        default=False,
        help_text='Indica se o interessado já possui uma cadeira de rodas motorizada.'
    )

    class Meta:
        verbose_name = 'Interesse (Lead)'
        verbose_name_plural = 'Interesses (Leads)'
        ordering = ['-data_hora']
        indexes = [
            models.Index(fields=['status_lead'], name='idx_interesse_status'),
            models.Index(fields=['origem'], name='idx_interesse_origem'),
            models.Index(fields=['-data_hora'], name='idx_interesse_data'),
            models.Index(
                fields=['status_lead', 'origem'],
                name='idx_interesse_status_origem',
            ),
            models.Index(
                fields=['pessoa', '-data_hora'],
                name='idx_interesse_pessoa_data',
            ),
        ]

    def __str__(self):
        return f'Lead #{self.pk} - {self.pessoa.nome} → {self.modelo}'


class Beneficio(models.Model):
    """Item de benefício exibido na landing page institucional.

    Conteúdo dinâmico consumido pelo Frontend via GET /api/beneficios
    (Contrato de Integração v3.0)
    """

    titulo = models.CharField('Título', max_length=200)
    descricao = models.TextField('Descrição')
    icone = models.CharField(
        'Ícone',
        max_length=50,
        help_text='Identificador do ícone a ser exibido no Frontend (ex: "microphone").'
    )
    ordem = models.PositiveIntegerField('Ordem de exibição', default=0)
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Benefício'
        verbose_name_plural = 'Benefícios'
        ordering = ['ordem']

    def __str__(self):
        return self.titulo


class Depoimento(models.Model):
    """Depoimento de cliente exibido na landing page institucional.

    Conteúdo dinâmico consumido pelo Frontend via GET /api/depoimentos
    (Contrato de Integração v3.0).
    """

    nome = models.CharField('Nome', max_length=200)
    foto = models.CharField(
        'Foto',
        max_length=300,
        blank=True,
        help_text='URL da foto do depoente.'
    )
    texto = models.TextField('Texto do depoimento')
    avaliacao = models.PositiveSmallIntegerField(
        'Avaliação',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Nota de 1 a 5.'
    )
    ordem = models.PositiveIntegerField('Ordem de exibição', default=0)
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Depoimento'
        verbose_name_plural = 'Depoimentos'
        ordering = ['ordem']

    def __str__(self):
        return f'{self.nome} ({self.avaliacao}★)'


class Faq(models.Model):
    """Pergunta frequente exibida na landing page institucional.

    Conteúdo dinâmico consumido pelo Frontend via GET /api/faq
    (Contrato de Integração v3.0).
    """

    pergunta = models.CharField('Pergunta', max_length=300)
    resposta = models.TextField('Resposta')
    ordem = models.PositiveIntegerField('Ordem de exibição', default=0)
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Pergunta Frequente'
        verbose_name_plural = 'Perguntas Frequentes (FAQ)'
        ordering = ['ordem']

    def __str__(self):
        return self.pergunta
