"""Validadores customizados do app EasyRide.

Implementa a verificação dos dígitos verificadores de CPF e CNPJ
conforme as regras da Receita Federal, complementando a validação
de formato feita por RegexValidator nos models.
"""

import re

from django.core.exceptions import ValidationError


def _somente_digitos(valor: str) -> str:
    """Remove pontos, traços, barras e espaços, mantendo apenas dígitos."""
    return re.sub(r'\D', '', valor or '')


def validar_cpf(valor: str) -> None:
    """Valida o CPF conforme o algoritmo da Receita Federal.

    Aceita CPF com ou sem formatação (000.000.000-00 ou 00000000000).
    Vazio é considerado válido (a obrigatoriedade é controlada por blank/required).

    Raises:
        ValidationError: Se o CPF for inválido (tamanho, repetição ou DV incorreto).
    """
    if not valor:
        return

    cpf = _somente_digitos(valor)

    if len(cpf) != 11:
        raise ValidationError('CPF deve conter 11 dígitos.')

    # Rejeita sequências repetidas (000.000.000-00, 111.111.111-11, etc.)
    if cpf == cpf[0] * 11:
        raise ValidationError('CPF inválido.')

    # Cálculo do primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = (soma * 10) % 11
    digito1 = 0 if resto == 10 else resto

    if digito1 != int(cpf[9]):
        raise ValidationError('CPF inválido.')

    # Cálculo do segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = (soma * 10) % 11
    digito2 = 0 if resto == 10 else resto

    if digito2 != int(cpf[10]):
        raise ValidationError('CPF inválido.')


def validar_cnpj(valor: str) -> None:
    """Valida o CNPJ conforme o algoritmo da Receita Federal.

    Aceita CNPJ com ou sem formatação (00.000.000/0000-00 ou 00000000000000).
    Vazio é considerado válido (a obrigatoriedade é controlada por blank/required).

    Raises:
        ValidationError: Se o CNPJ for inválido (tamanho, repetição ou DV incorreto).
    """
    if not valor:
        return

    cnpj = _somente_digitos(valor)

    if len(cnpj) != 14:
        raise ValidationError('CNPJ deve conter 14 dígitos.')

    if cnpj == cnpj[0] * 14:
        raise ValidationError('CNPJ inválido.')

    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    soma = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto

    if digito1 != int(cnpj[12]):
        raise ValidationError('CNPJ inválido.')

    soma = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto

    if digito2 != int(cnpj[13]):
        raise ValidationError('CNPJ inválido.')
