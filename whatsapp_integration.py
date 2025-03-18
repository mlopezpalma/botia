# Integración con WhatsApp utilizando Twilio

# Archivo: whatsapp_integration.py

import os
from flask import Flask, request, jsonify
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from handlers.conversation import generar_respuesta

class WhatsAppBot:
    def __init__(self, app):
        self.app = app
        self.user_states = app.user_states if hasattr(app, 'user_states') else {}
        
        # Configurar Twilio
        self.account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.whatsapp_number = os.environ.get('TWILIO_WHATSAPP_NUMBER')
        
        # Comprobar si se han proporcionado las credenciales de Twilio
        self.client = None
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
        
        # Añadir ruta para manejar mensajes de WhatsApp
        app.route('/api/whatsapp', methods=['POST'])(self.handle_whatsapp_message)
    
    def handle_whatsapp_message(self):
        """Maneja los mensajes entrantes de WhatsApp."""
        # Extraer el cuerpo del mensaje y el número de teléfono
        incoming_msg = request.values.get('Body', '').strip()
        sender = request.values.get('From', '').strip()
        
        print(f"DEBUG - WhatsApp: Mensaje recibido de {sender}: '{incoming_msg}'")
        
        # Generar una ID de usuario basada en el número de WhatsApp (sin el prefijo 'whatsapp:')
        user_id = f"whatsapp_{sender.replace('whatsapp:', '')}"
        
        try:
            # Procesar el mensaje utilizando la lógica de conversación existente
            respuesta = generar_respuesta(incoming_msg, user_id, self.user_states)
            
            # Eliminar cualquier formato especial del mensaje (como [MENU:...])
            respuesta_limpia = self._limpiar_mensaje(respuesta)
            
            # Responder utilizando Twilio (Función preferida para producción)
            if self.client:
                self._send_whatsapp_message(sender, respuesta_limpia)
                print(f"DEBUG - WhatsApp: Respuesta enviada a {sender} usando Twilio")
            
            # Responder utilizando TwiML (Alternativa si se utiliza webhook de Twilio)
            resp = MessagingResponse()
            resp.message(respuesta_limpia)
            
            return str(resp)
        except Exception as e:
            print(f"ERROR - WhatsApp: {str(e)}")
            
            # Responder con un mensaje de error
            resp = MessagingResponse()
            resp.message("Lo siento, ha ocurrido un error al procesar tu mensaje. Por favor, inténtalo de nuevo.")
            
            return str(resp)
    
    def _limpiar_mensaje(self, mensaje):
        """Elimina formatos especiales del mensaje para WhatsApp."""
        # Eliminar indicadores especiales
        mensaje = mensaje.replace('[Indicador pequeño]', '')
        
        # Manejar opciones de menú
        import re
        menu_match = re.search(r'\[MENU:(.*?)\]', mensaje)
        if menu_match:
            opciones = menu_match.group(1).split('|')
            menu_formateado = "\n\nOpciones disponibles:\n" + "\n".join([f"- {opcion}" for opcion in opciones])
            mensaje = re.sub(r'\[MENU:.*?\]', menu_formateado, mensaje)
        
        return mensaje
    
    def _send_whatsapp_message(self, to, body):
        """Envía un mensaje de WhatsApp utilizando Twilio."""
        if not self.client:
            print("ERROR - WhatsApp: Cliente de Twilio no inicializado")
            return False
        
        try:
            message = self.client.messages.create(
                from_=f'whatsapp:{self.whatsapp_number}',
                body=body,
                to=to
            )
            print(f"DEBUG - WhatsApp: Mensaje enviado con SID: {message.sid}")
            return True
        except Exception as e:
            print(f"ERROR - WhatsApp: No se pudo enviar el mensaje: {str(e)}")
            return False

