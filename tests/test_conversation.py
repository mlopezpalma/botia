import unittest
import sys
import os

# Agregar el directorio raíz del proyecto al path para poder importar módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from handlers.conversation import generar_respuesta

class TestConversation(unittest.TestCase):
    
    def setUp(self):
        """Configuración inicial para cada test."""
        # Simular estados de usuario para las pruebas
        self.user_states = {}
    
    def test_flujo_completo_cita(self):
        """Prueba un flujo completo para agendar una cita."""
        user_id = "test_user"
        
        # Iniciar conversación
        respuesta = generar_respuesta("hola", user_id, self.user_states)
        self.assertIn("Soy el asistente de citas legales", respuesta)
        
        # Seleccionar tipo de reunión
        respuesta = generar_respuesta("presencial", user_id, self.user_states)
        self.assertIn("tema de la consulta legal", respuesta)
        
        # Proporcionar tema de la reunión
        respuesta = generar_respuesta("Consulta sobre contrato de arrendamiento", user_id, self.user_states)
        self.assertIn("¿Cómo te gustaría agendar tu cita?", respuesta)
        
        # Seleccionar día específico
        respuesta = generar_respuesta("día específico", user_id, self.user_states)
        self.assertIn("indícame qué día te gustaría", respuesta)
        
        # Seleccionar fecha
        respuesta = generar_respuesta("mañana", user_id, self.user_states)
        # La respuesta debería mostrar horarios disponibles o indicar que no hay
        self.assertTrue("horarios disponibles" in respuesta or "no hay horarios disponibles" in respuesta)
        
        # Si hay horarios disponibles, continuar con el flujo
        if "horarios disponibles" in respuesta:
            # Extraer la primera hora del menú
            menu_start = respuesta.find("[MENU:")
            if menu_start != -1:
                menu_content = respuesta[menu_start:].split(']')[0]
                first_option = menu_content.split('|')[0].replace("[MENU:", "")
                
                respuesta = generar_respuesta(first_option, user_id, self.user_states)
                self.assertIn("Para confirmar tu cita, necesito", respuesta)
                
                # Proporcionar datos personales
                respuesta = generar_respuesta("me llamo Test User, mi email es test@example.com y mi teléfono es 612345678", user_id, self.user_states)
                self.assertIn("Resumiendo tu cita", respuesta)
                
                # Confirmar cita
                respuesta = generar_respuesta("sí, confirmar", user_id, self.user_states)
                self.assertIn("Cita confirmada con éxito", respuesta)
                
                # Verificar que el estado se ha reiniciado
                self.assertEqual(self.user_states[user_id]["estado"], "inicial")
    
    def test_respuesta_inicial(self):
        """Prueba la respuesta inicial del bot."""
        user_id = "test_initial"
        
        # Probar saludo
        respuesta = generar_respuesta("hola", user_id, self.user_states)
        self.assertIn("Soy el asistente de citas legales", respuesta)
        
        # Probar iniciar directamente con agendar
        user_id = "test_initial2"  # Usuario diferente
        respuesta = generar_respuesta("quiero agendar una cita", user_id, self.user_states)
        self.assertIn("¿Qué tipo de reunión prefieres?", respuesta)
    
    def test_seleccion_tipo_reunion(self):
        """Prueba la selección de tipo de reunión."""
        user_id = "test_tipo"
        
        # Iniciar y seleccionar tipo directamente
        generar_respuesta("hola", user_id, self.user_states)
        
        respuesta = generar_respuesta("videoconferencia", user_id, self.user_states)
        self.assertIn("tema de la consulta legal", respuesta)
        
        # Proporcionar tema de la reunión
        respuesta = generar_respuesta("Consulta laboral", user_id, self.user_states)
        self.assertIn("¿Cómo te gustaría agendar tu cita?", respuesta)
        
        # Verificar que se ha guardado el tipo
        self.assertEqual(self.user_states[user_id]["tipo_reunion"], "videoconferencia")
        self.assertEqual(self.user_states[user_id]["tema_reunion"], "Consulta laboral")
    
    def test_extraccion_datos_personales(self):
        """Prueba la extracción de datos personales durante la conversación."""
        user_id = "test_datos"
        
        # Configurar el estado para simular solicitud de datos
        self.user_states[user_id] = {
            "estado": "esperando_datos",
            "tipo_reunion": "presencial",
            "fecha": "2023-06-01",
            "hora": "10:00",
            "tema_reunion": "Consulta jurídica general",
            "datos": {"nombre": None, "email": None, "telefono": None}
        }
        
        # Proporcionar nombre
        respuesta = generar_respuesta("me llamo Juan Pérez", user_id, self.user_states)
        self.assertEqual(self.user_states[user_id]["datos"]["nombre"], "Juan Pérez")
        
        # Proporcionar email
        respuesta = generar_respuesta("mi email es juan@example.com", user_id, self.user_states)
        self.assertEqual(self.user_states[user_id]["datos"]["email"], "juan@example.com")
        
        # Proporcionar teléfono
        respuesta = generar_respuesta("mi teléfono es 612345678", user_id, self.user_states)
        self.assertEqual(self.user_states[user_id]["datos"]["telefono"], "612345678")
        
        # Verificar que después de proporcionar todos los datos, se pasa a confirmación
        self.assertEqual(self.user_states[user_id]["estado"], "esperando_confirmacion")
    
    def test_cancelacion_cita(self):
        """Prueba la cancelación de una cita durante el flujo."""
        user_id = "test_cancelacion"
        
        # Configurar el estado para simular una cita pendiente de confirmación
        self.user_states[user_id] = {
            "estado": "esperando_confirmacion",
            "tipo_reunion": "presencial",
            "fecha": "2023-06-01",
            "hora": "10:00",
            "tema_reunion": "Consulta sobre herencia",
            "datos": {"nombre": "Test User", "email": "test@example.com", "telefono": "612345678"}
        }
        
        # Cancelar la cita
        respuesta = generar_respuesta("no, quiero cambiar la fecha", user_id, self.user_states)
        
        # Verificar que se vuelve al estado de preferencia de fecha
        self.assertEqual(self.user_states[user_id]["estado"], "esperando_preferencia_fecha")
    
    def test_mostrar_calendario(self):
        """Prueba la opción de mostrar el calendario."""
        user_id = "test_calendario"
        
        # Configurar el estado para simular selección de tipo de cita
        self.user_states[user_id] = {
            "estado": "esperando_preferencia_fecha",
            "tipo_reunion": "presencial",
            "tema_reunion": "Consulta sobre divorcio",
            "fecha": None,
            "hora": None,
            "datos": {"nombre": None, "email": None, "telefono": None}
        }
        
        # Solicitar ver el calendario
        respuesta = generar_respuesta("ver calendario", user_id, self.user_states)
        
        # Verificar que se muestra el indicador del calendario
        self.assertIn("[Indicador pequeño]", respuesta)
        
        # Verificar que se cambia el estado
        self.assertEqual(self.user_states[user_id]["estado"], "mostrando_calendario")
    
    def test_lo_antes_posible(self):
        """Prueba la opción de agendar lo antes posible."""
        user_id = "test_antes_posible"
        
        # Configurar el estado para simular selección de tipo de cita
        self.user_states[user_id] = {
            "estado": "esperando_preferencia_fecha",
            "tipo_reunion": "telefonica",
            "tema_reunion": "Consulta rápida",
            "fecha": None,
            "hora": None,
            "datos": {"nombre": None, "email": None, "telefono": None}
        }
        
        # Solicitar lo antes posible
        respuesta = generar_respuesta("lo antes posible", user_id, self.user_states)
        
        # Verificar que se asigna una fecha y hora o indica que no hay disponibilidad
        self.assertTrue(
            (self.user_states[user_id]["fecha"] is not None and 
             self.user_states[user_id]["hora"] is not None) or
            "no encontramos citas disponibles" in respuesta
        )
    
    def test_manejo_entrada_incorrecta(self):
        """Prueba el manejo de entradas incorrectas o ambiguas."""
        user_id = "test_error"
        
        # Iniciar conversación
        generar_respuesta("hola", user_id, self.user_states)
        
        # Enviar un mensaje que no corresponde al flujo esperado
        respuesta = generar_respuesta("xyz abc 123", user_id, self.user_states)
        
        # Verificar que el bot responde adecuadamente a la entrada incorrecta
        self.assertIn("indica qué tipo de reunión prefieres", respuesta)

if __name__ == '__main__':
    unittest.main()