import datetime
import re
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
from handlers.email_service import enviar_correo_confirmacion, enviar_sms_confirmacion, enviar_correo_cancelacion, enviar_sms_cancelacion

# Añadir importación de casos_db y ESTADOS_CASO al inicio del archivo
from config import HORARIOS_POR_TIPO, TIPOS_REUNION, INTENCIONES, MENSAJES_MENU, citas_db, clientes_db, casos_db, ESTADOS_CASO

from flask import url_for

# Configurar logging
import logging
logger = logging.getLogger(__name__)



# Modificar la función reset_conversacion para incluir el nuevo estado
# Modificar la función reset_conversacion para incluir la información de documentos
def reset_conversacion(user_id, user_states, preserve_user_data=True):
    """
    Reinicia el estado de la conversación para un usuario específico.
    
    Args:
        user_id: ID del usuario
        user_states: Diccionario de estados de usuario
        preserve_user_data: Si se deben preservar los datos personales del usuario
    """
    # Guardar datos del usuario si están disponibles y deseamos preservarlos
    datos_usuario = None
    if preserve_user_data and user_id in user_states and "datos" in user_states[user_id]:
        datos_usuario = user_states[user_id]["datos"]

    # Eliminar completamente el estado anterior
    if user_id in user_states:
        del user_states[user_id]

    # Crear un nuevo estado limpio
    user_states[user_id] = {
        "estado": "inicial",
        "tipo_reunion": None,
        "fecha": None,
        "hora": None,
        "tema_reunion": None,
        "datos": datos_usuario if datos_usuario else {"nombre": None, "email": None, "telefono": None},
        "consulta_caso": {
            "numero_expediente": None,
            "email_cliente": None,
            "caso_encontrado": False
        },
        "documentos_pendientes": False,  # Añadir esta línea para rastrear si hay documentos pendientes
        "cita_id_temp": None,  # ID temporal de cita para asociar documentos
        "doc_upload_token": None  # Token para subir documentos después de la conversación
    }
    print(f"DEBUG - Conversación reiniciada para usuario: {user_id}, datos preservados: {preserve_user_data}")

# Añadir esta función para manejar la solicitud de documentos
def _solicitar_documentos(estado_usuario):
    """Solicita al usuario documentos para la cita."""
    estado_usuario["documentos_pendientes"] = True

    # Importar el gestor de tokens
    import token_manager
    
    # Generar token
    cita_id = estado_usuario.get('cita_id_temp')
    if not cita_id:
        return "Error al generar token para documentos. Por favor, contacta con soporte."
    
    token = token_manager.generate_token(cita_id)
    estado_usuario["doc_upload_token"] = token
   
    
    # Intentar obtener la función get_base_url de app
    try:
        from app import get_base_url
        base_url = get_base_url()
    except (ImportError, AttributeError):
        # Si falla, usar valor predeterminado
        base_url = "http://127.0.0.1:5000"

    # Usar URL absoluta para asegurar que funcione desde cualquier contexto
    #base_url = "http://127.0.0.1:5000"  # Para desarrollo local
    # En producción sería algo como "https://tudominio.com"
    
    # Generar el mensaje de solicitud de documentos
    mensaje = f"""
¿Deseas adjuntar algún documento para esta cita? Esto puede ser útil para que el abogado pueda revisar previamente información relevante.

Puedes subir documentos como:
- Contratos
- Facturas
- Escrituras
- Identificaciones
- Cualquier otro documento relevante para tu consulta

Si deseas adjuntar algún documento, puedes hacerlo ahora usando este enlace: {base_url}/documentos/subir/{token}
[MENU:Sí, quiero adjuntar documentos|No, continuaré sin documentos]
"""
    return mensaje



