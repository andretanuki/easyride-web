"""Management command para popular o banco de dados com dados de exemplo.

Substitui o antigo seed_data.py (script solto) por um comando nativo do Django,
permitindo execução padronizada via: python manage.py seed

Vantagens sobre o script anterior:
- Integração nativa com o ecossistema de comandos do Django
- Saída colorida via self.stdout / self.style
- Possibilidade de receber argumentos (--clear, --verbose, etc.) no futuro
- Compatível com automações CI/CD e scripts Docker
"""

from django.core.management.base import BaseCommand
from EasyRide.models import (
    Modelo, Pessoa, PessoaFisica, PessoaJuridica, Interesse,
    Beneficio, Depoimento, Faq,
)


class Command(BaseCommand):
    help = 'Popula o banco de dados do EasyRide com dados iniciais de exemplo.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Iniciando seed do EasyRide...\n'))

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
            label = 'Criado' if created else 'Já existe'
            self.stdout.write(f'  [{label}] Modelo: {obj}')

        # ── Leads B2C (Pessoas Físicas) ──────────────────────────────
        leads_b2c = [
            {
                'pessoa': {
                    'nome': 'Carlos Lima', 'email': 'carlos.lima@email.com',
                    'telefone': '71988887777', 'estado': 'BA', 'cidade': 'Salvador',
                },
                'pf': {
                    'cpf': '98765432100', 'tipo_deficiencia': 'Paralisia cerebral',
                    'perfil': 'familiar', 'comunicacao_verbal_preservada': True,
                },
                'interesse': {
                    'modelo_idx': 0, 'quantidade_estimada': 1,
                    'mensagem': 'Meu filho precisa de mais autonomia. Gostaria de saber mais sobre o kit.',
                    'origem': 'google', 'aceite_termos': True, 'possui_cadeira': True,
                },
            },
            {
                'pessoa': {
                    'nome': 'Ana Clara Santos', 'email': 'ana.clara@email.com',
                    'telefone': '11977776666', 'estado': 'SP', 'cidade': 'São Paulo',
                },
                'pf': {
                    'cpf': '12345678901',
                    'tipo_deficiencia': 'Esclerose lateral amiotrófica (ELA)',
                    'perfil': 'paciente', 'comunicacao_verbal_preservada': True,
                },
                'interesse': {
                    'modelo_idx': 2, 'quantidade_estimada': 1,
                    'mensagem': 'Tenho ELA e gostaria de manter minha independência de locomoção.',
                    'origem': 'instagram', 'aceite_termos': True, 'possui_cadeira': True,
                },
            },
            {
                'pessoa': {
                    'nome': 'Roberto Mendes', 'email': 'roberto.m@email.com',
                    'telefone': '21966665555', 'estado': 'RJ', 'cidade': 'Rio de Janeiro',
                },
                'pf': {
                    'cpf': '45678912300', 'tipo_deficiencia': 'Lesão medular (T4)',
                    'perfil': 'cuidador', 'comunicacao_verbal_preservada': True,
                },
                'interesse': {
                    'modelo_idx': 3, 'quantidade_estimada': 1,
                    'mensagem': 'Sou cuidador e busco solução para o paciente que acompanho.',
                    'origem': 'indicacao', 'aceite_termos': True, 'possui_cadeira': False,
                },
            },
        ]

        for lead in leads_b2c:
            p_data = lead['pessoa']
            pessoa, created = Pessoa.objects.get_or_create(
                email=p_data['email'], defaults=p_data,
            )
            pf_data = lead['pf']
            PessoaFisica.objects.get_or_create(pessoa=pessoa, defaults=pf_data)
            i_data = lead['interesse'].copy()
            modelo = modelos[i_data.pop('modelo_idx')]
            Interesse.objects.get_or_create(
                pessoa=pessoa, modelo=modelo,
                defaults=i_data,
            )
            label = 'Criado' if created else 'Já existe'
            self.stdout.write(f'  [{label}] Lead B2C: {pessoa.nome}')

        # ── Leads B2B (Pessoas Jurídicas) ────────────────────────────
        leads_b2b = [
            {
                'pessoa': {
                    'nome': 'Clínica Esperança',
                    'email': 'contato@clinicaesperanca.com.br',
                    'telefone': '7133334444', 'estado': 'BA',
                    'cidade': 'Feira de Santana',
                },
                'pj': {
                    'cnpj': '12345678000195', 'tipo_instituicao': 'clinica',
                    'contato_responsavel': 'Dr. Pedro Almeida',
                    'cargo_responsavel': 'Diretor Clínico',
                },
                'interesse': {
                    'modelo_idx': 1, 'quantidade_estimada': 5,
                    'mensagem': 'Temos interesse em equipar nosso setor de reabilitação com 5 kits.',
                    'origem': 'evento', 'aceite_termos': True, 'possui_cadeira': True,
                },
            },
            {
                'pessoa': {
                    'nome': 'Hospital São Lucas', 'email': 'compras@hsl.org.br',
                    'telefone': '1132221111', 'estado': 'SP', 'cidade': 'Campinas',
                },
                'pj': {
                    'cnpj': '98765432000198', 'tipo_instituicao': 'hospital',
                    'contato_responsavel': 'Maria Fernanda Costa',
                    'cargo_responsavel': 'Coordenadora de Compras',
                },
                'interesse': {
                    'modelo_idx': 5, 'quantidade_estimada': 10,
                    'mensagem': 'Gostaríamos de participar do Programa Piloto.',
                    'origem': 'google', 'aceite_termos': True, 'possui_cadeira': False,
                },
            },
        ]

        for lead in leads_b2b:
            p_data = lead['pessoa']
            pessoa, created = Pessoa.objects.get_or_create(
                email=p_data['email'], defaults=p_data,
            )
            pj_data = lead['pj']
            PessoaJuridica.objects.get_or_create(pessoa=pessoa, defaults=pj_data)
            i_data = lead['interesse'].copy()
            modelo = modelos[i_data.pop('modelo_idx')]
            Interesse.objects.get_or_create(
                pessoa=pessoa, modelo=modelo,
                defaults=i_data,
            )
            label = 'Criado' if created else 'Já existe'
            self.stdout.write(f'  [{label}] Lead B2B: {pessoa.nome}')

        # ── Conteúdo da Landing Page (Beneficio/Depoimento/Faq) ──────
        beneficios_data = [
            {
                'titulo': 'Autonomia Total', 'ordem': 1,
                'descricao': 'Navegue pela sua casa apenas com comandos de voz.',
                'icone': 'microphone',
            },
            {
                'titulo': 'Fácil Instalação', 'ordem': 2,
                'descricao': 'O kit acopla sem danificar a estrutura da cadeira atual.',
                'icone': 'tools',
            },
            {
                'titulo': 'Compatibilidade Ampla', 'ordem': 3,
                'descricao': 'Funciona com a grande maioria dos modelos motorizados do mercado.',
                'icone': 'check-circle',
            },
        ]
        for b in beneficios_data:
            obj, created = Beneficio.objects.get_or_create(titulo=b['titulo'], defaults=b)
            label = 'Criado' if created else 'Já existe'
            self.stdout.write(f'  [{label}] Benefício: {obj}')

        depoimentos_data = [
            {
                'nome': 'Dona Maria', 'ordem': 1,
                'foto': 'https://easyride.example.com/depoimentos/dona-maria.jpg',
                'texto': 'O kit devolveu a independência que eu havia perdido.',
                'avaliacao': 5,
            },
            {
                'nome': 'Carlos Lima', 'ordem': 2,
                'foto': 'https://easyride.example.com/depoimentos/carlos-lima.jpg',
                'texto': 'Meu filho ganhou muito mais autonomia dentro de casa.',
                'avaliacao': 5,
            },
        ]
        for d in depoimentos_data:
            obj, created = Depoimento.objects.get_or_create(nome=d['nome'], defaults=d)
            label = 'Criado' if created else 'Já existe'
            self.stdout.write(f'  [{label}] Depoimento: {obj}')

        faqs_data = [
            {
                'pergunta': 'O Kit é compatível com minha cadeira?', 'ordem': 1,
                'resposta': 'Sim, com 90% dos modelos motorizados do mercado.',
            },
            {
                'pergunta': 'É necessário reformar a cadeira para instalar o kit?', 'ordem': 2,
                'resposta': 'Não. A instalação é feita sem qualquer dano à estrutura original.',
            },
        ]
        for f in faqs_data:
            obj, created = Faq.objects.get_or_create(pergunta=f['pergunta'], defaults=f)
            label = 'Criado' if created else 'Já existe'
            self.stdout.write(f'  [{label}] FAQ: {obj}')

        # ── Resumo ───────────────────────────────────────────────────
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ Seed concluído com sucesso!'))
        self.stdout.write(f'   → {Modelo.objects.count()} modelos de cadeiras')
        self.stdout.write(f'   → {Pessoa.objects.count()} pessoas cadastradas')
        self.stdout.write(f'   → {PessoaFisica.objects.count()} pessoas físicas (B2C)')
        self.stdout.write(f'   → {PessoaJuridica.objects.count()} pessoas jurídicas (B2B)')
        self.stdout.write(f'   → {Interesse.objects.count()} interesses/leads')
        self.stdout.write(f'   → {Beneficio.objects.count()} benefícios')
        self.stdout.write(f'   → {Depoimento.objects.count()} depoimentos')
        self.stdout.write(f'   → {Faq.objects.count()} perguntas frequentes (FAQ)')
