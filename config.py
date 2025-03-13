# Configuración de horarios según tipo de reunión
HORARIOS_POR_TIPO = {
    "presencial": {
        "manana": ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30"],
        "tarde": ["15:00", "15:30", "16:00", "16:30", "17:00", "17:30", "18:00", "18:30"]
    },
    "videoconferencia": {
        "manana": ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30"],
        "tarde": ["15:00", "15:30", "16:00", "16:30", "17:00", "17:30", "18:00", "18:30"]
    },
    "telefonica": {
        "manana": ["09:00", "09:15", "09:30", "09:45", "10:00", "10:15", "10:30", "10:45", 
                  "11:00", "11:15", "11:30", "11:45", "12:00", "12:15", "12:30", "12:45"],
        "tarde": ["15:00", "15:15", "15:30", "15:45", "16:00", "16:15", "16:30", "16:45",
                 "17:00", "17:15", "17:30", "17:45", "18:00", "18:15", "18:30", "18:45"]
    }
}

# Tipos de reuniones y sus duraciones
TIPOS_REUNION = {
    "presencial": {"duracion_real": 30, "duracion_cliente": 30},
    "videoconferencia": {"duracion_real": 30, "duracion_cliente": 25},
    "telefonica": {"duracion_real": 15, "duracion_cliente": 10}
}

# Definir intenciones y sus ejemplos
INTENCIONES = {
    "saludo": ["hola", "buenos días", "buenas tardes", "buenas noches", "saludos", "qué tal"],
    "agendar": ["quiero agendar una cita", "necesito una cita", "deseo programar una visita", 
                "quisiera reservar un horario", "puedo sacar una hora", "disponibilidad para cita"],
    "antes_posible": ["lo antes posible", "cuanto antes", "urgente", "próxima disponible"],
    "ver_calendario": ["quiero ver el calendario", "mostrar calendario", "ver fechas disponibles"],
    "dia_especifico": ["día específico", "semana próxima", "mes próximo"],
    "reunion_presencial": ["presencial", "en persona", "cara a cara", "en la oficina"],
    "reunion_video": ["videoconferencia", "virtual", "online", "por video", "videollamada"],
    "reunion_telefonica": ["telefónica", "teléfono", "llamada", "telefonica", "por teléfono"],
    "fecha": ["hoy", "mañana", "próxima semana", "este lunes", "este martes", "este miércoles",
             "próximo jueves", "próximo viernes", "días disponibles", "horarios disponibles"],
    "datos_personales": ["mi nombre es", "me llamo", "mi correo", "mi email", "mi teléfono", "mi número"],
    "informacion": ["información", "detalles", "qué servicios ofrecen", "precios", "duración"],
    "confirmacion": ["confirmar", "acepto", "de acuerdo", "sí", "si", "correcto", "ok", "vale"],
    "negacion": ["cancelar", "no", "rechazar", "cambiar", "otro día", "otra hora"]
}

# Guardar los ejemplos de entrenamiento para referencia
EJEMPLOS_INTENCIONES = INTENCIONES

# Datos de entrenamiento para el modelo de IA
FRASES_INTENCIONES = [
    # Saludos
    "hola", "buenos días", "buenas tardes", "buenas noches", "saludos", "qué tal",
    # Agendar cita
    "quiero agendar una cita", "necesito una cita", "deseo programar una visita", 
    "quisiera reservar un horario", "puedo sacar una hora", "disponibilidad para cita",
    # Opciones de agendamiento
    "lo antes posible", "cuanto antes", "urgente", "próxima disponible",
    "quiero ver el calendario", "mostrar calendario", "ver fechas disponibles",
    "día específico", "semana próxima", "mes próximo",
    # Tipos de reunión
    "presencial", "en persona", "cara a cara", "en la oficina",
    "videoconferencia", "virtual", "online", "por video", "videollamada",
    "telefónica", "por teléfono", "llamada", "conferencia telefónica",
    # Fechas
    "hoy", "mañana", "próxima semana", "este lunes", "este martes", "este miércoles",
    "próximo jueves", "próximo viernes", "días disponibles", "horarios disponibles",
    # Datos personales
    "mi nombre es", "me llamo", "mi correo", "mi email", "mi teléfono", "mi número",
    # Información
    "información", "detalles", "qué servicios ofrecen", "precios", "duración",
    # Confirmación
    "confirmar", "acepto", "de acuerdo", "sí", "si", "correcto", "ok", "vale",
    # Negación
    "cancelar", "no", "rechazar", "cambiar", "otro día", "otra hora"
]

ETIQUETAS_INTENCIONES = [
    "saludo", "saludo", "saludo", "saludo", "saludo", "saludo",
    "agendar", "agendar", "agendar", "agendar", "agendar", "agendar",
    "antes_posible", "antes_posible", "antes_posible", "antes_posible",
    "ver_calendario", "ver_calendario", "ver_calendario",
    "dia_especifico", "dia_especifico", "dia_especifico",
    "reunion_presencial", "reunion_presencial", "reunion_presencial", "reunion_presencial",
    "reunion_video", "reunion_video", "reunion_video", "reunion_video", "reunion_video",
    "reunion_telefonica", "reunion_telefonica", "reunion_telefonica", "reunion_telefonica",
    "fecha", "fecha", "fecha", "fecha", "fecha", "fecha",
    "fecha", "fecha", "fecha", "fecha",
    "datos_personales", "datos_personales", "datos_personales", "datos_personales", "datos_personales", "datos_personales",
    "informacion", "informacion", "informacion", "informacion", "informacion",
    "confirmacion", "confirmacion", "confirmacion", "confirmacion", "confirmacion", "confirmacion", "confirmacion", "confirmacion",
    "negacion", "negacion", "negacion", "negacion", "negacion", "negacion"
]

# Información de email
EMAIL_CONFIG = {
    "smtp_server": "smtp.example.com",
    "port": 587,
    "sender_email": "bot@example.com",
    "password": "your_password"  # En producción usar variables de entorno
}

# Base de datos simulada de citas y clientes
citas_db = {}
clientes_db = {}

# Configuración para los menús de selección
MENSAJES_MENU = {
    "tipo_reunion": "¿Qué tipo de reunión prefieres? [MENU:Presencial|Videoconferencia|Telefónica]",
    "preferencia_fecha": "¿Cómo te gustaría agendar tu cita? [MENU:Lo antes posible|En un día específico|Ver calendario]",
    "confirmacion": "¿Deseas confirmar esta cita? [MENU:Sí, confirmar|No, cambiar detalles]"
}
