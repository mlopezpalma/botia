from flask import Flask, request, jsonify, send_from_directory
import os
from handlers.conversation import generar_respuesta

app = Flask(__name__)

# Inicializar estado de usuarios
app.user_states = {}

@app.route('/')
def home():
    # Retornar directamente el HTML
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
    
    try:
        respuesta = generar_respuesta(mensaje, user_id, app.user_states)
        return jsonify({'respuesta': respuesta})
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({'respuesta': 'Lo siento, ha ocurrido un error al procesar tu mensaje.'})

@app.route('/chat-widget.js')
def widget_js():
    # Servir el archivo JavaScript del widget desde la carpeta static
    return send_from_directory('static', 'chat-widget.js')

if __name__ == '__main__':
    app.run(debug=True)
