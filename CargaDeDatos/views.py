from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import user_passes_test,login_required

from django.http import JsonResponse
import numpy as np
import pandas as pd

from django.http import JsonResponse
from db.models import *


def CargaDeDatos(request):

    
    return render(request, 'CargaDeDatos/cargaDeDatosLayout.html')




def CargarAServidor(request):
    if request.method == 'POST':
        archivo = request.FILES.get('archivo_csv')
        
        if not archivo:
            return JsonResponse({'error': 'No hay archivo', 'color': '#ff0000'}, status=400)

        if archivo.name.lower().endswith('.csv'):
            try:
                df = pd.read_csv(archivo, header=None, encoding='utf-8-sig')
                
                df = df.replace({np.nan: None})

                reemplazos = {
                    'física_con_actividad_económica': 'física',
                    'moral_legalmente_constituida': 'moral'
                }
                df = df.replace(reemplazos)

                df[0] = pd.to_datetime(df[0], dayfirst=True).dt.strftime('%Y-%m-%d')

                datos_finales = df.values.tolist()

                for i, dato in enumerate(datos_finales):
                    try:
                        if Prospecto.objects.filter(nombreCompleto=dato[4]).exists():
                            continue
                        else:    
                            Prospecto.objects.create(
                                fechaCapturado=dato[0],
                                tipoPersona=dato[1],
                                servicioInteresado=dato[2],
                                medioDeContacto=dato[3],
                                nombreCompleto=dato[4],
                                email=dato[5],
                                telefono=str(dato[6]) if dato[6] else "",
                                ciudad=dato[7],
                                direccion="",
                                comentario=str(dato[8]) if dato[8] else "",
                                status="Nuevo",
                                empresa="",
                                montoSolicitado=0,
                                ejecutivoAsignado=None
                            )
                    except Exception as e:
                        print(f"Error en la fila {i}: {e}")
                        print(f"Datos de la fila: {dato}")

                return JsonResponse({
                    'status': 'ok',
                    'mensaje': 'Archivo procesado y guardado',
                    'color': '#27bd31',
                    'datos': len(df)
                })
                
            except Exception as e:
                import traceback
                print(traceback.format_exc())
                return JsonResponse({'error': str(e), 'color': '#ff0000'}, status=500)
        
        return JsonResponse({'error': 'Formato no soportado', 'color': '#ff0000'}, status=400)

    return JsonResponse({'error': 'Metodo no permitido'}, status=405)


