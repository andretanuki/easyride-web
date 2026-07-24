import './Sections.css';

const MEMBROS = [
  {
    nome: 'Luiz Eduardo Andrade de Oliveira',
    papel:
      'Coordenação geral, estratégia de mercado, desenvolvimento da interface mobile e integração do reconhecimento de voz com o hardware.',
  },
  {
    nome: 'Matheus Cardoso Santos',
    papel:
      'Pesquisador e Engenheiro de Software Embarcado. Responsável pela IA, navegação autônoma, mapeamento indoor e registro do software.',
  },
  {
    nome: 'Vinícius Conceição Ferreira dos Santos',
    papel:
      'Engenheiro de Hardware responsável pela integração elétrica, homologação dos componentes e placas eletrônicas.',
  },
];

export default function TeamSection() {
  return (
    <section id="equipe" className="team" aria-labelledby="equipe-titulo">
      <div className="container">
        <div className="section-title">
          <span>EQUIPE</span>
          <h2 id="equipe-titulo">Quem está construindo a EasyRide</h2>
        </div>

        <div className="cards cards-3">
          {MEMBROS.map((membro) => (
            <article key={membro.nome} className="audience-card">
              <h3>{membro.nome}</h3>
              <p>{membro.papel}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
