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

# Añadir importación de casos_db y ESTADOS_CASO al inicio del archivo
from config import HORARIOS_POR_TIPO, TIPOS_REUNION, INTENCIONES, MENSAJES_MENU, citas_db, clientes_db, casos_db, ESTADOS_CASO


# Modificar la función reset_conversacion para incluir el nuevo estado
def reset_conversacion(user_id, user_states):
    """
    Reinicia el estado de la conversación para un usuario específico.
    
    Args:
        user_id: ID del usuario
        user_states: Diccionario de estados de usuario
    """
    user_states[user_id] = {
        "estado": "inicial",
        "tipo_reunion": None,
        "fecha": None,
        "hora": None,
        "tema_reunion": None,
        "datos": {"nombre": None, "email": None, "telefono": None},
        "consulta_caso": {
            "numero_expediente": None,
            "email_cliente": None,
            "caso_encontrado": False
        }
    }
    print(f"DEBUG - Conversación reiniciada para usuario: {user_id}")

def generar_respuesta(mensaje, user_id, user_states):
    print(f"DEBUG - generar_respuesta recibió: '{mensaje}' de usuario: {user_id}")
    
    # Estado del usuario
    if user_id not in user_states:
        reset_conversacion(user_id, user_states)
    
    estado_usuario = user_states[user_id]
    print(f"DEBUG - estado actual del usuario: {estado_usuario['estado']}")
    
    # Procesamiento directo para respuestas simples según el estado
    mensaje_lower = mensaje.lower().strip()
    
    # Buscar datos personales en cualquier mensaje
    datos_identificados = identificar_datos_personales(mensaje)
    for campo, valor in datos_identificados.items():
        if valor and not estado_usuario["datos"][campo]:
            # Evitar que el tipo de reunión se confunda con el nombre
            if campo == "nombre" and valor.lower() in ["presencial", "videoconferencia", "telefonica", "telefónica"]:
                continue  # Saltar este valor para evitar confusión
            
            estado_usuario["datos"][campo] = valor
            print(f"DEBUG - identificado {campo}: {valor}")
            
            # Si se identifica un email o teléfono, intentar buscar el cliente
            if campo == "email" and not estado_usuario["datos"]["nombre"]:
                cliente = _buscar_cliente_por_email(valor)
                if cliente:
                    # Completar los datos faltantes del cliente
                    if not estado_usuario["datos"]["nombre"] and cliente.get("nombre"):
                        estado_usuario["datos"]["nombre"] = cliente["nombre"]
                        print(f"DEBUG - recuperado nombre: {cliente['nombre']} de cliente existente")
                    if not estado_usuario["datos"]["telefono"] and cliente.get("telefono"):
                        estado_usuario["datos"]["telefono"] = cliente["telefono"]
                        print(f"DEBUG - recuperado teléfono: {cliente['telefono']} de cliente existente")
            
            # Si se identifica un teléfono, intentar buscar el cliente
            elif campo == "telefono" and not estado_usuario["datos"]["nombre"]:
                cliente = _buscar_cliente_por_telefono(valor)
                if cliente:
                    # Completar los datos faltantes del cliente
                    if not estado_usuario["datos"]["nombre"] and cliente.get("nombre"):
                        estado_usuario["datos"]["nombre"] = cliente["nombre"]
                        print(f"DEBUG - recuperado nombre: {cliente['nombre']} de cliente existente")
                    if not estado_usuario["datos"]["email"] and cliente.get("email"):
                        estado_usuario["datos"]["email"] = cliente["email"]
                        print(f"DEBUG - recuperado email: {cliente['email']} de cliente existente")


    # Manejo de estados específicos
    if estado_usuario["estado"] == "inicial":
        intencion = identificar_intencion(mensaje)
        
        if intencion == "saludo":
            estado_usuario["estado"] = "esperando_inicio"
            return ("¡Hola! Soy el asistente de citas legales. Puedo ayudarte a agendar una consulta con nuestros abogados o consultar el estado de tu caso.\n" + 
                    "¿Qué te gustaría hacer? [MENU:Agendar una cita|Consultar estado de mi caso]")
        
        elif intencion == "agendar":
            estado_usuario["estado"] = "esperando_tipo_reunion"
            return MENSAJES_MENU["tipo_reunion"]
            
        elif intencion == "consultar_estado":
            estado_usuario["estado"] = "esperando_opcion_consulta"
            return MENSAJES_MENU["consulta_estado"]
        
        else:
            # Si no se identifica intención específica, ofrecer opciones
            estado_usuario["estado"] = "esperando_inicio"
            return ("Bienvenido al asistente de citas legales. Puedo ayudarte a agendar una consulta o verificar el estado de tu caso.\n" + 
                   "¿Qué te gustaría hacer? [MENU:Agendar una cita|Consultar estado de mi caso]")
    
    elif estado_usuario["estado"] == "esperando_inicio":
        # Verificar si quiere consultar estado del caso
        if "estado" in mensaje_lower or "consultar" in mensaje_lower or "caso" in mensaje_lower or "expediente" in mensaje_lower:
            estado_usuario["estado"] = "esperando_opcion_consulta"
            return MENSAJES_MENU["consulta_estado"]   


    elif estado_usuario["estado"] == "esperando_inicio" or estado_usuario["estado"] == "esperando_tipo_reunion":
        # Identificar tipo de reunión
        tipo_reunion = identificar_tipo_reunion(mensaje)
        
        if tipo_reunion:
            estado_usuario["tipo_reunion"] = tipo_reunion
            estado_usuario["estado"] = "esperando_tema_reunion"
            return "¿Cuál es el motivo o tema de la consulta legal?"
        
        # Verificación directa para opciones de menú
        if mensaje_lower in ["presencial", "videoconferencia", "telefónica", "telefonica"]:
            tipo_reunion = mensaje_lower
            if tipo_reunion == "telefónica":
                tipo_reunion = "telefonica"
            
            estado_usuario["tipo_reunion"] = tipo_reunion
            estado_usuario["estado"] = "esperando_tema_reunion"
            return "¿Cuál es el motivo o tema de la consulta legal?"
        
        # Si no se reconoce el tipo, preguntar de nuevo
        return "Por favor, indica qué tipo de reunión prefieres: Presencial, Videoconferencia o Telefónica."
    
    elif estado_usuario["estado"] == "esperando_tema_reunion":
        # Guardar el tema de la reunión y pasar al siguiente estado
        if len(mensaje.strip()) > 0:
            estado_usuario["tema_reunion"] = mensaje.strip()
            estado_usuario["estado"] = "esperando_preferencia_fecha"
            return MENSAJES_MENU["preferencia_fecha"]
        else:
            return "Por favor, indícame brevemente el motivo de tu consulta legal."
    
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
                            f"- Teléfono: {estado_usuario['datos']['telefono']}\n"
                            f"- Tema: {estado_usuario['tema_reunion']}\n\n" +
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
        
        # Si hemos reconocido al cliente, mostrar mensaje de bienvenida
        if estado_usuario["datos"]["nombre"] and estado_usuario["datos"]["email"] and estado_usuario["datos"]["telefono"]:
            # Verificar si estos datos provienen de la base de datos (cliente existente)
            cliente_existente = _buscar_cliente_por_email(estado_usuario["datos"]["email"])
            if cliente_existente:
                estado_usuario["estado"] = "esperando_confirmacion"
                fecha_formateada = datetime.datetime.strptime(estado_usuario["fecha"], "%Y-%m-%d").strftime("%d/%m/%Y")
                duracion = TIPOS_REUNION[estado_usuario["tipo_reunion"]]["duracion_cliente"]
                return (f"¡Bienvenido de nuevo, {estado_usuario['datos']['nombre']}! Hemos reconocido tus datos. Resumiendo tu cita:\n"
                        f"- Tipo: {estado_usuario['tipo_reunion']}\n"
                        f"- Fecha: {fecha_formateada}\n"
                        f"- Hora: {estado_usuario['hora']}\n"
                        f"- Duración: {duracion} minutos\n"
                        f"- Tema: {estado_usuario['tema_reunion']}\n"
                        f"- Nombre: {estado_usuario['datos']['nombre']}\n"
                        f"- Email: {estado_usuario['datos']['email']}\n"
                        f"- Teléfono: {estado_usuario['datos']['telefono']}\n\n" +
                        MENSAJES_MENU["confirmacion"])
        
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
                    f"- Tema: {estado_usuario['tema_reunion']}\n"
                    f"- Nombre: {estado_usuario['datos']['nombre']}\n"
                    f"- Email: {estado_usuario['datos']['email']}\n"
                    f"- Teléfono: {estado_usuario['datos']['telefono']}\n\n" +
                    MENSAJES_MENU["confirmacion"])

    
    elif estado_usuario["estado"] == "esperando_confirmacion":
        intencion = identificar_intencion(mensaje)
        
        if intencion == "confirmacion" or "si" in mensaje_lower or "sí" in mensaje_lower or "confirmar" in mensaje_lower or mensaje_lower == "sí, confirmar":
            return _confirmar_cita(estado_usuario, user_id, user_states)
        
        elif intencion == "negacion" or "no" in mensaje_lower or "cancelar" in mensaje_lower or mensaje_lower == "no, cambiar detalles":
            # Preguntar qué desea cambiar el usuario
            return _preguntar_cambios(estado_usuario)
        
        else:
            return "No he entendido tu respuesta. ¿Deseas confirmar esta cita?" + MENSAJES_MENU["confirmacion"]
            
    elif estado_usuario["estado"] == "esperando_seleccion_cambio":
        # Manejar la selección de lo que desea cambiar
        if "fecha" in mensaje_lower or "hora" in mensaje_lower:
            estado_usuario["estado"] = "esperando_preferencia_fecha"
            return MENSAJES_MENU["preferencia_fecha"]
            
        elif "tipo" in mensaje_lower or "reunion" in mensaje_lower or "reunión" in mensaje_lower:
            estado_usuario["estado"] = "esperando_tipo_reunion"
            return "¿Qué tipo de reunión prefieres? [MENU:Presencial|Videoconferencia|Telefónica]"
            
        elif "tema" in mensaje_lower:
            estado_usuario["estado"] = "esperando_tema_reunion"
            return "¿Cuál es el nuevo tema o motivo de la consulta legal?"
            
        elif "datos" in mensaje_lower or "personales" in mensaje_lower or "nombre" in mensaje_lower or "email" in mensaje_lower or "correo" in mensaje_lower or "teléfono" in mensaje_lower or "telefono" in mensaje_lower:
            # Resetear los datos personales
            estado_usuario["datos"] = {"nombre": None, "email": None, "telefono": None}
            estado_usuario["estado"] = "esperando_datos"
            return "Por favor, proporciona tus datos de nuevo (nombre, email y teléfono)."
            
        else:
            return "No he entendido qué deseas cambiar. Por favor, selecciona una de las opciones: Fecha y hora, Tipo de reunión, Tema, o Mis datos personales."
    elif estado_usuario["estado"] == "esperando_opcion_consulta":
        # Determinar si quiere buscar por número o por email
        if "numero" in mensaje_lower or "expediente" in mensaje_lower or mensaje_lower == "mi número de expediente":
            estado_usuario["estado"] = "esperando_numero_expediente"
            return "Por favor, indícame el número de expediente de tu caso (ej: C2023-001):"
            
        elif "email" in mensaje_lower or "correo" in mensaje_lower or mensaje_lower == "mi email para buscar mis casos":
            estado_usuario["estado"] = "esperando_email_cliente"
            return "Por favor, indícame tu dirección de email para buscar tus casos:"
            
        else:
            return "No he entendido tu elección. " + MENSAJES_MENU["consulta_estado"]
            
    elif estado_usuario["estado"] == "esperando_numero_expediente":
        # Buscar caso por número de expediente
        numero_expediente = mensaje.strip().upper()
        resultado = _buscar_caso_por_numero(numero_expediente)
        
        if resultado:
            estado_usuario["consulta_caso"]["numero_expediente"] = numero_expediente
            estado_usuario["consulta_caso"]["caso_encontrado"] = True
            
            # Mostrar detalles del caso
            return _formatear_detalles_caso(resultado)
        else:
            return "No he podido encontrar ningún caso con el número de expediente proporcionado. Por favor, verifica el número e inténtalo de nuevo, o elige otra opción. " + MENSAJES_MENU["consulta_estado"]
            
    elif estado_usuario["estado"] == "esperando_email_cliente":
        # Buscar casos por email del cliente
        email = mensaje.strip().lower()
        casos = _buscar_casos_por_email(email)
        
        if casos:
            estado_usuario["consulta_caso"]["email_cliente"] = email
            estado_usuario["consulta_caso"]["caso_encontrado"] = True
            
            # Si hay varios casos, mostrar listado
            if len(casos) > 1:
                respuesta = f"Hemos encontrado {len(casos)} casos asociados a tu email:\n\n"
                for i, caso in enumerate(casos, 1):
                    respuesta += f"{i}. Expediente {caso['numero']}: {caso['titulo']} - {caso['estado']}\n"
                
                respuesta += "\nPara ver detalles de un caso específico, escribe su número de expediente (ej: C2023-001)."
                estado_usuario["estado"] = "esperando_numero_expediente"
                return respuesta
            else:
                # Si hay un solo caso, mostrar detalles
                return _formatear_detalles_caso(casos[0])
        else:
            return "No hemos encontrado casos asociados al email proporcionado. Si crees que es un error, por favor contacta directamente con nuestras oficinas o verifica el email e inténtalo de nuevo."




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
    
    # Verificar si el nombre es el mismo que el tipo de reunión (corrección)
    if estado_usuario["datos"]["nombre"] and estado_usuario["datos"]["nombre"].lower() == estado_usuario["tipo_reunion"]:
        estado_usuario["datos"]["nombre"] = None
        if "nombre" not in datos_faltantes:
            datos_faltantes.append("nombre")
    
    # Verificar si el cliente existe por su email (si tenemos el email)
    if estado_usuario["datos"]["email"] and not estado_usuario["datos"]["nombre"]:
        cliente = _buscar_cliente_por_email(estado_usuario["datos"]["email"])
        if cliente and cliente.get("nombre"):
            estado_usuario["datos"]["nombre"] = cliente["nombre"]
            datos_faltantes = _verificar_datos_faltantes(estado_usuario["datos"])
    
    # Verificar si el cliente existe por su teléfono (si tenemos el teléfono)
    if estado_usuario["datos"]["telefono"] and not estado_usuario["datos"]["nombre"]:
        cliente = _buscar_cliente_por_telefono(estado_usuario["datos"]["telefono"])
        if cliente and cliente.get("nombre"):
            estado_usuario["datos"]["nombre"] = cliente["nombre"]
            if not estado_usuario["datos"]["email"] and cliente.get("email"):
                estado_usuario["datos"]["email"] = cliente["email"]
            datos_faltantes = _verificar_datos_faltantes(estado_usuario["datos"])
    
    # Si el cliente es reconocido (tenemos todos los datos), mostrar mensaje de bienvenida
    if not datos_faltantes:
        cliente_existente = _buscar_cliente_por_email(estado_usuario["datos"]["email"])
        if cliente_existente:
            estado_usuario["estado"] = "esperando_confirmacion"
            fecha_formateada = datetime.datetime.strptime(estado_usuario["fecha"], "%Y-%m-%d").strftime("%d/%m/%Y")
            duracion = TIPOS_REUNION[estado_usuario["tipo_reunion"]]["duracion_cliente"]
            return (f"¡Bienvenido de nuevo, {estado_usuario['datos']['nombre']}! Hemos reconocido tus datos. Resumiendo tu cita:\n"
                    f"- Tipo: {estado_usuario['tipo_reunion']}\n"
                    f"- Fecha: {fecha_formateada}\n"
                    f"- Hora: {estado_usuario['hora']}\n"
                    f"- Duración: {duracion} minutos\n"
                    f"- Tema: {estado_usuario['tema_reunion']}\n"
                    f"- Nombre: {estado_usuario['datos']['nombre']}\n"
                    f"- Email: {estado_usuario['datos']['email']}\n"
                    f"- Teléfono: {estado_usuario['datos']['telefono']}\n\n" +
                    MENSAJES_MENU["confirmacion"])
    
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
                f"- Tema: {estado_usuario['tema_reunion']}\n"
                f"- Nombre: {estado_usuario['datos']['nombre']}\n"
                f"- Email: {estado_usuario['datos']['email']}\n"
                f"- Teléfono: {estado_usuario['datos']['telefono']}\n\n" +
                MENSAJES_MENU["confirmacion"])
    
