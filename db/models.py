import os
import tempfile
from datetime import timezone

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Define a model manager for User model with a username field instead of an email."""

    use_in_migrations = True

    def _create_user(self, username, password, **extra_fields):
        if not username:
            raise ValueError('The given username must be set')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, password, **extra_fields)

    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, password, **extra_fields)


class User(AbstractUser):
    username = models.CharField("Usuario", max_length=15, unique=True, null=False, blank=False)
    is_active = models.BooleanField(default=True)
    ROLES = (
        ('Ejecutivo', 'Ejecutivo'),
        ('Crédito', 'Crédito'),
        ('Jurídico', 'Jurídico'),
        ('Sistemas', 'Sistemas'),
    )
    nombre = models.CharField(max_length=50, blank=True, null=True)
    rol = models.CharField(max_length=30, choices=ROLES, default='Ejecutivo')
    email = models.EmailField(_('email address'), blank=True, null=True)
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return str(self.username)


class Encuesta(models.Model):
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    creador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='encuestas_creadas')
    activa = models.BooleanField(default=True)
    fechaCreacion = models.DateField(auto_now=True)
    fechaVencimiento = models.DateField(blank=True, null=True)
    imagen = models.ImageField(upload_to='images/', null=True, blank=True)
    dirigido = models.ManyToManyField(User)
    maxIntentos = models.IntegerField(default=0)
    def __str__(self):
        return self.titulo


class EncuestaArchivo(models.Model):
    nombre = models.CharField(max_length=20, blank=True, null=True)
    archivo = models.FileField(upload_to='archivos_encuesta/', blank=True, null=True)


class Pregunta(models.Model):
    TIPOS_PREGUNTA = (
        ('OPCION_MULTIPLE', 'Opción Múltiple'),
        ('TEXTO', 'Texto Libre'),
    )
    encuesta = models.ForeignKey(Encuesta, on_delete=models.CASCADE, related_name='preguntas')
    texto_pregunta = models.CharField(max_length=255)
    imagen = models.ImageField(upload_to='preguntas/', null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=TIPOS_PREGUNTA, default='OPCION_MULTIPLE')

    def __str__(self):
        return self.texto_pregunta


class OpcionRespuesta(models.Model):
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, related_name='opciones')
    texto_opcion = models.CharField(max_length=150)
    puntos = models.IntegerField(default=0)
    es_correcta = models.BooleanField(default=False)

    def __str__(self):
        return self.texto_opcion


class RespuestaEncuesta(models.Model):
    encuesta = models.ForeignKey(
        Encuesta,
        on_delete=models.CASCADE,
        related_name='respuestas_registradas'
    )
    empleado = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='encuestas_respondidas'
    )
    intento = models.PositiveIntegerField(default=1)
    puntuacion = models.IntegerField(default=0)
    fecha_respuesta = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['encuesta', 'empleado', 'intento'],
                name='unique_encuesta_empleado_intento'
            )
        ]


class DetalleRespuesta(models.Model):
    respuesta_encuesta = models.ForeignKey(
        RespuestaEncuesta,
        on_delete=models.CASCADE,
        related_name='detalles'
    )

    pregunta = models.ForeignKey(
        Pregunta,
        on_delete=models.CASCADE
    )

    opcion_seleccionada = models.ForeignKey(
        OpcionRespuesta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    texto_respuesta = models.TextField(
        null=True,
        blank=True
    )
