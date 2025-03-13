# Bot de Agendamiento de Citas Legales

Este bot utiliza inteligencia artificial para agendar citas legales a través de una interfaz de chat web.

## Características

- Procesamiento de lenguaje natural para entender las solicitudes
- Múltiples tipos de reuniones (presencial, videoconferencia, telefónica)
- Integración con Google Calendar
- Envío de confirmaciones por correo electrónico
- Interfaz web responsive

## Instalación

1. Clonar el repositorio
2. Crear un entorno virtual: `python -m venv botia_env`
3. Activar el entorno: `source botia_env/bin/activate` (Linux/Mac) o `botia_env\Scripts\activate` (Windows)
4. Instalar dependencias: `pip install -r requirements.txt`
5. Descargar modelo de spaCy: `python -m spacy download es_core_news_md`
6. Ejecutar: `python app.py`

## Estructura del Proyecto

- `app.py`: Aplicación principal
- `config.py`: Configuraciones
- `models/`: Modelos para el procesamiento de lenguaje
- `handlers/`: Gestores de la conversación y servicios
- `utils/`: Utilidades
- `static/`: Archivos estáticos

## Uso

Visita `http://localhost:5000` en tu navegador para interactuar con el bot.
