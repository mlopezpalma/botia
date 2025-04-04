import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_CONFIG, TIPOS_REUNION

def enviar_correo_confirmacion(datos_cliente, fecha, hora, tipo_reunion, tema_reunion=None):
    """
    Simula el envío de correos de confirmación.
    En un entorno real, esta función enviaría correos a través de SMTP.
    
    Args:
        datos_cliente: Diccionario con datos del cliente
        fecha: Fecha en formato "YYYY-MM-DD"
        hora: Hora en formato "HH:MM"
        tipo_reunion: Tipo de reunión
        tema_reunion: Tema o motivo de la reunión (opcional)
    
    Returns:
        True si se envió correctamente (simulado)
    """
    # En un entorno real, se usaría SMTP para enviar correos
    # Aquí simulamos el envío imprimiendo en consola
    print(f"DEBUG - Simulando envío de correo a {datos_cliente['email']}")
    print(f"DEBUG - Asunto: Confirmación de Cita Legal")
    
    # Formatear fecha para mostrar
    fecha_dt = datetime.datetime.strptime(fecha, "%Y-%m-%d")
    fecha_formateada = fecha_dt.strftime("%d/%m/%Y (%A)")
    
    duracion = TIPOS_REUNION[tipo_reunion]["duracion_cliente"]
    
    # Mensaje para el cliente
    mensaje_cliente = f"""
Estimado/a {datos_cliente['nombre']},

Su cita {tipo_reunion} ha sido agendada con éxito para el {fecha_formateada} a las {hora}.

Detalles de la cita:
- Tipo: {tipo_reunion}
- Duración: {duracion} minutos
- Fecha: {fecha_formateada}
- Hora: {hora}
"""

    if tema_reunion:
        mensaje_cliente += f"- Tema de la consulta: {tema_reunion}\n"

    mensaje_cliente += """
Le recordamos que para citas presenciales debe presentarse 5 minutos antes en nuestra oficina.
Para videoconferencias, recibirá un enlace 10 minutos antes de la cita.
Para citas telefónicas, recibirá una llamada al número proporcionado.

Si necesita modificar o cancelar su cita, por favor contacte con nosotros respondiendo a este correo o llamando al teléfono de atención al cliente.

Gracias por confiar en nuestros servicios legales.

Atentamente,
El equipo de Asesoramiento Legal
"""
    print(f"DEBUG - Cuerpo del mensaje para cliente:\n{mensaje_cliente}")
    
    # Mensaje para la empresa
    mensaje_empresa = f"""
NUEVA CITA AGENDADA

Se ha registrado una nueva cita con los siguientes detalles:

- Cliente: {datos_cliente['nombre']}
- Email: {datos_cliente['email']}
- Teléfono: {datos_cliente['telefono']}
- Tipo: {tipo_reunion}
- Fecha: {fecha_formateada}
- Hora: {hora}
- Duración: {duracion} minutos
"""

    if tema_reunion:
        mensaje_empresa += f"- Tema de la consulta: {tema_reunion}\n"

    mensaje_empresa += """
Por favor, asegúrese de preparar todo lo necesario para esta cita.
"""
    print(f"DEBUG - Cuerpo del mensaje para la empresa:\n{mensaje_empresa}")
    
    # En un entorno real, aquí iría el código para enviar los correos
    # usando la configuración de EMAIL_CONFIG
    try:
        # Crear mensaje para el cliente
        msg_cliente = MIMEMultipart()
        msg_cliente['From'] = EMAIL_CONFIG['sender_email']
        msg_cliente['To'] = datos_cliente['email']
        msg_cliente['Subject'] = "Confirmación de Cita Legal"
        msg_cliente.attach(MIMEText(mensaje_cliente, 'plain'))
        
        # Crear mensaje para la empresa
        msg_empresa = MIMEMultipart()
        msg_empresa['From'] = EMAIL_CONFIG['sender_email']
        msg_empresa['To'] = "empresa@example.com"
        msg_empresa['Subject'] = "Nueva Cita Agendada"
        msg_empresa.attach(MIMEText(mensaje_empresa, 'plain'))
        
        # En modo de desarrollo/debug, solo imprimimos los mensajes
        # En producción, descomentar el siguiente código para enviar correos reales
        """
        # Establecer conexión con el servidor SMTP
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['port'])
        server.starttls()
        server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['password'])
        
        # Enviar correos
        server.send_message(msg_cliente)
        server.send_message(msg_empresa)
        
        # Cerrar conexión
        server.quit()
        """
        
        return True
    except Exception as e:
        print(f"ERROR - No se pudo enviar el correo: {str(e)}")
        return False

