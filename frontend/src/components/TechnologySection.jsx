import './Sections.css';

const PASSOS = [
  {
    numero: 1,
    titulo: 'Reconhecimento de Voz',
    descricao: 'O usuário utiliza comandos simples como "Ir para o quarto" ou "Voltar".',
  },
  {
    numero: 2,
    titulo: 'Mapeamento do Ambiente',
    descricao: 'Sensores analisam o espaço em tempo real e criam um mapa do ambiente.',
  },
  {
    numero: 3,
    titulo: 'IA de Navegação',
    descricao: 'O sistema calcula automaticamente a melhor rota para o destino.',
  },
  {
    numero: 4,
    titulo: 'Segurança Automática',
    descricao: 'Obstáculos são detectados e evitados durante o trajeto.',
  },
];

export default function TechnologySection() {
  return (
    <section id="tecnologia" className="technology" aria-labelledby="tecnologia-titulo">
      <div className="container">
        <div className="section-title">
          <span>A TECNOLOGIA</span>
          <h2 id="tecnologia-titulo">Como a EasyRide funciona</h2>
        </div>

        <ol className="steps">
          {PASSOS.map((passo) => (
            <li key={passo.numero} className="step">
              <span className="step-numero" aria-hidden="true">
                {passo.numero}
              </span>
              <h3>{passo.titulo}</h3>
              <p>{passo.descricao}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
