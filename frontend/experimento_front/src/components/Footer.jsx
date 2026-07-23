import './Footer.css';

const ADMIN_URL = `${(import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')}/admin/`;

/* Footer (Arquitetura 1.7) — dados institucionais da landing de referência. */
export default function Footer() {
  return (
    <footer className="rodape">
      <div className="container footer-content">
        <div>
          <h2 className="rodape-logo">EasyRide</h2>
          <p>Tecnologia Assistiva Inteligente para Autonomia e Inclusão.</p>
          <p>Startup fundada em 2025 - Lagarto/SE</p>
        </div>

        <div>
          <h3>Contato</h3>
          <p>
            <a href="mailto:contato@easyride.com.br">contato@easyride.com.br</a>
          </p>
          <p>Lagarto - Sergipe</p>
        </div>
      </div>

      <div className="container rodape-admin">
        <a href={ADMIN_URL} rel="noopener noreferrer">
          Área administrativa
        </a>
      </div>
    </footer>
  );
}