def obtener_dias_disponibles(mes, anio, tipo_reunion):
    """
    Obtiene los días con disponibilidad para un mes y tipo de reunión específicos.
    
    Args:
        mes: Número de mes (1-12)
        anio: Año (ej: 2023)
        tipo_reunion: Tipo de reunión (presencial, videoconferencia, telefonica)
        
    Returns:
        Lista de números de días con disponibilidad
    """
    import calendar
    import datetime
    
    # Obtener el número de días en el mes
    _, num_dias = calendar.monthrange(anio, mes)
    
    # Lista para almacenar los días disponibles
    dias_disponibles = []
    
    # Comprobar cada día del mes
    for dia in range(1, num_dias + 1):
        try:
            # Crear fecha para el día
            fecha = datetime.datetime(anio, mes, dia)
            
            # Saltar fines de semana
            if fecha.weekday() >= 5:  # 5=Sábado, 6=Domingo
                continue
                
            # Obtener horarios disponibles para ese día
            horarios = obtener_horarios_disponibles(fecha, tipo_reunion)
            
            # Si hay horarios disponibles, añadir el día a la lista
            if horarios:
                dias_disponibles.append(dia)
        except Exception as e:
            print(f"Error al comprobar disponibilidad del día {dia}/{mes}/{anio}: {str(e)}")
    
    return dias_disponibles

# En caso de error o para uso en tests, versión simulada

def _obtener_dias_disponibles_simulados(mes, anio, tipo_reunion):
    """Versión simulada de obtener_dias_disponibles para usar en caso de errores."""
    import calendar
    import datetime
    import random
    
    print(f"ADVERTENCIA: Usando días disponibles simulados para {mes}/{anio} y {tipo_reunion}")
    
    # Obtener el número de días en el mes
    _, num_dias = calendar.monthrange(anio, mes)
    
    # Determinar días laborables (lunes a viernes)
    dias_laborables = []
    for dia in range(1, num_dias + 1):
        fecha = datetime.datetime(anio, mes, dia)
        if fecha.weekday() < 5:  # 0-4 = Lunes a Viernes
            dias_laborables.append(dia)
    
    # Seleccionar aleatoriamente entre 60% y 80% de los días laborables como disponibles
    num_disponibles = int(len(dias_laborables) * random.uniform(0.6, 0.8))
    dias_disponibles = sorted(random.sample(dias_laborables, num_disponibles))
    
    return dias_disponibles


def enviar_sms_confirmacion(telefono, fecha, hora, tipo_reunion, tema_reunion=None):
    """
    Envía un SMS de confirmación utilizando Twilio.
    
    Args:
        telefono: Número de teléfono del cliente
        fecha: Fecha en formato "YYYY-MM-DD"
        hora: Hora en formato "HH:MM"
        tipo_reunion: Tipo de reunión
        tema_reunion: Tema o motivo de la reunión (opcional)
    
    Returns:
        True si se envió correctamente (simulado)
    """
    import os
    from datetime import datetime
    from twilio.rest import Client
    from config import TIPOS_REUNION
    
    # Credenciales de Twilio
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    twilio_number = os.environ.get('TWILIO_PHONE_NUMBER', '')  # Número de teléfono de Twilio
    
    if not all([account_sid, auth_token, twilio_number]):
        print("ERROR - Faltan credenciales de Twilio para enviar SMS")
        return False
    
    try:
        # Formatear fecha para mostrar
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d")
        fecha_formateada = fecha_dt.strftime("%d/%m/%Y")
        
        duracion = TIPOS_REUNION[tipo_reunion]["duracion_cliente"]
        
        # Crear mensaje SMS
        mensaje = f"Confirmación de cita legal: {tipo_reunion} el {fecha_formateada} a las {hora}. "
        
        if tema_reunion:
            mensaje += f"Tema: {tema_reunion}. "
            
        mensaje += f"Duración: {duracion} min. Gracias por utilizar nuestros servicios."
        
        # Limpiar número de teléfono (quitar espacios, guiones, etc.)
        import re
        telefono_limpio = re.sub(r'[\s\-\(\)\+]', '', telefono)
        if not telefono_limpio.startswith('+'):
            telefono_limpio = '+34' + telefono_limpio  # Añadir prefijo España si no tiene código de país
            
        # Enviar SMS con Twilio
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=mensaje,
            from_=twilio_number,
            to=telefono_limpio
        )
        
        print(f"DEBUG - SMS enviado con SID: {message.sid}")
        return True
        
    except Exception as e:
        print(f"ERROR - No se pudo enviar el SMS: {str(e)}")
        return False

# Modificar en handlers/conversation.py la función _confirmar_cita para incluir SMS

# Añadir esta línea después de enviar_correo_confirmacion:
enviar_sms_confirmacion(
    estado_usuario["datos"]["telefono"],
    estado_usuario["fecha"],
    estado_usuario["hora"],
    estado_usuario["tipo_reunion"],
    estado_usuario["tema_reunion"]
)