def generar_respuesta(mensaje, user_id, user_states):
    print(f"DEBUG - generar_respuesta recibió: '{mensaje}' de usuario: {user_id}")

    # Preparar el mensaje en minúsculas para análisis
    mensaje_lower = mensaje.lower().strip()

    # Estado del usuario
    if user_id not in user_states:
        reset_conversacion(user_id, user_states, preserve_user_data=True)

    estado_usuario = user_states[user_id]
    print(f"DEBUG - estado actual del usuario: {estado_usuario['estado']}")

    # Manejo especial para cancelación de citas
    if "cancelar" in mensaje_lower and "cita" in mensaje_lower:
        if estado_usuario["estado"] in ["esperando_seleccion_cita_cancelar", "esperando_confirmacion_cancelacion", "esperando_datos_cancelacion"]:
            # Ya estamos en proceso de cancelación, procesar selección o confirmación
            return procesar_seleccion_cancelacion(mensaje, user_id, user_states)
        else:
            # Iniciar proceso de cancelación
            return cancelar_cita_cliente(user_id, user_states)
    
    # Continuar con estados de cancelación
    if estado_usuario["estado"] in ["esperando_seleccion_cita_cancelar", "esperando_confirmacion_cancelacion", "esperando_datos_cancelacion"]:
        return procesar_seleccion_cancelacion(mensaje, user_id, user_states)
    
    # Detectar despedida o finalización
    palabras_despedida = ["no gracias", "adiós", "adios", "hasta luego", "terminar", 
                         "finalizar", "cerrar", "no quiero", "no deseo", "eso es todo",
                         "nada más", "no necesito", "gracias", "ya está", "ya terminé"]
    
    if any(palabra in mensaje_lower for palabra in palabras_despedida) or mensaje_lower == "no":
        # Si estamos en un estado donde "no" puede ser una respuesta normal, verificar contexto
        if estado_usuario["estado"] == "esperando_confirmacion":
            # Aquí "no" significa cambiar detalles, no despedida
            if mensaje_lower == "no" or "cambiar" in mensaje_lower:
                pass  # Continuar con el flujo normal
            else:
                # Es una despedida - borrado completo porque el usuario se está despidiendo
                reset_conversacion(user_id, user_states, preserve_user_data=False)
                return "Gracias por usar nuestro servicio de asistencia para citas legales. ¡Hasta pronto!"
        else:
            # En cualquier otro estado, es una despedida - borrado completo
            reset_conversacion(user_id, user_states, preserve_user_data=False) 
            return "Gracias por usar nuestro servicio de asistencia para citas legales. ¡Hasta pronto!"
    
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
        
        # Verificar si ya tenemos datos del usuario para personalizar el saludo
        if estado_usuario["datos"]["nombre"]:
            nombre_cliente = estado_usuario["datos"]["nombre"].split()[0]  # Primer nombre
            
            if intencion == "saludo":
                estado_usuario["estado"] = "esperando_inicio"
                return (f"¡Hola de nuevo, {nombre_cliente}! Soy el asistente de citas legales. Puedo ayudarte a agendar una consulta con nuestros abogados o consultar el estado de tu caso.\n" + 
                        "¿Qué te gustaría hacer? [MENU:Agendar una cita|Consultar estado de mi caso|Cancelar cita]")
            
            elif intencion == "agendar":
                estado_usuario["estado"] = "esperando_tipo_reunion"
                return MENSAJES_MENU["tipo_reunion"]
                
            elif intencion == "consultar_estado":
                estado_usuario["estado"] = "esperando_opcion_consulta"
                return MENSAJES_MENU["consulta_estado"]
            
            else:
                # Si no se identifica intención específica, ofrecer opciones con saludo personalizado
                estado_usuario["estado"] = "esperando_inicio"
                return (f"Bienvenido de nuevo, {nombre_cliente}. Puedo ayudarte a agendar una consulta o verificar el estado de tu caso.\n" + 
                       "¿Qué te gustaría hacer? [MENU:Agendar una cita|Consultar estado de mi caso|Cancelar cita]")
        else:
            # Comportamiento original para usuarios sin datos previos
            if intencion == "saludo":
                estado_usuario["estado"] = "esperando_inicio"
                return ("¡Hola! Soy el asistente de citas legales. Puedo ayudarte a agendar una consulta con nuestros abogados o consultar el estado de tu caso.\n" + 
                        "¿Qué te gustaría hacer? [MENU:Agendar una cita|Consultar estado de mi caso|Cancelar cita]")
            
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
                       "¿Qué te gustaría hacer? [MENU:Agendar una cita|Consultar estado de mi caso|Cancelar cita]")
    
    elif estado_usuario["estado"] == "esperando_inicio":
        # Si el usuario selecciona "Agendar una cita"
        if mensaje_lower == "agendar una cita" or "agendar" in mensaje_lower or "cita" in mensaje_lower:
            estado_usuario["estado"] = "esperando_tipo_reunion"
            return MENSAJES_MENU["tipo_reunion"]
        
        # Si el usuario selecciona "Cancelar cita"
        elif mensaje_lower == "cancelar cita" or "cancelar" in mensaje_lower:
            return cancelar_cita_cliente(user_id, user_states)
        
        # Verificar si quiere consultar estado del caso
        elif "estado" in mensaje_lower or "consultar" in mensaje_lower or "caso" in mensaje_lower or "expediente" in mensaje_lower:
            estado_usuario["estado"] = "esperando_opcion_consulta"
            return MENSAJES_MENU["consulta_estado"]
        
        # Verificar si el mensaje es un tipo de reunión
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
            
        # Si no se reconoce la intención, preguntar de nuevo
        return "Por favor, indica qué deseas hacer: agendar una cita (presencial, videoconferencia o telefónica) o consultar el estado de un caso."

    elif estado_usuario["estado"] == "esperando_tipo_reunion":
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
            return ("Para ver el calendario completo, se mostrará un calendario visual abajo donde podrás seleccionar una fecha disponible. [Indicador pequeño]\n\n"
                    "También puedes indicarme directamente qué día te gustaría agendar tu cita (ej: mañana, próximo lunes, etc.)")
        
        # Si no se reconoce la preferencia, preguntar de nuevo
        return "Por favor, indica cómo te gustaría agendar tu cita: Lo antes posible, En un día específico, o Ver calendario."
    
    elif estado_usuario["estado"] == "esperando_fecha" or estado_usuario["estado"] == "mostrando_calendario":
        # Si el mensaje es exactamente "Ver calendario" (podría ser una confusión del usuario)
        if mensaje_lower == "ver calendario":
            return ("El calendario ya está visible abajo. Por favor, selecciona una fecha haciendo clic en uno de los días disponibles (en verde), o escribe una fecha específica como 'mañana' o 'próximo lunes'.")
        
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
            return "No he podido identificar la fecha. Por favor, selecciona un día directamente en el calendario que se muestra abajo, o indica una fecha específica como 'mañana', 'próximo lunes', etc."
    
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
            # MODIFICACIÓN: Verificar primero si ya tenemos el email del usuario
            if estado_usuario["datos"]["email"]:
                # Ya tenemos el email, usarlo directamente
                email = estado_usuario["datos"]["email"]
            
            # Comprobar si el email existe en la base de datos de casos
                email_existe = False
                for caso in casos_db.values():
                    if caso["cliente_email"].lower() == email.lower():
                        email_existe = True
                        break
            
                if email_existe:
                    # Almacenar el email para verificación posterior
                    estado_usuario["consulta_caso"]["email_cliente"] = email

                    # Generar un código de verificación
                    import random
                    codigo_verificacion = ''.join(random.choices('0123456789', k=6))
                
                    # Almacenar el código para verificación posterior
                    estado_usuario["consulta_caso"]["codigo_verificacion"] = codigo_verificacion
                    estado_usuario["estado"] = "esperando_codigo_verificacion"
                
                    # Para fines de prueba, mostramos el código en el mensaje
                    return (f"Ya tengo tu email ({email}). Por seguridad, hemos enviado un código de verificación de 6 dígitos. " +
                           f"Por favor, introduce ese código para acceder a la información de tus casos.\n\n" +
                           f"(SOLO PARA PRUEBAS: Tu código es {codigo_verificacion})")
                else:
                    estado_usuario["estado"] = "esperando_inicio"
                    return f"No hemos encontrado casos asociados a tu email ({email}). Si crees que es un error, por favor contacta directamente con nuestras oficinas."
            else:
                # No tenemos el email, pedirlo
                estado_usuario["estado"] = "esperando_email_cliente"
                return "Por favor, indícame tu dirección de email para buscar tus casos:"
        
        else:
            return "No he entendido tu elección. " + MENSAJES_MENU["consulta_estado"]
            
    elif estado_usuario["estado"] == "esperando_email_cliente":
        # Buscar casos por email del cliente
        email = mensaje.strip().lower()
        
        # Comprobar si el email existe en la base de datos de casos
        email_existe = False
        for caso in casos_db.values():
            if caso["cliente_email"].lower() == email.lower():
                email_existe = True
                break
        
        if email_existe:
            # Almacenar el email para verificación posterior y para sincronizar datos de usuario
            estado_usuario["consulta_caso"]["email_cliente"] = email
            
            # Si tenemos email del cliente pero no nombre ni teléfono, intentar buscar en base de datos
            if not estado_usuario["datos"]["email"]:
                estado_usuario["datos"]["email"] = email
                # Buscar cliente para obtener más datos
                cliente = _buscar_cliente_por_email(email)
                if cliente:
                    if not estado_usuario["datos"]["nombre"] and cliente.get("nombre"):
                        estado_usuario["datos"]["nombre"] = cliente["nombre"]
                    if not estado_usuario["datos"]["telefono"] and cliente.get("telefono"):
                        estado_usuario["datos"]["telefono"] = cliente["telefono"]
            
            # Generar un código de verificación
            import random
            codigo_verificacion = ''.join(random.choices('0123456789', k=6))
            
            # Almacenar el código para verificación posterior
            estado_usuario["consulta_caso"]["codigo_verificacion"] = codigo_verificacion
            estado_usuario["estado"] = "esperando_codigo_verificacion"
            
            # En un entorno real, enviaríamos el código por email
            # Para fines de prueba, mostramos el código en el mensaje
            return (f"Por seguridad, hemos enviado un código de verificación de 6 dígitos " +
                   f"a tu email {email}. Por favor, introduce ese código para acceder a " +
                   f"la información de tus casos.\n\n" +
                   f"(SOLO PARA PRUEBAS: Tu código es {codigo_verificacion})")
        else:
            estado_usuario["estado"] = "esperando_inicio"
            return "No hemos encontrado casos asociados al email proporcionado. Si crees que es un error, por favor contacta directamente con nuestras oficinas o verifica el email e inténtalo de nuevo."
            
    elif estado_usuario["estado"] == "esperando_codigo_verificacion":
        # Verificar el código introducido
        if mensaje.strip() == estado_usuario["consulta_caso"]["codigo_verificacion"]:
            email = estado_usuario["consulta_caso"]["email_cliente"]
            casos = _buscar_casos_por_email(email)
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
            return "El código introducido no es correcto. Por favor, verifica e inténtalo de nuevo, o escribe 'cancelar' para volver al menú principal."
            
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

        # Añadir al final de generar_respuesta() este nuevo case para manejar la decisión de documentos
    elif estado_usuario["estado"] == "esperando_decision_documentos":
       # Procesar la respuesta sobre documentos
        if "sí" in mensaje_lower or "si" in mensaje_lower or "quiero adjuntar" in mensaje_lower or mensaje_lower == "sí, quiero adjuntar documentos":
            # Usuario quiere adjuntar documentos
            # Generar enlace de carga temporal
            upload_token = estado_usuario["doc_upload_token"]
            cita_id = estado_usuario["cita_id_temp"]

            # Importar token_manager y guardar el token
            import token_manager
            from db_manager import DatabaseManager
        
            # Obtener el gestor de base de datos para pasar su db_file
            db_manager = DatabaseManager()
            token_manager.store_token(db_manager.db_file, upload_token, cita_id)

            # Intentar obtener la función get_base_url de app
            try:
                from app import get_base_url
                base_url = get_base_url()
            except (ImportError, AttributeError):
                # Si falla, usar valor predeterminado
                base_url = "http://127.0.0.1:5000"

            # producción sería algo como "https://tudominio.com"
        
            enlace_carga = f"{base_url}/documentos/subir/{upload_token}"
        
            # Reiniciar estado conservando los datos del usuario
            reset_conversacion(user_id, user_states, preserve_user_data=True)
        
            return (f"Puedes subir los documentos para tu cita utilizando el siguiente enlace:\n\n"
                    f"{enlace_carga}\n\n"
                    f"Este enlace estará disponible durante las próximas 24 horas. También puedes subir documentos "
                    f"más adelante a través del panel de cliente.\n\n"
                    f"¿Hay algo más en lo que pueda ayudarte?")
        else:
            # Usuario no quiere adjuntar documentos
            # Reiniciar estado conservando los datos del usuario
            reset_conversacion(user_id, user_states, preserve_user_data=True)
        
            return ("Perfecto, no se adjuntarán documentos a tu cita. Si necesitas enviar algún documento más adelante, "
                    "podrás hacerlo a través del panel de cliente.\n\n"
                    "¿Hay algo más en lo que pueda ayudarte?")


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


