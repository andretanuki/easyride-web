"""Roteamento de URLs do app EasyRide.

Mapeia cada prefixo para o ViewSet ou view funcional correspondente,
seguindo o Contrato de Integração da API (Atualização - Entrega 2):

  GET/POST /api/leads/              → LeadViewSet (listar / criar)
  GET      /api/leads/{id}/         → LeadViewSet (detalhar)
  PATCH    /api/leads/{id}/status/  → LeadViewSet.atualizar_status
  GET      /api/leads/estatisticas/ → estatisticas_leads (view funcional)
  GET/POST /api/modelos/            → ModeloViewSet (CRUD)
  GET      /api/pessoas/            → PessoaViewSet (somente leitura)
  GET      /api/beneficios/         → BeneficioViewSet (somente leitura, cacheado)
  GET      /api/depoimentos/        → DepoimentoViewSet (somente leitura, cacheado)
  GET      /api/faq/                → FaqViewSet (somente leitura, cacheado)
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'pessoas', views.PessoaViewSet, basename='pessoa')
router.register(r'modelos', views.ModeloViewSet, basename='modelo')
router.register(r'leads', views.LeadViewSet, basename='lead')
router.register(r'beneficios', views.BeneficioViewSet, basename='beneficio')
router.register(r'depoimentos', views.DepoimentoViewSet, basename='depoimento')
router.register(r'faq', views.FaqViewSet, basename='faq')

urlpatterns = [
    # Rota de estatísticas precisa vir ANTES do include do router
    # para não ser capturada pelo padrão leads/{id}/
    path('leads/estatisticas/', views.estatisticas_leads, name='lead-estatisticas'),

    # Endpoints CRUD via DRF Router
    path('', include(router.urls)),
]
