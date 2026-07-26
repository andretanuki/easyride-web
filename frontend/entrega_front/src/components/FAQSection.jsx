import { useEffect, useMemo, useState } from 'react';
import { listarFaq } from '../services/api.js';
import { FAQ_FALLBACK } from '../data/fallbacks.js';
import FAQItem from './FAQItem.jsx';
import './FAQSection.css';

/*
 * FAQSection (Arquitetura 1.5)
 * GET /api/faq — accordion com busca por palavra-chave.
 * Estados: Carregando / Sucesso / Erro 500 (5 perguntas hardcoded) / Vazio.
 */
export default function FAQSection({ perguntas: perguntasIniciais }) {
  const [estado, setEstado] = useState(perguntasIniciais ? 'sucesso' : 'carregando');
  const [perguntas, setPerguntas] = useState(perguntasIniciais || []);
  const [busca, setBusca] = useState('');

  useEffect(() => {
    if (perguntasIniciais) return;
    let ativo = true;
    listarFaq()
      .then((lista) => {
        if (!ativo) return;
        setPerguntas(lista);
        setEstado(lista.length > 0 ? 'sucesso' : 'vazio');
      })
      .catch(() => {
        if (!ativo) return;
        setPerguntas(FAQ_FALLBACK);
        setEstado('fallback');
      });
    return () => {
      ativo = false;
    };
  }, [perguntasIniciais]);

  const filtradas = useMemo(() => {
    const termo = busca.trim().toLowerCase();
    if (!termo) return perguntas;
    return perguntas.filter(
      (item) =>
        item.pergunta?.toLowerCase().includes(termo) ||
        item.resposta?.toLowerCase().includes(termo)
    );
  }, [perguntas, busca]);

  return (
    <section id="faq" className="faq" aria-labelledby="faq-titulo">
      <div className="container">
        <div className="section-title">
          <span>FAQ</span>
          <h2 id="faq-titulo">Perguntas Frequentes</h2>
        </div>

        {estado === 'carregando' && (
          <div aria-busy="true" aria-label="Carregando perguntas frequentes">
            {[1, 2, 3].map((n) => (
              <div key={n} className="skeleton faq-skeleton" />
            ))}
          </div>
        )}

        {estado === 'vazio' && (
          <p className="faq-vazio">Em breve publicaremos as perguntas mais frequentes.</p>
        )}

        {(estado === 'sucesso' || estado === 'fallback') && (
          <>
            <div className="faq-busca">
              <label htmlFor="faq-campo-busca">Buscar pergunta</label>
              <input
                id="faq-campo-busca"
                type="search"
                placeholder="Digite uma palavra-chave, ex.: instalação"
                value={busca}
                onChange={(evento) => setBusca(evento.target.value)}
              />
            </div>

            <p className="sr-only" aria-live="polite">
              {filtradas.length} pergunta(s) encontrada(s)
            </p>

            {filtradas.length === 0 ? (
              <p className="faq-vazio">Nenhuma pergunta encontrada para “{busca}”.</p>
            ) : (
              <div className="faq-lista">
                {filtradas.map((item) => (
                  <FAQItem
                    key={item.id ?? item.pergunta}
                    pergunta={item.pergunta}
                    resposta={item.resposta}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </section>
  );
}
