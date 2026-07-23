import { useEffect, useState } from 'react';
import './WhatsAppButton.css';

/*
 * WhatsAppButton (Arquitetura 1.6)
 * Props: numero, mensagem — abre wa.me em nova aba.
 * Estados: Visível / Pulsando (após 10s parado) / Oculto (prop oculto).
 */
export default function WhatsAppButton({ numero, mensagem, oculto = false }) {
  const [pulsando, setPulsando] = useState(false);

  useEffect(() => {
    if (oculto) return undefined;
    const temporizador = setTimeout(() => setPulsando(true), 10000);
    return () => clearTimeout(temporizador);
  }, [oculto]);

  if (oculto || !numero) return null;

  const url = `https://wa.me/${numero}?text=${encodeURIComponent(mensagem || '')}`;

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className={`whatsapp-botao ${pulsando ? 'pulsando' : ''}`}
      aria-label="Falar com a EasyRide pelo WhatsApp (abre em nova aba)"
    >
      {/* Ícone WhatsApp em SVG inline (sem dependências externas) */}
      <svg viewBox="0 0 32 32" width="28" height="28" aria-hidden="true" fill="currentColor">
        <path d="M16 3C9.373 3 4 8.373 4 15c0 2.65.862 5.1 2.32 7.09L4.5 28.5l6.59-1.77A11.94 11.94 0 0 0 16 27c6.627 0 12-5.373 12-12S22.627 3 16 3zm0 21.6a9.55 9.55 0 0 1-4.87-1.33l-.35-.21-3.91 1.05 1.06-3.81-.23-.37A9.55 9.55 0 0 1 6.4 15c0-5.29 4.31-9.6 9.6-9.6s9.6 4.31 9.6 9.6-4.31 9.6-9.6 9.6zm5.26-7.19c-.29-.14-1.7-.84-1.97-.93-.26-.1-.46-.14-.65.14-.19.29-.74.93-.91 1.12-.17.19-.34.22-.62.07-.29-.14-1.22-.45-2.32-1.43-.86-.76-1.44-1.7-1.6-1.99-.17-.29-.02-.44.12-.59.13-.13.29-.34.43-.5.14-.17.19-.29.29-.48.1-.19.05-.36-.02-.5-.07-.14-.65-1.56-.89-2.14-.23-.56-.47-.48-.65-.49h-.55c-.19 0-.5.07-.77.36-.26.29-1 .98-1 2.4 0 1.42 1.03 2.79 1.18 2.98.14.19 2.03 3.1 4.93 4.35.69.3 1.23.48 1.65.61.69.22 1.32.19 1.82.11.56-.08 1.7-.7 1.94-1.37.24-.67.24-1.25.17-1.37-.07-.12-.26-.19-.55-.34z" />
      </svg>
      <span className="sr-only">WhatsApp</span>
    </a>
  );
}
