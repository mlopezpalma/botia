from flask import Flask, request, jsonify, send_from_directory, session
import os
import logging
from handlers.conversation import generar_respuesta, reset_conversacion
from db_manager import DatabaseManager
from datetime import timedelta
from document_manager import DocumentManager
from flask import send_file

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv()

# Verificar que las credenciales se cargaron correctamente
twilio_sid = os.environ.get('TWILIO_ACCOUNT_SID')
if twilio_sid:
    logger.info("Credenciales de Twilio cargadas correctamente")
else:
    logger.warning("Faltan credenciales de Twilio")

# Inicializar la aplicación Flask
app = Flask(__name__)

# Configuración de secreto para sesiones
app.secret_key = os.environ.get('SECRET_KEY', 'desarrollo_secreto_temporal')
app.permanent_session_lifetime = timedelta(hours=12)

# Inicializar estado de usuarios
app.user_states = {}

# Inicializar gestor de base de datos
db_manager = DatabaseManager()

# Variable para controlar la inicialización de la base de datos
database_initialized = False

def initialize_database():
    """Inicializa la base de datos con datos existentes si está vacía."""
    global database_initialized
    if database_initialized:
        return
        
    # Comprobar si ya hay datos en la base de datos
    clientes = db_manager.get_all_clientes()
    if not clientes:
        logger.info("Inicializando base de datos con datos existentes...")
        from config import clientes_db, citas_db, casos_db
        db_manager.import_from_memory(clientes_db, citas_db, casos_db)
        logger.info("Base de datos inicializada correctamente.")
    
    


    # Inicializar gestor de documentos
    upload_dir = os.environ.get('UPLOAD_DIR', 'uploads')
    document_manager = DocumentManager(upload_dir=upload_dir, db_manager=db_manager)

     # Asegurar que existen los directorios de documentos
    try:
        document_manager.create_directories()
    except Exception as e:
        logger.error(f"Error al crear directorios para documentos: {str(e)}")

    database_initialized = True


# Registrar las rutas del panel de administración
from admin_routes import admin_bp
app.register_blueprint(admin_bp)

