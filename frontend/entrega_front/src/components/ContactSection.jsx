import LeadCaptureForm from './LeadCaptureForm.jsx';
import './ContactSection.css';

/*
 * Seção "Contatos/Leads" (briefing §3.1) — visual "Fale com a EasyRide"
 * da landing de referência, hospedando o LeadCaptureForm integrado à API.
 */
export default function ContactSection() {
  return (
    <section id="contato" className="contact" aria-labelledby="contato-titulo">
      <div className="container">
        <div className="form-box">
          <h2 id="contato-titulo">Fale com a EasyRide</h2>
          <p className="contato-subtitulo">
            Preencha o formulário e nossa equipe entrará em contato para uma demonstração.
          </p>
          <LeadCaptureForm origem="landing" />
        </div>
      </div>
    </section>
  );
}
