"""Script para popular o banco de dados com dados de exemplo.

Execute com: python manage.py shell < seed_data.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from EasyRide.models import Modelo, Pessoa, PessoaFisica, PessoaJuridica, Interesse

# ── Modelos de Cadeiras ──────────────────────────────────────
modelos_data = [
    {'nome_modelo': 'Freedom One', 'marca': 'Freedom', 'motorizada': True},
    {'nome_modelo': 'Freedom CGR', 'marca': 'Freedom', 'motorizada': True},
    {'nome_modelo': 'Power Lite', 'marca': 'Quickie', 'motorizada': True},
    {'nome_modelo': 'Salsa M2', 'marca': 'Sunrise Medical', 'motorizada': True},
    {'nome_modelo': 'Compact', 'marca': 'Ortobras', 'motorizada': False},
    {'nome_modelo': 'Star Lite', 'marca': 'Ortobras', 'motorizada': True},
    {'nome_modelo': 'Styles Comfort', 'marca': 'Ottobock', 'motorizada': True},
    {'nome_modelo': 'Avantgarde', 'marca': 'Ottobock', 'motorizada': False},
]

modelos = []
for m in modelos_data:
    obj, created = Modelo.objects.get_or_create(**m)
    modelos.append(obj)
    status = 'Criado' if created else 'Já existe'
    print(f'  [{status}] Modelo: {obj}')

# ── Leads B2C (Pessoas Físicas) ──────────────────────────────
leads_b2c = [
    {
        'pessoa': {'nome': 'Carlos Lima', 'email': 'carlos.lima@email.com', 'telefone': '71988887777', 'estado': 'BA', 'cidade': 'Salvador'},
        'pf': {'cpf': '98765432100', 'tipo_deficiencia': 'Paralisia cerebral', 'perfil': 'familiar', 'comunicacao_verbal_preservada': True},
        'interesse': {'modelo_idx': 0, 'quantidade_estimada': 1, 'mensagem': 'Meu filho precisa de mais autonomia. Gostaria de saber mais sobre o kit.', 'origem': 'site_b2c', 'aceite_termos': True, 'possui_cadeira': True},
    },
    {
        'pessoa': {'nome': 'Ana Clara Santos', 'email': 'ana.clara@email.com', 'telefone': '11977776666', 'estado': 'SP', 'cidade': 'São Paulo'},
        'pf': {'cpf': '12345678901', 'tipo_deficiencia': 'Esclerose lateral amiotrófica (ELA)', 'perfil': 'paciente', 'comunicacao_verbal_preservada': True},
        'interesse': {'modelo_idx': 2, 'quantidade_estimada': 1, 'mensagem': 'Tenho ELA e gostaria de manter minha independência de locomoção.', 'origem': 'site_b2c', 'aceite_termos': True, 'possui_cadeira': True},
    },
    {
        'pessoa': {'nome': 'Roberto Mendes', 'email': 'roberto.m@email.com', 'telefone': '21966665555', 'estado': 'RJ', 'cidade': 'Rio de Janeiro'},
        'pf': {'cpf': '45678912300', 'tipo_deficiencia': 'Lesão medular (T4)', 'perfil': 'cuidador', 'comunicacao_verbal_preservada': True},
        'interesse': {'modelo_idx': 3, 'quantidade_estimada': 1, 'mensagem': 'Sou cuidador e busco solução para o paciente que acompanho.', 'origem': 'site_b2c', 'aceite_termos': True, 'possui_cadeira': False},
    },
]

for lead in leads_b2c:
    p_data = lead['pessoa']
    pessoa, created = Pessoa.objects.get_or_create(email=p_data['email'], defaults=p_data)
    pf_data = lead['pf']
    PessoaFisica.objects.get_or_create(pessoa=pessoa, defaults=pf_data)
    i_data = lead['interesse']
    modelo = modelos[i_data.pop('modelo_idx')]
    Interesse.objects.get_or_create(
        pessoa=pessoa, modelo=modelo,
        defaults={k: v for k, v in i_data.items()}
    )
    status = 'Criado' if created else 'Já existe'
    print(f'  [{status}] Lead B2C: {pessoa.nome}')

# ── Leads B2B (Pessoas Jurídicas) ────────────────────────────
leads_b2b = [
    {
        'pessoa': {'nome': 'Clínica Esperança', 'email': 'contato@clinicaesperanca.com.br', 'telefone': '7133334444', 'estado': 'BA', 'cidade': 'Feira de Santana'},
        'pj': {'cnpj': '12345678000199', 'tipo_instituicao': 'clinica', 'contato_responsavel': 'Dr. Pedro Almeida', 'cargo_responsavel': 'Diretor Clínico'},
        'interesse': {'modelo_idx': 1, 'quantidade_estimada': 5, 'mensagem': 'Temos interesse em equipar nosso setor de reabilitação com 5 kits.', 'origem': 'site_b2b', 'aceite_termos': True, 'possui_cadeira': True},
    },
    {
        'pessoa': {'nome': 'Hospital São Lucas', 'email': 'compras@hsl.org.br', 'telefone': '1132221111', 'estado': 'SP', 'cidade': 'Campinas'},
        'pj': {'cnpj': '98765432000188', 'tipo_instituicao': 'hospital', 'contato_responsavel': 'Maria Fernanda Costa', 'cargo_responsavel': 'Coordenadora de Compras'},
        'interesse': {'modelo_idx': 5, 'quantidade_estimada': 10, 'mensagem': 'Gostaríamos de participar do Programa Piloto.', 'origem': 'site_b2b', 'aceite_termos': True, 'possui_cadeira': False},
    },
]

for lead in leads_b2b:
    p_data = lead['pessoa']
    pessoa, created = Pessoa.objects.get_or_create(email=p_data['email'], defaults=p_data)
    pj_data = lead['pj']
    PessoaJuridica.objects.get_or_create(pessoa=pessoa, defaults=pj_data)
    i_data = lead['interesse']
    modelo = modelos[i_data.pop('modelo_idx')]
    Interesse.objects.get_or_create(
        pessoa=pessoa, modelo=modelo,
        defaults={k: v for k, v in i_data.items()}
    )
    status = 'Criado' if created else 'Já existe'
    print(f'  [{status}] Lead B2B: {pessoa.nome}')

print('\n✅ Seed concluído com sucesso!')
print(f'   → {Modelo.objects.count()} modelos de cadeiras')
print(f'   → {Pessoa.objects.count()} pessoas cadastradas')
print(f'   → {PessoaFisica.objects.count()} pessoas físicas (B2C)')
print(f'   → {PessoaJuridica.objects.count()} pessoas jurídicas (B2B)')
print(f'   → {Interesse.objects.count()} interesses/leads')