# Modificar la función _confirmar_cita para incluir la gestión de documentos
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
    
    # Enviar SMS de confirmación si el teléfono está disponible
    if estado_usuario["datos"]["telefono"]:
        try:
            enviar_sms_confirmacion(
                estado_usuario["datos"]["telefono"],
                estado_usuario["fecha"],
                estado_usuario["hora"],
                estado_usuario["tipo_reunion"],
                estado_usuario["tema_reunion"]
            )
        except Exception as e:
            print(f"Error al enviar SMS: {str(e)}")
    
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
    
    # Guardar ID de cita para posible asociación con documentos
    estado_usuario["cita_id_temp"] = cita_id
    
    # Generar mensaje de confirmación
    fecha_formateada = datetime.datetime.strptime(estado_usuario["fecha"], "%Y-%m-%d").strftime("%d/%m/%Y")
    duracion = TIPOS_REUNION[estado_usuario["tipo_reunion"]]["duracion_cliente"]
    
    # Preguntar si desea adjuntar documentos
    if not estado_usuario["documentos_pendientes"]:
        estado_usuario["estado"] = "esperando_decision_documentos"
        
        mensaje_confirmacion = (f"¡Cita confirmada con éxito! Se ha agendado una consulta legal {estado_usuario['tipo_reunion']} "
                               f"para el {fecha_formateada} a las {estado_usuario['hora']} ({duracion} minutos).\n\n"
                               f"Tema de la consulta: {estado_usuario['tema_reunion']}\n\n"
                               f"Hemos enviado un correo de confirmación a {estado_usuario['datos']['email']} con todos los detalles.\n\n")
        
        return mensaje_confirmacion + _solicitar_documentos(estado_usuario)
    else:
        # Si ya se decidió sobre los documentos, finalizar normalmente
        # Reiniciar estado pero preservar datos del usuario
        reset_conversacion(user_id, user_states, preserve_user_data=True)
        
        return (f"¡Cita confirmada con éxito! Se ha agendado una consulta legal {estado_usuario['tipo_reunion']} "
                f"para el {fecha_formateada} a las {estado_usuario['hora']} ({duracion} minutos).\n\n"
                f"Tema de la consulta: {estado_usuario['tema_reunion']}\n\n"
                f"Hemos enviado un correo de confirmación a {estado_usuario['datos']['email']} con todos los detalles.\n\n"
                f"Gracias por usar nuestro servicio. ¿Hay algo más en lo que pueda ayudarte?")



