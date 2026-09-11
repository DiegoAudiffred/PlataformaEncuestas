from email.message import EmailMessage
import re
import smtplib
import webbrowser
import pywhatkit
from whatsapp_api_client_python import API

from django.http import JsonResponse
from django.shortcuts import redirect, render
from db.models import *
from django.core.paginator import Paginator
from django.db.models import Q, CharField, DateField, DurationField, ExpressionWrapper, IntegerField
from django.contrib.auth.decorators import user_passes_test,login_required

from django.db.models import OuterRef, Subquery
from django.db.models import OuterRef, Subquery, DateTimeField

from django.db.models import OuterRef, Subquery, DateTimeField, Case, When, Value, F
from django.db.models.functions import Cast, ExtractDay, Now
from datetime import timedelta

def EnviosIndex(request):
    ultimo_envio_subquery = TablaEnvios.objects.filter(
        prospecto=OuterRef('pk')    
    ).order_by('-numeroEnvio').values('numeroEnvio')[:1]

    ultima_fecha_subquery = TablaEnvios.objects.filter(
        prospecto=OuterRef('pk')
    ).order_by('-fecha_envio').values('fecha_envio')[:1]

    hoy = Now()

    prospectos = Prospecto.objects.filter(checkmarck=True).annotate(
        ultimo_envio=Subquery(ultimo_envio_subquery),
        ultima_fecha=Subquery(ultima_fecha_subquery, output_field=DateTimeField())
    ).annotate(
        rango_tiempo=Case(
            When(ultima_fecha__gte=hoy - timedelta(days=1), then=Value('Hoy')),
            When(ultima_fecha__gte=hoy - timedelta(days=2), then=Value('Ayer')),
            When(ultima_fecha__gte=hoy - timedelta(days=6), then=Value('Menos de 7 días')),
            When(ultima_fecha__gte=hoy - timedelta(days=7), then=Value('1 Semana')),
            When(ultima_fecha__gte=hoy - timedelta(days=30), then=Value('Menos de 30 días')),
            When(ultima_fecha__gte=hoy - timedelta(days=60), then=Value('30 a 60 días')),
            When(ultima_fecha__gte=hoy - timedelta(days=90), then=Value('60 a 90 días')),
            When(ultima_fecha__lt=hoy - timedelta(days=90), then=Value('Más de 90 días')),
            default=Value('Sin envíos'),
            output_field=CharField(),
        ),dias_transcurridos = ExpressionWrapper(
        Now() - F('ultima_fecha'),
        output_field=DurationField()
    )).order_by('-id')
    
    todosMensajes = TablaEnvios.objects.all()
    
    paginator = Paginator(prospectos, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'registros': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'todosMensajes': todosMensajes,
    }
    return render(request, 'Envios/EnviosIndex.html', context)

def filtrarProspectos(request):
    page_number = request.GET.get('page', 1)
    prospectos = Prospecto.objects.filter(checkmarck=True).order_by('id')
    
    paginator = Paginator(prospectos, 8)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'registros': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator
    }
    return render(request, 'Envios/tablaEnvios.html', context)

def checkmarckChange(request):
    if request.method == 'POST':
        prospecto_id = request.POST.get('prospecto_id')
        check_value = request.POST.get('checkmarck') == 'true'
        try:
            prospecto = Prospecto.objects.get(id=prospecto_id)
            prospecto.checkmarck = check_value
            prospecto.save()
            return JsonResponse({'status': 'success'})
        except Prospecto.DoesNotExist:
            return JsonResponse({'status': 'error'}, status=404)
    return JsonResponse({'status': 'invalid'}, status=400)

def listaEnvios(request, id):
    prospecto = Prospecto.objects.get(id=id)
   
    envios = TablaEnvios.objects.filter(prospecto=id)
    print(envios)
    context = {'prospecto': prospecto, 'envios': envios}
    return render(request, 'Envios/listaEnvios.html', context)




