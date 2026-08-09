import CTAButton from './CTAButton.jsx';
import './Sections.css';

/* Avisa o LeadCaptureForm para pré-selecionar o tipo de cadastro
   (a rolagem até #contato acontece pelo próprio href do CTA). */
const preSelecionarTipo = (tipo) => () =>
  window.dispatchEvent(new CustomEvent('easyride:tipo-pessoa', { detail: tipo }));

/* Público-Alvo (briefing §3.1): seções distintas para B2C e B2B. */
export default function AudienceSection() {
  return (
    <section id="publico" className="audience" aria-labelledby="publico-titulo">
      <div className="container">
        <div className="section-title">
          <span>PÚBLICO-ALVO</span>
          <h2 id="publico-titulo">Soluções para diferentes necessidades</h2>
        </div>

        <div className="cards">
          <article className="audience-card">
            <h3>B2C – Usuários e Famílias</h3>
            <ul>
              <li>Pessoas com tetraplegia</li>
              <li>Pacientes com ELA</li>
              <li>Maior independência diária</li>
              <li>Melhoria da qualidade de vida</li>
            </ul>
            <CTAButton href="#contato" variante="primary" onClick={preSelecionarTipo('FISICA')}>
              Quero conhecer
            </CTAButton>
          </article>

          <article className="audience-card">
            <h3>B2B – Clínicas e Hospitais</h3>
            <ul>
              <li>Hospitais</li>
              <li>Clínicas de reabilitação</li>
              <li>Automação do transporte interno</li>
              <li>Otimização da equipe assistencial</li>
            </ul>
            <CTAButton href="#contato" variante="primary" onClick={preSelecionarTipo('JURIDICA')}>
              Solicitar Parceria
            </CTAButton>
          </article>
        </div>
      </div>
    </section>
  );
}