def _buscar_cliente_por_email(email):
    """
    Busca si un cliente existe en la base de datos por su email.
    Versión mejorada con debugging y normalización.
    
    Args:
        email: Email del cliente a buscar
        
    Returns:
        Diccionario con los datos del cliente si existe, None en caso contrario
    """
    if not email:
        return None
        
    # Normalizar el email (minúsculas y sin espacios)
    email = email.lower().strip()
    
    print(f"DEBUG - Buscando cliente por email: {email}")
    
    # Buscar en la base de datos en memoria
    if email in clientes_db:
        print(f"DEBUG - Cliente encontrado en DB por email: {email}")
        return clientes_db[email]
    
    # Si no está en memoria, intentar buscar en la base de datos SQLite
    try:
        from db_manager import DatabaseManager
        db = DatabaseManager()
        cliente = db.get_cliente_by_email(email)
        if cliente:
            print(f"DEBUG - Cliente encontrado en SQLite por email: {email}")
            # Actualizar la base de datos en memoria para futuras consultas
            clientes_db[email] = {
                "nombre": cliente.get('nombre'),
                "email": cliente.get('email'),
                "telefono": cliente.get('telefono'),
                "citas": []
            }
            return clientes_db[email]
    except Exception as e:
        print(f"ERROR - No se pudo buscar en SQLite: {str(e)}")
    
    print(f"DEBUG - No se encontró cliente con email: {email}")
    return None

