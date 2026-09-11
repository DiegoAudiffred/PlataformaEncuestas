from django.contrib import admin

from db.models import *

# Register your models here.
admin.site.register(User)
admin.site.register(Encuesta)
admin.site.register(Pregunta)
admin.site.register(OpcionRespuesta)
admin.site.register(RespuestaEncuesta)
admin.site.register(DetalleRespuesta)

