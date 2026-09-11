from email.message import EmailMessage
import smtplib

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from CargaDeDatos.forms import ProspectoForm
from db.models import *
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib.auth.decorators import user_passes_test,login_required

def InsigthsIndex(request):
    ejecutivos = User.objects.filter(roles='Ejecutivo').annotate(
    total_prospectos=Count('prospectos_asignados') # Usa el related_name de tu modelo
)    
    registros = Prospecto.objects.all().order_by('-id')
  
    context = {'registros':registros,
               'ejecutivos':ejecutivos}
    return render(request, 'Insigths/InsigthsLayout.html',context)