# 2. Añadir una función para buscar clientes por teléfono


def _buscar_cliente_por_telefono(telefono):
    """
    Busca si un cliente existe en la base de datos por su teléfono.
    Versión mejorada con debugging y normalización.
    
    Args:
        telefono: Número de teléfono del cliente a buscar
        
    Returns:
        Diccionario con los datos del cliente si existe, None en caso contrario
    """
    if not telefono:
        return None
        
    # Normalizar el teléfono (eliminar espacios, guiones, etc.)
    import re
    telefono_limpio = re.sub(r'[\s\-\(\)\+]', '', telefono)
    
    print(f"DEBUG - Buscando cliente por teléfono: {telefono} (normalizado: {telefono_limpio})")
    
    # Buscar en la base de datos en memoria
    for email, cliente in clientes_db.items():
        tel_cliente = cliente.get("telefono", "")
        if tel_cliente:
            tel_cliente_limpio = re.sub(r'[\s\-\(\)\+]', '', tel_cliente)
            if tel_cliente_limpio == telefono_limpio:
                print(f"DEBUG - Cliente encontrado en DB por teléfono: {email}")
                return cliente
    
    # Si no está en memoria, intentar buscar en la base de datos SQLite
    try:
        from db_manager import DatabaseManager
        db = DatabaseManager()
        cliente = db.get_cliente_by_telefono(telefono)
        if cliente:
            print(f"DEBUG - Cliente encontrado en SQLite por teléfono: {telefono}")
            # Actualizar la base de datos en memoria para futuras consultas
            email = cliente.get('email')
            if email:
                clientes_db[email] = {
                    "nombre": cliente.get('nombre'),
                    "email": cliente.get('email'),
                    "telefono": cliente.get('telefono'),
                    "citas": []
                }
                return clientes_db[email]
    except Exception as e:
        print(f"ERROR - No se pudo buscar en SQLite: {str(e)}")
    
    print(f"DEBUG - No se encontró cliente con teléfono: {telefono}")
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

