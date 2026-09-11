from django.urls import path
from . import views
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
app_name = 'Envios'

urlpatterns = [
    path("", views.EnviosIndex, name='EnviosIndex'),
    path('prospector/filtrar/', views.filtrarProspectos, name='filtrarProspectos'),
    path('checkmarckChange/', views.checkmarckChange, name='checkmarckChange'),
    path('mandarCorreos/', views.mandarCorreos, name='mandarCorreos'),
    path('listaEnvios/<int:id>', views.listaEnvios, name='listaEnvios')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
