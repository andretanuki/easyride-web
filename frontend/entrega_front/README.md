# EasyRide — Front-end (Landing Page)

Landing page de captação de leads da EasyRide, construída em **React + Vite (JavaScript, CSS3 puro)** conforme:

- `docs/Arquitetura_Componentes_React_v3.0.pdf` — árvore de componentes, props e estados
- `docs/Atualizacao_Contrato_API_v4.0.pdf` — contrato vigente da API
- `docs/wireframe/Guia_de_Estilos_e_Regras_de_Acessibilidade_WCAG.pdf` — Inter, corpo ≥16px, contraste ≥4.5:1, ARIA
- Base visual: https://flaviaa666.github.io/easyride-landing-page/

## Como rodar

Pré-requisito: backend rodando em `http://127.0.0.1:8000` (ver [`backend/entrega-backend/README.md`](../../backend/entrega-backend/README.md)), a partir da raiz do repositório:

```bash
cd backend/entrega-backend
python manage.py migrate && python manage.py seed && python manage.py runserver
```

Front-end (porta **3000**, já liberada no CORS do backend), em outro terminal e também a partir da raiz do repositório:

```bash
cd frontend/entrega_front
npm install
cp .env.example .env   # ajuste VITE_API_BASE_URL se necessário
npm run dev            # http://localhost:3000
npm run build          # build de produção em dist/
```

## Estrutura

```
src/
├── App.jsx                     # ordem das seções (briefing §3.1)
├── context/AccessibilityContext.jsx  # fonte, contraste, leitor (LocalStorage)
├── services/api.js             # cliente da API (fetch, erros 400/409/500)
├── data/fallbacks.js           # conteúdo de contingência (estado "Erro 500")
├── styles/global.css           # variáveis, foco visível, alto contraste
└── components/                 # um .jsx + .css por componente
```

## Componentes ↔ Arquitetura v3

| PDF | Componente |
|---|---|
| 1.1 AccessibilityToolbar | `AccessibilityToolbar.jsx` (A+/A−, alto contraste, leitor por hover) |
| 1.2 HeroSection | `HeroSection.jsx` (fade-in, fallback de imagem) |
| 1.2.1 LeadCaptureForm | `LeadCaptureForm.jsx` (polimórfico FISICA/JURIDICA, estados 201/400/409/500) |
| 1.2.2 CTAButton | `CTAButton.jsx` |
| 1.3 BenefitsSection | `BenefitsSection.jsx` + `BenefitCard.jsx` (GET /api/beneficios/) |
| 1.4 TestimonialsSection | `TestimonialsSection.jsx` + `TestimonialCard.jsx` (GET /api/depoimentos/, carrossel 5s) |
| 1.5 FAQSection | `FAQSection.jsx` + `FAQItem.jsx` (GET /api/faq/, busca) |
| 1.6 WhatsAppButton | `WhatsAppButton.jsx` (wa.me, pulso após 10s) |
| 1.7 Footer | `Footer.jsx` |

Seções do briefing §3.1 sem componente no PDF (implementadas a partir da landing de referência): `TechnologySection`, `ImpactSection`, `AudienceSection`, `DifferentialsSection`, `TeamSection`, `ContactSection` (hospeda o LeadCaptureForm).

## Acessibilidade

Navegação completa por teclado (foco visível + skip-link), `label` em todos os campos, ARIA (`aria-live`, `aria-expanded`, `role="alert"`), alto contraste (fundo preto/letras amarelas), fonte escalável 100–150%, leitor de tela por hover (Web Speech API), `prefers-reduced-motion` respeitado.