# Añadir al archivo handlers/conversation.py

def cancelar_cita_cliente(user_id, user_states, datos_cliente=None):
    """
    Permite al cliente cancelar su próxima cita
    
    Args:
        user_id: ID del usuario en la conversación
        user_states: Diccionario con estados de los usuarios
        datos_cliente: Datos del cliente si ya se han identificado
        
    Returns:
        Mensaje de confirmación o error
    """
    # Si no tenemos datos del cliente, los buscamos en el estado
    estado_usuario = user_states[user_id]
    
    if not datos_cliente:
        # Primero verificar si hay datos en el estado actual
        if estado_usuario["datos"].get("email"):
            datos_cliente = {
                "email": estado_usuario["datos"]["email"],
                "nombre": estado_usuario["datos"].get("nombre"),
                "telefono": estado_usuario["datos"].get("telefono")
            }
            print(f"DEBUG - Usando datos del estado: {datos_cliente}")
        else:
            estado_usuario["estado"] = "esperando_datos_cancelacion"
            return "Para cancelar una cita, necesito verificar tu identidad. Por favor, indícame tu email o teléfono."
    
    # Buscar el cliente en la base de datos
    cliente = None
    if datos_cliente.get("email"):
        cliente = _buscar_cliente_por_email(datos_cliente["email"])
    elif datos_cliente.get("telefono"):
        cliente = _buscar_cliente_por_telefono(datos_cliente["telefono"])
    
    if not cliente:
        estado_usuario["estado"] = "esperando_datos_cancelacion"
        return "No he podido encontrar tus datos en nuestro sistema. Por favor, proporciona tu email o teléfono para verificar tu identidad."
    
    # Buscar citas pendientes del cliente
    email_cliente = cliente.get("email")
    
    # Obtener la fecha actual para filtrar correctamente
    fecha_actual = datetime.datetime.now()
    
    # Encontrar todas las citas del cliente
    citas_cliente = []
    
    # Buscar en la base de datos de citas por el email
    for cita_id, cita_info in citas_db.items():
        if cita_info["cliente"]["email"] == email_cliente:
            # Solo considerar citas futuras que no estén canceladas
            try:
                fecha_cita = datetime.datetime.strptime(cita_info["fecha"], "%Y-%m-%d")
                hora_partes = cita_info["hora"].split(":")
                fecha_hora_cita = fecha_cita.replace(
                    hour=int(hora_partes[0]), 
                    minute=int(hora_partes[1])
                )
                
                # Verificar que la cita es futura y no está cancelada
                if fecha_hora_cita > fecha_actual and cita_info.get("estado", "pendiente") != "cancelada":
                    # Añadir ID para referencia posterior
                    cita_info["id"] = cita_id
                    citas_cliente.append(cita_info)
            except Exception as e:
                logger.warning(f"Error al procesar fecha de cita {cita_id}: {e}")
                continue
    
    # Ordenar por fecha/hora
    citas_cliente.sort(key=lambda x: (x["fecha"], x["hora"]))
    
    # Verificar si hay citas pendientes
    if not citas_cliente:
        estado_usuario["estado"] = "inicial"
        return f"No hemos encontrado citas pendientes para ti, {cliente.get('nombre', 'estimado cliente')}. ¿En qué más puedo ayudarte?"
    
    # Guardar las citas en el estado para referencia posterior
    estado_usuario["citas_cancelables"] = citas_cliente
    
    # Si hay una sola cita, ofrecer cancelarla directamente
    if len(citas_cliente) == 1:
        cita = citas_cliente[0]
        fecha_formateada = datetime.datetime.strptime(cita["fecha"], "%Y-%m-%d").strftime("%d/%m/%Y")
        
        estado_usuario["estado"] = "esperando_confirmacion_cancelacion"
        estado_usuario["cita_a_cancelar"] = cita["id"]
        
        return f"Hemos encontrado una cita pendiente para el {fecha_formateada} a las {cita['hora']} de tipo {cita['tipo']}. ¿Deseas cancelarla? [MENU:Sí, cancelar cita|No, mantener cita]"
    
    # Si hay varias citas, mostrar un menú para seleccionar
    mensaje = f"Hemos encontrado {len(citas_cliente)} citas pendientes para ti:\n\n"
    
    opciones_menu = []
    for i, cita in enumerate(citas_cliente, 1):
        fecha_formateada = datetime.datetime.strptime(cita["fecha"], "%Y-%m-%d").strftime("%d/%m/%Y")
        mensaje += f"{i}. {fecha_formateada} a las {cita['hora']} - {cita['tipo']}"
        if cita.get("tema"):
            mensaje += f" - Tema: {cita['tema']}"
        mensaje += "\n"
        opciones_menu.append(f"Cancelar cita {i}")
    
    opciones_menu.append("No cancelar ninguna")
    estado_usuario["estado"] = "esperando_seleccion_cita_cancelar"
    
    mensaje += "\n¿Cuál deseas cancelar? "
    
    # Construir el menú con las opciones disponibles
    menu_options = "|".join(opciones_menu)
    return mensaje + f"[MENU:{menu_options}]"

