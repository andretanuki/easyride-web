"""Matriz de controle de acesso do painel administrativo (RBAC).

Item 5 da Especificação Técnica do Painel Administrativo. A plataforma
gerencia dados sensíveis de saúde — tipo de deficiência, CPF, comunicação
verbal preservada —, o que sob a LGPD exige acesso restrito ao mínimo
necessário para cada função.

Os grupos são criados pela migration 0007 a partir de `MATRIZ_GRUPOS`.
Mantê-la aqui, e não dentro da migration, permite que o admin e os testes
importem os mesmos nomes sem duplicar strings soltas pelo código.
"""

GRUPO_ADMIN_TI = 'Administrador (TI)'
GRUPO_VENDAS = 'Equipe de Vendas'
GRUPO_AUDITORIA = 'Auditoria / Instrutores'


# Permissões por grupo, no formato (app_label, codename).
#
# Administrador (TI) aparece com a lista vazia de propósito: a matriz lhe dá
# acesso total mais gestão de credenciais e infraestrutura, o que corresponde
# a `is_superuser` — uma flag do usuário, não um conjunto de permissões
# enumerável. O grupo é criado mesmo assim para que a matriz das três funções
# fique visível na tela de grupos do admin e sirva de rótulo organizacional.
#
# `view_pessoa*` é concedido aos dois grupos operacionais porque a listagem
# de Interesse resolve nome, e-mail e documento por relação: sem ele o
# painel de triagem fica inutilizável. A escrita em Pessoa permanece fora
# de ambos — corrigir cadastro de titular é ação do Administrador.
MATRIZ_GRUPOS = {
    GRUPO_ADMIN_TI: [],
    GRUPO_VENDAS: [
        ('EasyRide', 'view_interesse'),
        ('EasyRide', 'change_interesse'),
        ('EasyRide', 'view_modelo'),
        ('EasyRide', 'view_pessoa'),
        ('EasyRide', 'view_pessoafisica'),
        ('EasyRide', 'view_pessoajuridica'),
    ],
    GRUPO_AUDITORIA: [
        ('EasyRide', 'view_interesse'),
        ('EasyRide', 'view_modelo'),
        ('EasyRide', 'view_pessoa'),
        ('EasyRide', 'view_pessoafisica'),
        ('EasyRide', 'view_pessoajuridica'),
    ],
}
