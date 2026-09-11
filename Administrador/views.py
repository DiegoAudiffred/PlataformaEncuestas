from pyexpat.errors import messages

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from db.models import *
from Administrador.forms import *

from django.contrib.auth.decorators import user_passes_test,login_required

def AdministradorIndex(request):
    form = UserAdminPassForm()
    usuarios = User.objects.all().order_by('username')
    context = {
        "usuarios": usuarios,
        "current_user_id": request.user.id,
        "form":form,
    }
    
    return render(request, 'Administrador/administrador.html',context)

def editarUsuario(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    form = UserAdminForm(instance=usuario)
    
    formpassowrd = UserPasswordForm()
    context = {
        'form': form,
        'usuario': usuario,
        'formpassowrd':formpassowrd
    }
    return render(request, "Administrador/editarUsuario.html", context)

def altaUsuarios(request):
    if request.method == 'POST':
        form = UserAdminPassForm(request.POST) 
        if form.is_valid():
            user = form.save() 

            return redirect('Administrador:AdministradorIndex')
        else:
            usuarios = User.objects.all().order_by('username')
            
            context = {
                "usuarios": usuarios,
                "current_user_id": request.user.id,
                "form": form,  
                "show_modal_error": True 
            }
            return render(request, 'Administrador/administrador.html', context)
    else:
        return redirect('Administrador:AdministradorIndex')

def editarContrasena(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = UserPasswordForm(request.POST) 
        
        if form.is_valid():
            nueva_contrasena = form.cleaned_data['nueva_contrasena']
            
            usuario.set_password(nueva_contrasena)
            usuario.save()
            
            #messages.success(request, f"Contraseña del usuario {usuario.username} actualizada correctamente.")
            return redirect('Administrador:AdministradorIndex')
        else:
            form_datos = UserAdminForm(instance=usuario)
            context = {
                'form': form_datos,
                'usuario': usuario,
                'formpassowrd':form
            }
            return render(request, "Administrador/editarUsuario.html", context)



def editarUsuarioDatos(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UserAdminForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            #messages.success(request, f"Usuario {usuario.username} actualizado correctamente.")
            return redirect('Administrador:AdministradorIndex')
        else:

            formpassowrd = UserPasswordForm()
            context = {
                'form': form,
                'usuario': usuario,
                'formpassowrd':formpassowrd
            }
            return render(request, "Administrador/editarUsuario.html", context)

def editarMensajes(request):
    mensajes = Mensaje.objects.all().prefetch_related('preguntas_set').order_by('-id')
    
    if request.method == 'POST':
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            mensaje_id = request.POST.get('mensaje_id')
            texto_pregunta = request.POST.get('pregunta')
            
            if mensaje_id and texto_pregunta:
                mensaje = Mensaje.objects.get(id=mensaje_id)
                pregunta = Preguntas.objects.create(mensaje=mensaje, pregunta=texto_pregunta)
                return JsonResponse({
                    'status': 'success', 
                    'id': pregunta.id, 
                    'texto': pregunta.pregunta
                })
            return JsonResponse({'status': 'error'}, status=400)

        mensaje_id = request.POST.get('mensaje_id')
        if mensaje_id:
            instancia = Mensaje.objects.get(id=mensaje_id)
            form = MensajeForm(request.POST, instance=instancia)
        else:
            form = MensajeForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('Administrador:editarMensajes')

    mensajes_con_forms = []
    for mensaje in mensajes:
        form_edit = MensajeForm(instance=mensaje)
        mensajes_con_forms.append({
            'mensaje': mensaje, 
            'form': form_edit,
            'preguntas': mensaje.preguntas_set.all()
        })

    form2 = MensajeForm()
    
    context = {
        'mensajes_con_forms': mensajes_con_forms, 
        'form2': form2
    }
    return render(request, 'Administrador/editarMensajes.html', context)

def borrarPregunta(request, id):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            pregunta = Preguntas.objects.get(id=id)
            pregunta.delete()
            return JsonResponse({'status': 'success'})
        except Preguntas.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'La pregunta no existe'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=400)

def getRespuestas(request, pregunta_id):
    try:
        pregunta = Preguntas.objects.get(id=pregunta_id)
        respuestas = pregunta.respuesta_set.all().values('id', 'respuesta')
        lista_respuestas = [{'id': r['id'], 'texto': r['respuesta']} for r in respuestas]
        return JsonResponse({'respuestas': lista_respuestas})
    except Preguntas.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Pregunta no encontrada'}, status=404)

def agregarRespuesta(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        pregunta_id = request.POST.get('pregunta_id')
        texto_respuesta = request.POST.get('respuesta')
        
        if not texto_respuesta:
            return JsonResponse({'status': 'error', 'message': 'Texto vacío'}, status=400)
            
        try:
            pregunta = Preguntas.objects.get(id=pregunta_id)
            nueva_respuesta = Respuesta.objects.create(
                pregunta=pregunta,
                respuesta=texto_respuesta
            )
            return JsonResponse({
                'status': 'success',
                'id': nueva_respuesta.id,
                'texto': nueva_respuesta.respuesta
            })
        except Preguntas.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Pregunta no encontrada'}, status=404)
    return JsonResponse({'status': 'error'}, status=400)

def borrarRespuesta(request, id):
    if request.method == 'POST':
        try:
            respuesta = Respuesta.objects.get(id=id)
            respuesta.delete()
            return JsonResponse({'status': 'success'})
        except Respuesta.DoesNotExist:
            return JsonResponse({'status': 'error'}, status=404)
    return JsonResponse({'status': 'error'}, status=400)

