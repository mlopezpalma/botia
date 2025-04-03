# BotIA - Bot de Agendamiento de Citas Legales

BotIA es un asistente virtual inteligente diseñado para la gestión y agendamiento de citas legales. Utiliza procesamiento de lenguaje natural para entender las solicitudes de los usuarios y facilitarles la programación de consultas legales a través de diferentes canales de comunicación.

## Características Principales

- **Procesamiento de lenguaje natural**: Entiende solicitudes en lenguaje natural gracias a spaCy y NLTK
- **Múltiples tipos de reuniones**: 
  - Presencial (30 minutos)
  - Videoconferencia (25 minutos)
  - Telefónica (10 minutos)
- **Integración con calendarios**: Sincronización con Google Calendar
- **Notificaciones automatizadas**: Envío de confirmaciones por correo electrónico
- **Interfaz web adaptable**: Experiencia de usuario optimizada para diferentes dispositivos
- **Integración con WhatsApp**: Disponible a través de la API de Twilio

## Requisitos Técnicos

- Python 3.8 o superior
- Dependencias principales:
  - Flask 2.0.1
  - spaCy 3.4.1
  - NLTK 3.6.5
  - Numpy 1.21.2
  - Scikit-learn 1.0.1

## Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/tuusuario/botia.git
   cd botia
   ```

2. **Crear un entorno virtual**
   ```bash
   python -m venv botia_env
   ```

3. **Activar el entorno virtual**
   - En Windows:
     ```bash
     botia_env\Scripts\activate
     ```
   - En Linux/Mac:
     ```bash
     source botia_env/bin/activate
     ```

4. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

5. **Descargar el modelo de spaCy**
   ```bash
   python -m spacy download es_core_news_md
   ```

6. **Ejecutar la aplicación**
   ```bash
   python app.py
   ```

## Estructura del Proyecto

```
botia/
│
├── app.py                 # Aplicación principal y endpoints
├── config.py              # Configuraciones globales
├── whatsapp_integration.py # Integración con WhatsApp mediante Twilio
│
├── models/                # Modelos de procesamiento de lenguaje
│   ├── __init__.py
│   ├── intent_model.py    # Modelo de identificación de intenciones
│   └── data_extraction.py # Extracción de datos (fechas, horas, etc.)
│
├── handlers/              # Gestores de la conversación y servicios
│   ├── __init__.py
│   ├── conversation.py    # Manejo de conversación y flujo de diálogo
│   ├── calendar_service.py # Servicios de calendario
│   └── email_service.py   # Servicios de correo electrónico
│
├── utils/                 # Utilidades
│   ├── __init__.py
│   └── helpers.py         # Funciones auxiliares
│
├── static/                # Archivos estáticos
│   └── chat-widget.js     # Widget de chat para la web
│
└── tests/                 # Pruebas unitarias y de integración
    ├── __init__.py
    ├── test_conversation.py
    ├── test_intent_model.py
    └── ...
```

## Uso

1. Accede a `http://localhost:5000` en tu navegador
2. Utiliza el widget de chat para interactuar con el bot
3. Sigue las instrucciones del bot para agendar tu cita legal

## Integración con WhatsApp

Para habilitar la integración con WhatsApp, configura las siguientes variables de entorno:

```bash
export TWILIO_ACCOUNT_SID="tu_account_sid"
export TWILIO_AUTH_TOKEN="tu_auth_token"
export TWILIO_WHATSAPP_NUMBER="tu_numero_whatsapp"
```

## Desarrollo y Pruebas

Ejecuta todas las pruebas con:

```bash
python -m tests.run_tests
```

## Contribuciones

1. Haz un fork del repositorio
2. Crea una nueva rama (`git checkout -b feature/nueva-funcionalidad`)
3. Realiza tus cambios y haz commit (`git commit -am 'Añade nueva funcionalidad'`)
4. Sube tus cambios (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## Licencia

Este proyecto está licenciado bajo [MIT License](LICENSE).
