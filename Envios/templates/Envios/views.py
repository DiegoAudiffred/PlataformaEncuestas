from django.http import JsonResponse
from django.shortcuts import render
from db.models import *
from django.core.paginator import Paginator
from django.db.models import Q

def EnviosIndex(request):
    registros = Prospecto.objects.filter(checkmarck=True)
    context = {'registros': registros}
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


def mandarCorreos(request): 
    return render(request, 'Envios/mandarCorreos.html')