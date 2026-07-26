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

    def add_arguments(self, parser):
        parser.add_argument(
            '--bulk',
            type=int,
            default=0,
            metavar='N',
            help=(
                'Gera N leads sintéticos adicionais para teste de volume. '
                'O CT02 da Especificação exige ao menos 100 registros para '
                'validar a paginação profunda do admin.'
            ),
        )

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

        # ── Massa de teste do item 8 da Especificação Técnica ────────
        #
        # Os 15 registros nomeados do documento, na ordem original (id 1..15).
        # Três adaptações foram necessárias para que a massa fosse carregável:
        #
        # 1. CPF/CNPJ — os documentos do PDF (111.222.333-44 e afins) não
        #    passam por `validar_cpf`/`validar_cnpj`, que conferem o dígito
        #    verificador pelo algoritmo da Receita. O prefixo do documento foi
        #    preservado e apenas o DV recalculado, então cada registro continua
        #    reconhecível (111.222.333-44 → 111.222.333-96).
        #
        # 2. status_lead — o PDF usa 'contato' e 'fechado', que não existem em
        #    `Interesse.STATUS_CHOICES`. O funil do sistema é mais granular
        #    (novo, contatado, qualificado, negociacao, convertido, perdido) e
        #    foi mantido: 'contato' → 'contatado', 'fechado' → 'convertido'.
        #
        # 3. modelo_id — o PDF referencia ids 1..3 de um catálogo próprio.
        #    Aqui os leads são ancorados por índice nos modelos criados acima,
        #    preservando o mapeamento relativo do documento.
        leads_doc = [
            {
                'pessoa': {
                    'nome': 'João da Silva', 'email': 'joao.silva@email.com',
                    'telefone': '79998633911', 'estado': 'SE', 'cidade': 'Aracaju',
                },
                'pf': {
                    'cpf': '111.222.333-96', 'data_nascimento': '1990-05-20',
                    'tipo_deficiencia': 'Tetraplegia', 'perfil': 'paciente',
                    'comunicacao_verbal_preservada': True,
                },
                'interesse': {
                    'modelo_idx': 0, 'quantidade_estimada': 1,
                    'mensagem': 'Gostaria de testar os comandos de voz em ambiente residencial.',
                    'origem': 'google', 'aceite_termos': True,
                    'possui_cadeira': False, 'status_lead': 'novo',
                },
            },
            {
                'pessoa': {
                    'nome': 'Clínica Reabilitar Lagarto', 'email': 'contato@reabilitarlag.com',
                    'telefone': '7936312244', 'estado': 'SE', 'cidade': 'Lagarto',
                },
                'pj': {
                    'cnpj': '12.345.678/0001-95', 'tipo_instituicao': 'clinica',
                    'contato_responsavel': 'Dra. Paula Souza',
                    'cargo_responsavel': 'Diretora Clínica',
                },
                'interesse': {
                    'modelo_idx': 1, 'quantidade_estimada': 5,
                    'mensagem': 'Cotação de frota para automação do transporte interno de pacientes.',
                    'origem': 'evento', 'aceite_termos': True,
                    'possui_cadeira': True, 'status_lead': 'qualificado',
                },
            },
            {
                'pessoa': {
                    'nome': 'Carlos Mendes Santos', 'email': 'carlos.mendes@outlook.com',
                    'telefone': '71988884422', 'estado': 'BA', 'cidade': 'Salvador',
                },
                'pf': {
                    'cpf': '222.333.444-05', 'data_nascimento': '1985-11-12',
                    'tipo_deficiencia': 'Esclerose Lateral Amiotrófica (ELA)',
                    'perfil': 'paciente', 'comunicacao_verbal_preservada': False,
                },
                'interesse': {
                    'modelo_idx': 0, 'quantidade_estimada': 1,
                    'mensagem': 'O leitor de tela do site funcionou muito bem via teclado. Parabéns.',
                    'origem': 'instagram', 'aceite_termos': True,
                    'possui_cadeira': True, 'status_lead': 'contatado',
                },
            },
            {
                'pessoa': {
                    'nome': 'Hospital São Lucas Corporativo',
                    'email': 'suprimentos@saolucas.com.br',
                    'telefone': '1130034455', 'estado': 'SP', 'cidade': 'São Paulo',
                },
                'pj': {
                    'cnpj': '98.765.432/0001-98', 'tipo_instituicao': 'hospital',
                    'contato_responsavel': 'Marcos Roberto',
                    'cargo_responsavel': 'Gerente de Compras',
                },
                'interesse': {
                    'modelo_idx': 2, 'quantidade_estimada': 12,
                    'mensagem': 'Interesse em parceria de longo prazo para programa piloto de frotas autônomas.',
                    'origem': 'indicacao', 'aceite_termos': True,
                    'possui_cadeira': True, 'status_lead': 'convertido',
                },
            },
            {
                'pessoa': {
                    'nome': 'Mariana Rocha Oliveira', 'email': 'mari.rocha@gmail.com',
                    'telefone': '79991223344', 'estado': 'SE', 'cidade': 'Itabaiana',
                },
                'pf': {
                    'cpf': '333.444.555-08', 'data_nascimento': '1998-03-25',
                    'tipo_deficiencia': 'Paralisia Cerebral', 'perfil': 'familiar',
                    'comunicacao_verbal_preservada': True,
                },
                'interesse': {
                    'modelo_idx': 1, 'quantidade_estimada': 1,
                    'mensagem': 'Estou comprando para o meu irmão. Gostaria de saber sobre prazos de entrega.',
                    'origem': 'facebook', 'aceite_termos': True,
                    'possui_cadeira': False, 'status_lead': 'novo',
                },
            },
            {
                'pessoa': {
                    'nome': 'Roberto Alencar Lima', 'email': 'roberto.alencar@yahoo.com.br',
                    'telefone': '21981112233', 'estado': 'RJ', 'cidade': 'Niterói',
                },
                'pf': {
                    'cpf': '444.555.666-19', 'data_nascimento': '1972-07-08',
                    'tipo_deficiencia': 'Lesão Medular Severa', 'perfil': 'cuidador',
                    'comunicacao_verbal_preservada': True,
                },
                'interesse': {
                    'modelo_idx': 0, 'quantidade_estimada': 1,
                    'mensagem': 'Sou cuidador profissional e vejo que esse sistema trará muita independência.',
                    'origem': 'google', 'aceite_termos': True,
                    'possui_cadeira': True, 'status_lead': 'contatado',
                },
            },
            {
                'pessoa': {
                    'nome': 'Lar dos Idosos Esperança', 'email': 'diretoria@laresperanca.org',
                    'telefone': '8134221199', 'estado': 'PE', 'cidade': 'Recife',
                },
                'pj': {
                    'cnpj': '45.678.901/0001-75', 'tipo_instituicao': 'ong',
                    'contato_responsavel': 'Irmã Clara Santos',
                    'cargo_responsavel': 'Coordenadora Geral',
                },
                'interesse': {
                    'modelo_idx': 1, 'quantidade_estimada': 3,
                    'mensagem': 'Somos uma instituição filantrópica. Existe algum programa de desconto para ONGs?',
                    'origem': 'outro', 'aceite_termos': True,
                    'possui_cadeira': True, 'status_lead': 'qualificado',
                },
            },
            {
                'pessoa': {
                    'nome': 'Beatriz Cavalcante Fonseca', 'email': 'bia.fonseca@gmail.com',
                    'telefone': '85992223355', 'estado': 'CE', 'cidade': 'Fortaleza',
                },
                'pf': {
                    'cpf': '555.666.777-20', 'data_nascimento': '1993-01-14',
                    'tipo_deficiencia': 'Distrofia Muscular', 'perfil': 'paciente',
                    'comunicacao_verbal_preservada': True,
                },
                'interesse': {
                    'modelo_idx': 0, 'quantidade_estimada': 1,
                    'mensagem': 'Preciso confirmar se as dimensões do joystick padrão encaixam no meu modelo.',
                    'origem': 'instagram', 'aceite_termos': True,
                    'possui_cadeira': True, 'status_lead': 'novo',
                },
            },
            {
                'pessoa': {
                    'nome': 'Associação de Assistência à Criança Deficiente SE',
                    'email': 'contato@aacdse.org.br',
                    'telefone': '7932115566', 'estado': 'SE', 'cidade': 'Aracaju',
                },
                'pj': {
                    'cnpj': '12.987.654/0002-10', 'tipo_instituicao': 'ong',
                    'contato_responsavel': 'Dr. Henrique Lima',
                    'cargo_responsavel': 'Diretor Técnico',
                },
                'interesse': {
                    'modelo_idx': 2, 'quantidade_estimada': 8,
                    'mensagem': 'Mapeamento de demanda para implantação piloto nas salas de fisioterapia robótica.',
                    'origem': 'evento', 'aceite_termos': True,
                    'possui_cadeira': True, 'status_lead': 'qualificado',
                },
            },
            {
                'pessoa': {
                    'nome': 'Ricardo Pereira Souza', 'email': 'ricardopereira@outlook.com',
                    'telefone': '31984445566', 'estado': 'MG', 'cidade': 'Belo Horizonte',
                },
                'pf': {
                    'cpf': '666.777.888-30', 'data_nascimento': '1968-09-30',
                    'tipo_deficiencia': 'Tetraplegia por trauma', 'perfil': 'familiar',
                    'comunicacao_verbal_preservada': True,
                },
                'interesse': {
                    'modelo_idx': 1, 'quantidade_estimada': 1,
                    'mensagem': 'Aguardando ansiosamente a liberação do lote comercial para Minas Gerais.',
                    'origem': 'google', 'aceite_termos': True,
                    'possui_cadeira': False, 'status_lead': 'contatado',
                },
            },
            {
                'pessoa': {
                    'nome': 'Juliana Vasconcelos Dias', 'email': 'ju.vasconcelos@gmail.com',
                    'telefone': '51991117788', 'estado': 'RS', 'cidade': 'Porto Alegre',
                },
                'pf': {
                    'cpf': '777.888.999-41', 'data_nascimento': '1991-04-18',
                    'tipo_deficiencia': 'Atrofia Muscular Espinhal (AME)',
                    'perfil': 'paciente', 'comunicacao_verbal_preservada': False,
                },
                'interesse': {
                    'modelo_idx': 0, 'quantidade_estimada': 1,
                    'mensagem': 'Garantimos que a IA processada localmente necessita de calibração por voz.',
                    'origem': 'outro', 'aceite_termos': True,
                    'possui_cadeira': True, 'status_lead': 'novo',
                },
            },
            {
                'pessoa': {
                    'nome': 'Clínica NeuroVida Nordeste', 'email': 'comercial@neurovidane.com',
                    'telefone': '8432219988', 'estado': 'RN', 'cidade': 'Natal',
                },
                'pj': {
                    'cnpj': '34.567.890/0001-30', 'tipo_instituicao': 'clinica',
                    'contato_responsavel': 'Patrícia Dantas',
                    'cargo_responsavel': 'Gestora Administrativa',
                },
                'interesse': {
                    'modelo_idx': 1, 'quantidade_estimada': 4,
                    'mensagem': 'Solicito envio de proposta comercial formalizada e especificações de garantia.',
                    'origem': 'indicacao', 'aceite_termos': True,
                    'possui_cadeira': True, 'status_lead': 'convertido',
                },
            },
            {
                'pessoa': {
                    'nome': 'Antônio Carlos Vieira', 'email': 'antonio.vieira@bol.com.br',
                    'telefone': '11987776655', 'estado': 'SP', 'cidade': 'Santos',
                },
                'pf': {
                    'cpf': '888.999.000-78', 'data_nascimento': '1960-12-05',
                    'tipo_deficiencia': 'Sequela de AVC severo', 'perfil': 'familiar',
                    'comunicacao_verbal_preservada': False,
                },
                'interesse': {
                    'modelo_idx': 0, 'quantidade_estimada': 1,
                    'mensagem': 'Meu pai perdeu os movimentos do lado direito e a fala está muito comprometida.',
                    'origem': 'google', 'aceite_termos': True,
                    'possui_cadeira': True, 'status_lead': 'novo',
                },
            },
            {
                'pessoa': {
                    'nome': 'Centro de Apoio Psico-Motor de Lagarto',
                    'email': 'diretoria@capmlag.com.br',
                    'telefone': '7936319988', 'estado': 'SE', 'cidade': 'Lagarto',
                },
                'pj': {
                    'cnpj': '56.789.012/0001-00', 'tipo_instituicao': 'outro',
                    'contato_responsavel': 'Prof. Roberto Santos',
                    'cargo_responsavel': 'Coordenador de Projetos',
                },
                'interesse': {
                    'modelo_idx': 1, 'quantidade_estimada': 2,
                    'mensagem': 'Mapeamento inicial de viabilidade para cooperação técnica científica com o campus.',
                    'origem': 'evento', 'aceite_termos': True,
                    'possui_cadeira': True, 'status_lead': 'contatado',
                },
            },
            {
                'pessoa': {
                    'nome': 'Fernanda Lima Cavalcanti', 'email': 'fer.cavalcanti@live.com',
                    'telefone': '81992228899', 'estado': 'PE', 'cidade': 'Olinda',
                },
                'pf': {
                    'cpf': '999.000.111-12', 'data_nascimento': '1995-08-19',
                    'tipo_deficiencia': 'Monoplegia com espasticidade',
                    'perfil': 'paciente', 'comunicacao_verbal_preservada': True,
                },
                'interesse': {
                    'modelo_idx': 2, 'quantidade_estimada': 1,
                    'mensagem': 'Gostaria de agendar uma demonstração em vídeo do kit desviando de obstáculos.',
                    'origem': 'instagram', 'aceite_termos': True,
                    'possui_cadeira': False, 'status_lead': 'qualificado',
                },
            },
        ]

        for lead in leads_doc:
            p_data = lead['pessoa']
            pessoa, created = Pessoa.objects.get_or_create(
                email=p_data['email'], defaults=p_data,
            )

            if 'pf' in lead:
                PessoaFisica.objects.get_or_create(pessoa=pessoa, defaults=lead['pf'])
                tipo = 'B2C'
            else:
                PessoaJuridica.objects.get_or_create(pessoa=pessoa, defaults=lead['pj'])
                tipo = 'B2B'

            i_data = lead['interesse'].copy()
            modelo = modelos[i_data.pop('modelo_idx')]
            Interesse.objects.get_or_create(
                pessoa=pessoa, modelo=modelo, defaults=i_data,
            )

            label = 'Criado' if created else 'Já existe'
            self.stdout.write(f'  [{label}] Lead {tipo}: {pessoa.nome}')

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

        # ── Volume sintético para o CT02 ─────────────────────────────
        if options['bulk']:
            self._gerar_volume(options['bulk'], modelos)

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

    # ── Geração de volume (CT02) ─────────────────────────────────────

    @staticmethod
    def _cpf_valido(seq: int) -> str:
        """Deriva um CPF com dígitos verificadores corretos a partir de `seq`.

        Os CPFs de exemplo da Especificação (111.222.333-44 e afins) não
        passam por `validar_cpf`, que confere o DV pelo algoritmo da Receita.
        Gerar o dígito aqui mantém a massa de teste aceitável pelo mesmo
        validador que a API aplica.

        A base começa em 100.000.000 para nunca cair em sequência repetida
        (`00000000000`), que o validador rejeita mesmo com o DV correto.
        """
        base = f'{100_000_000 + (seq % 800_000_000):09d}'

        soma = sum(int(base[i]) * (10 - i) for i in range(9))
        resto = (soma * 10) % 11
        d1 = 0 if resto == 10 else resto

        parcial = base + str(d1)
        soma = sum(int(parcial[i]) * (11 - i) for i in range(10))
        resto = (soma * 10) % 11
        d2 = 0 if resto == 10 else resto

        return f'{base}{d1}{d2}'

    @staticmethod
    def _cnpj_valido(seq: int) -> str:
        """Deriva um CNPJ com dígitos verificadores corretos a partir de `seq`."""
        base = f'{seq % 100_000_000:08d}0001'

        pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

        soma = sum(int(base[i]) * pesos1[i] for i in range(12))
        resto = soma % 11
        d1 = 0 if resto < 2 else 11 - resto

        parcial = base + str(d1)
        soma = sum(int(parcial[i]) * pesos2[i] for i in range(13))
        resto = soma % 11
        d2 = 0 if resto < 2 else 11 - resto

        return f'{base}{d1}{d2}'

    def _gerar_volume(self, quantidade, modelos):
        """Cria `quantidade` leads sintéticos alternando B2C e B2B.

        Usado pelo CT02 (paginação profunda), que exige ao menos 100
        registros. As Pessoas são criadas em lote, mas os Interesses não
        podem ser: `data_hora` é auto_now_add e o bulk_create gravaria todos
        com o mesmo carimbo, deixando a ordenação por data — justamente o
        que o CT02 verifica ao mudar de página — sem critério de desempate.
        """
        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'Gerando {quantidade} lead(s) sintético(s) para teste de volume...'
        ))

        estados = ['SE', 'BA', 'SP', 'RJ', 'PE', 'CE', 'MG', 'RS', 'RN']
        origens = ['google', 'instagram', 'facebook', 'indicacao', 'evento', 'outro']
        status_leads = ['novo', 'contatado', 'qualificado', 'negociacao', 'convertido', 'perdido']
        perfis = ['paciente', 'familiar', 'cuidador']
        tipos_inst = ['clinica', 'hospital', 'ong', 'outro']

        # Continua a numeração de execuções anteriores para não colidir nos
        # unique de email/cpf/cnpj quando o comando é chamado mais de uma vez.
        offset = Pessoa.objects.filter(email__startswith='volume').count()
        criados = 0

        for i in range(offset, offset + quantidade):
            juridica = i % 3 == 0
            email = f'volume{i}@easyride-teste.com'

            if Pessoa.objects.filter(email=email).exists():
                continue

            pessoa = Pessoa.objects.create(
                nome=f'{"Instituicao" if juridica else "Lead"} Volume {i:04d}',
                email=email,
                telefone=f'{79900000000 + i}',
                estado=estados[i % len(estados)],
                cidade='Cidade Teste',
            )

            if juridica:
                PessoaJuridica.objects.create(
                    pessoa=pessoa,
                    cnpj=self._cnpj_valido(i),
                    tipo_instituicao=tipos_inst[i % len(tipos_inst)],
                    contato_responsavel=f'Responsavel {i:04d}',
                    cargo_responsavel='Coordenacao',
                )
            else:
                PessoaFisica.objects.create(
                    pessoa=pessoa,
                    cpf=self._cpf_valido(i),
                    tipo_deficiencia='Registro sintetico de teste',
                    perfil=perfis[i % len(perfis)],
                    comunicacao_verbal_preservada=i % 2 == 0,
                )

            Interesse.objects.create(
                pessoa=pessoa,
                modelo=modelos[i % len(modelos)],
                quantidade_estimada=(i % 12) + 1,
                mensagem=f'Lead sintetico #{i:04d} para validacao de paginacao (CT02).',
                origem=origens[i % len(origens)],
                status_lead=status_leads[i % len(status_leads)],
                aceite_termos=True,
                possui_cadeira=i % 2 == 0,
            )
            criados += 1

        self.stdout.write(f'  {criados} lead(s) sintético(s) criado(s).')
