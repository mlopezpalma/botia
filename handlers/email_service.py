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
    
# Añadir a handlers/email_service.py

def enviar_correo_cancelacion(datos_cliente, fecha, hora, tipo_reunion, tema=None):
    """
    Envía un correo electrónico notificando la cancelación de una cita.
    
    Args:
        datos_cliente: Diccionario con datos del cliente
        fecha: Fecha en formato "YYYY-MM-DD"
        hora: Hora en formato "HH:MM"
        tipo_reunion: Tipo de reunión
        tema: Tema o motivo de la cita (opcional)
    
    Returns:
        True si se envió correctamente (simulado)
    """
    try:
        print(f"DEBUG - Simulando envío de correo de CANCELACIÓN a {datos_cliente['email']}")
        print(f"DEBUG - Asunto: Cancelación de Cita Legal")
        
        # Formatear fecha para mostrar
        fecha_dt = datetime.datetime.strptime(fecha, "%Y-%m-%d")
        fecha_formateada = fecha_dt.strftime("%d/%m/%Y (%A)")
        
        # Mensaje para el cliente
        mensaje_cliente = f"""
Estimado/a {datos_cliente['nombre']},

Tu cita {tipo_reunion} del {fecha_formateada} a las {hora} ha sido cancelada correctamente.
"""
        
        if tema:
            mensaje_cliente += f"\nTema de la cita: {tema}\n"
            
        mensaje_cliente += """
Si necesitas reagendar, puedes hacerlo respondiendo a este correo o llamando al teléfono de atención al cliente.

Gracias por confiar en nuestros servicios legales.

Atentamente,
El equipo de Asesoramiento Legal
"""
        print(f"DEBUG - Cuerpo del mensaje para cliente:\n{mensaje_cliente}")
        
        # Mensaje para la empresa
        mensaje_empresa = f"""
CITA CANCELADA

Se ha cancelado la siguiente cita:

- Cliente: {datos_cliente['nombre']}
- Email: {datos_cliente['email']}
- Teléfono: {datos_cliente['telefono']}
- Tipo: {tipo_reunion}
- Fecha: {fecha_formateada}
- Hora: {hora}
"""

        if tema:
            mensaje_empresa += f"- Tema: {tema}\n"
            
        print(f"DEBUG - Cuerpo del mensaje para la empresa:\n{mensaje_empresa}")
        
        # En un entorno real, aquí iría el código para enviar los correos
        # usando la configuración de EMAIL_CONFIG
        return True
        
    except Exception as e:
        print(f"ERROR - Error general en enviar_correo_cancelacion: {str(e)}")
        return False

def enviar_sms_cancelacion(telefono, fecha, hora, tipo_reunion, tema=None):
    """
    Envía un SMS notificando la cancelación de una cita.
    
    Args:
        telefono: Número de teléfono del cliente
        fecha: Fecha en formato "YYYY-MM-DD"
        hora: Hora en formato "HH:MM"
        tipo_reunion: Tipo de reunión
        tema: Tema o motivo de la cita (opcional)
    
    Returns:
        True si se envió correctamente (simulado)
    """
    try:
        # Formatear fecha para mostrar
        fecha_dt = datetime.datetime.strptime(fecha, "%Y-%m-%d")
        fecha_formateada = fecha_dt.strftime("%d/%m/%Y")
        
        # Crear mensaje SMS
        mensaje = f"Confirmamos la cancelación de tu cita legal {tipo_reunion} del {fecha_formateada} a las {hora}. "
        
        if tema and len(tema) < 50:  # Limitar longitud del tema para SMS
            mensaje += f"Tema: {tema}. "
            
        mensaje += "Gracias por utilizar nuestros servicios."
        
        print(f"DEBUG - Simulando envío de SMS de cancelación a {telefono}")
        print(f"DEBUG - Mensaje: {mensaje}")
        
        # En un entorno real, aquí iría el código para enviar SMS con Twilio
        return True
        
    except Exception as e:
        print(f"ERROR - No se pudo enviar el SMS de cancelación: {str(e)}")
        return False