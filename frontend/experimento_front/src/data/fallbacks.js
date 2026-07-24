/*
 * Conteúdo de contingência exigido pela Arquitetura_Componentes_React_v3
 * para o estado "Erro 500" das seções dinâmicas:
 *  - BenefitsSection: fallback hardcoded
 *  - TestimonialsSection: 3 depoimentos hardcoded
 *  - FAQSection: 5 perguntas hardcoded
 */

export const BENEFICIOS_FALLBACK = [
  {
    id: 'fb-1',
    titulo: 'Controle por Voz',
    descricao: 'Comandos simples como "Ir para o quarto" ou "Voltar" movem a cadeira sem esforço físico.',
    icone: '🎙️',
  },
  {
    id: 'fb-2',
    titulo: 'Kit Universal Plug & Play',
    descricao: 'Instala na cadeira motorizada que o usuário já possui, sem precisar comprar uma nova.',
    icone: '🔌',
  },
  {
    id: 'fb-3',
    titulo: 'Navegação Inteligente com IA',
    descricao: 'Sensores mapeiam o ambiente e a IA calcula automaticamente a melhor rota até o destino.',
    icone: '🧠',
  },
  {
    id: 'fb-4',
    titulo: 'Segurança Automática',
    descricao: 'Obstáculos são detectados e evitados em tempo real durante todo o trajeto.',
    icone: '🛡️',
  },
];

export const DEPOIMENTOS_FALLBACK = [
  {
    id: 'fb-1',
    nome: 'Ana Paula M.',
    foto: '',
    texto:
      'Depois do kit EasyRide, meu irmão voltou a se mover pela casa sozinho. A autonomia dele mudou a rotina de toda a família.',
    avaliacao: 5,
  },
  {
    id: 'fb-2',
    nome: 'Dr. Carlos Menezes',
    foto: '',
    texto:
      'Na clínica, o transporte interno dos pacientes ficou mais seguro e liberou a equipe assistencial para o que realmente importa.',
    avaliacao: 5,
  },
  {
    id: 'fb-3',
    nome: 'Roberto S.',
    foto: '',
    texto:
      'Convivo com ELA e o controle por voz me devolveu uma independência que eu achava que tinha perdido para sempre.',
    avaliacao: 5,
  },
];

export const FAQ_FALLBACK = [
  {
    id: 'fb-1',
    pergunta: 'O kit funciona em qualquer cadeira motorizada?',
    resposta:
      'O projeto foi desenvolvido para ser compatível com a maioria das cadeiras motorizadas disponíveis no mercado.',
  },
  {
    id: 'fb-2',
    pergunta: 'Preciso comprar uma cadeira nova?',
    resposta:
      'Não. O diferencial da EasyRide é transformar a cadeira que o usuário já possui em uma cadeira autônoma.',
  },
  {
    id: 'fb-3',
    pergunta: 'Quem pode utilizar a solução?',
    resposta:
      'Pessoas com tetraplegia, ELA e outras limitações motoras, além de clínicas e hospitais.',
  },
  {
    id: 'fb-4',
    pergunta: 'Como é feita a instalação do kit?',
    resposta:
      'O kit é Plug & Play: a instalação é feita sobre a cadeira motorizada existente, sem modificações estruturais permanentes.',
  },
  {
    id: 'fb-5',
    pergunta: 'A EasyRide atende clínicas e hospitais?',
    resposta:
      'Sim. Oferecemos parcerias B2B para automação do transporte interno de pacientes e otimização da equipe assistencial.',
  },
];
