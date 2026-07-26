/*
 * CTAButton (Arquitetura 1.2.2) — botão de chamada para ação reutilizável.
 * Variantes visuais da landing de referência: "primary" e "secondary".
 */
export default function CTAButton({ href, onClick, variante = 'primary', children, ...resto }) {
  const classe = variante === 'secondary' ? 'btn-secondary' : 'btn-primary';

  if (href) {
    return (
      <a href={href} className={classe} onClick={onClick} {...resto}>
        {children}
      </a>
    );
  }
  return (
    <button type="button" className={classe} onClick={onClick} {...resto}>
      {children}
    </button>
  );
}