# Crear direcciones para archivos estáticos y templates
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Ruta para la página principal
@app.route('/')
def home():
    # Asegurar que la base de datos está inicializada
    initialize_database()
    
    # Código HTML existente sin cambios...
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bot de Agendamiento de Citas Legales</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                line-height: 1.6;
                background-color: #f4f7fc;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                padding: 30px;
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 0 15px rgba(0,0,0,0.1);
            }
            h1 {
                color: #2c3e50;
                text-align: center;
                margin-bottom: 30px;
            }
            p {
                margin-bottom: 20px;
                color: #555;
            }
            .card {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 20px;
                margin-bottom: 20px;
                background-color: #f9f9f9;
                transition: transform 0.3s ease;
            }
            .card:hover {
                transform: translateY(-5px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            .instructions {
                background-color: #e6f7ff;
                padding: 15px;
                border-radius: 5px;
                border-left: 4px solid #1890ff;
            }
            code {
                background-color: #f5f5f5;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: monospace;
            }
            .btn-calendar {
                display: inline-block;
                padding: 10px 15px;
                background-color: #1890ff;
                color: white;
                border-radius: 4px;
                text-decoration: none;
                margin-top: 10px;
                font-size: 14px;
                cursor: pointer;
                transition: background-color 0.3s ease;
            }
            .btn-calendar:hover {
                background-color: #40a9ff;
            }
            .calendar-preview {
                display: none;
                margin-top: 15px;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            .show-calendar {
                display: block;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Bot de Agendamiento de Citas Legales</h1>
            
            <div class="card">
                <h2>Demostración del Bot</h2>
                <p>Interactúa con el bot usando el widget en la esquina inferior derecha para agendar tu consulta legal.</p>
                <p>Puedes elegir entre tres tipos de consultas:</p>
                <ul>
                    <li><strong>Presencial:</strong> 30 minutos en nuestras oficinas</li>
                    <li><strong>Videoconferencia:</strong> 25 minutos por videollamada</li>
                    <li><strong>Telefónica:</strong> 10 minutos de consulta por teléfono</li>
                </ul>
            </div>
            
            <div class="instructions">
                <h2>Instrucciones para incrustar en tu sitio web</h2>
                <p>Para agregar este bot a tu sitio web, simplemente añade el siguiente código antes del cierre del tag <code>&lt;/body&gt;</code>:</p>
                <code>&lt;script src="http://tudominio.com/chat-widget.js"&gt;&lt;/script&gt;</code>
                <p>Reemplaza "tudominio.com" con la URL donde esté alojado este servicio.</p>
            </div>
            
            <div class="card">
                <h2>Calendario de Disponibilidad</h2>
                <p>Aquí puedes ver nuestros horarios disponibles para los próximos días:</p>
                <button class="btn-calendar" onclick="toggleCalendar()">Ver Calendario</button>
                <div id="calendar-preview" class="calendar-preview">
                    <p><small>Haz clic en cualquier fecha para ver los horarios disponibles</small></p>
                    <div style="text-align: center;">
                        <p><i>El calendario aparecerá aquí cuando se implemente la versión completa.</i></p>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            function toggleCalendar() {
                var calendar = document.getElementById('calendar-preview');
                calendar.classList.toggle('show-calendar');
            }
        </script>
        
        <!-- Cargar el widget del bot -->
        <script src="/chat-widget.js"></script>
    </body>
    </html>
    """

# Nueva ruta para acceder a la API del calendario en formato JSON
@app.route('/api/calendar', methods=['GET'])
def calendar_events():
    # Asegurar que la base de datos está inicializada
    initialize_database()
    
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    # Obtener eventos del calendario usando el gestor de base de datos
    eventos = db_manager.get_all_calendar_events(start_date, end_date)
    
    return jsonify(eventos)

# Añadir rutas para sincronizar entre la API del bot y la base de datos
@app.route('/api/sync_database', methods=['POST'])
def sync_database():
    """
    Sincroniza los datos entre las estructuras en memoria y la base de datos SQLite.
    Esta ruta se puede llamar periódicamente o después de cambios importantes.
    """
    try:
        from config import clientes_db, citas_db, casos_db
        db_manager.import_from_memory(clientes_db, citas_db, casos_db)
        return jsonify({"success": True, "message": "Base de datos sincronizada correctamente"})
    except Exception as e:
        logger.error(f"Error al sincronizar base de datos: {str(e)}")
        return jsonify({"success": False, "message": f"Error al sincronizar: {str(e)}"})

# Ruta para el API del bot
@app.route('/api/bot', methods=['POST'])
def chat():
    # Asegurar que la base de datos está inicializada
    initialize_database()
    
    data = request.json
    mensaje = data.get('mensaje', '')
    user_id = data.get('user_id', 'default_user')
    
    logger.debug(f"API recibió: '{mensaje}' de usuario: {user_id}")
    
    try:
        # Verificar si es un mensaje de reseteo
        if mensaje == "reset_conversation":
            # Reinicio preservando datos del usuario
            reset_conversacion(user_id, app.user_states, preserve_user_data=True)
            return jsonify({'respuesta': 'Conversación reiniciada.'})
        elif mensaje == "reset_conversation_complete":
            # Asegurar un reinicio completo eliminando la entrada existente
            try:
                if user_id in app.user_states:
                    del app.user_states[user_id]
            except Exception as e:
                logger.error(f"Error al eliminar estado de usuario: {str(e)}")
        
            reset_conversacion(user_id, app.user_states, preserve_user_data=False)
            return jsonify({'respuesta': 'Conversación reiniciada completamente.'})
        
        # Verificar si el usuario existe, si no existe entonces inicializarlo
        if user_id not in app.user_states:
            logger.debug(f"Inicializando nuevo usuario: {user_id}")
            reset_conversacion(user_id, app.user_states)
        
        # Ver el estado actual antes de procesar
        logger.debug(f"Estado actual del usuario antes de procesar: {app.user_states.get(user_id, {}).get('estado', 'no definido')}")
        
        # Detectar despedidas o cierres de conversación
        mensaje_lower = mensaje.lower().strip()
        palabras_despedida = ["no gracias", "adiós", "adios", "hasta luego", "terminar", 
                            "finalizar", "cerrar", "no quiero", "no deseo", "eso es todo"]
        
        if any(palabra in mensaje_lower for palabra in palabras_despedida):
            reset_conversacion(user_id, app.user_states)
            return jsonify({'respuesta': 'Gracias por usar nuestro servicio de asistencia para citas legales. ¡Hasta pronto!'})
        
        # Procesar la respuesta normalmente
        #respuesta = generar_respuesta(mensaje, user_id, app.user_states)
        

        # Capturar el estado antes de procesar la respuesta
        estado_usuario_antes = app.user_states.get(user_id, {}).copy()

        # Procesar la respuesta normalmente
        respuesta = generar_respuesta(mensaje, user_id, app.user_states)

        # NUEVA SECCIÓN: Sincronizar con la base de datos si se confirmó una cita
        if "Cita confirmada con éxito" in respuesta:
            # Usar el estado capturado antes de que se resetee
            try:
                if "datos" in estado_usuario_antes and estado_usuario_antes["datos"].get("email"):
                    email_cliente = estado_usuario_antes["datos"]["email"]
                    nombre_cliente = estado_usuario_antes["datos"]["nombre"]
                    telefono_cliente = estado_usuario_antes["datos"]["telefono"]
            
                    logger.debug(f"Intentando guardar cliente: {nombre_cliente}, {email_cliente}, {telefono_cliente}")
            
                    # Actualizar o crear cliente en la base de datos
                    cliente_id = db_manager.add_cliente(
                    nombre=nombre_cliente,
                    email=email_cliente,
                    telefono=telefono_cliente
                    )
                    logger.debug(f"Cliente guardado con ID: {cliente_id}")
            
                    # Si tenemos información de la cita, agregarla a la base de datos
                    if all(key in estado_usuario_antes for key in ["tipo_reunion", "fecha", "hora", "tema_reunion"]):
                        cita_id = db_manager.add_cita(
                            cliente_id=cliente_id,
                            tipo=estado_usuario_antes["tipo_reunion"],
                            fecha=estado_usuario_antes["fecha"],
                            hora=estado_usuario_antes["hora"],
                            tema=estado_usuario_antes["tema_reunion"]
                        )
                        logger.info(f"Cita registrada en base de datos con ID: {cita_id} para cliente: {email_cliente}")
                    else:
                        logger.warning(f"No se pudo guardar la cita: faltan datos. Estado: {estado_usuario_antes}")
                else:
                    logger.warning(f"No se pudieron guardar los datos: información de cliente insuficiente. Estado: {estado_usuario_antes}")
            except Exception as e:
                logger.error(f"ERROR al sincronizar con la base de datos: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
        
        # Ver el estado después de procesar
        logger.debug(f"Estado después de procesar: {app.user_states.get(user_id, {}).get('estado', 'no definido')}")
        logger.debug(f"Enviando respuesta: '{respuesta}'")
        
        return jsonify({'respuesta': respuesta})
    except Exception as e:
        logger.error(f"ERROR DETALLADO: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Intentar reiniciar la conversación en caso de error
        try:
            reset_conversacion(user_id, app.user_states)
        except Exception as reset_error:
            logger.error(f"Error al resetear conversación: {str(reset_error)}")
            # Si falla el reinicio, al menos asegurarse de que el usuario exista
            if user_id not in app.user_states:
                app.user_states[user_id] = {}
        
        return jsonify({'respuesta': 'Lo siento, ha ocurrido un error al procesar tu mensaje. He reiniciado la conversación para evitar problemas futuros. ¿En qué puedo ayudarte?'})

@app.route('/chat-widget.js')
def widget_js():
    # Servir el archivo JavaScript del widget desde la carpeta static
    return send_from_directory('static', 'chat-widget.js')


# Rutas para APIs de documentos
@app.route('/api/documentos/<int:documento_id>', methods=['GET'])
def get_documento_api(documento_id):
    try:
        documento = db_manager.get_documento(documento_id)
        if not documento:
            return jsonify({"success": False, "message": "Documento no encontrado"}), 404
        return jsonify({"success": True, "documento": documento})
    except Exception as e:
        logger.error(f"Error al obtener documento: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@app.route('/api/documentos/cliente/<int:cliente_id>', methods=['GET'])
def get_documentos_cliente_api(cliente_id):
    try:
        documentos = db_manager.get_documentos_cliente(cliente_id)
        return jsonify({"success": True, "documentos": documentos})
    except Exception as e:
        logger.error(f"Error al obtener documentos del cliente: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@app.route('/api/documentos/proyecto/<int:proyecto_id>', methods=['GET'])
def get_documentos_proyecto_api(proyecto_id):
    try:
        documentos = db_manager.get_documentos_proyecto(proyecto_id)
        return jsonify({"success": True, "documentos": documentos})
    except Exception as e:
        logger.error(f"Error al obtener documentos del proyecto: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@app.route('/api/documentos/cita/<int:cita_id>', methods=['GET'])
def get_documentos_cita_api(cita_id):
    try:
        documentos = db_manager.get_documentos_cita(cita_id)
        return jsonify({"success": True, "documentos": documentos})
    except Exception as e:
        logger.error(f"Error al obtener documentos de la cita: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@app.route('/api/documentos/upload/<string:entity_type>/<int:entity_id>', methods=['POST'])
def upload_documento_api(entity_type, entity_id):
    try:
        # Verificar que se ha subido un archivo
        if 'file' not in request.files:
            return jsonify({"success": False, "message": "No se seleccionó ningún archivo"}), 400
        
        file = request.files['file']
        
        # Verificar que tiene un nombre
        if file.filename == '':
            return jsonify({"success": False, "message": "No se seleccionó ningún archivo"}), 400
        
        # Obtener notas (opcional)
        notas = request.form.get('notas', None)
        
        # Procesar entidad
        if entity_type not in ['cliente', 'proyecto', 'cita']:
            return jsonify({"success": False, "message": "Tipo de entidad no válido"}), 400
        
        # Verificar que la entidad existe
        entity_exists = False
        if entity_type == 'cliente':
            cliente = db_manager.get_cliente_by_id(entity_id)
            entity_exists = cliente is not None
        elif entity_type == 'proyecto':
            proyecto = db_manager.get_proyecto(entity_id)
            entity_exists = proyecto is not None
        elif entity_type == 'cita':
            cita = db_manager.get_cita(entity_id)
            entity_exists = cita is not None
        
        if not entity_exists:
            return jsonify({"success": False, "message": f"La entidad {entity_type} con ID {entity_id} no existe"}), 404
        
        # Subir documento
        doc_id = document_manager.upload_documento(file, entity_type, entity_id, notas)
        
        if doc_id:
            return jsonify({"success": True, "documento_id": doc_id, "message": "Documento subido correctamente"})
        else:
            return jsonify({"success": False, "message": "Error al subir documento"}), 500
        
    except Exception as e:
        logger.error(f"Error al subir documento: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@app.route('/api/documentos/delete/<int:documento_id>', methods=['DELETE'])
def delete_documento_api(documento_id):
    try:
        result = db_manager.delete_documento(documento_id)
        if result:
            return jsonify({"success": True, "message": "Documento eliminado correctamente"})
        else:
            return jsonify({"success": False, "message": "No se pudo eliminar el documento"}), 500
    except Exception as e:
        logger.error(f"Error al eliminar documento: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@app.route('/documentos/download/<int:documento_id>')
def download_documento(documento_id):
    try:
        result = document_manager.download_documento(documento_id)
        
        if not result:
            return "Documento no encontrado", 404
        
        file_path, original_name, mime_type = result
        
        # Enviar archivo para descarga
        return send_file(
            file_path,
            mimetype=mime_type,
            as_attachment=True,
            download_name=original_name
        )
    except Exception as e:
        logger.error(f"Error al descargar documento: {str(e)}")
        return f"Error al descargar documento: {str(e)}", 500

# Crear una tabla en SQLite para manejar tokens de carga de documentos
@app.before_first_request
def create_upload_tokens_table():
    conn = sqlite3.connect(db_manager.db_file)
    cursor = conn.cursor()
    
    # Tabla para tokens de carga temporales
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS upload_tokens (
        token TEXT PRIMARY KEY,
        cita_id TEXT NOT NULL,
        fecha_creacion TEXT NOT NULL,
        fecha_expiracion TEXT NOT NULL,
        usado INTEGER DEFAULT 0
    )
    ''')
    
    conn.commit()
    conn.close()
# Importar la integración de WhatsApp
from whatsapp_integration import WhatsAppBot

# Inicializar la integración de WhatsApp
whatsapp_bot = WhatsAppBot(app)

if __name__ == '__main__':
    # Inicializar la base de datos antes de iniciar la aplicación
    initialize_database()
    app.run(debug=True)


# Función para crear tokens de carga
def create_upload_token(cita_id):
    """Crea un token de carga temporal para una cita."""
    import hashlib
    import time
    import random
    import datetime
    
    # Generar token
    token_base = f"{cita_id}-{time.time()}-{random.randint(1000, 9999)}"
    token = hashlib.md5(token_base.encode()).hexdigest()
    
    # Fechas de creación y expiración
    now = datetime.datetime.now()
    expiration = now + datetime.timedelta(hours=24)
    
    # Guardar en la base de datos
    conn = sqlite3.connect(db_manager.db_file)
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO upload_tokens (token, cita_id, fecha_creacion, fecha_expiracion, usado) VALUES (?, ?, ?, ?, ?)",
        (token, cita_id, now.strftime("%Y-%m-%d %H:%M:%S"), expiration.strftime("%Y-%m-%d %H:%M:%S"), 0)
    )
    
    conn.commit()
    conn.close()
    
    return token

# Función para validar tokens de carga
def validate_upload_token(token):
    """Valida un token de carga y lo marca como usado."""
    conn = sqlite3.connect(db_manager.db_file)
    cursor = conn.cursor()
    
    cursor.execute("SELECT cita_id, fecha_expiracion, usado FROM upload_tokens WHERE token = ?", (token,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return None
    
    cita_id, fecha_expiracion, usado = result
    
    # Verificar si el token ya fue usado
    if usado:
        conn.close()
        return None
    
    # Verificar si el token ha expirado
    import datetime
    expiration = datetime.datetime.strptime(fecha_expiracion, "%Y-%m-%d %H:%M:%S")
    now = datetime.datetime.now()
    
    if now > expiration:
        conn.close()
        return None
    
    # Marcar el token como usado
    cursor.execute("UPDATE upload_tokens SET usado = 1 WHERE token = ?", (token,))
    conn.commit()
    conn.close()
    
    return cita_id

# Ruta pública para subir documentos con token
@app.route('/documentos/subir/<string:token>', methods=['GET', 'POST'])
def upload_document_by_token(token):
    """Permite subir documentos utilizando un token temporal."""
    if request.method == 'POST':
        # Validar token
        cita_id = validate_upload_token(token)
        
        if not cita_id:
            return render_template('upload_error.html', error="El enlace ha expirado o no es válido.")
        
        # Convertir el cita_id de formato string "cita_XXXX" a entero
        numeric_id = int(cita_id.split('_')[1]) if cita_id.startswith('cita_') else int(cita_id)
        
        # Verificar que se ha subido un archivo
        if 'file' not in request.files:
            return render_template('upload_document.html', 
                                 token=token, 
                                 error="No se seleccionó ningún archivo",
                                 max_files=5)
        
        files = request.files.getlist('file')
        
        if not files or files[0].filename == '':
            return render_template('upload_document.html', 
                                 token=token, 
                                 error="No se seleccionó ningún archivo",
                                 max_files=5)
        
        # Verificar número máximo de archivos
        if len(files) > 5:
            return render_template('upload_document.html', 
                                 token=token, 
                                 error="Máximo 5 archivos permitidos",
                                 max_files=5)
        
        # Obtener notas (opcional)
        notas = request.form.get('notas', None)
        
        # Inicializar gestor de documentos
        from document_manager import DocumentManager
        doc_manager = DocumentManager(upload_dir='uploads', db_manager=db_manager)
        
        # Procesar cada archivo
        uploaded_files = []
        errors = []
        
        for file in files:
            try:
                # Subir documento
                doc_id = doc_manager.upload_documento(file, 'cita', numeric_id, notas)
                
                if doc_id:
                    uploaded_files.append(file.filename)
                else:
                    errors.append(f"Error al subir el archivo {file.filename}")
            except Exception as e:
                errors.append(f"Error: {str(e)}")
        
        if uploaded_files:
            return render_template('upload_success.html', 
                                 files=uploaded_files, 
                                 errors=errors)
        else:
            return render_template('upload_document.html', 
                                 token=token, 
                                 error="Error al subir los archivos", 
                                 errors=errors,
                                 max_files=5)
    
    # GET: Mostrar formulario de carga
    return render_template('upload_document.html', token=token, max_files=5)
