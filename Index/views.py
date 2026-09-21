import email
from email.message import EmailMessage
from email.mime.text import MIMEText
import smtplib

from django.contrib import messages
from django.db.models import OuterRef, Subquery
from django.db.models.aggregates import Count
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import user_passes_test,login_required
from Index.forms import *
from db.models import * 
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.db import transaction



@login_required(login_url='/login/')    

def index(request):

    
    return render(request, 'index/index.html')


@login_required(login_url='/login/')
def indexEncuestas(request):
    usuario = request.user

    subconsulta_intentos = RespuestaEncuesta.objects.filter(
        encuesta_id=OuterRef('pk'),
        empleado_id=usuario.id
    ).values('encuesta').annotate(
        total=Count('id')
    ).values('total')

    encuestas = Encuesta.objects.filter(
        activa=True,
        dirigido=usuario
    ).annotate(
        intentos_realizados=Coalesce(Subquery(subconsulta_intentos), 0)
    ).order_by('-id')
    creadoes = User.objects.all().order_by('username')

    paginator = Paginator(encuestas, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'encuestas': page_obj,
        'creadoes': creadoes,
    }

    return render(request, 'Index/indexEncuestas.html', context)

@login_required(login_url='/login/')
def encuestasUsuario(request):
    encuestas = Encuesta.objects.filter(creador=request.user).order_by('-id')
    creadoes = User.objects.all().order_by('username')

    paginator = Paginator(encuestas, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'encuestas': page_obj,
        'creadoes': creadoes,
    }

    return render(request, 'Index/misEncuestasUsuario.html', context)

@login_required(login_url='/login/')
def buscarEncuestas(request):
    usuario = request.user
    titulo = request.GET.get('nombre', '').strip()
    estado = request.GET.get('estado', '0').strip()
    autor = request.GET.get('autor', '0').strip()
    page = request.GET.get('page', 1)

    subconsulta_intentos = RespuestaEncuesta.objects.filter(
        encuesta_id=OuterRef('pk'),
        empleado_id=usuario.id
    ).values('encuesta').annotate(
        total=Count('id')
    ).values('total')

    encuestas = Encuesta.objects.filter(
        activa=True,
        dirigido=usuario
    ).annotate(
        intentos_realizados=Coalesce(Subquery(subconsulta_intentos), 0)
    ).order_by('-id')

    if titulo:
        encuestas = encuestas.filter(
            titulo__icontains=titulo
        )

    if estado == '1':
        encuestas = encuestas.filter(
            activa=True
        )
    elif estado == '2':
        encuestas = encuestas.filter(
            activa=False
        )

    if autor and autor != '0':
        encuestas = encuestas.filter(
            creador_id=autor
        )

    paginator = Paginator(encuestas, 10)
    page_obj = paginator.get_page(page)

    contexto = {
        'encuestas': page_obj
    }

    return render(
        request,
        'Index/listaEncuestas.html',
        contexto
    )
@login_required(login_url='/login/')
def buscarEncuestasSelfUser(request):
    titulo = request.GET.get('nombre', '').strip()
    estado = request.GET.get('estado', '0').strip()
    autor = request.GET.get('autor', '0').strip()
    page = request.GET.get('page', 1)

    encuestas = Encuesta.objects.all().order_by('-id')

    if titulo:
        encuestas = encuestas.filter(
            titulo__icontains=titulo
        )

    if estado == '1':
        encuestas = encuestas.filter(
            activa=True
        )
    elif estado == '2':
        encuestas = encuestas.filter(
            activa=False
        )

    if autor and autor != '0':
        encuestas = encuestas.filter(
            creador_id=autor
        )

    paginator = Paginator(encuestas, 10)
    page_obj = paginator.get_page(page)

    contexto = {
        'encuestas': page_obj
    }

    return render(
        request,
        'Index/listaEncuestasSelfUser.html',
        contexto
    )


@login_required(login_url='/login/')    
def encuestasContestadas(request):
    return render(request, 'index/encuestasContestadas.html')

