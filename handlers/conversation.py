import datetime
import re
from config import HORARIOS_POR_TIPO, TIPOS_REUNION, INTENCIONES, MENSAJES_MENU, citas_db, clientes_db
from models.intent_model import identificar_intencion
from models.data_extraction import (
    identificar_fecha, identificar_hora,
    identificar_tipo_reunion, identificar_datos_personales
)
from handlers.calendar_service import (
    obtener_horarios_disponibles, 
    encontrar_proxima_fecha_disponible,
    agendar_en_calendario
)
from handlers.email_service import enviar_correo_confirmacion

def generar_respuesta(mensaje, user_id, user_states):
    print(f"DEBUG - generar_respuesta recibió: '{mensaje}' de usuario: {user_id}")
    
    # Estado del usuario
    if user_id not in user_states:
        user_states[user_id] = {
            "estado": "inicial",
            "tipo_reunion": None,
            "fecha": None,
            "hora": None,
            "datos": {"nombre": None, "email": None, "telefono": None}
        }
    
    estado_usuario = user_states[user_id]
    print(f"DEBUG - estado actual del usuario: {estado_usuario['estado']}")
    
    # Procesamiento directo para respuestas simples según el estado
    mensaje_lower = mensaje.lower().strip()
    
    # Buscar datos personales en cualquier mensaje
    datos_identificados = identificar_datos_personales(mensaje)
    for campo, valor in datos_identificados.items():
        if valor and not estado_usuario["datos"][campo]:
            estado_usuario["datos"][campo] = valor
            print(f"DEBUG - identificado {campo}: {valor}")
    
    # Manejo de estados específicos
    if estado_usuario["estado"] == "inicial":
        intencion = identificar_intencion(mensaje)
        
        if intencion == "saludo":
            estado_usuario["estado"] = "esperando_inicio"
            return ("¡Hola! Soy el asistente de citas legales. Puedo ayudarte a agendar una consulta con nuestros abogados.\n" + 
                    MENSAJES_MENU["tipo_reunion"])
        
        elif intencion == "agendar":
            estado_usuario["estado"] = "esperando_tipo_reunion"
            return MENSAJES_MENU["tipo_reunion"]
        
        else:
            # Si no es saludo ni agendar, asumir que quiere agendar
            estado_usuario["estado"] = "esperando_tipo_reunion"
            return ("Bienvenido al asistente de citas legales. Para comenzar, necesito saber " + 
                   MENSAJES_MENU["tipo_reunion"])
    
    elif estado_usuario["estado"] == "esperando_inicio" or estado_usuario["estado"] == "esperando_tipo_reunion":
        # Identificar tipo de reunión
        tipo_reunion = identificar_tipo_reunion(mensaje)
        
        if tipo_reunion:
            estado_usuario["tipo_reunion"] = tipo_reunion
            estado_usuario["estado"] = "esperando_preferencia_fecha"
            return MENSAJES_MENU["preferencia_fecha"]
        
        # Verificación directa para opciones de menú
        if mensaje_lower in ["presencial", "videoconferencia", "telefónica", "telefonica"]:
            tipo_reunion = mensaje_lower
            if tipo_reunion == "telefónica":
                tipo_reunion = "telefonica"
            
            estado_usuario["tipo_reunion"] = tipo_reunion
            estado_usuario["estado"] = "esperando_preferencia_fecha"
            return MENSAJES_MENU["preferencia_fecha"]
        
        # Si no se reconoce el tipo, preguntar de nuevo
        return "Por favor, indica qué tipo de reunión prefieres: Presencial, Videoconferencia o Telefónica."
    
    elif estado_usuario["estado"] == "esperando_preferencia_fecha":
        intencion = identificar_intencion(mensaje)
        
        # Opción: Lo antes posible
        if intencion == "antes_posible" or "antes posible" in mensaje_lower or "1" == mensaje.strip() or mensaje_lower == "lo antes posible":
            fecha, hora = encontrar_proxima_fecha_disponible(estado_usuario["tipo_reunion"])
            
            if fecha and hora:
                estado_usuario["fecha"] = fecha
                estado_usuario["hora"] = hora
                estado_usuario["estado"] = "esperando_datos"
                
                fecha_formateada = datetime.datetime.strptime(fecha, "%Y-%m-%d").strftime("%d/%m/%Y")
                duracion = TIPOS_REUNION[estado_usuario["tipo_reunion"]]["duracion_cliente"]
                
                datos_faltantes = _verificar_datos_faltantes(estado_usuario["datos"])
                
                if datos_faltantes:
                    return (f"La próxima cita disponible es el {fecha_formateada} a las {hora} ({duracion} minutos).\n"
                            f"Para confirmar, necesito los siguientes datos: {', '.join(datos_faltantes)}. ¿Podrías proporcionármelos?")
                else:
                    estado_usuario["estado"] = "esperando_confirmacion"
                    return (f"La próxima cita disponible es el {fecha_formateada} a las {hora} ({duracion} minutos).\n"
                            f"Tus datos son:\n"
                            f"- Nombre: {estado_usuario['datos']['nombre']}\n"
                            f"- Email: {estado_usuario['datos']['email']}\n"
                            f"- Teléfono: {estado_usuario['datos']['telefono']}\n\n" +
                            MENSAJES_MENU["confirmacion"])
            else:
                return "Lo siento, no encontramos citas disponibles en los próximos 14 días. Por favor, intenta más tarde."
        
        # Opción: Día específico
        elif intencion == "dia_especifico" or "día específico" in mensaje_lower or "dia especifico" in mensaje_lower or "2" == mensaje.strip() or mensaje_lower == "en un día específico":
            estado_usuario["estado"] = "esperando_fecha"
            return "Por favor, indícame qué día te gustaría agendar tu cita (ej: mañana, próximo lunes, etc.)"
        
        # Opción: Ver calendario
        elif intencion == "ver_calendario" or "calendario" in mensaje_lower or "3" == mensaje.strip() or mensaje_lower == "ver calendario":
            estado_usuario["estado"] = "mostrando_calendario"
            return ("Para ver el calendario completo, haz clic en 'Ver Calendario' abajo. [Indicador pequeño]\n\n"
                    "Mientras tanto, puedes indicarme directamente qué día te gustaría agendar tu cita (ej: mañana, próximo lunes, etc.)")
        
        # Si no se reconoce la preferencia, preguntar de nuevo
        return "Por favor, indica cómo te gustaría agendar tu cita: Lo antes posible, En un día específico, o Ver calendario."
    
    elif estado_usuario["estado"] == "esperando_fecha" or estado_usuario["estado"] == "mostrando_calendario":
        fecha = identificar_fecha(mensaje)
        
        if fecha:
            fecha_dt = datetime.datetime.strptime(fecha, "%Y-%m-%d")
            horarios = obtener_horarios_disponibles(fecha_dt, estado_usuario["tipo_reunion"])
            
            if horarios:
                estado_usuario["fecha"] = fecha
                estado_usuario["estado"] = "esperando_hora"
                
                fecha_formateada = fecha_dt.strftime("%d/%m/%Y (%A)")
                respuesta = f"Para el {fecha_formateada}, tenemos los siguientes horarios disponibles:\n"
                
                # Crear menú de selección para los horarios
                opciones_menu = "|".join(horarios)
                return respuesta + f"[MENU:{opciones_menu}]"
            else:
                return f"Lo siento, no hay horarios disponibles para esa fecha con una reunión {estado_usuario['tipo_reunion']}. ¿Te gustaría elegir otra fecha?"
        else:
            return "No he podido identificar la fecha. Por favor, indica una fecha específica como 'mañana', 'próximo lunes', etc."
    
    elif estado_usuario["estado"] == "esperando_hora":
        # Verificar si el mensaje es uno de los horarios disponibles
        horarios = obtener_horarios_disponibles(estado_usuario["fecha"], estado_usuario["tipo_reunion"])
        
        # Verificar si es un número de opción
        if mensaje.strip().isdigit():
            opcion = int(mensaje.strip())
            if 1 <= opcion <= len(horarios):
                hora = horarios[opcion-1]
                estado_usuario["hora"] = hora
                return _procesar_seleccion_hora(estado_usuario)
        
        # Verificar si es una hora específica
        if mensaje in horarios:
            estado_usuario["hora"] = mensaje
            return _procesar_seleccion_hora(estado_usuario)
        
        # Intenta identificar la hora en el mensaje
        hora_identificada = identificar_hora(mensaje)
        if hora_identificada in horarios:
            estado_usuario["hora"] = hora_identificada
            return _procesar_seleccion_hora(estado_usuario)
        
        # Si no se reconoce la hora, mostrar opciones de nuevo
        opciones_menu = "|".join(horarios)
        return f"Por favor, selecciona uno de los horarios disponibles:\n[MENU:{opciones_menu}]"
    
    elif estado_usuario["estado"] == "esperando_datos":
        # Verificar si ya tenemos todos los datos del cliente
        datos_faltantes = _verificar_datos_faltantes(estado_usuario["datos"])
        
        if datos_faltantes:
            campos = ", ".join(datos_faltantes)
            return f"Aún necesito los siguientes datos: {campos}. ¿Podrías proporcionármelos?"
        else:
            # Ya tenemos todos los datos, pasar a confirmación
            estado_usuario["estado"] = "esperando_confirmacion"
            fecha_formateada = datetime.datetime.strptime(estado_usuario["fecha"], "%Y-%m-%d").strftime("%d/%m/%Y")
            duracion = TIPOS_REUNION[estado_usuario["tipo_reunion"]]["duracion_cliente"]
            return (f"Perfecto. Resumiendo tu cita:\n"
                    f"- Tipo: {estado_usuario['tipo_reunion']}\n"
                    f"- Fecha: {fecha_formateada}\n"
                    f"- Hora: {estado_usuario['hora']}\n"
                    f"- Duración: {duracion} minutos\n"
                    f"- Nombre: {estado_usuario['datos']['nombre']}\n"
                    f"- Email: {estado_usuario['datos']['email']}\n"
                    f"- Teléfono: {estado_usuario['datos']['telefono']}\n\n" +
                    MENSAJES_MENU["confirmacion"])
    
    elif estado_usuario["estado"] == "esperando_confirmacion":
        intencion = identificar_intencion(mensaje)
        
        if intencion == "confirmacion" or "si" in mensaje_lower or "sí" in mensaje_lower or "confirmar" in mensaje_lower or mensaje_lower == "sí, confirmar":
            return _confirmar_cita(estado_usuario, user_id, user_states)
        
        elif intencion == "negacion" or "no" in mensaje_lower or "cancelar" in mensaje_lower or mensaje_lower == "no, cambiar detalles":
            # Reiniciar parcialmente el estado para permitir cambios
            estado_usuario["estado"] = "esperando_preferencia_fecha"
            return MENSAJES_MENU["preferencia_fecha"]
        
        else:
            return "No he entendido tu respuesta. ¿Deseas confirmar esta cita?" + MENSAJES_MENU["confirmacion"]
    
    # Si no coincide con ningún estado específico, respuesta genérica
    return "Disculpa, no he entendido tu solicitud. ¿Puedes reformularla? Puedo ayudarte a agendar citas legales presenciales, por videoconferencia o telefónicas."

