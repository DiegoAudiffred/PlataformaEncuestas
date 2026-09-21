import os
import tempfile
from datetime import timezone

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def validar_tamano_imagen(archivo, max_mb=5):
    """Evita subir imágenes gigantes que tumben el request o el storage."""
    limite = max_mb * 1024 * 1024
    if archivo.size > limite:
        raise ValidationError(f'La imagen no debe superar los {max_mb}MB.')


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
    titulo = models.CharField(max_length=150,blank=False,null=False,unique=True)
    descripcion = models.TextField(blank=True,null=True)
    creador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='encuestas_creadas',blank=True)
    activa = models.BooleanField(default=True)
    fechaCreacion = models.DateField(auto_now=True)
    fechaVencimiento = models.DateField(blank=True, null=True)
    imagen = models.ImageField(upload_to='images/', null=True, blank=True)
    dirigido = models.ManyToManyField(User, null=True, blank=True)
    maxIntentos = models.IntegerField(default=1)

    def __str__(self):
        return self.titulo

    def puede_editar(self, user):
        """Solo el creador o un staff/superuser puede modificar la encuesta."""
        if user.is_superuser or user.is_staff:
            return True
        return self.creador_id == user.id


class EncuestaArchivo(models.Model):
    nombre = models.CharField(max_length=20, blank=True, null=True)
    archivo = models.FileField(upload_to='archivos_encuesta/', blank=True, null=True)


class Pregunta(models.Model):
    TIPOS_PREGUNTA = (
        ('OPCION_MULTIPLE', 'Opción Múltiple'),
        ('TEXTO', 'Texto Libre'),
        ('USUARIO_UNICO', 'Selección de Usuario (uno)'),
        ('USUARIO_MULTIPLE', 'Selección de Usuarios (varios)'),
    )

    # Tipos que se resuelven contra la tabla User en vez de OpcionRespuesta
    TIPOS_USUARIO = ('USUARIO_UNICO', 'USUARIO_MULTIPLE')
    # Tipos que usan OpcionRespuesta (texto libre no aplica)
    TIPOS_CON_OPCIONES = ('OPCION_MULTIPLE',)

    encuesta = models.ForeignKey(Encuesta, on_delete=models.CASCADE, related_name='preguntas')
    texto_pregunta = models.CharField(max_length=255)
    imagen = models.ImageField(
        upload_to='preguntas/',
        null=True,
        blank=True,
        validators=[validar_tamano_imagen],
    )
    tipo = models.CharField(max_length=20, choices=TIPOS_PREGUNTA, default='OPCION_MULTIPLE')
    orden = models.PositiveIntegerField(default=0)

    # Para USUARIO_UNICO / USUARIO_MULTIPLE: universo de usuarios que se pueden
    # elegir como respuesta. Si se deja vacío, se asume "todos los usuarios
    # dirigidos a la encuesta" al momento de responder.
    usuarios_opciones = models.ManyToManyField(
        User,
        blank=True,
        related_name='preguntas_como_opcion',
        verbose_name='Usuarios seleccionables',
    )

    class Meta:
        ordering = ['orden', 'id']

    def __str__(self):
        return self.texto_pregunta

    def es_tipo_usuario(self):
        return self.tipo in self.TIPOS_USUARIO

    def es_tipo_opciones(self):
        return self.tipo in self.TIPOS_CON_OPCIONES


class OpcionRespuesta(models.Model):
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, related_name='opciones')
    texto_opcion = models.CharField(max_length=150)
    puntos = models.IntegerField(default=0)
    es_correcta = models.BooleanField(default=False)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden', 'id']

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

    # NUEVO: para preguntas tipo USUARIO_UNICO / USUARIO_MULTIPLE.
    # No se usa OpcionRespuesta aquí porque la "opción" es un User real,
    # no texto libre inventado por el creador de la encuesta.
    usuarios_seleccionados = models.ManyToManyField(
        User,
        blank=True,
        related_name='seleccionado_en_respuestas',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['respuesta_encuesta', 'pregunta'],
                name='unique_respuesta_por_pregunta'
            )
        ]