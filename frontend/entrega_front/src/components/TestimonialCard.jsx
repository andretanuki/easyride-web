/* TestimonialCard — depoimento individual ({nome, foto, texto, avaliacao}). */
export default function TestimonialCard({ nome, foto, texto, avaliacao }) {
  const estrelas = Math.max(0, Math.min(5, Number(avaliacao) || 0));

  return (
    <figure className="testimonial-card">
      {foto ? (
        <img className="testimonial-foto" src={foto} alt={`Foto de ${nome}`} />
      ) : (
        <span className="testimonial-foto testimonial-foto-fallback" aria-hidden="true">
          {nome?.charAt(0) || '?'}
        </span>
      )}
      <blockquote>
        <p>“{texto}”</p>
      </blockquote>
      <figcaption>
        <strong>{nome}</strong>
        <span
          className="testimonial-estrelas"
          role="img"
          aria-label={`Avaliação: ${estrelas} de 5 estrelas`}
        >
          {'★'.repeat(estrelas)}
          {'☆'.repeat(5 - estrelas)}
        </span>
      </figcaption>
    </figure>
  );
}
