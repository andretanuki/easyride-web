import { createContext, useContext, useEffect, useState } from 'react';

/*
 * AccessibilityToolbar (Arquitetura_Componentes_React_v3, item 1.1):
 * estado 100% local (Context API + LocalStorage) — latência zero,
 * funciona offline e NÃO consome a API.
 */

const STORAGE_KEY = 'easyride-acessibilidade';

const FONTE_MIN = 100; // %
const FONTE_MAX = 150; // %
const FONTE_PASSO = 10;

const AccessibilityContext = createContext(null);

function carregarPreferencias() {
  try {
    const salvo = localStorage.getItem(STORAGE_KEY);
    if (salvo) return JSON.parse(salvo);
  } catch {
    /* localStorage indisponível — usa padrões */
  }
  return { tamanhoFonte: FONTE_MIN, modoContraste: false, leitorAtivo: false };
}

/* ---- Leitor de tela por hover/foco ------------------------------------- */

const SELETOR_LEGIVEL =
  'h1, h2, h3, h4, p, li, a, button, label, summary, legend, input, select, textarea';

function extrairTexto(alvo) {
  return (
    alvo.getAttribute('aria-label') ||
    alvo.labels?.[0]?.innerText ||
    alvo.innerText?.trim() ||
    alvo.value ||
    ''
  );
}

function escolherVoz() {
  const vozes = window.speechSynthesis.getVoices();
  return (
    vozes.find((v) => v.lang === 'pt-BR') ||
    vozes.find((v) => v.lang?.startsWith('pt')) ||
    vozes[0] ||
    null
  );
}

export function AccessibilityProvider({ children }) {
  const [prefs, setPrefs] = useState(carregarPreferencias);
  // Texto atualmente sendo lido — exibido como legenda visual pelo
  // componente ReaderCaption (o leitor funciona mesmo sem vozes no sistema).
  const [textoLido, setTextoLido] = useState('');
  const [temVoz, setTemVoz] = useState(true);

  // Aplica fonte e contraste na raiz do documento em tempo real
  useEffect(() => {
    document.documentElement.style.fontSize = `${prefs.tamanhoFonte}%`;
    document.documentElement.classList.toggle('alto-contraste', prefs.modoContraste);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
    } catch {
      /* persistência é melhor esforço */
    }
  }, [prefs]);

  // Leitor por hover/foco: destaca, mostra legenda e fala (quando há vozes)
  useEffect(() => {
    if (!prefs.leitorAtivo) return undefined;

    const suportaFala = 'speechSynthesis' in window;
    let elementoAtual = null;
    let timerDebounce = null;
    let timerFala = null;

    // As vozes carregam de forma assíncrona no Chrome
    if (suportaFala) {
      setTemVoz(window.speechSynthesis.getVoices().length > 0);
      window.speechSynthesis.onvoiceschanged = () =>
        setTemVoz(window.speechSynthesis.getVoices().length > 0);
    } else {
      setTemVoz(false);
    }

    const limparDestaque = () => {
      elementoAtual?.classList.remove('sendo-lido');
      elementoAtual = null;
    };

    const ler = (alvo) => {
      const texto = extrairTexto(alvo);
      if (!texto || alvo === elementoAtual) return;

      limparDestaque();
      elementoAtual = alvo;
      alvo.classList.add('sendo-lido');
      setTextoLido(texto);

      if (!suportaFala) return;
      // cancel() imediatamente antes de speak() pode engolir a fala no
      // Chrome — pequeno intervalo entre os dois resolve.
      window.speechSynthesis.cancel();
      clearTimeout(timerFala);
      timerFala = setTimeout(() => {
        const fala = new SpeechSynthesisUtterance(texto);
        fala.lang = 'pt-BR';
        const voz = escolherVoz();
        if (voz) fala.voice = voz;
        window.speechSynthesis.speak(fala);
      }, 60);
    };

    const aoApontar = (evento) => {
      const alvo = evento.target.closest?.(SELETOR_LEGIVEL);
      if (!alvo) return;
      clearTimeout(timerDebounce);
      timerDebounce = setTimeout(() => ler(alvo), 120);
    };

    document.addEventListener('mouseover', aoApontar);
    document.addEventListener('focusin', aoApontar); // também lê ao navegar por Tab
    return () => {
      document.removeEventListener('mouseover', aoApontar);
      document.removeEventListener('focusin', aoApontar);
      clearTimeout(timerDebounce);
      clearTimeout(timerFala);
      limparDestaque();
      setTextoLido('');
      if (suportaFala) {
        window.speechSynthesis.onvoiceschanged = null;
        window.speechSynthesis.cancel();
      }
    };
  }, [prefs.leitorAtivo]);

  const aumentarFonte = () =>
    setPrefs((p) => ({ ...p, tamanhoFonte: Math.min(p.tamanhoFonte + FONTE_PASSO, FONTE_MAX) }));

  const diminuirFonte = () =>
    setPrefs((p) => ({ ...p, tamanhoFonte: Math.max(p.tamanhoFonte - FONTE_PASSO, FONTE_MIN) }));

  const alternarContraste = () =>
    setPrefs((p) => ({ ...p, modoContraste: !p.modoContraste }));

  const alternarLeitor = () =>
    setPrefs((p) => ({ ...p, leitorAtivo: !p.leitorAtivo }));

  return (
    <AccessibilityContext.Provider
      value={{
        tamanhoFonteAtual: prefs.tamanhoFonte,
        modoContraste: prefs.modoContraste,
        leitorAtivo: prefs.leitorAtivo,
        textoLido,
        temVoz,
        aumentarFonte,
        diminuirFonte,
        alternarContraste,
        alternarLeitor,
      }}
    >
      {children}
    </AccessibilityContext.Provider>
  );
}

export function useAccessibility() {
  const contexto = useContext(AccessibilityContext);
  if (!contexto) {
    throw new Error('useAccessibility deve ser usado dentro de <AccessibilityProvider>');
  }
  return contexto;
}
