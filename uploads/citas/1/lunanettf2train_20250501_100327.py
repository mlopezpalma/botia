"""
Modelo de predicción de coordenadas lunares con TensorFlow 2
Adaptado para ser compatible con el enfoque VGG22 para imágenes lunares

Este script está adaptado para usar un enfoque similar al código de referencia
donde:
- Se redimensionan las imágenes a 224x224
- Se convierten a escala de grises
- Se aplica un factor de escala y desplazamiento específico a las coordenadas
"""

import os
import re
import sys
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from PIL import Image
import time

# Configuración de variables de entorno para resolver problemas de compatibilidad
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Reducir mensajes de TensorFlow
# Desactivar GPU si es necesario (descomentar si hay problemas con la GPU)
# os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# Configuración global
DEBUG = True
IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 20
LEARNING_RATE = 0.0001

# Configuración específica para coordenadas lunares según el código de referencia
YSCALE = [60, 25]  # Escala para lat, lon
YOFFSET = [30, -10]  # Desplazamiento para lat, lon

def extract_coordinates_from_filename(filename):
    """
    Extrae las coordenadas del nombre del archivo utilizando múltiples patrones.
    Adaptado para identificar formatos similares a los del código de referencia.
    """
    # Lista de patrones a probar en orden
    patterns = [
        # Patrón estándar: lat seguido de números, luego lon seguido de números
        {'regex': r'lat([-\d.]+)_lon([-\d.]+)', 'invert': False},
        
        # Formatos específicos para imágenes lunares basados en el código de referencia
        {'regex': r'N(\d+)_E(\d+)', 'invert': False},  # Norte/Este: N045_E030
        {'regex': r'N(\d+)_W(\d+)', 'invert': False, 'west_neg': True},  # Norte/Oeste: N045_W030
        {'regex': r'S(\d+)_E(\d+)', 'invert': False, 'south_neg': True},  # Sur/Este: S045_E030
        {'regex': r'S(\d+)_W(\d+)', 'invert': False, 'south_neg': True, 'west_neg': True},  # Sur/Oeste: S045_W030
        
        # Patrones para formatos con W y E en el nombre (nomenclatura lunar común)
        {'regex': r'W(\d+)_E(\d+)_N(\d+)_N(\d+)', 'special': 'region'},  # Region: W030_E030_N000_N045
        {'regex': r'W(\d+)_E(\d+)_S(\d+)_S(\d+)', 'special': 'region_south'},  # Region sur
        
        # Variaciones de formato lat/lon generales
        {'regex': r'lat[-_\s]*([-\d.]+).*lon[-_\s]*([-\d.]+)', 'invert': False},
        {'regex': r'lon[-_\s]*([-\d.]+).*lat[-_\s]*([-\d.]+)', 'invert': True},
        
        # Cualquier patrón numérico que podría representar coordenadas
        {'regex': r'([-+]?\d*\.\d+|[-+]?\d+)[_\s,.-]([-+]?\d*\.\d+|[-+]?\d+)', 'invert': False}
    ]
    
    # Probar cada patrón
    for pattern in patterns:
        match = re.search(pattern['regex'], filename)
        if match:
            try:
                # Manejo de formatos especiales
                if pattern.get('special') == 'region':
                    # Formato W030_E030_N000_N045 - tomamos el punto medio
                    w_val = float(match.group(1))
                    e_val = float(match.group(2))
                    n1_val = float(match.group(3))
                    n2_val = float(match.group(4))
                    
                    # Calcular centro de la región
                    lon = (e_val - w_val) / 2 - w_val  # Longitud media, oeste negativo
                    lat = (n1_val + n2_val) / 2        # Latitud media
                    
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        return lat, lon
                elif pattern.get('special') == 'region_south':
                    # Similar al anterior pero para regiones sur
                    w_val = float(match.group(1))
                    e_val = float(match.group(2))
                    s1_val = float(match.group(3))
                    s2_val = float(match.group(4))
                    
                    lon = (e_val - w_val) / 2 - w_val
                    lat = -1 * (s1_val + s2_val) / 2   # Sur es negativo
                    
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        return lat, lon
                else:
                    # Procesamiento normal
                    if pattern.get('invert'):
                        lon, lat = float(match.group(1)), float(match.group(2))
                    else:
                        lat, lon = float(match.group(1)), float(match.group(2))
                    
                    # Ajustes para nomenclatura lunar
                    if pattern.get('south_neg'):
                        lat = -lat  # Sur es negativo
                    if pattern.get('west_neg'):
                        lon = -lon  # Oeste es negativo
                    
                    # Verificar que las coordenadas son razonables
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        return lat, lon
            except (ValueError, IndexError):
                continue
    
    if DEBUG:
        print(f"No se pudieron extraer coordenadas de: {filename}")
    return None, None

