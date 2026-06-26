"""
Configuração de URLs do projeto core.

Roteia as URLs principais do projeto, incluindo o admin
e as rotas da API do EasyRide.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('EasyRide.urls')),
]
