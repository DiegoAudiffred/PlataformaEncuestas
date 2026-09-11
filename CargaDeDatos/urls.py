from django.urls import path
from . import views
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
app_name = 'CargaDeDatos'

urlpatterns = [
    path("", views.CargaDeDatos, name='CargaDeDatos'),
    path("CargarAServidor", views.CargarAServidor, name='CargarAServidor'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