def preprocess_lunar_image(img_path):
    """
    Preprocesa una imagen lunar de acuerdo con el enfoque del código de referencia.
    """
    try:
        # Cargar imagen y convertir a escala de grises (modo 'LA')
        image = Image.open(img_path).convert('LA').resize(IMAGE_SIZE)
        
        # Convertir a array numpy y normalizar
        img_array = np.asarray(image)
        gray_img = img_array[:, :, 0] / 255.0  # Tomar solo el canal de intensidad
        
        # Normalizar al máximo
        gray_img = gray_img / np.max(gray_img)
        
        # Preparar formato para el modelo (añadir dimensiones de batch y canal)
        processed_img = np.zeros((1, IMAGE_SIZE[0], IMAGE_SIZE[1], 1), dtype=np.float32)
        processed_img[0, :, :, 0] = gray_img
        
        return processed_img[0]  # Retornar sin la dimensión de batch
    except Exception as e:
        print(f"Error al preprocesar imagen {img_path}: {e}")
        return None

def load_dataset(directory):
    """
    Carga las imágenes y coordenadas desde el directorio utilizando el preprocesamiento específico.
    """
    images = []
    coordinates = []
    filenames = []
    
    print(f"Buscando imágenes en: {directory}")
    if not os.path.exists(directory):
        print(f"¡Error! El directorio {directory} no existe.")
        return [], [], []
    
    file_count = 0
    valid_count = 0
    
    for filename in os.listdir(directory):
        if filename.lower().endswith(('.jpg', '.png', '.jpeg', '.tif', '.tiff')):
            file_count += 1
            lat, lon = extract_coordinates_from_filename(filename)
            
            if lat is not None and lon is not None:
                # Preprocesar imagen
                img_path = os.path.join(directory, filename)
                processed_img = preprocess_lunar_image(img_path)
                
                if processed_img is not None:
                    valid_count += 1
                    images.append(processed_img)
                    coordinates.append([lat, lon])
                    filenames.append(filename)
                    
                    if DEBUG and valid_count <= 5:
                        print(f"Imagen cargada: {filename}, Coordenadas: lat={lat}, lon={lon}")
    
    print(f"Total de archivos de imagen encontrados: {file_count}")
    print(f"Imágenes con coordenadas válidas: {valid_count}")
    
    return np.array(images) if images else [], np.array(coordinates) if coordinates else [], filenames