def procesar_seleccion_cancelacion(mensaje, user_id, user_states):
    """
    Procesa la selección de la cita a cancelar
    
    Args:
        mensaje: Mensaje del usuario
        user_id: ID del usuario en la conversación
        user_states: Diccionario con estados de los usuarios
        
    Returns:
        Mensaje de confirmación o error
    """
    estado_usuario = user_states[user_id]
    
    if estado_usuario["estado"] == "esperando_datos_cancelacion":
        # Procesar datos de identificación
        datos_identificados = identificar_datos_personales(mensaje)
        
        if datos_identificados["email"] or datos_identificados["telefono"]:
            # Actualizar estado con los datos identificados
            if datos_identificados["email"]:
                estado_usuario["datos"]["email"] = datos_identificados["email"]
            if datos_identificados["telefono"]:
                estado_usuario["datos"]["telefono"] = datos_identificados["telefono"]
            
            # Llamar a cancelar_cita_cliente con los datos actualizados
            return cancelar_cita_cliente(user_id, user_states, estado_usuario["datos"])
        else:
            return "No he podido identificar tu email o teléfono. Por favor, proporciona tu email o teléfono para poder buscar tus citas."
    
    elif estado_usuario["estado"] == "esperando_seleccion_cita_cancelar":
        # Determinar qué cita se quiere cancelar
        citas = estado_usuario["citas_cancelables"]
        
        indice = None
        
        # Verificar si el mensaje contiene un número de cita
        if mensaje.isdigit():
            indice = int(mensaje) - 1
        else:
            # Buscar patrones como "Cancelar cita X" o simplemente el número
            match = re.search(r'cancelar\s+cita\s+(\d+)', mensaje.lower())
            if match:
                indice = int(match.group(1)) - 1
            else:
                # Buscar solo el número
                match = re.search(r'(\d+)', mensaje)
                if match:
                    indice = int(match.group(1)) - 1
                else:
                    # No cancelar ninguna
                    if "no cancelar" in mensaje.lower() or "ninguna" in mensaje.lower():
                        estado_usuario["estado"] = "inicial"
                        return "Entendido, no se cancelará ninguna cita. ¿En qué más puedo ayudarte?"
        
        # Verificar que el índice es válido
        if indice is not None and 0 <= indice < len(citas):
            cita = citas[indice]
            estado_usuario["estado"] = "esperando_confirmacion_cancelacion"
            estado_usuario["cita_a_cancelar"] = cita["id"]
            
            fecha_formateada = datetime.datetime.strptime(cita["fecha"], "%Y-%m-%d").strftime("%d/%m/%Y")
            mensaje = f"¿Estás seguro de que deseas cancelar tu cita del {fecha_formateada} a las {cita['hora']}?"
            if cita.get("tema"):
                mensaje += f"\nTema: {cita['tema']}"
            mensaje += "\n\n[MENU:Sí, cancelar|No, mantener]"
            return mensaje
        else:
            return "No he podido identificar qué cita deseas cancelar. Por favor, elige una de las opciones numeradas."
    
    elif estado_usuario["estado"] == "esperando_confirmacion_cancelacion":
        # Confirmar la cancelación
        confirmacion = mensaje.lower()
        if "si" in confirmacion or "sí" in confirmacion or "cancelar" in confirmacion:
            cita_id = estado_usuario["cita_a_cancelar"]
            
            # Obtener información de la cita antes de cancelarla
            cita_info = citas_db.get(cita_id, {})
            
            # Cambiar estado de la cita a cancelada
            if cita_id in citas_db:
                citas_db[cita_id]["estado"] = "cancelada"
                
                # Intentar actualizar la base de datos SQLite también
                try:
                    # Extraer el ID numérico si está en formato "cita_XXXX"
                    if cita_id.startswith("cita_"):
                        cita_id_num = int(cita_id.split("_")[1])
                    else:
                        cita_id_num = int(cita_id)
                    
                    # Actualizar en SQLite
                    from db_manager import DatabaseManager
                    db = DatabaseManager()
                    db.update_cita(cita_id_num, estado="cancelada")
                    logger.info(f"Cita {cita_id_num} actualizada en base de datos SQLite")
                except Exception as e:
                    logger.error(f"Error al actualizar cita en SQLite: {str(e)}")
                
                # Enviar notificación por email y SMS
                if cita_info:
                    try:
                        from handlers.email_service import enviar_correo_cancelacion, enviar_sms_cancelacion
                        
                        datos_cliente = cita_info.get("cliente", {})
                        fecha = cita_info.get("fecha", "")
                        hora = cita_info.get("hora", "")
                        tipo_reunion = cita_info.get("tipo", "")
                        tema = cita_info.get("tema", "")
                        
                        # Enviar notificaciones
                        if datos_cliente.get("email"):
                            enviar_correo_cancelacion(datos_cliente, fecha, hora, tipo_reunion, tema)
                        
                        if datos_cliente.get("telefono"):
                            enviar_sms_cancelacion(datos_cliente["telefono"], fecha, hora, tipo_reunion, tema)
                            
                        logger.info(f"Notificaciones de cancelación enviadas para cita {cita_id}")
                    except Exception as e:
                        logger.error(f"Error al enviar notificaciones de cancelación: {str(e)}")
                
                # Resetear estado
                reset_conversacion(user_id, user_states)
                
                fecha_formateada = datetime.datetime.strptime(cita_info.get("fecha", ""), "%Y-%m-%d").strftime("%d/%m/%Y") if "fecha" in cita_info else ""
                
                return f"Tu cita del {fecha_formateada} a las {cita_info.get('hora', '')} ha sido cancelada con éxito. " + \
                       f"Hemos enviado una confirmación a tu correo electrónico. ¿Necesitas algo más?"
            else:
                return "Lo siento, no se ha podido cancelar la cita. Por favor, contacta directamente con nuestras oficinas."
        else:
            # No se confirma la cancelación
            estado_usuario["estado"] = "inicial"
            return "Entendido, tu cita no será cancelada. ¿En qué más puedo ayudarte?"
    
    # Estado incorrecto
    return "Lo siento, ha ocurrido un error en el proceso de cancelación. Por favor, intenta nuevamente o contacta con nuestras oficinas."



