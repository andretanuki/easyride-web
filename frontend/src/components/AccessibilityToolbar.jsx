import { useEffect, useRef, useState } from 'react';
import { useAccessibility } from '../context/AccessibilityContext.jsx';
import './AccessibilityToolbar.css';

/*
 * AccessibilityToolbar (Arquitetura 1.1)
 * Botão flutuante discreto que expande um painel compacto com:
 * A+/A- (fonte em tempo real), Alto Contraste (fundo preto/letras
 * amarelas) e Leitor de Tela por hover (Web Speech API).
 * Estado 100% local (Context + LocalStorage) — não consome a API.
 */
export default function AccessibilityToolbar() {
  const {
    tamanhoFonteAtual,
    modoContraste,
    leitorAtivo,
    aumentarFonte,
    diminuirFonte,
    alternarContraste,
    alternarLeitor,
  } = useAccessibility();

  const [aberto, setAberto] = useState(false);
  const painelRef = useRef(null);

  const suportaLeitor = typeof window !== 'undefined' && 'speechSynthesis' in window;

  // Fecha com Esc ou clique fora do painel
  useEffect(() => {
    if (!aberto) return undefined;
    const aoTeclar = (evento) => {
      if (evento.key === 'Escape') setAberto(false);
    };
    const aoClicarFora = (evento) => {
      if (painelRef.current && !painelRef.current.contains(evento.target)) {
        setAberto(false);
      }
    };
    document.addEventListener('keydown', aoTeclar);
    document.addEventListener('mousedown', aoClicarFora);
    return () => {
      document.removeEventListener('keydown', aoTeclar);
      document.removeEventListener('mousedown', aoClicarFora);
    };
  }, [aberto]);

  return (
    <div className="acessibilidade" ref={painelRef}>
      <button
        type="button"
        className="acessibilidade-gatilho"
        onClick={() => setAberto((a) => !a)}
        aria-expanded={aberto}
        aria-controls="painel-acessibilidade"
        aria-label="Ferramentas de acessibilidade"
        title="Acessibilidade"
      >
        {/* Símbolo universal de acessibilidade: figura humana de braços
            abertos em círculo (ícone neutro, não centrado em cadeira de rodas) */}
        <svg viewBox="0 0 24 24" width="26" height="26" aria-hidden="true" fill="currentColor">
          <circle cx="12" cy="12" r="10.5" fill="none" stroke="currentColor" strokeWidth="1.6" />
          <circle cx="12" cy="6.4" r="1.7" />
          <path d="M12 9.1c-.5 0-4.2-.55-4.9-.7a.8.8 0 0 0-.35 1.56c.6.14 3 .6 3.75.72v2.16c0 .2-.03.4-.1.59l-1.65 4.6a.85.85 0 0 0 1.6.58l1.45-4.05c.1-.27.5-.27.6 0l1.45 4.05a.85.85 0 0 0 1.6-.58l-1.65-4.6a1.7 1.7 0 0 1-.1-.59v-2.16c.76-.12 3.15-.58 3.75-.72a.8.8 0 0 0-.35-1.56c-.7.15-4.4.7-4.9.7z" />
        </svg>
      </button>

      {aberto && (
        <div
          id="painel-acessibilidade"
          className="acessibilidade-painel"
          role="group"
          aria-label="Ferramentas de acessibilidade"
        >
          <p className="acessibilidade-titulo">Acessibilidade</p>

          <div className="acessibilidade-linha">
            <span id="rotulo-fonte">Tamanho da fonte</span>
            <div className="acessibilidade-fonte" role="group" aria-labelledby="rotulo-fonte">
              <button
                type="button"
                onClick={diminuirFonte}
                aria-label="Diminuir tamanho da fonte"
                disabled={tamanhoFonteAtual <= 100}
              >
                A−
              </button>
              <span aria-live="polite">{tamanhoFonteAtual}%</span>
              <button
                type="button"
                onClick={aumentarFonte}
                aria-label="Aumentar tamanho da fonte"
                disabled={tamanhoFonteAtual >= 150}
              >
                A+
              </button>
            </div>
          </div>

          <button
            type="button"
            className="acessibilidade-opcao"
            onClick={alternarContraste}
            aria-pressed={modoContraste}
          >
            Alto contraste {modoContraste ? 'ligado' : 'desligado'}
          </button>

          {suportaLeitor && (
            <button
              type="button"
              className="acessibilidade-opcao"
              onClick={alternarLeitor}
              aria-pressed={leitorAtivo}
            >
              Leitor por hover {leitorAtivo ? 'ligado' : 'desligado'}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