def create_vgg22_model():
    """
    Crea un modelo VGG22 similar al del código de referencia.
    """
    try:
        import tensorflow as tf
        from tensorflow import keras
        from tensorflow.keras import layers, models, applications
    except ImportError:
        print("Error: No se pudo importar TensorFlow. Verifica tu instalación.")
        return None
    
    # Intentar cargar el modelo VGG16 base
    try:
        # Modificar la capa de entrada para trabajar con imágenes en escala de grises (1 canal)
        inputs = keras.Input(shape=(224, 224, 1))
        
        # Expandir a 3 canales para compatibilidad con VGG16
        x = layers.Conv2D(3, (1, 1), padding='same')(inputs)
        
        # Cargar VGG16 sin la parte superior
        vgg16 = applications.VGG16(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
        
        # Congelar capas del VGG16
        for layer in vgg16.layers:
            layer.trainable = False
        
        # Conectar nuestra entrada con el VGG16
        x = vgg16(x)
        
        # Añadir capas adicionales para crear "VGG22"
        x = layers.Flatten()(x)
        x = layers.Dense(4096, activation='relu')(x)
        x = layers.Dropout(0.5)(x)
        x = layers.Dense(4096, activation='relu')(x)
        x = layers.Dropout(0.5)(x)
        x = layers.Dense(1024, activation='relu')(x)
        x = layers.Dropout(0.5)(x)
        x = layers.Dense(512, activation='relu')(x)
        x = layers.Dropout(0.3)(x)
        x = layers.Dense(256, activation='relu')(x)
        x = layers.Dropout(0.3)(x)
        x = layers.Dense(2)(x)  # Salida: 2 valores (lat, lon)
        
        model = keras.Model(inputs=inputs, outputs=x)
        
        # Compilar el modelo
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
            loss='mse',
            metrics=['mae']
        )
        
        # Mostrar resumen
        model.summary()
        
        return model
    except Exception as e:
        print(f"Error al crear el modelo VGG22: {e}")
        
        # Si falla, intentar con un modelo más simple
        try:
            print("Intentando crear un modelo alternativo...")
            
            model = models.Sequential([
                layers.Conv2D(32, (3, 3), activation='relu', padding='same', input_shape=(224, 224, 1)),
                layers.MaxPooling2D((2, 2)),
                layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
                layers.MaxPooling2D((2, 2)),
                layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
                layers.MaxPooling2D((2, 2)),
                layers.Conv2D(256, (3, 3), activation='relu', padding='same'),
                layers.MaxPooling2D((2, 2)),
                layers.Flatten(),
                layers.Dense(512, activation='relu'),
                layers.Dropout(0.5),
                layers.Dense(256, activation='relu'),
                layers.Dropout(0.3),
                layers.Dense(2)  # Salida: lat, lon
            ])
            
            model.compile(
                optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
                loss='mse',
                metrics=['mae']
            )
            
            return model
        except Exception as e2:
            print(f"Error al crear modelo alternativo: {e2}")
            return None

def normalize_coordinates(coordinates):
    """
    Normaliza las coordenadas para el entrenamiento usando los factores del código de referencia.
    """
    if len(coordinates) == 0:
        return [], np.array(YOFFSET), np.array(YSCALE)
    
    # Aplicar transformación inversa a la del código de referencia
    # En el código original: predQ = prediction * yscale - yoffset
    # Entonces: prediction = (predQ + yoffset) / yscale
    normalized = (coordinates + np.array(YOFFSET)) / np.array(YSCALE)
    
    return normalized, np.array(YOFFSET), np.array(YSCALE)

def denormalize_coordinates(normalized, yoffset, yscale):
    """
    Desnormaliza las coordenadas utilizando los factores de escala y desplazamiento.
    """
    # Aplicar la transformación directa
    return normalized * yscale - yoffset

