from django.urls import path
from . import views
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
app_name = 'Administrador'

urlpatterns = [
    path("", views.AdministradorIndex, name='AdministradorIndex'),
    path('Administrador/alta/', views.altaUsuarios, name='altaUsuarios'),
    path('editar/<int:user_id>/', views.editarUsuario, name='editarUsuario'),
    path('editarContrasena/<int:user_id>/', views.editarContrasena, name='editarContrasena'),
    path('editarUsuarioDatos/<int:user_id>/', views.editarUsuarioDatos, name='editarUsuarioDatos'),
    path('editarMensajes/', views.editarMensajes, name='editarMensajes'),
    path('borrarPregunta/<int:id>', views.borrarPregunta, name='borrarPregunta'),
    path('agregarRespuesta/', views.agregarRespuesta, name='agregarRespuesta'),
    path('getRespuestas/<int:pregunta_id>/', views.getRespuestas, name='getRespuestas'),
    path('borrarRespuesta/<int:id>/', views.borrarRespuesta, name='borrarRespuesta'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
