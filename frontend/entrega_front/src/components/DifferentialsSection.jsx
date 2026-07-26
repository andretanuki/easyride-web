import './Sections.css';

/* Diferenciais — comparativo com o mercado tradicional (landing de referência). */
export default function DifferentialsSection() {
  return (
    <section id="diferenciais" className="differentials" aria-labelledby="diferenciais-titulo">
      <div className="container">
        <div className="section-title">
          <span>DIFERENCIAIS</span>
          <h2 id="diferenciais-titulo">Por que a EasyRide é diferente?</h2>
        </div>

        <div className="cards">
          <article className="audience-card">
            <h3>EasyRide</h3>
            <ul className="lista-comparativa">
              <li>✔ Instala em cadeiras existentes</li>
              <li>✔ Controle por voz</li>
              <li>✔ Navegação autônoma</li>
              <li>✔ Menor custo</li>
              <li>✔ Desenvolvida no Brasil</li>
            </ul>
          </article>

          <article className="audience-card">
            <h3>Mercado Tradicional</h3>
            <ul className="lista-comparativa">
              <li>✖ Exige cadeira nova</li>
              <li>✖ Alto custo de aquisição</li>
              <li>✖ Dependência de importação</li>
              <li>✖ Menor acessibilidade financeira</li>
            </ul>
          </article>
        </div>
      </div>
    </section>
  );
}