def _verificar_datos_faltantes(datos):
    """Verifica qué datos faltan del cliente"""
    datos_faltantes = []
    if not datos["nombre"]:
        datos_faltantes.append("nombre")
    if not datos["email"]:
        datos_faltantes.append("email")
    if not datos["telefono"]:
        datos_faltantes.append("teléfono")
    return datos_faltantes

def _procesar_seleccion_hora(estado_usuario):
    """Procesa la selección de hora y solicita datos o confirmación"""
    estado_usuario["estado"] = "esperando_datos"
    
    # Verificar si ya tenemos todos los datos del cliente
    datos_faltantes = _verificar_datos_faltantes(estado_usuario["datos"])
    
    if datos_faltantes:
        campos = ", ".join(datos_faltantes)
        return f"Para confirmar tu cita, necesito los siguientes datos: {campos}. ¿Podrías proporcionármelos?"
    else:
        # Ya tenemos todos los datos, pasar a confirmación
        estado_usuario["estado"] = "esperando_confirmacion"
        fecha_formateada = datetime.datetime.strptime(estado_usuario["fecha"], "%Y-%m-%d").strftime("%d/%m/%Y")
        duracion = TIPOS_REUNION[estado_usuario["tipo_reunion"]]["duracion_cliente"]
        return (f"Perfecto. Resumiendo tu cita:\n"
                f"- Tipo: {estado_usuario['tipo_reunion']}\n"
                f"- Fecha: {fecha_formateada}\n"
                f"- Hora: {estado_usuario['hora']}\n"
                f"- Duración: {duracion} minutos\n"
                f"- Nombre: {estado_usuario['datos']['nombre']}\n"
                f"- Email: {estado_usuario['datos']['email']}\n"
                f"- Teléfono: {estado_usuario['datos']['telefono']}\n\n" +
                MENSAJES_MENU["confirmacion"])

