/*
 * Reveal-on-scroll global: elementos entram com fade + subida suave
 * conforme aparecem no viewport, com stagger entre irmãos da mesma grade.
 * Um MutationObserver registra conteúdo que chega depois (seções que
 * carregam da API). Respeita prefers-reduced-motion (não anima nada).
 */

const SELETOR_REVEAL = [
  '.section-title',
  '.step',
  '.stat-card',
  '.impact-text',
  '.audience-card',
  '.benefit-card',
  '.testimonial-card',
  '.faq-item',
  '.faq-busca',
  '.form-box',
].join(', ');

export function iniciarReveal() {
  if (
    window.matchMedia('(prefers-reduced-motion: reduce)').matches ||
    !('IntersectionObserver' in window)
  ) {
    return () => {};
  }

  const observador = new IntersectionObserver(
    (entradas) => {
      for (const entrada of entradas) {
        if (entrada.isIntersecting) {
          entrada.target.classList.add('visivel');
          observador.unobserve(entrada.target);
        }
      }
    },
    { threshold: 0.12, rootMargin: '0px 0px -6% 0px' }
  );

  // Rastreia o que ESTA instância já observa. Não dá para confiar na
  // classe .reveal-auto como marcador: no StrictMode (dev) o efeito roda,
  // limpa e roda de novo — a classe sobrevive à limpeza e, sem re-observar,
  // os elementos ficariam presos em opacity: 0 para sempre.
  const observados = new WeakSet();

  const registrar = () => {
    document.querySelectorAll(SELETOR_REVEAL).forEach((el) => {
      if (observados.has(el) || el.classList.contains('visivel')) return;
      observados.add(el);
      el.classList.add('reveal-auto');
      // Stagger: irmãos diretos na mesma grade entram em cascata
      const irmaos = el.parentElement
        ? [...el.parentElement.children].filter((f) => f.matches?.(SELETOR_REVEAL))
        : [el];
      const indice = Math.max(0, irmaos.indexOf(el));
      el.style.transitionDelay = `${Math.min(indice, 7) * 80}ms`;
      observador.observe(el);
    });
  };

  registrar();
  const mutacoes = new MutationObserver(registrar);
  mutacoes.observe(document.body, { childList: true, subtree: true });

  return () => {
    observador.disconnect();
    mutacoes.disconnect();
    // Reverte tudo: nada fica preso invisível e uma próxima instância
    // (remontagem do StrictMode) recomeça do zero, com animação
    document.querySelectorAll('.reveal-auto').forEach((el) => {
      el.classList.remove('reveal-auto', 'visivel');
      el.style.transitionDelay = '';
    });
  };
}
