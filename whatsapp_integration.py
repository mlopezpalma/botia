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
        self.enabled = False
        
        if all([self.account_sid, self.auth_token, self.whatsapp_number]):
            try:
                self.client = Client(self.account_sid, self.auth_token)
                self.enabled = True
                print("INFO - Integración de WhatsApp configurada correctamente")
            except Exception as e:
                print(f"ERROR - No se pudo inicializar el cliente de Twilio: {str(e)}")
                self.enabled = False
        else:
            missing = []
            if not self.account_sid:
                missing.append("TWILIO_ACCOUNT_SID")
            if not self.auth_token:
                missing.append("TWILIO_AUTH_TOKEN")
            if not self.whatsapp_number:
                missing.append("TWILIO_WHATSAPP_NUMBER")
                
            print(f"ADVERTENCIA - Faltan credenciales de Twilio: {', '.join(missing)}. La integración con WhatsApp estará deshabilitada")
        
        # Añadir ruta para manejar mensajes de WhatsApp
        app.route('/api/whatsapp', methods=['POST'])(self.handle_whatsapp_message)
    
    def handle_whatsapp_message(self):
        """Maneja los mensajes entrantes de WhatsApp."""
        if not self.enabled:
            return jsonify({"error": "La integración de WhatsApp no está configurada correctamente"}), 503
        
        # Extraer el cuerpo del mensaje y el número de teléfono
        incoming_msg = request.values.get('Body', '').strip()
        sender = request.values.get('From', '').strip()
    
        print(f"DEBUG - WhatsApp: Mensaje recibido de {sender}: '{incoming_msg}'")
    
        # Verificar mensajes vacíos
        if not incoming_msg:
            resp = MessagingResponse()
            resp.message("No se recibió ningún mensaje. Por favor, intenta de nuevo.")
            return str(resp)
    
        # Generar una ID de usuario basada en el número de WhatsApp (sin el prefijo 'whatsapp:')
        user_id = f"whatsapp_{sender.replace('whatsapp:', '')}"
    
        try:
            # Detectar mensajes de reinicio o despedida
            incoming_msg_lower = incoming_msg.lower().strip()
            if incoming_msg_lower in ["reiniciar", "comenzar", "reset", "inicio", "empezar", "start"]:
                # Reiniciar la conversación
                try:
                    if user_id in self.user_states:
                        del self.user_states[user_id]
                except Exception as e:
                    print(f"ERROR - WhatsApp: Error al eliminar estado de usuario: {str(e)}")
            
                try:
                    from handlers.conversation import reset_conversacion
                    reset_conversacion(user_id, self.user_states)
                    mensaje_respuesta = "Conversación reiniciada. ¡Hola! Soy el asistente de citas legales. ¿En qué puedo ayudarte?"
                except Exception as e:
                    print(f"ERROR - WhatsApp: Error al resetear conversación: {str(e)}")
                    mensaje_respuesta = "Conversación reiniciada. ¿En qué puedo ayudarte?"
            
                # Responder usando TwiML (solo una respuesta)
                resp = MessagingResponse()
                resp.message(mensaje_respuesta)
                return str(resp)
        
            # Obtener el estado actual del usuario
            estado_usuario = self.user_states.get(user_id, {})
        
            # Procesamiento especial para respuestas numéricas (selección de menú)
            if incoming_msg.isdigit() and int(incoming_msg) > 0:
                print(f"DEBUG - WhatsApp: Detectada respuesta numérica: {incoming_msg}")
            
                # Obtener el último mensaje enviado al usuario
                last_response = estado_usuario.get('last_whatsapp_response', '')
            
                # Si el último mensaje contenía un menú, extraer las opciones
                import re
                menu_match = re.search(r'\[MENU:(.*?)\]', last_response)
                if menu_match:
                    opciones = menu_match.group(1).split('|')
                    opcion_index = int(incoming_msg) - 1
                
                    # Verificar que el índice es válido
                    if 0 <= opcion_index < len(opciones):
                        # Usar la opción correspondiente como el mensaje
                        incoming_msg = opciones[opcion_index].strip()
                        print(f"DEBUG - WhatsApp: Mensaje convertido a: '{incoming_msg}'")
        
            # Procesar el mensaje utilizando la lógica de conversación existente
            respuesta = generar_respuesta(incoming_msg, user_id, self.user_states)
        
            # Guardar la respuesta original para procesamiento futuro
            if user_id not in self.user_states:
                self.user_states[user_id] = {}
            self.user_states[user_id]['last_whatsapp_response'] = respuesta
        
            # Eliminar cualquier formato especial del mensaje (como [MENU:...])
            respuesta_limpia = self._limpiar_mensaje(respuesta)
        
            # Responder utilizando SOLO TwiML (para evitar mensajes duplicados)
            resp = MessagingResponse()
        
            # Dividir mensajes largos si es necesario (límite ~1600 caracteres)
            if len(respuesta_limpia) <= 1600:
                resp.message(respuesta_limpia)
            else:
                # Dividir en partes
                first_part = respuesta_limpia[:1590] + "... (continúa)"
                resp.message(first_part)
            
                # Enviar la segunda parte usando Twilio directamente
                # Esto solo ocurrirá en casos muy raros donde el mensaje sea muy largo
                second_part = "(continuación) ... " + respuesta_limpia[1590:]
                try:
                    self._send_whatsapp_message_safe(sender, second_part)
                except Exception as e:
                    print(f"ERROR - WhatsApp: Error al enviar segunda parte: {str(e)}")
        
            return str(resp)
        except Exception as e:
            print(f"ERROR - WhatsApp: {str(e)}")
            import traceback
            print(traceback.format_exc())
        
            # Responder con un mensaje de error
            resp = MessagingResponse()
            resp.message("Lo siento, ha ocurrido un error al procesar tu mensaje. Por favor, intenta de nuevo o escribe 'reiniciar' para comenzar una nueva conversación.")
        
            return str(resp)
    
    def _limpiar_mensaje(self, mensaje):
        """
        Limpia y formatea el mensaje para WhatsApp, añadiendo índices numéricos a las opciones de menú.
    
        Args:
            mensaje: El mensaje original con posibles indicadores especiales
        
        Returns:
            Mensaje formateado para WhatsApp
        """
        # Eliminar indicadores especiales
        mensaje = mensaje.replace('[Indicador pequeño]', '')
    
        # Manejar opciones de menú
        import re
        menu_match = re.search(r'\[MENU:(.*?)\]', mensaje)
        if menu_match:
            opciones = menu_match.group(1).split('|')
            menu_formateado = "\n\nOpciones disponibles:\n"
        
            # Añadir índices numéricos a las opciones
            for i, opcion in enumerate(opciones, 1):
                menu_formateado += f"{i}. {opcion.strip()}\n"
        
            # Añadir instrucción para usar los índices
            menu_formateado += "\nResponde con el número de la opción deseada."

            mensaje = re.sub(r'\[MENU:.*?\]', menu_formateado, mensaje)
    
        return mensaje
    
    def _send_whatsapp_message_safe(self, to, body):
        """Envía un mensaje de WhatsApp utilizando Twilio, dividiendo mensajes largos si es necesario."""
        if not self.enabled or not self.client:
            print("ERROR - WhatsApp: Cliente de Twilio no inicializado")
            return False
        
        try:
            # Dividir mensajes largos (límite de WhatsApp ~1600 caracteres)
            max_length = 1600
            messages_sent = 0
            
            if len(body) <= max_length:
                # Mensaje único
                message = self.client.messages.create(
                    from_=f'whatsapp:{self.whatsapp_number}',
                    body=body,
                    to=to
                )
                print(f"DEBUG - WhatsApp: Mensaje enviado con SID: {message.sid}")
                messages_sent = 1
            else:
                # Dividir el mensaje en partes
                parts = []
                
                # Intentar dividir por párrafos para mantener coherencia
                paragraphs = body.split('\n\n')
                current_part = ""
                
                for p in paragraphs:
                    # Si añadir este párrafo excede el límite, enviar lo que tenemos y empezar nuevo
                    if len(current_part) + len(p) + 2 > max_length:
                        if current_part:
                            parts.append(current_part)
                            current_part = p
                        else:
                            # El párrafo es demasiado largo por sí mismo, dividirlo
                            for i in range(0, len(p), max_length):
                                parts.append(p[i:i+max_length])
                    else:
                        if current_part:
                            current_part += "\n\n" + p
                        else:
                            current_part = p
                
                # Añadir la última parte si queda algo
                if current_part:
                    parts.append(current_part)
                
                # Enviar cada parte
                for i, part in enumerate(parts):
                    prefix = f"Parte {i+1}/{len(parts)}: " if len(parts) > 1 else ""
                    message = self.client.messages.create(
                        from_=f'whatsapp:{self.whatsapp_number}',
                        body=prefix + part,
                        to=to
                    )
                    print(f"DEBUG - WhatsApp: Parte {i+1}/{len(parts)} enviada con SID: {message.sid}")
                    messages_sent += 1
            
            return messages_sent > 0
        except Exception as e:
            print(f"ERROR - WhatsApp: No se pudo enviar el mensaje: {str(e)}")
            return False