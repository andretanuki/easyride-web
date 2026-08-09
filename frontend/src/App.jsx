import { useEffect } from 'react';
import { AccessibilityProvider } from './context/AccessibilityContext.jsx';
import { iniciarRolagemSuave } from './utils/rolagem.js';
import { iniciarReveal } from './utils/reveal.js';
import AccessibilityToolbar from './components/AccessibilityToolbar.jsx';
import ReaderCaption from './components/ReaderCaption.jsx';
import Header from './components/Header.jsx';
import HeroSection from './components/HeroSection.jsx';
import TechnologySection from './components/TechnologySection.jsx';
import BenefitsSection from './components/BenefitsSection.jsx';
import ImpactSection from './components/ImpactSection.jsx';
import AudienceSection from './components/AudienceSection.jsx';
import DifferentialsSection from './components/DifferentialsSection.jsx';
import TeamSection from './components/TeamSection.jsx';
import TestimonialsSection from './components/TestimonialsSection.jsx';
import FAQSection from './components/FAQSection.jsx';
import ContactSection from './components/ContactSection.jsx';
import WhatsAppButton from './components/WhatsAppButton.jsx';
import Footer from './components/Footer.jsx';

const WHATSAPP_NUMERO = import.meta.env.VITE_WHATSAPP_NUMERO || '';

/*
 * Ordem das seções conforme o briefing §3.1 e a landing de referência:
 * Home (Hero) → Tecnologia → Benefícios → Impacto Social → Público-Alvo
 * → Diferenciais → Equipe → Depoimentos → FAQ → Contatos/Leads.
 */
export default function App() {
  // Rolagem animada das âncoras + reveal-on-scroll de todas as seções
  useEffect(() => {
    const pararRolagem = iniciarRolagemSuave();
    const pararReveal = iniciarReveal();
    return () => {
      pararRolagem();
      pararReveal();
    };
  }, []);

  return (
    <AccessibilityProvider>
      <a href="#conteudo" className="skip-link">
        Pular para o conteúdo
      </a>

      <Header />

      <main id="conteudo">
        <HeroSection
          titulo="Mobilidade com mais autonomia e acessibilidade"
          subtitulo="A EasyRide transforma cadeiras de rodas motorizadas convencionais em veículos autônomos através de Inteligência Artificial, reconhecimento de voz e navegação inteligente. Uma solução acessível para pessoas com tetraplegia, Esclerose Lateral Amiotrófica (ELA) e outras deficiências motoras severas."
        />
        <TechnologySection />
        <BenefitsSection />
        <ImpactSection />
        <AudienceSection />
        <DifferentialsSection />
        <TeamSection />
        <TestimonialsSection />
        <FAQSection />
        <ContactSection />
      </main>

      <Footer />

      <AccessibilityToolbar />
      <ReaderCaption />
      <WhatsAppButton
        numero={WHATSAPP_NUMERO}
        mensagem="Olá! Tenho interesse em conhecer o kit EasyRide."
      />
    </AccessibilityProvider>
  );
}