def train_lunar_coordinates_model(data_directory):
    """
    Función principal para entrenar el modelo, adaptada para usar el enfoque del código de referencia.
    """
    # 1. Cargar datos
    print("\n=== Cargando dataset... ===")
    images, coordinates, filenames = load_dataset(data_directory)
    
    if len(images) == 0:
        print("No se encontraron imágenes con coordenadas válidas.")
        return None, None, None
    
    print(f"Dataset cargado: {len(images)} imágenes")
    
    # Mostrar estadísticas
    if len(coordinates) > 0:
        print("\nEstadísticas de coordenadas:")
        print(f"Rango latitud: {np.min(coordinates[:, 0]):.2f} a {np.max(coordinates[:, 0]):.2f}")
        print(f"Rango longitud: {np.min(coordinates[:, 1]):.2f} a {np.max(coordinates[:, 1]):.2f}")
    
    # 2. Normalizar coordenadas usando los factores específicos
    norm_coords, yoffset, yscale = normalize_coordinates(coordinates)
    print(f"\nFactores de normalización:")
    print(f"Escala (yscale): {yscale}")
    print(f"Desplazamiento (yoffset): {yoffset}")
    
    # 3. Dividir dataset
    if len(images) < 3:
        print("Conjunto de datos demasiado pequeño para dividir.")
        return None, None, None
        
    X_train, X_temp, y_train, y_temp = train_test_split(images, norm_coords, test_size=0.3, random_state=42)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)
    
    print(f"\nConjunto de entrenamiento: {len(X_train)} imágenes")
    print(f"Conjunto de validación: {len(X_val)} imágenes")
    print(f"Conjunto de prueba: {len(X_test)} imágenes")
    
    # 4. Crear modelo VGG22
    model = create_vgg22_model()
    if model is None:
        print("Error al crear el modelo.")
        return None, None, None
    
    # 5. Configurar callbacks
    try:
        import tensorflow as tf
        
        callbacks = []
        
        # Early stopping
        early_stopping = tf.keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=5,
            restore_best_weights=True
        )
        callbacks.append(early_stopping)
        
        # Checkpoint
        model_checkpoint = tf.keras.callbacks.ModelCheckpoint(
            'best_lunar_model.h5',
            monitor='val_loss',
            save_best_only=True,
            verbose=1
        )
        callbacks.append(model_checkpoint)
    except Exception as e:
        print(f"Error al configurar callbacks: {e}")
        callbacks = []
    
    # 6. Entrenar modelo
    print("\n=== Iniciando entrenamiento... ===")
    try:
        history = model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            batch_size=min(BATCH_SIZE, len(X_train)),
            epochs=EPOCHS,
            callbacks=callbacks,
            verbose=1
        )
    except Exception as e:
        print(f"Error durante el entrenamiento: {e}")
        return None, None, None
    
    # 7. Evaluar modelo
    print("\n=== Evaluando modelo... ===")
    try:
        loss, mae = model.evaluate(X_test, y_test, verbose=1)
        print(f"Loss en test: {loss:.4f}")
        print(f"MAE en test: {mae:.4f}")
    except Exception as e:
        print(f"Error durante la evaluación: {e}")
        loss, mae = 0, 0
    
    # 8. Hacer predicciones
    try:
        pred_norm = model.predict(X_test)
        pred_coords = denormalize_coordinates(pred_norm, yoffset, yscale)
        true_coords = denormalize_coordinates(y_test, yoffset, yscale)
        
        # Mostrar ejemplos
        if len(true_coords) > 0:
            print("\nEjemplos de predicciones:")
            n_examples = min(5, len(true_coords))
            for i in range(n_examples):
                print(f"Real: (lat={true_coords[i, 0]:.4f}, lon={true_coords[i, 1]:.4f}) | "
                      f"Predicción: (lat={pred_coords[i, 0]:.4f}, lon={pred_coords[i, 1]:.4f})")
    except Exception as e:
        print(f"Error al hacer predicciones: {e}")
    
    # 9. Visualizar resultados
    try:
        plt.figure(figsize=(12, 5))
        
        # Gráfico de pérdida
        plt.subplot(1, 2, 1)
        plt.plot(history.history['loss'], label='train')
        plt.plot(history.history['val_loss'], label='validation')
        plt.title('Pérdida durante entrenamiento')
        plt.xlabel('Época')
        plt.ylabel('Pérdida (MSE)')
        plt.legend()
        
        # Gráfico de error absoluto medio
        plt.subplot(1, 2, 2)
        plt.plot(history.history['mae'], label='train')
        plt.plot(history.history['val_mae'], label='validation')
        plt.title('Error Absoluto Medio')
        plt.xlabel('Época')
        plt.ylabel('MAE')
        plt.legend()
        
        plt.tight_layout()
        plt.savefig('entrenamiento.png')
        print("Gráfico de entrenamiento guardado como 'entrenamiento.png'")
        
        # Mostrar predicciones vs realidad
        plt.figure(figsize=(10, 8))
        plt.scatter(true_coords[:, 0], true_coords[:, 1], c='blue', alpha=0.5, label='Coordenadas reales')
        plt.scatter(pred_coords[:, 0], pred_coords[:, 1], c='red', alpha=0.5, label='Coordenadas predichas')
        
        # Conectar puntos correspondientes
        for i in range(len(true_coords)):
            plt.plot([true_coords[i, 0], pred_coords[i, 0]], 
                     [true_coords[i, 1], pred_coords[i, 1]], 
                     'k-', alpha=0.2)
        
        plt.title("Coordenadas Reales vs Predichas")
        plt.xlabel('Latitud')
        plt.ylabel('Longitud')
        plt.legend()
        plt.grid(True)
        plt.savefig('predicciones_coordenadas.png')
        
        try:
            plt.show()
        except:
            pass
    except Exception as e:
        print(f"Error al visualizar resultados: {e}")
    
    # 10. Guardar modelo y parámetros
    try:
        model.save('vgg22_lunar_model.h5')
        print("Modelo guardado como 'vgg22_lunar_model.h5'")
        
        # Guardar parámetros de normalización
        np.savez('normalization_params.npz', 
                yoffset=yoffset, 
                yscale=yscale)
        print("Parámetros de normalización guardados en 'normalization_params.npz'")
    except Exception as e:
        print(f"Error al guardar el modelo: {e}")
    
    return model, yoffset, yscale