def mandarCorreos(): 
    
    directorio = Prospecto.objects.filter(checkmarck=True)
    for prospecto in directorio:

        if prospecto.email and prospecto.medioDeContacto == "correo_electrónico" :
            try:
                ultimoMensaje = TablaEnvios.objects.filter(prospecto=prospecto).order_by('-numeroEnvio').first()
                ultimoMensaje = ultimoMensaje.numeroEnvio
            except TablaEnvios.DoesNotExist:
                ultimoMensaje = 0
            print(f"El mensaje a enviar sera el numero {ultimoMensaje+1}")    
            mensaje = Mensaje.objects.get(numEnvio=(ultimoMensaje+1))              
            preguntas_db = Preguntas.objects.filter(mensaje=mensaje)
      
            asunto = mensaje.asunto
            cuerpo_html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                    <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">
                        <h2 style="color: #2c3e50;">Actualización de status del UCG</h2>
                        <p>Estimado <strong>{prospecto.nombreCompleto}</strong> </p>
                        <p>{mensaje.cuerpo}</p
            """
            if mensaje.encuesta:                                             
                for p in preguntas_db:
                    pregunta_texto = p.pregunta
                    respuestas_db = p.respuesta_set.all()
                    cuerpo_html += f"""<p>{pregunta_texto}</p>"""
                   
                    for r in respuestas_db:
                            #opciones.append({"optionName": r.respuesta})
                            cuerpo_html += f"""<p>{r.respuesta}</p>"""
            
            cuerpo_html += """
                        </div>
                    </body>
                </html>
            """
                      
      
            SMTP_HOST = "ucg.com.mx"
            SMTP_PORT = 587
            USUARIO = "centrodenegocios@ucg.com.mx"
            CONTRASENA = "UcG911_@!#"
        
            mensaje = EmailMessage()
            mensaje["From"] = USUARIO
            mensaje["To"] =  prospecto.email
            mensaje["Subject"] = asunto
            
        
            mensaje.add_alternative(cuerpo_html, subtype="html")
        
            try:
                
                servidor = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
                servidor.starttls()
                servidor.login(USUARIO, CONTRASENA)
                servidor.send_message(mensaje)
                servidor.quit()
                print("Correo enviado correctamente")
                if prospecto.status == "NUEVO":
                    prospecto.status = "ENVIADO"
                    prospecto.save()
                TablaEnvios.objects.create(prospecto=prospecto,
                                           medioDeContacto=prospecto.medioDeContacto,
                                           numeroEnvio=ultimoMensaje+1)
                
            except Exception as e:
                print("Error al enviar correo:", e)
        if prospecto.telefono and prospecto.medioDeContacto == "llamada_telefónica":
            asunto = "Informe listo para revisión"

        

        if prospecto.telefono and prospecto.medioDeContacto == "whatsapp":
            greenAPI = API.GreenApi(
                "7107614191", 
                "efd7424742c442fe915fb51c101f26c0fb16420c8fbc44bc80"
            )
            import re         
            solo_numeros = re.sub(r'\D', '', str(prospecto.telefono))
            
            if not solo_numeros.startswith('52'):
                solo_numeros = f"521{solo_numeros}"
            elif solo_numeros.startswith('52') and not solo_numeros.startswith('521'):
                solo_numeros = f"521{solo_numeros[2:]}"
        
            chat_id = f"{solo_numeros}@c.us"

            #pregunta = "¿Qué te pareció el informe técnico?"
            #opciones = [
            #{"optionName": "Excelente"},
            #{"optionName": "Tiene dudas"},
            #{"optionName": "Agendar llamada"}
            #]
            #response = greenAPI.sending.sendPoll(
            #chatId=chat_id,
            #message=pregunta,
            #options=opciones,
            #multipleAnswers=False
            #)
            try:
                
                ultimoMensaje = TablaEnvios.objects.filter(prospecto=prospecto).order_by('-numeroEnvio').first()
                mensaje = Mensaje.objects.get(numEnvio=(ultimoMensaje.numeroEnvio+1))

                preguntas_db = Preguntas.objects.filter(mensaje=mensaje)
                responseAsunto = greenAPI.sending.sendMessage(chatId=chat_id, message=mensaje.asunto)
                responseCuerpo = greenAPI.sending.sendMessage(chatId=chat_id, message=mensaje.cuerpo)
                if mensaje.encuesta:                                             
                    for p in preguntas_db:
                        pregunta_texto = p.pregunta
                        respuestas_db = p.respuesta_set.all()

                        opciones = []
                        for r in respuestas_db:
                            opciones.append({"optionName": r.respuesta})

                        if opciones:
                            responseEnecuesta = greenAPI.sending.sendPoll(
                                chatId=chat_id,
                                message=pregunta_texto,
                                options=opciones,
                                multipleAnswers=False
                            )
          
                if responseAsunto.code == 200:
                    print(f"WhatsApp enviado con éxito a {chat_id}")
                    ultimoMensaje = TablaEnvios.objects.filter(prospecto=prospecto).order_by('-numeroEnvio').first()

                    TablaEnvios.objects.create(prospecto=prospecto,
                    medioDeContacto=prospecto.medioDeContacto,
                    numeroEnvio=ultimoMensaje.numeroEnvio+1)
                else:
                    print(f"Error al enviar: {responseEnecuesta.error}")           
            except Exception as e:
                print(f"Error al enviar WhatsApp: {e}")
    return redirect('Envios:EnviosIndex')