def _preguntar_cambios(estado_usuario):
    """Pregunta al usuario qué desea cambiar de la cita."""
    # Actualizar el estado para manejar la respuesta sobre qué cambiar
    estado_usuario["estado"] = "esperando_seleccion_cambio"
    
    return ("¿Qué información deseas cambiar?\n"
            "[MENU:Fecha y hora|Tipo de reunión|Tema|Mis datos personales]")

def _confirmar_cita(estado_usuario, user_id, user_states):
    """Confirma la cita y resetea el estado del usuario"""
    # Agendar cita en el calendario
    evento = agendar_en_calendario(
        estado_usuario["fecha"], 
        estado_usuario["hora"], 
        estado_usuario["tipo_reunion"], 
        estado_usuario["datos"],
        estado_usuario["tema_reunion"]
    )
    
    # Enviar correos de confirmación
    enviar_correo_confirmacion(
        estado_usuario["datos"],
        estado_usuario["fecha"],
        estado_usuario["hora"],
        estado_usuario["tipo_reunion"],
        estado_usuario["tema_reunion"]
    )
    
    # Guardar en base de datos
    cita_id = f"cita_{len(citas_db) + 1:04d}"
    citas_db[cita_id] = {
        "tipo": estado_usuario["tipo_reunion"],
        "fecha": estado_usuario["fecha"],
        "hora": estado_usuario["hora"],
        "tema": estado_usuario["tema_reunion"],
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
    reset_conversacion(user_id, user_states)
    
    return (f"¡Cita confirmada con éxito! Se ha agendado una consulta legal {estado_usuario['tipo_reunion']} para el {fecha_formateada} a las {estado_usuario['hora']} ({duracion} minutos).\n\n"
            f"Tema de la consulta: {estado_usuario['tema_reunion']}\n\n"
            f"Hemos enviado un correo de confirmación a {estado_usuario['datos']['email']} con todos los detalles.\n\n"
            f"Gracias por usar nuestro servicio. ¿Hay algo más en lo que pueda ayudarte?")


def _buscar_cliente_por_email(email):
    """
    Busca si un cliente existe en la base de datos por su email.
    
    Args:
        email: Email del cliente a buscar
        
    Returns:
        Diccionario con los datos del cliente si existe, None en caso contrario
    """
    if email in clientes_db:
        return clientes_db[email]
    return None

# 2. Añadir una función para buscar clientes por teléfono
def _buscar_cliente_por_telefono(telefono):
    """
    Busca si un cliente existe en la base de datos por su teléfono.
    
    Args:
        telefono: Número de teléfono del cliente a buscar
        
    Returns:
        Diccionario con los datos del cliente si existe, None en caso contrario
    """
    for email, cliente in clientes_db.items():
        if cliente.get("telefono") == telefono:
            return cliente
    return None

def _buscar_cliente_por_telefono(telefono):
    """
    Busca si un cliente existe en la base de datos por su teléfono.
    
    Args:
        telefono: Número de teléfono del cliente a buscar
        
    Returns:
        Diccionario con los datos del cliente si existe, None en caso contrario
    """
    for email, cliente in clientes_db.items():
        if cliente.get("telefono") == telefono:
            return cliente
    return None


# Añade estas funciones auxiliares para la consulta de casos al final del archivo

def _buscar_caso_por_numero(numero_expediente):
    """
    Busca un caso legal por su número de expediente.
    
    Args:
        numero_expediente: Número de referencia del caso
        
    Returns:
        Diccionario con la información del caso o None si no se encuentra
    """
    if numero_expediente in casos_db:
        caso = casos_db[numero_expediente].copy()
        caso["numero"] = numero_expediente  # Añadir el número al diccionario
        return caso
    return None

def _buscar_casos_por_email(email):
    """
    Busca todos los casos asociados a un cliente por su email.
    
    Args:
        email: Email del cliente
        
    Returns:
        Lista de diccionarios con la información de los casos encontrados
    """
    casos_encontrados = []
    
    for numero, caso in casos_db.items():
        if caso["cliente_email"].lower() == email.lower():
            caso_copia = caso.copy()
            caso_copia["numero"] = numero  # Añadir el número al diccionario
            casos_encontrados.append(caso_copia)
    
    return casos_encontrados

def _formatear_detalles_caso(caso):
    """
    Formatea los detalles de un caso para mostrarlos al cliente.
    
    Args:
        caso: Diccionario con la información del caso
        
    Returns:
        String con la información formateada del caso
    """
    # Obtener la descripción del estado o usar el estado directamente
    estado_desc = ESTADOS_CASO.get(caso["estado"], caso["estado"].replace("_", " ").title())
    
    # Formatear fecha
    from datetime import datetime
    fecha_actualiz = datetime.strptime(caso["ultima_actualizacion"], "%Y-%m-%d").strftime("%d/%m/%Y")
    
    # Preparar la respuesta
    respuesta = (
        f"📁 Información del caso: {caso['numero']}\n\n"
        f"Asunto: {caso['titulo']}\n"
        f"Estado actual: {estado_desc}\n"
        f"Abogado asignado: {caso['abogado']}\n"
        f"Última actualización: {fecha_actualiz}\n\n"
        f"Descripción: {caso['descripcion']}\n\n"
        f"Últimas actuaciones:\n"
    )
    
    # Añadir notas recientes (limitadas a las 3 últimas)
    notas = sorted(caso["notas"], key=lambda x: x["fecha"], reverse=True)
    for i, nota in enumerate(notas[:3]):
        fecha_nota = datetime.strptime(nota["fecha"], "%Y-%m-%d").strftime("%d/%m/%Y")
        respuesta += f"- {fecha_nota}: {nota['texto']}\n"
    
    # Añadir mensaje final
    respuesta += "\nSi necesitas más información o programar una cita de seguimiento, no dudes en indicármelo."
    
    return respuesta
