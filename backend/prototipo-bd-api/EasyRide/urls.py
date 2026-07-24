"""Roteamento de URLs do app EasyRide.

Mapeia cada prefixo para o ViewSet ou view funcional correspondente,
seguindo o Contrato de Integração da API (Atualização - Entrega 2):

  GET/POST /api/leads/              → LeadViewSet (listar / criar)
  GET      /api/leads/{id}/         → LeadViewSet (detalhar)
  PATCH    /api/leads/{id}/status/  → LeadViewSet.atualizar_status
  GET      /api/leads/estatisticas/ → estatisticas_leads (view funcional)
  GET/POST /api/modelos/            → ModeloViewSet (CRUD)
  GET      /api/pessoas/            → PessoaViewSet (somente leitura)
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'pessoas', views.PessoaViewSet, basename='pessoa')
router.register(r'modelos', views.ModeloViewSet, basename='modelo')
router.register(r'leads', views.LeadViewSet, basename='lead')

urlpatterns = [
    # Rota de estatísticas precisa vir ANTES do include do router
    # para não ser capturada pelo padrão leads/{id}/
    path('leads/estatisticas/', views.estatisticas_leads, name='lead-estatisticas'),

    # Endpoints CRUD via DRF Router
    path('', include(router.urls)),
]
