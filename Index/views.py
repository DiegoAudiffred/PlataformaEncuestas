from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import user_passes_test,login_required
from Index.forms import *
from db.models import * 
from django.core.paginator import Paginator
@login_required(login_url='/login/')    

def index(request):

    
    return render(request, 'index/index.html')


@login_required(login_url='/login/')
def indexEncuestas(request):
    encuestas = Encuesta.objects.filter(activa=True).order_by('-id')
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
        'Index/listaEncuestas.html',
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
                if request.user.is_authenticated:
                    encuesta.creador = request.user
                encuesta.save()
                form.save_m2m()
                return redirect('Index:encuestasPreguntas', id=encuesta.id)
    else:
            form = crearEncuestaForm()

    return render(request, 'index/crearEncuestas.html', {'form': form})

@login_required(login_url='/login/')
def encuestasPreguntas(request, id):

    encuesta = get_object_or_404(Encuesta, id=id)

    if request.method == 'POST':

        action = request.POST.get('action')

        # EDITAR ENCUESTA
        if action == 'editar_encuesta':

            form_encuesta = crearEncuestaForm(
                request.POST,
                request.FILES,
                instance=encuesta
            )

            if form_encuesta.is_valid():

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


        # ELIMINAR PREGUNTA
        if action == 'delete':

            pregunta_id = request.POST.get('pregunta_id')

            pregunta = get_object_or_404(
                Pregunta,
                id=pregunta_id,
                encuesta=encuesta
            )

            pregunta.delete()

            return JsonResponse({
                'status': 'success'
            })


        # CREAR / EDITAR PREGUNTA

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


        if form.is_valid():

            pregunta = form.save(commit=False)

            pregunta.encuesta = encuesta

            pregunta.save()


            # Si estamos editando, eliminamos
            # las opciones anteriores para recrearlas
            if pregunta_id:
                pregunta.opciones.all().delete()


            opciones_creadas = []


            # Las preguntas de texto no tienen opciones
            if pregunta.tipo != 'TEXTO':

                opciones_list = request.POST.getlist(
                    'opciones[]'
                )

                puntos_list = request.POST.getlist(
                    'puntos[]'
                )

                correctas_list = request.POST.getlist(
                    'es_correcta[]'
                )


                for index, texto in enumerate(opciones_list):

                    texto_clean = texto.strip()

                    if not texto_clean:
                        continue


                    pts = 0

                    if (
                        index < len(puntos_list)
                        and puntos_list[index].strip().isdigit()
                    ):
                        pts = int(
                            puntos_list[index]
                        )


                    es_cor = str(index) in correctas_list


                    opcion = OpcionRespuesta.objects.create(
                        pregunta=pregunta,
                        texto_opcion=texto_clean,
                        puntos=pts,
                        es_correcta=es_cor
                    )


                    opciones_creadas.append({
                        'id': opcion.id,
                        'texto': opcion.texto_opcion,
                        'puntos': opcion.puntos,
                        'es_correcta': opcion.es_correcta
                    })


            image_url = (
                pregunta.imagen.url
                if pregunta.imagen
                else None
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

                    'opciones': opciones_creadas

                }

            })


        return JsonResponse({

            'status': 'error',

            'errors': form.errors

        }, status=400)


    # GET

    form = PreguntaForm()

    form_encuesta = crearEncuestaForm(
        instance=encuesta
    )


    preguntas = (
        encuesta.preguntas
        .prefetch_related('opciones')
        .all()
    )


    return render(
        request,
        'index/preguntasEncuesta.html',
        {
            'encuesta': encuesta,
            'preguntas': preguntas,
            'form': form,
            'form_encuesta': form_encuesta
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
        .prefetch_related('opciones')
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
