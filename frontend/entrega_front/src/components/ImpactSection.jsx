import './Sections.css';

const ODS = [
  { sigla: 'ODS 3', nome: 'Saúde e Bem-Estar' },
  { sigla: 'ODS 9', nome: 'Indústria, Inovação e Infraestrutura' },
  { sigla: 'ODS 10', nome: 'Redução das Desigualdades' },
];

export default function ImpactSection() {
  return (
    <section id="impacto" className="impact" aria-labelledby="impacto-titulo">
      <div className="container">
        <div className="section-title">
          <span>IMPACTO SOCIAL</span>
          <h2 id="impacto-titulo">Inovação alinhada aos Objetivos da ONU</h2>
        </div>

        <ul className="stats" aria-label="Objetivos de Desenvolvimento Sustentável atendidos">
          {ODS.map((ods) => (
            <li key={ods.sigla} className="stat-card">
              <h3>{ods.sigla}</h3>
              <p>{ods.nome}</p>
            </li>
          ))}
        </ul>

        <p className="impact-text">
          A EasyRide busca democratizar o acesso à tecnologia assistiva, oferecendo uma
          alternativa acessível às cadeiras robóticas importadas — com economia circular
          pelo reaproveitamento das cadeiras que os usuários já possuem.
        </p>
      </div>
    </section>
  );
}