@login_required(login_url='/login/')
def crearEncuesta(request):
    if request.method == 'POST':
        form = crearEncuestaForm(request.POST, request.FILES)
        if form.is_valid():
            encuesta = form.save(commit=False)
            encuesta.activa = True
            encuesta.creador = request.user
            encuesta.save()
            
            dirigido_seleccionados = form.cleaned_data.get('dirigido')
            if not dirigido_seleccionados:
                usuarios_activos = User.objects.filter(is_active=True)
                encuesta.dirigido.set(usuarios_activos)
            else:
                form.save_m2m()
                
            return redirect('Index:editarEncuesta', id=encuesta.id)
        else:
            print(form.errors)
    else:
        form = crearEncuestaForm()

    return render(request, 'index/crearEncuestas.html', {'form': form})


@login_required(login_url='/login/')
def editarEncuesta(request, id):

    encuesta = get_object_or_404(Encuesta, id=id)

    # --- PERMISOS: solo el creador o staff puede tocar esta encuesta ---
    if not encuesta.puede_editar(request.user):
        raise PermissionDenied('No tienes permiso para editar esta encuesta.')

    if request.method == 'POST':

        action = request.POST.get('action')

        # ================= EDITAR ENCUESTA =================
        if action == 'editar_encuesta':

            form_encuesta = crearEncuestaForm(
                request.POST,
                request.FILES,
                instance=encuesta
            )

            if form_encuesta.is_valid():

                with transaction.atomic():
                    encuesta = form_encuesta.save()

                return JsonResponse({
                    'status': 'success',
                    'encuesta': {
                        'id': encuesta.id,
                        'titulo': encuesta.titulo,
                        'descripcion': encuesta.descripcion,
                        'activa': encuesta.activa,
                        'fechaVencimiento': (
                            encuesta.fechaVencimiento.strftime('%Y-%m-%d')
                            if encuesta.fechaVencimiento
                            else ''
                        ),
                        'imagen_url': (
                            encuesta.imagen.url
                            if encuesta.imagen
                            else None
                        )
                    }
                })

            return JsonResponse({
                'status': 'error',
                'errors': form_encuesta.errors
            }, status=400)

        # ================= ELIMINAR PREGUNTA =================
        if action == 'delete':

            pregunta_id = request.POST.get('pregunta_id')

            pregunta = get_object_or_404(
                Pregunta,
                id=pregunta_id,
                encuesta=encuesta
            )

            tiene_respuestas = DetalleRespuesta.objects.filter(
                pregunta=pregunta
            ).exists()

            if tiene_respuestas and request.POST.get('force') != '1':
                return JsonResponse({
                    'status': 'confirm_required',
                    'message': (
                        'Esta pregunta ya tiene respuestas registradas de '
                        'empleados. Si la eliminas, se perderá ese historial. '
                        '¿Deseas continuar?'
                    )
                }, status=409)

            with transaction.atomic():
                pregunta.delete()

            return JsonResponse({'status': 'success'})

        # ================= CREAR / EDITAR PREGUNTA =================

        pregunta_id = request.POST.get('pregunta_id')

        if pregunta_id:

            pregunta = get_object_or_404(
                Pregunta,
                id=pregunta_id,
                encuesta=encuesta
            )

            form = PreguntaForm(
                request.POST,
                request.FILES,
                instance=pregunta
            )

        else:

            form = PreguntaForm(
                request.POST,
                request.FILES
            )

        if not form.is_valid():
            return JsonResponse({
                'status': 'error',
                'errors': form.errors
            }, status=400)

        tipo = form.cleaned_data['tipo']

        # --- Validación de datos según el tipo ANTES de guardar nada ---
        opciones_list, puntos_list, correctas_list, ids_list = [], [], [], []
        usuarios_ids = []

        if tipo == 'OPCION_MULTIPLE':

            opciones_list = [
                t.strip() for t in request.POST.getlist('opciones[]')
            ]
            puntos_list = request.POST.getlist('puntos[]')
            correctas_list = request.POST.getlist('es_correcta[]')
            ids_list = request.POST.getlist('opcion_id[]')

            if not any(opciones_list):
                return JsonResponse({
                    'status': 'error',
                    'errors': {'opciones': ['Agrega al menos una opción.']}
                }, status=400)

        elif tipo in Pregunta.TIPOS_USUARIO:

            usuarios_ids = request.POST.getlist('usuarios_opciones[]')

            if not usuarios_ids:
                return JsonResponse({
                    'status': 'error',
                    'errors': {
                        'usuarios_opciones': [
                            'Selecciona al menos un usuario disponible '
                            'para esta pregunta.'
                        ]
                    }
                }, status=400)

        # --- Guardado atómico ---
        with transaction.atomic():

            pregunta = form.save(commit=False)
            pregunta.encuesta = encuesta
            pregunta.save()

            # Limpieza de relaciones que no aplican al tipo actual
            if tipo != 'OPCION_MULTIPLE':
                pregunta.opciones.all().delete()
            if tipo not in Pregunta.TIPOS_USUARIO:
                pregunta.usuarios_opciones.clear()

            opciones_creadas = []

            if tipo == 'OPCION_MULTIPLE':

                ids_vistos = set()

                for index, texto in enumerate(opciones_list):

                    texto_clean = texto.strip()
                    if not texto_clean:
                        continue

                    pts = 0
                    if (
                        index < len(puntos_list)
                        and puntos_list[index].strip().lstrip('-').isdigit()
                    ):
                        pts = int(puntos_list[index])

                    es_cor = str(index) in correctas_list

                    opcion_id = (
                        ids_list[index]
                        if index < len(ids_list) and ids_list[index]
                        else None
                    )

                    if opcion_id:
                        # Actualiza la opción existente en vez de recrearla,
                        # así no se rompen respuestas ya guardadas que
                        # apuntan a este OpcionRespuesta.id
                        opcion = get_object_or_404(
                            OpcionRespuesta, id=opcion_id, pregunta=pregunta
                        )
                        opcion.texto_opcion = texto_clean
                        opcion.puntos = pts
                        opcion.es_correcta = es_cor
                        opcion.orden = index
                        opcion.save()
                        ids_vistos.add(opcion.id)
                    else:
                        opcion = OpcionRespuesta.objects.create(
                            pregunta=pregunta,
                            texto_opcion=texto_clean,
                            puntos=pts,
                            es_correcta=es_cor,
                            orden=index,
                        )
                        ids_vistos.add(opcion.id)

                    opciones_creadas.append({
                        'id': opcion.id,
                        'texto': opcion.texto_opcion,
                        'puntos': opcion.puntos,
                        'es_correcta': opcion.es_correcta,
                    })

                # Borra en BD las opciones que el usuario quitó del form
                pregunta.opciones.exclude(id__in=ids_vistos).delete()

            elif tipo in Pregunta.TIPOS_USUARIO:

                usuarios_validos = User.objects.filter(id__in=usuarios_ids)
                pregunta.usuarios_opciones.set(usuarios_validos)

                opciones_creadas = [
                    {'id': u.id, 'texto': u.nombre or u.username}
                    for u in usuarios_validos
                ]

            image_url = pregunta.imagen.url if pregunta.imagen else None

            usuarios_opciones_payload = (
                [
                    {'id': u.id, 'nombre': u.nombre or u.username}
                    for u in pregunta.usuarios_opciones.all()
                ]
                if pregunta.es_tipo_usuario()
                else []
            )

        return JsonResponse({
            'status': 'success',
            'is_edit': bool(pregunta_id),
            'pregunta': {
                'id': pregunta.id,
                'texto': pregunta.texto_pregunta,
                'tipo_val': pregunta.tipo,
                'tipo': pregunta.get_tipo_display(),
                'imagen_url': image_url,
                'opciones': opciones_creadas,
                'usuarios_opciones': usuarios_opciones_payload,
            }
        })

    # ================= GET =================
    form = PreguntaForm()
    form_encuesta = crearEncuestaForm(instance=encuesta)

    preguntas = (
        encuesta.preguntas
        .prefetch_related('opciones', 'usuarios_opciones')
        .all()
    )

    # Todos los usuarios que la encuesta puede ofrecer como "opción de usuario".
    # Por defecto: los usuarios a quienes está dirigida la encuesta.
    usuarios_disponibles = encuesta.dirigido.all()

    return render(
        request,
        'index/editarEncuesta.html',
        {
            'encuesta': encuesta,
            'preguntas': preguntas,
            'form': form,
            'form_encuesta': form_encuesta,
            'usuarios_disponibles': usuarios_disponibles,
        }
    )

