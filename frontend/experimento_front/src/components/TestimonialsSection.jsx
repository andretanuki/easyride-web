import { useEffect, useRef, useState } from 'react';
import { listarDepoimentos } from '../services/api.js';
import { DEPOIMENTOS_FALLBACK } from '../data/fallbacks.js';
import TestimonialCard from './TestimonialCard.jsx';
import './TestimonialsSection.css';

/*
 * TestimonialsSection (Arquitetura 1.4)
 * GET /api/depoimentos — carrossel com swipe no mobile e rotação
 * automática a cada 5s. Estados: Carregando / Sucesso / Erro 500
 * (3 depoimentos hardcoded) / Vazio (seção oculta).
 */
export default function TestimonialsSection({ depoimentos: depoimentosIniciais }) {
  const [estado, setEstado] = useState(depoimentosIniciais ? 'sucesso' : 'carregando');
  const [depoimentos, setDepoimentos] = useState(depoimentosIniciais || []);
  const [indice, setIndice] = useState(0);
  const [direcao, setDirecao] = useState('frente'); // frente | tras — orienta o deslize
  const [pausado, setPausado] = useState(false);
  const toqueInicialX = useRef(null);

  const irPara = (novoIndice, novaDirecao) => {
    setDirecao(novaDirecao);
    setIndice(novoIndice);
  };

  useEffect(() => {
    if (depoimentosIniciais) return;
    let ativo = true;
    listarDepoimentos()
      .then((lista) => {
        if (!ativo) return;
        setDepoimentos(lista);
        setEstado(lista.length > 0 ? 'sucesso' : 'vazio');
      })
      .catch(() => {
        if (!ativo) return;
        setDepoimentos(DEPOIMENTOS_FALLBACK);
        setEstado('fallback');
      });
    return () => {
      ativo = false;
    };
  }, [depoimentosIniciais]);

  // Rotação automática a cada 5 segundos (pausa com hover/foco)
  useEffect(() => {
    if (pausado || depoimentos.length < 2) return undefined;
    const temporizador = setInterval(() => {
      setDirecao('frente');
      setIndice((atual) => (atual + 1) % depoimentos.length);
    }, 5000);
    return () => clearInterval(temporizador);
  }, [depoimentos.length, pausado]);

  // Estado "Vazio": a seção fica oculta
  if (estado === 'vazio') return null;

  const anterior = () =>
    irPara((indice - 1 + depoimentos.length) % depoimentos.length, 'tras');
  const proximo = () => irPara((indice + 1) % depoimentos.length, 'frente');

  const aoIniciarToque = (evento) => {
    toqueInicialX.current = evento.touches[0].clientX;
  };

  const aoTerminarToque = (evento) => {
    if (toqueInicialX.current === null) return;
    const delta = evento.changedTouches[0].clientX - toqueInicialX.current;
    if (Math.abs(delta) > 40) {
      if (delta < 0) proximo();
      else anterior();
    }
    toqueInicialX.current = null;
  };

  return (
    <section id="depoimentos" className="testimonials" aria-labelledby="depoimentos-titulo">
      <div className="container">
        <div className="section-title">
          <span>DEPOIMENTOS</span>
          <h2 id="depoimentos-titulo">Quem já vive essa autonomia</h2>
        </div>

        {estado === 'carregando' && (
          <div className="skeleton carrossel-skeleton" aria-busy="true" aria-label="Carregando depoimentos" />
        )}

        {(estado === 'sucesso' || estado === 'fallback') && depoimentos.length > 0 && (
          <div
            className="carrossel"
            role="region"
            aria-roledescription="carrossel"
            aria-label="Depoimentos de usuários"
            onMouseEnter={() => setPausado(true)}
            onMouseLeave={() => setPausado(false)}
            onFocus={() => setPausado(true)}
            onBlur={() => setPausado(false)}
            onTouchStart={aoIniciarToque}
            onTouchEnd={aoTerminarToque}
          >
            <button
              type="button"
              className="carrossel-seta"
              onClick={anterior}
              aria-label="Depoimento anterior"
            >
              ‹
            </button>

            <div key={indice} className={`slide-depoimento slide-${direcao}`}>
              <TestimonialCard {...depoimentos[indice]} />
            </div>

            <button
              type="button"
              className="carrossel-seta"
              onClick={proximo}
              aria-label="Próximo depoimento"
            >
              ›
            </button>

            <div className="carrossel-indicadores" role="tablist" aria-label="Escolher depoimento">
              {depoimentos.map((depoimento, i) => (
                <button
                  key={depoimento.id ?? i}
                  type="button"
                  role="tab"
                  aria-selected={i === indice}
                  aria-label={`Depoimento ${i + 1} de ${depoimentos.length}`}
                  className={`indicador ${i === indice ? 'ativo' : ''}`}
                  onClick={() => irPara(i, i > indice ? 'frente' : 'tras')}
                />
              ))}
            </div>

            <p className="sr-only" aria-live="polite">
              Exibindo depoimento {indice + 1} de {depoimentos.length}
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
