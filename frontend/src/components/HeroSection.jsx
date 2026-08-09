import { useState } from 'react';
import CTAButton from './CTAButton.jsx';
import './HeroSection.css';

/*
 * HeroSection (Arquitetura 1.2)
 * Props: titulo, subtitulo, imagemFundo
 * Estados: Carregando (placeholder) / Pronto / Erro Imagem (fallback cor sólida)
 * Comportamento: fade-in na entrada, altura ajustada ao viewport.
 */
export default function HeroSection({ titulo, subtitulo, imagemFundo }) {
  const [estadoImagem, setEstadoImagem] = useState(imagemFundo ? 'carregando' : 'erro');

  return (
    <section id="inicio" className="hero" aria-labelledby="hero-titulo">
      <div className="container hero-content">
        <div className="hero-text">
          <h1 id="hero-titulo" className="hero-entra">
            {titulo}
          </h1>
          <p className="hero-entra">{subtitulo}</p>

          <div className="hero-buttons hero-entra">
            <CTAButton href="#contato">Quero Saber Mais</CTAButton>
            <CTAButton href="#tecnologia" variante="secondary">
              Ver Tecnologia
            </CTAButton>
          </div>

          <ul className="features hero-entra" aria-label="Principais recursos">
            <li className="feature-card">Controle por Voz</li>
            <li className="feature-card">Kit Universal Plug &amp; Play</li>
            <li className="feature-card">Navegação Inteligente com IA</li>
          </ul>
        </div>

        <div className={`hero-image hero-entra estado-${estadoImagem}`}>
          {imagemFundo && estadoImagem !== 'erro' && (
            <img
              src={imagemFundo}
              alt="Pessoa utilizando cadeira de rodas motorizada com o kit de navegação autônoma EasyRide"
              onLoad={() => setEstadoImagem('pronto')}
              onError={() => setEstadoImagem('erro')}
            />
          )}
          {estadoImagem === 'erro' && (
            <div className="hero-fallback" role="img" aria-label="Ilustração: cadeira de rodas inteligente EasyRide">
              <span aria-hidden="true">♿</span>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