@login_required(login_url='/login/')    
def encuestasResultados(request):
    return render(request, 'index/encuestasResultados.html')

@login_required(login_url='/login/')
def responderEncuesta(request, id):

    encuesta = get_object_or_404(
        Encuesta,
        id=id
    )

    if not encuesta.activa:
        return render(
            request,
            'index/responderEncuesta.html',
            {
                'encuesta': encuesta,
                'error': 'Esta encuesta ya no está activa.'
            }
        )

    if encuesta.fechaVencimiento:
        if timezone.localdate() > encuesta.fechaVencimiento:
            return render(
                request,
                'index/responderEncuesta.html',
                {
                    'encuesta': encuesta,
                    'error': 'Esta encuesta ya venció.'
                }
            )

    if not encuesta.dirigido.filter(
        id=request.user.id
    ).exists():
        return render(
            request,
            'index/responderEncuesta.html',
            {
                'encuesta': encuesta,
                'error': 'No tienes autorización para responder esta encuesta.'
            }
        )

    intentos_realizados = RespuestaEncuesta.objects.filter(
        encuesta=encuesta,
        empleado=request.user
    ).count()

    intentos_restantes = (
        encuesta.maxIntentos - intentos_realizados
    )

    if intentos_restantes <= 0:

        ultima_respuesta = (
            RespuestaEncuesta.objects
            .filter(
                encuesta=encuesta,
                empleado=request.user
            )
            .order_by('-intento')
            .first()
        )

        return render(
            request,
            'index/responderEncuesta.html',
            {
                'encuesta': encuesta,
                'bloqueada': True,
                'intentos_realizados': intentos_realizados,
                'intentos_restantes': 0,
                'ultima_respuesta': ultima_respuesta
            }
        )

    preguntas = (
        encuesta.preguntas
        .prefetch_related('opciones', 'usuarios_opciones')
        .all()
    )

    if request.method == 'POST':

        intentos_realizados = RespuestaEncuesta.objects.filter(
            encuesta=encuesta,
            empleado=request.user
        ).count()

        if intentos_realizados >= encuesta.maxIntentos:

            return JsonResponse({
                'status': 'error',
                'mensaje': 'Ya alcanzaste el número máximo de intentos.'
            }, status=400)

        intento = intentos_realizados + 1

        respuesta_encuesta = RespuestaEncuesta.objects.create(
            encuesta=encuesta,
            empleado=request.user,
            intento=intento,
            puntuacion=0
        )

        puntuacion_total = 0

        for pregunta in preguntas:

            if pregunta.tipo == 'USUARIO_MULTIPLE':

                usuario_ids = request.POST.getlist(
                    f'pregunta_{pregunta.id}[]'
                )

                if not usuario_ids:
                    continue

                detalle = DetalleRespuesta.objects.create(
                    respuesta_encuesta=respuesta_encuesta,
                    pregunta=pregunta
                )

                usuarios_validos = pregunta.usuarios_opciones.filter(
                    id__in=usuario_ids
                )

                detalle.usuarios_seleccionados.set(usuarios_validos)

                continue

            respuesta = request.POST.get(
                f'pregunta_{pregunta.id}'
            )

            if not respuesta:
                continue

            if pregunta.tipo == 'OPCION_MULTIPLE':

                opcion = get_object_or_404(
                    OpcionRespuesta,
                    id=respuesta,
                    pregunta=pregunta
                )

                DetalleRespuesta.objects.create(
                    respuesta_encuesta=respuesta_encuesta,
                    pregunta=pregunta,
                    opcion_seleccionada=opcion
                )

                if opcion.es_correcta:
                    puntuacion_total += opcion.puntos

            elif pregunta.tipo == 'TEXTO':

                DetalleRespuesta.objects.create(
                    respuesta_encuesta=respuesta_encuesta,
                    pregunta=pregunta,
                    texto_respuesta=respuesta
                )

            elif pregunta.tipo == 'USUARIO_UNICO':

                usuario = pregunta.usuarios_opciones.filter(
                    id=respuesta
                ).first()

                if not usuario:
                    continue

                detalle = DetalleRespuesta.objects.create(
                    respuesta_encuesta=respuesta_encuesta,
                    pregunta=pregunta
                )

                detalle.usuarios_seleccionados.add(usuario)

        respuesta_encuesta.puntuacion = puntuacion_total
        respuesta_encuesta.save(update_fields=['puntuacion'])

        return JsonResponse({
            'status': 'success',
            'mensaje': 'Encuesta respondida correctamente.',
            'intento': intento,
            'puntuacion': puntuacion_total,
            'intentos_restantes': encuesta.maxIntentos - intento
        })

    return render(
        request,
        'index/responderEncuesta.html',
        {
            'encuesta': encuesta,
            'preguntas': preguntas,
            'intentos_realizados': intentos_realizados,
            'intentos_restantes': intentos_restantes,
            'bloqueada': False
        }
    )

