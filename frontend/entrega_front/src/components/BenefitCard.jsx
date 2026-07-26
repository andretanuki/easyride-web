/* BenefitCard — card individual de benefício ({titulo, descricao, icone}). */

// A API envia o ícone como slug (ex.: "microphone"); mapeia para um símbolo visual.
const ICONES = {
  microphone: '🎙️',
  tools: '🛠️',
  'check-circle': '✅',
  brain: '🧠',
  shield: '🛡️',
  plug: '🔌',
  wheelchair: '♿',
  heart: '❤️',
};

function resolverIcone(icone) {
  if (!icone) return null;
  if (ICONES[icone]) return ICONES[icone];
  // Slugs desconhecidos (texto ascii) não devem aparecer como texto cru
  return /^[a-z0-9-]+$/i.test(icone) ? '✨' : icone;
}

export default function BenefitCard({ titulo, descricao, icone }) {
  const simbolo = resolverIcone(icone);
  return (
    <li className="benefit-card">
      {simbolo && (
        <span className="benefit-icone" aria-hidden="true">
          {simbolo}
        </span>
      )}
      <h3>{titulo}</h3>
      <p>{descricao}</p>
    </li>
  );
}
