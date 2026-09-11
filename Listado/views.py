from email.message import EmailMessage
import smtplib

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from db.models import *
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import user_passes_test,login_required

def index(request):

    return render(request, 'Listado/listadoLayout.html')

