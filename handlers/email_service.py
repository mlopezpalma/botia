import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_CONFIG, TIPOS_REUNION

def enviar_correo_confirmacion(datos_cliente, fecha, hora, tipo_reunion):
    """
    Simula el envío de correos de confirmación.
    En un entorno real, esta función enviaría correos a través de SMTP.
    
    Args:
        datos_cliente: Diccionario con datos del cliente
        fecha: Fecha en formato "YYYY-MM-DD"
        hora: Hora en formato "HH:MM"
        tipo_reunion: Tipo de reunión
    
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
