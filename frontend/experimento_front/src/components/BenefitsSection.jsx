import { useEffect, useState } from 'react';
import { listarBeneficios } from '../services/api.js';
import { BENEFICIOS_FALLBACK } from '../data/fallbacks.js';
import BenefitCard from './BenefitCard.jsx';
import './BenefitsSection.css';

/*
 * BenefitsSection (Arquitetura 1.3)
 * GET /api/beneficios — estados: Carregando (skeleton) / Sucesso /
 * Erro 500 (fallback hardcoded) / Vazio ("Em breve mais informações").
 * Grid 2 colunas mobile, 4 desktop; fade-in ao rolar a página
 * (via reveal global de utils/reveal.js, com stagger nos cards).
 */
export default function BenefitsSection({ beneficios: beneficiosIniciais }) {
  const [estado, setEstado] = useState(beneficiosIniciais ? 'sucesso' : 'carregando');
  const [beneficios, setBeneficios] = useState(beneficiosIniciais || []);

  useEffect(() => {
    if (beneficiosIniciais) return;
    let ativo = true;
    listarBeneficios()
      .then((lista) => {
        if (!ativo) return;
        setBeneficios(lista);
        setEstado(lista.length > 0 ? 'sucesso' : 'vazio');
      })
      .catch(() => {
        if (!ativo) return;
        setBeneficios(BENEFICIOS_FALLBACK);
        setEstado('fallback');
      });
    return () => {
      ativo = false;
    };
  }, [beneficiosIniciais]);

  return (
    <section id="beneficios" className="benefits" aria-labelledby="beneficios-titulo">
      <div className="container">
        <div className="section-title">
          <span>BENEFÍCIOS</span>
          <h2 id="beneficios-titulo">O que a EasyRide entrega</h2>
        </div>

        {estado === 'carregando' && (
          <div className="benefits-grid" aria-busy="true" aria-label="Carregando benefícios">
            {[1, 2, 3, 4].map((n) => (
              <div key={n} className="skeleton" />
            ))}
          </div>
        )}

        {estado === 'vazio' && <p className="benefits-vazio">Em breve mais informações.</p>}

        {(estado === 'sucesso' || estado === 'fallback') && (
          <ul className="benefits-grid">
            {beneficios.map((beneficio) => (
              <BenefitCard
                key={beneficio.id ?? beneficio.titulo}
                titulo={beneficio.titulo}
                descricao={beneficio.descricao}
                icone={beneficio.icone}
              />
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