def _confirmar_cita(estado_usuario, user_id, user_states):
    """Confirma la cita y resetea el estado del usuario"""
    # Agendar cita en el calendario
    evento = agendar_en_calendario(
        estado_usuario["fecha"], 
        estado_usuario["hora"], 
        estado_usuario["tipo_reunion"], 
        estado_usuario["datos"]
    )
    
    # Enviar correos de confirmación
    enviar_correo_confirmacion(
        estado_usuario["datos"],
        estado_usuario["fecha"],
        estado_usuario["hora"],
        estado_usuario["tipo_reunion"]
    )
    
    # Guardar en base de datos
    cita_id = f"cita_{len(citas_db) + 1:04d}"
    citas_db[cita_id] = {
        "tipo": estado_usuario["tipo_reunion"],
        "fecha": estado_usuario["fecha"],
        "hora": estado_usuario["hora"],
        "cliente": estado_usuario["datos"],
        "evento_id": evento.get('id', 'unknown')
    }
    
    # Guardar cliente en base de datos
    cliente_id = estado_usuario["datos"]["email"]
    if cliente_id not in clientes_db:
        clientes_db[cliente_id] = estado_usuario["datos"]
        clientes_db[cliente_id]["citas"] = [cita_id]
    else:
        if "citas" not in clientes_db[cliente_id]:
            clientes_db[cliente_id]["citas"] = []
        clientes_db[cliente_id]["citas"].append(cita_id)
    
    # Generar mensaje de confirmación
    fecha_formateada = datetime.datetime.strptime(estado_usuario["fecha"], "%Y-%m-%d").strftime("%d/%m/%Y")
    duracion = TIPOS_REUNION[estado_usuario["tipo_reunion"]]["duracion_cliente"]
    
    # Reiniciar estado
    user_states[user_id] = {
        "estado": "inicial",
        "tipo_reunion": None,
        "fecha": None,
        "hora": None,
        "datos": {"nombre": None, "email": None, "telefono": None}
    }
    
    return (f"¡Cita confirmada con éxito! Se ha agendado una consulta legal {estado_usuario['tipo_reunion']} para el {fecha_formateada} a las {estado_usuario['hora']} ({duracion} minutos).\n\n"
            f"Hemos enviado un correo de confirmación a {estado_usuario['datos']['email']} con todos los detalles.\n\n"
            f"Gracias por usar nuestro servicio. ¿Hay algo más en lo que pueda ayudarte?")
