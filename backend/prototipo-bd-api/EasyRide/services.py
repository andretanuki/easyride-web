"""Camada de serviços (Service Layer) do app EasyRide.

Contém a lógica de negócio para operações de escrita (POST/PUT/DELETE).
As Views devem chamar estes serviços em vez de manipular models diretamente.
"""

from django.db import transaction
from .models import Pessoa, PessoaFisica, PessoaJuridica, Modelo, Interesse


@transaction.atomic
def criar_lead(dados_validados: dict) -> Interesse:
    """Cria um lead completo a partir do payload aninhado validado pelo LeadSerializer.

    Suporta tanto Pessoa Física quanto Pessoa Jurídica através do campo
    discriminador 'tipo_pessoa'. Utiliza transaction.atomic para garantir
    que todas as inserções ocorram com sucesso ou nenhuma seja persistida.

    Args:
        dados_validados: Dicionário com dados já validados pelo LeadSerializer.
                         Espera as chaves 'tipo_pessoa', campos raiz da Pessoa,
                         'dados_fisica' ou 'dados_juridica' (conforme tipo),
                         e 'interesse'.

    Returns:
        Instância de Interesse criada.

    Raises:
        ValueError: Se tipo_pessoa for um valor inesperado.
        Modelo.DoesNotExist: Se o modelo_id referenciado não existir.
    """
    tipo_pessoa = dados_validados['tipo_pessoa']

    # ── 1. Criar a Pessoa base ──────────────────────────────────
    # Usamos create para que um email duplicado levante IntegrityError,
    # resultando num HTTP 409 Conflict no endpoint.
    pessoa = Pessoa.objects.create(
        email=dados_validados['email'],
        nome=dados_validados['nome'],
        telefone=dados_validados.get('telefone', ''),
        estado=dados_validados.get('estado', ''),
        cidade=dados_validados.get('cidade', ''),
    )

    # ── 2. Criar a especialização (Física ou Jurídica) ───────────
    if tipo_pessoa == 'FISICA':
        dados_fisica = dados_validados.get('dados_fisica', {})
        PessoaFisica.objects.create(
            pessoa=pessoa,
            cpf=dados_fisica.get('cpf', ''),
            data_nascimento=dados_fisica.get('data_nascimento'),
            tipo_deficiencia=dados_fisica.get('tipo_deficiencia', ''),
            perfil=dados_fisica.get('perfil', 'paciente'),
            comunicacao_verbal_preservada=dados_fisica.get(
                'comunicacao_verbal_preservada', True
            ),
        )

    elif tipo_pessoa == 'JURIDICA':
        dados_juridica = dados_validados.get('dados_juridica', {})
        PessoaJuridica.objects.create(
            pessoa=pessoa,
            cnpj=dados_juridica.get('cnpj', ''),
            tipo_instituicao=dados_juridica.get('tipo_instituicao', 'clinica'),
            contato_responsavel=dados_juridica.get('contato_responsavel', ''),
            cargo_responsavel=dados_juridica.get('cargo_responsavel', ''),
        )

    else:
        raise ValueError(
            f'tipo_pessoa inválido: "{tipo_pessoa}". '
            'Valores aceitos: "FISICA", "JURIDICA".'
        )

    # ── 3. Criar o registro de Interesse ────────────────────────────────────
    dados_interesse = dados_validados['interesse']
    modelo = Modelo.objects.get(pk=dados_interesse['modelo_id'])

    interesse = Interesse.objects.create(
        pessoa=pessoa,
        modelo=modelo,
        quantidade_estimada=dados_interesse.get('quantidade_estimada', 1),
        mensagem=dados_interesse.get('mensagem', ''),
        origem=dados_interesse.get('origem', 'outro'),
        status_lead='novo',
        aceite_termos=dados_interesse['aceite_termos'],
        possui_cadeira=dados_interesse.get('possui_cadeira', False),
    )

    return interesse


def atualizar_status_lead(interesse_id: int, novo_status: str) -> Interesse:
    """Atualiza o status de um lead existente.

    Args:
        interesse_id: PK do Interesse a ser atualizado.
        novo_status: Novo valor para status_lead.

    Returns:
        Instância de Interesse atualizada.

    Raises:
        Interesse.DoesNotExist: Se o interesse não for encontrado.
        ValueError: Se o status for inválido.
    """
    status_validos = [choice[0] for choice in Interesse.STATUS_CHOICES]
    if novo_status not in status_validos:
        raise ValueError(
            f'Status inválido: "{novo_status}". '
            f'Valores permitidos: {status_validos}'
        )

    interesse = Interesse.objects.get(pk=interesse_id)
    interesse.status_lead = novo_status
    interesse.save(update_fields=['status_lead'])
    return interesse