def predict_coords_from_image(model, image_path, yoffset, yscale, plot=True):
    """
    Predice coordenadas a partir de una imagen lunar, similar al método main() del código de referencia.
    """
    if not os.path.exists(image_path):
        print(f"No se encontró la imagen: {image_path}")
        return None
    
    try:
        # Preprocesar imagen como en el código de referencia
        image = Image.open(image_path).convert('LA').resize((224, 224))
        img = np.asarray(image)
        img = img[:, :, 0] / 255
        img = img/np.max(img)
        test_images = np.zeros((1, 224, 224, 1), dtype=np.float32)
        test_images[0, :, :, 0] = img
        
        # Predecir
        prediction = model.predict(test_images)
        
        # Aplicar escala y desplazamiento
        predQ = prediction * yscale - yoffset
        
        # Mostrar predicción
        lat, lon = predQ[0]
        print(f"\nCoordenadas predichas para {image_path}:")
        print(f"Latitud: {lat:.4f}")
        print(f"Longitud: {lon:.4f}")
        
        # Mostrar imagen con predicción
        if plot:
            plt.figure(figsize=(8, 8))
            plt.imshow(test_images[0, :, :, 0], cmap='gray')
            plt.title(f'Predicción: Lat={lat:.4f}, Lon={lon:.4f}')
            plt.colorbar(label='Intensidad')
            
            # Guardar imagen
            plt.savefig('prediccion.png')
            
            try:
                plt.show()
            except:
                pass
        
        return (lat, lon)
    except Exception as e:
        print(f"Error al predecir coordenadas: {e}")
        return None

def main():
    print("\n========================================================")
    print("  MODELO VGG22 PARA PREDICCIÓN DE COORDENADAS LUNARES")
    print("========================================================\n")
    
    # Verificar TensorFlow
    try:
        import tensorflow as tf
        print(f"TensorFlow versión: {tf.__version__}")
    except ImportError:
        print("Error: TensorFlow no está instalado correctamente.")
        print("Instálalo con: pip install tensorflow==2.10.0 protobuf==3.19.6")
        sys.exit(1)
    
    # Obtener directorio de imágenes
    if len(sys.argv) > 1:
        data_directory = sys.argv[1]
    else:
        default_dir = "datos_lunares"
        data_directory = input(f"Ingresa la ruta al directorio de imágenes lunares [{default_dir}]: ").strip()
        if not data_directory:
            data_directory = default_dir
    
    # Entrenar modelo
    model, yoffset, yscale = train_lunar_coordinates_model(data_directory)
    
    if model is None:
        print("\nNo se pudo entrenar el modelo. Verifica los datos y dependencias.")
        sys.exit(1)
    
    # Ofrecer probar el modelo con imágenes
    while True:
        test_option = input("\n¿Deseas probar el modelo con una imagen? (s/n): ").strip().lower()
        if test_option != 's':
            break
            
        test_image = input("Ingresa la ruta a una imagen lunar de prueba: ").strip()
        if test_image:
            predict_coords_from_image(model, test_image, yoffset, yscale)
    
    print("\n========================================================")
    print("  PROCESO COMPLETADO")
    print("========================================================")

if __name__ == "__main__":
    main()
