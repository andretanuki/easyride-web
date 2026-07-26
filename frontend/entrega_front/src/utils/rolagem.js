/*
 * Rolagem suave com curva easeInOutQuint — fluida na largada e pouso
 * elegante, sem a secura do scroll-behavior nativo.
 * Respeita prefers-reduced-motion (salta direto ao destino).
 */

const easeInOutQuint = (t) =>
  t < 0.5 ? 16 * t * t * t * t * t : 1 - Math.pow(-2 * t + 2, 5) / 2;

function alturaCabecalho() {
  const cabecalho = document.querySelector('.cabecalho');
  return (cabecalho?.offsetHeight || 0) + 16;
}

let animacaoAtual = null;

export function rolarPara(alvo) {
  const destino = Math.max(
    0,
    alvo.getBoundingClientRect().top + window.scrollY - alturaCabecalho()
  );

  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    window.scrollTo(0, destino);
    focarAlvo(alvo);
    return;
  }

  const inicio = window.scrollY;
  const distancia = destino - inicio;
  // Duração proporcional à distância: curta não "arrasta", longa não voa
  const duracao = Math.min(1100, Math.max(450, Math.abs(distancia) * 0.45));
  const t0 = performance.now();

  cancelAnimationFrame(animacaoAtual);

  const quadro = (agora) => {
    const progresso = Math.min(1, (agora - t0) / duracao);
    window.scrollTo(0, inicio + distancia * easeInOutQuint(progresso));
    if (progresso < 1) {
      animacaoAtual = requestAnimationFrame(quadro);
    } else {
      focarAlvo(alvo);
    }
  };
  animacaoAtual = requestAnimationFrame(quadro);
}

/* Move o foco para a seção de destino (leitores de tela e teclado
   continuam do ponto certo) sem re-rolar a página. */
function focarAlvo(alvo) {
  if (!alvo.hasAttribute('tabindex')) alvo.setAttribute('tabindex', '-1');
  alvo.focus({ preventScroll: true });
}

/* Delegação global: qualquer <a href="#..."> anima até a âncora. */
export function iniciarRolagemSuave() {
  const aoClicar = (evento) => {
    const link = evento.target.closest?.('a[href^="#"]');
    if (!link) return;
    const alvo = document.querySelector(link.getAttribute('href'));
    if (!alvo) return;
    evento.preventDefault();
    history.replaceState(null, '', link.getAttribute('href'));
    rolarPara(alvo);
  };
  document.addEventListener('click', aoClicar);
  return () => document.removeEventListener('click', aoClicar);
}
