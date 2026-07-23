import { useState } from 'react';
import CTAButton from './CTAButton.jsx';
import './Header.css';

const LINKS = [
  { href: '#inicio', rotulo: 'Início' },
  { href: '#tecnologia', rotulo: 'Tecnologia' },
  { href: '#beneficios', rotulo: 'Benefícios' },
  { href: '#impacto', rotulo: 'Impacto Social' },
  { href: '#publico', rotulo: 'Público-Alvo' },
  { href: '#equipe', rotulo: 'Equipe' },
  { href: '#faq', rotulo: 'FAQ' },
];

export default function Header() {
  const [menuAberto, setMenuAberto] = useState(false);

  return (
    <header className="cabecalho">
      <div className="container navbar">
        <a href="#inicio" className="logo" aria-label="EasyRide - página inicial">
          EasyRide
        </a>

        <button
          type="button"
          className="menu-toggle"
          aria-expanded={menuAberto}
          aria-controls="menu-principal"
          aria-label={menuAberto ? 'Fechar menu de navegação' : 'Abrir menu de navegação'}
          onClick={() => setMenuAberto((aberto) => !aberto)}
        >
          ☰
        </button>

        <nav
          id="menu-principal"
          className={menuAberto ? 'aberto' : ''}
          aria-label="Navegação principal"
        >
          {LINKS.map((link) => (
            <a key={link.href} href={link.href} onClick={() => setMenuAberto(false)}>
              {link.rotulo}
            </a>
          ))}
        </nav>

        <CTAButton href="#contato">Quero Saber Mais</CTAButton>
      </div>
    </header>
  );
}