@login_required(login_url='/login/')
def enviarCorreoEncuesta(request, encuesta_id):
    if request.method == 'POST':
        encuesta = get_object_or_404(Encuesta, id=encuesta_id)
        
        destinatarios = list(encuesta.dirigido.filter(is_active=True).exclude(email='').values_list('email', flat=True))
        dominio = "http://192.168.0.29:8001/responderEncuesta/"
        url_final = f"{dominio}{encuesta.id}"

        if destinatarios:
            host = "ucg.com.mx"
            port = 587
            usuario_smtp = "informacion@ucg.com.mx"
            password_smtp = "UcG911_@!#"

            asunto = f"Nueva encuesta disponible: {encuesta.titulo}"

            cuerpo_html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                    <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">
                        <h2 style="color: #2c3e50;">Nueva Encuesta Asignada</h2>
                        <p>Estimado usuario,</p>
                        <p>Se le ha asignado la encuesta <strong>{encuesta.titulo}</strong> creada por {request.user.get_full_name() or request.user.username}.</p>
                        <p>Le invitamos a responderla ingresando al siguiente enlace:</p>
                        <div style="margin: 30px 0; text-align: center;">
                            <a href="{url_final}" 
                               style="background-color: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                                Responder Encuesta
                            </a>
                        </div>
                        <p style="font-size: 12px; color: #777;">Si el botón no funciona, copie y pegue el siguiente enlace en su navegador:<br>{url_final}</p>
                    </div>
                </body>
            </html>
            """

            mensaje = EmailMessage()
            mensaje['Subject'] = asunto
            mensaje['From'] = usuario_smtp
            mensaje['To'] = ", ".join(destinatarios)
            mensaje.add_alternative(cuerpo_html, subtype="html")

            try:
                server = smtplib.SMTP(host, port)
                server.starttls()
                server.login(usuario_smtp, password_smtp)
                server.sendmail(usuario_smtp, destinatarios, mensaje.as_string())
                server.quit()
                messages.success(request, "Correos enviados exitosamente.")
            except Exception as e:
                messages.error(request, f"Error al enviar los correos: {e}")
        else:
            messages.warning(request, "No hay usuarios con correo válido para notificar.")

        return redirect('Index:editarEncuesta', id=encuesta.id)

    return redirect('Index:indexEncuestas')