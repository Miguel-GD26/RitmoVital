# classifier/views.py

from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import tensorflow as tf
import numpy as np
import pandas as pd
import os
import random
import base64
from io import BytesIO
import matplotlib
matplotlib.use('Agg') # Usar un backend que no requiera GUI, crucial para servidores
import matplotlib.pyplot as plt
import json

# --- Carga del modelo y datos (se ejecuta una sola vez al iniciar el servidor) ---
MODEL_PATH = os.path.join(settings.BASE_DIR, 'classifier/ecg_classifier_model.h5')
TEST_DATA_PATH = os.path.join(settings.BASE_DIR, 'classifier/mitbih_test_data.csv')

model = None
test_data = None

try:
    # Desactivar GPU si no está configurada, para evitar errores
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
    
    print("Cargando modelo y datos de prueba...")
    model = tf.keras.models.load_model(MODEL_PATH)
    test_data = pd.read_csv(TEST_DATA_PATH, header=None)
    print("Modelo y datos cargados exitosamente.")

    # --- "CALENTAMIENTO" DEL MODELO PARA PREDICCIONES RÁPIDAS ---
    # 1. Creamos una entrada falsa con la forma correcta (1 muestra, 187 puntos de tiempo, 1 canal)
    dummy_input = np.zeros((1, 187, 1))
    # 2. Realizamos una predicción para forzar la inicialización de TensorFlow.
    print("Realizando 'calentamiento' del modelo...")
    model.predict(dummy_input, verbose=0) # verbose=0 para mantener la consola limpia
    print("Modelo 'caliente' y listo para predicciones rápidas.")
    # --- FIN DE LA SOLUCIÓN DE LA DEMORA ---

except Exception as e:
    print(f"Error crítico al cargar archivos o al calentar el modelo: {e}")


# Mapeo de clases para mostrar resultados legibles
LABELS_MAP = {
    0: "Latido Normal (N)",
    1: "Contracción Supraventricular (S)",
    2: "Contracción Ventricular (V)",
    3: "Latido de Fusión (F)",
    4: "Latido No Clasificado (Q)"
}

def plot_to_base64_dark(signal):
    """
    Convierte un gráfico de matplotlib a una imagen en base64, ESTILIZADO para el tema oscuro.
    """
    # Parámetros de estilo para coincidir con el frontend
    background_color = '#12121e'
    card_color = '#161626'
    text_color = '#f0f0f0'
    grid_color = (1.0, 1.0, 1.0, 0.1)  # Formato RGBA como tupla para Matplotlib
    line_color = '#667eea'

    # Creación de la figura con el estilo oscuro
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor(background_color)
    ax.set_facecolor(card_color)

    # Graficar la señal
    ax.plot(signal, color=line_color, linewidth=2)

    # Estilizar los textos y ejes
    ax.set_title('Señal de ECG a Clasificar', color=text_color, fontsize=14, weight='bold')
    ax.set_xlabel('Muestras de Tiempo', color=text_color, fontsize=10)
    ax.set_ylabel('Amplitud (mV)', color=text_color, fontsize=10)

    # Estilizar los bordes (spines) y los números de los ejes (ticks)
    ax.tick_params(axis='x', colors=text_color)
    ax.tick_params(axis='y', colors=text_color)
    for spine in ax.spines.values():
        spine.set_color(grid_color)

    # Añadir una rejilla sutil
    ax.grid(True, color=grid_color, linestyle='--', linewidth=0.5, alpha=0.7)

    plt.tight_layout()
    
    buf = BytesIO()
    # Guardar la figura con fondo transparente para que se vea el del contenedor
    plt.savefig(buf, format='png', facecolor='none', edgecolor='none')
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode('utf-8')


@csrf_exempt  # Desactiva la protección CSRF para esta vista de API
def classify_api(request):
    """API endpoint para la clasificación de ECG."""
    
    # --- Lógica para obtener una nueva muestra (petición GET) ---
    if request.method == 'GET':
        if test_data is not None:
            random_index = random.randint(0, len(test_data) - 1)
            ecg_signal = test_data.iloc[random_index, :187].values
            
            response_data = {
                'ecg_plot': plot_to_base64_dark(ecg_signal),
                'beat_index': random_index
            }
            return JsonResponse(response_data)
        else:
            return JsonResponse({'error': 'Los datos de prueba no están disponibles.'}, status=500)

    # --- Lógica para clasificar una muestra (petición POST) ---
    if request.method == 'POST':
        try:
            # Leer el cuerpo de la petición JSON
            data = json.loads(request.body)
            beat_index = data.get('beat_index')
            
            if beat_index is None:
                return JsonResponse({'error': 'Falta beat_index en la petición.'}, status=400)

            # Obtener datos del DataFrame
            ecg_signal = test_data.iloc[beat_index, :187].values
            true_label_index = int(test_data.iloc[beat_index, 187])
            
            # Pre-procesar para el modelo
            processed_signal = ecg_signal.reshape(1, 187, 1)
            
            # Realizar la predicción
            predictions = model.predict(processed_signal)
            
            # Procesar los resultados
            predicted_class_index = np.argmax(predictions[0])
            confidence = np.max(predictions[0]) * 100
            
            # Preparar la respuesta JSON
            response_data = {
                'prediction': LABELS_MAP.get(predicted_class_index, "Desconocido"),
                'confidence': f"{confidence:.2f}%",
                'confidence_percent': int(confidence),
                'true_label': LABELS_MAP.get(true_label_index, "Desconocido"),
                'is_correct': bool(predicted_class_index == true_label_index) # Convertir a bool nativo de Python
            }
            return JsonResponse(response_data)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    # Si la petición no es ni GET ni POST
    return JsonResponse({'error': 'Método no permitido.'}, status=405)