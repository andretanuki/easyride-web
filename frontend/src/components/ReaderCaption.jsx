import { useAccessibility } from '../context/AccessibilityContext.jsx';
import './ReaderCaption.css';

/*
 * Legenda do leitor por hover: mostra o texto do elemento apontado.
 * Garante que o recurso funcione visivelmente mesmo quando o sistema
 * operacional não tem vozes de síntese instaladas.
 */
export default function ReaderCaption() {
  const { leitorAtivo, textoLido, temVoz } = useAccessibility();

  if (!leitorAtivo || !textoLido) return null;

  return (
    <div className="leitor-legenda" role="status" aria-live="polite">
      <span className="leitor-legenda-icone" aria-hidden="true">
        {temVoz ? '🔊' : '💬'}
      </span>
      <p>{textoLido}</p>
      {!temVoz && (
        <small>Sem vozes de sistema disponíveis — exibindo somente a legenda.</small>
      )}
    </div>
  );
}
