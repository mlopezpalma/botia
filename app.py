from flask import Flask, request, jsonify, send_from_directory
import os
from handlers.conversation import generar_respuesta, reset_conversacion

# Al inicio de app.py
from dotenv import load_dotenv
import os

# Cargar variables de entorno desde .env
load_dotenv()

# Verificar que las credenciales se cargaron correctamente
twilio_sid = os.environ.get('TWILIO_ACCOUNT_SID')
if twilio_sid:
    print("Credenciales de Twilio cargadas correctamente")
else:
    print("ADVERTENCIA: Faltan credenciales de Twilio")



app = Flask(__name__)

# Inicializar estado de usuarios
app.user_states = {}

@app.route('/')
def home():
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

@app.route('/api/bot', methods=['POST'])
def chat():
    data = request.json
    mensaje = data.get('mensaje', '')
    user_id = data.get('user_id', 'default_user')
    
    print(f"DEBUG - API recibió: '{mensaje}' de usuario: {user_id}")
    
    try:
        # Verificar si es un mensaje de reseteo
        if mensaje == "reset_conversation":
            # Asegurar un reinicio completo eliminando la entrada existente
            try:
                if user_id in app.user_states:
                    del app.user_states[user_id]
            except:
                pass
            reset_conversacion(user_id, app.user_states)
            return jsonify({'respuesta': 'Conversación reiniciada.'})
        
        # Verificar si el usuario existe, si no existe entonces inicializarlo
        if user_id not in app.user_states:
            print(f"DEBUG - Inicializando nuevo usuario: {user_id}")
            reset_conversacion(user_id, app.user_states)
        
        # Ver el estado actual antes de procesar
        print(f"DEBUG - Estado actual del usuario antes de procesar: {app.user_states.get(user_id, {}).get('estado', 'no definido')}")
        
        # Detectar despedidas o cierres de conversación
        mensaje_lower = mensaje.lower().strip()
        palabras_despedida = ["no gracias", "adiós", "adios", "hasta luego", "terminar", 
                            "finalizar", "cerrar", "no quiero", "no deseo", "eso es todo"]
        
        if any(palabra in mensaje_lower for palabra in palabras_despedida):
            reset_conversacion(user_id, app.user_states)
            return jsonify({'respuesta': 'Gracias por usar nuestro servicio de asistencia para citas legales. ¡Hasta pronto!'})
        
        # Procesar la respuesta normalmente
        respuesta = generar_respuesta(mensaje, user_id, app.user_states)
        
        # Ver el estado después de procesar
        print(f"DEBUG - Estado después de procesar: {app.user_states.get(user_id, {}).get('estado', 'no definido')}")
        print(f"DEBUG - Enviando respuesta: '{respuesta}'")
        
        return jsonify({'respuesta': respuesta})
    except Exception as e:
        print(f"ERROR DETALLADO: {str(e)}")
        import traceback
        print(traceback.format_exc())
        
        # Intentar reiniciar la conversación en caso de error
        try:
            reset_conversacion(user_id, app.user_states)
        except:
            # Si falla el reinicio, al menos asegurarse de que el usuario exista
            if user_id not in app.user_states:
                app.user_states[user_id] = {}
        
        return jsonify({'respuesta': 'Lo siento, ha ocurrido un error al procesar tu mensaje. He reiniciado la conversación para evitar problemas futuros. ¿En qué puedo ayudarte?'})



@app.route('/chat-widget.js')
def widget_js():
    # Servir el archivo JavaScript del widget desde la carpeta static
    return send_from_directory('static', 'chat-widget.js')

# Importar la integración de WhatsApp
from whatsapp_integration import WhatsAppBot

# Inicializar la integración de WhatsApp
whatsapp_bot = WhatsAppBot(app)


if __name__ == '__main__':
    app.run(debug=True)
