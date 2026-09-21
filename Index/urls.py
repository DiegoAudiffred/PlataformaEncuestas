from django.urls import path
from . import views
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
app_name = 'Index'

urlpatterns = [
    path("", views.index, name='index'),
    path("encuestas/",views.indexEncuestas,name='indexEncuestas'),
        path("encuestasUsuario/",views.encuestasUsuario,name='encuestasUsuario'),
        path("encuestasUsuario2/",views.buscarEncuestasSelfUser,name='buscarEncuestasSelfUser'),

    path("encuestaContestada/",views.encuestasContestadas,name='encuestasContestadas'),
    path("encuestaCrear/",views.crearEncuesta,name='crearEncuesta'),
    path('buscarEncuestas/', views.buscarEncuestas, name='buscarEncuestas'),
    path("encuestasResultados/",views.encuestasResultados,name='encuestasResultados'),
    path("editarEncuesta/<int:id>",views.editarEncuesta,name='editarEncuesta'),
    path("enviarCorreoEncuesta/<int:encuesta_id>",views.enviarCorreoEncuesta,name='enviarCorreoEncuesta'),

    path("responderEncuesta/<int:id>",views.responderEncuesta,name='responderEncuesta'),
    path("misRespuestas/<int:id>/",views.verRespuestasEncuesta,name='verRespuestasEncuesta'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)