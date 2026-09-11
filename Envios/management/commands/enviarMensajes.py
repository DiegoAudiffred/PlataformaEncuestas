import re
import smtplib
from email.message import EmailMessage
from django.core.management.base import BaseCommand
from django.utils import timezone
from db.models import Prospecto, TablaEnvios, Mensaje, Preguntas
from whatsapp_api_client_python import API

class Command(BaseCommand):
    help = 'Procesa y envia correos y whatsapps automatizados segun el calendario de 15 dias'

    def handle(self, *args, **options):
        hoy = timezone.now()
        prospectos = Prospecto.objects.filter(checkmarck=True)
        self.stdout.write(f"Se encontraron {prospectos.count()} prospectos con checkmarck=True.")
        for prospecto in prospectos:
            ultimo_envio_obj = TablaEnvios.objects.filter(prospecto=prospecto).order_by('-numeroEnvio').first()
            if not ultimo_envio_obj:
                siguiente_envio = 1
                self.procesar_envio(prospecto, siguiente_envio)
            else:
                dias_transcurridos = (hoy - ultimo_envio_obj.fecha_envio).days
                if dias_transcurridos >= 4:
                    siguiente_envio = ultimo_envio_obj.numeroEnvio + 1
                    self.procesar_envio(prospecto, siguiente_envio)

    def procesar_envio(self, prospecto, numero_envio):
        mensaje_plantilla = Mensaje.objects.filter(numEnvio=numero_envio).first()
        
        if not mensaje_plantilla:
            self.stdout.write(f"Envio saltado: No existe plantilla de Mensaje para el numeroEnvio {numero_envio}")
            return

        if prospecto.medioDeContacto == "correo_electrónico" and prospecto.email:
            self.ejecutar_envio_correo(prospecto, mensaje_plantilla, numero_envio)
            
        elif prospecto.medioDeContacto == "whatsapp" and prospecto.telefono:
            self.ejecutar_envio_whatsapp(prospecto, mensaje_plantilla, numero_envio)

    def ejecutar_envio_correo(self, prospecto, mensaje, numero_envio):
        preguntas_db = Preguntas.objects.filter(mensaje=mensaje)
        asunto = mensaje.asunto
        
        cuerpo_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">
                    <h2 style="color: #2c3e50;">Actualización de status del UCG</h2>
                    <p>Estimado <strong>{prospecto.nombreCompleto}</strong> </p>
                    <p>{mensaje.cuerpo}</p>
        """
        
        if mensaje.encuesta:
            for p in preguntas_db:
                pregunta_texto = p.pregunta
                respuestas_db = p.respuesta_set.all()
                cuerpo_html += f"<p>{pregunta_texto}</p>"
                for r in respuestas_db:
                    cuerpo_html += f"<p>{r.respuesta}</p>"

        cuerpo_html += """
                </div>
            </body>
        </html>
        """

        SMTP_HOST = "ucg.com.mx"
        SMTP_PORT = 587
        USUARIO = "centrodenegocios@ucg.com.mx"
        CONTRASENA = "UcG911_@!#"

        email_msg = EmailMessage()
        email_msg["From"] = USUARIO
        email_msg["To"] = prospecto.email
        email_msg["Subject"] = asunto
        email_msg.add_alternative(cuerpo_html, subtype="html")

        try:
            servidor = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            servidor.starttls()
            servidor.login(USUARIO, CONTRASENA)
            servidor.send_message(email_msg)
            servidor.quit()
            
            self.stdout.write(f"Correo enviado correctamente a {prospecto.email}")
            
            if prospecto.status == "NUEVO":
                prospecto.status = "ENVIADO"
                prospecto.save()

            TablaEnvios.objects.create(
                prospecto=prospecto,
                medioDeContacto=prospecto.medioDeContacto,
                numeroEnvio=numero_envio
            )
        except Exception as e:
            self.stdout.write(f"Error al enviar correo a {prospecto.email}: {e}")

    def ejecutar_envio_whatsapp(self, prospecto, mensaje, numero_envio):
        greenAPI = API.GreenApi(
            "7107614191", 
            "efd7424742c442fe915fb51c101f26c0fb16420c8fbc44bc80"
        )
        
        solo_numeros = re.sub(r'\D', '', str(prospecto.telefono))
        if not solo_numeros.startswith('52'):
            solo_numeros = f"521{solo_numeros}"
        elif solo_numeros.startswith('52') and not solo_numeros.startswith('521'):
            solo_numeros = f"521{solo_numeros[2:]}"
        
        chat_id = f"{solo_numeros}@c.us"

        try:
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
                        greenAPI.sending.sendPoll(
                            chatId=chat_id,
                            message=pregunta_texto,
                            options=opciones,
                            multipleAnswers=False
                        )

            if responseAsunto.code == 200:
                self.stdout.write(f"WhatsApp enviado con éxito a {chat_id}")
                TablaEnvios.objects.create(
                    prospecto=prospecto,
                    medioDeContacto=prospecto.medioDeContacto,
                    numeroEnvio=numero_envio
                )
            else:
                self.stdout.write(f"Error reportado por GreenAPI al enviar a {chat_id}")
        except Exception as e:
            self.stdout.write(f"Error al enviar WhatsApp a {chat_id}: {e}")