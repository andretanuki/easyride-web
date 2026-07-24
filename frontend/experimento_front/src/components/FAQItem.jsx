import { useId, useState } from 'react';

/*
 * FAQItem — accordion acessível com animação fluida de expansão
 * (grid-template-rows 0fr→1fr) e seta que gira ao abrir.
 */
export default function FAQItem({ pergunta, resposta }) {
  const [aberto, setAberto] = useState(false);
  const idConteudo = useId();

  return (
    <div className={`faq-item ${aberto ? 'aberto' : ''}`}>
      <button
        type="button"
        className="faq-pergunta"
        aria-expanded={aberto}
        aria-controls={idConteudo}
        onClick={() => setAberto((a) => !a)}
      >
        <span>{pergunta}</span>
        <svg
          className="faq-seta"
          viewBox="0 0 24 24"
          width="20"
          height="20"
          aria-hidden="true"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      <div id={idConteudo} className="faq-conteudo" role="region" aria-hidden={!aberto}>
        <div className="faq-conteudo-interno">
          <p>{resposta}</p>
        </div>
      </div>
    </div>
  );
}
