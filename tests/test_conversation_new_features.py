import unittest
import sys
import os

# Agregar el directorio raíz del proyecto al path para poder importar módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from handlers.conversation import generar_respuesta
from config import clientes_db

class TestConversationNewFeatures(unittest.TestCase):
    
    def setUp(self):
        """Configuración inicial para cada test."""
        # Simular estados de usuario para las pruebas
        self.user_states = {}
        
        # Agregar un cliente simulado a la BD para pruebas de reconocimiento
        clientes_db.clear()  # Limpiar primero para evitar interferencias
        clientes_db["cliente_test@example.com"] = {
            "nombre": "Cliente Existente",
            "email": "cliente_test@example.com",
            "telefono": "612345678",
            "citas": []
        }
    
    def test_tema_reunion(self):
        """Prueba la captura y almacenamiento del tema de la reunión."""
        user_id = "test_tema"
        
        # Iniciar conversación y seleccionar tipo
        generar_respuesta("hola", user_id, self.user_states)
        generar_respuesta("presencial", user_id, self.user_states)
        
        # Proporcionar tema de la reunión
        respuesta = generar_respuesta("Consulta sobre herencia y testamento", user_id, self.user_states)
        
        # Verificar que se guardó el tema y que cambió al siguiente estado
        self.assertEqual(self.user_states[user_id]["tema_reunion"], "Consulta sobre herencia y testamento")
        self.assertEqual(self.user_states[user_id]["estado"], "esperando_preferencia_fecha")
        self.assertIn("¿Cómo te gustaría agendar tu cita?", respuesta)
    
    def test_reconocimiento_cliente_existente_por_email(self):
        """Prueba el reconocimiento de un cliente existente por su email."""
        user_id = "test_cliente_existente"
        
        # Configurar estado para simular selección de hora
        self.user_states[user_id] = {
            "estado": "esperando_datos",
            "tipo_reunion": "videoconferencia",
            "fecha": "2023-06-15",
            "hora": "10:00",
            "tema_reunion": "Consulta general",
            "datos": {"nombre": None, "email": None, "telefono": None},
            "consulta_caso": {
                "numero_expediente": None,
                "email_cliente": None,
                "caso_encontrado": False
            }
        }
        
        # Proporcionar email de un cliente existente
        respuesta = generar_respuesta("mi email es cliente_test@example.com", user_id, self.user_states)
        
        # Verificar que se reconoció al cliente y se completaron sus datos
        self.assertEqual(self.user_states[user_id]["datos"]["email"], "cliente_test@example.com")
        self.assertEqual(self.user_states[user_id]["datos"]["nombre"], "Cliente Existente")
        self.assertEqual(self.user_states[user_id]["datos"]["telefono"], "612345678")
        
        # Verificar que el mensaje incluye "Bienvenido de nuevo"
        self.assertIn("Bienvenido de nuevo", respuesta)
        self.assertIn("Cliente Existente", respuesta)
    
    def test_reconocimiento_cliente_existente_por_telefono(self):
        """Prueba el reconocimiento de un cliente existente por su teléfono."""
        user_id = "test_cliente_telefono"
        
        # Configurar estado para simular selección de hora
        self.user_states[user_id] = {
            "estado": "esperando_datos",
            "tipo_reunion": "telefonica",
            "fecha": "2023-06-15",
            "hora": "11:00",
            "tema_reunion": "Consulta rápida",
            "datos": {"nombre": None, "email": None, "telefono": None},
            "consulta_caso": {
                "numero_expediente": None,
                "email_cliente": None,
                "caso_encontrado": False
            }
        }
        
        # Proporcionar teléfono de un cliente existente
        respuesta = generar_respuesta("mi teléfono es 612345678", user_id, self.user_states)
        
        # Verificar que se reconoció al cliente y se completaron sus datos
        self.assertEqual(self.user_states[user_id]["datos"]["telefono"], "612345678")
        self.assertEqual(self.user_states[user_id]["datos"]["email"], "cliente_test@example.com")
        self.assertEqual(self.user_states[user_id]["datos"]["nombre"], "Cliente Existente")
    
    def test_cambio_fecha_hora(self):
        """Prueba la funcionalidad de cambiar fecha y hora antes de confirmar."""
        user_id = "test_cambio_fecha"
        
        # Configurar estado para simular cita pendiente de confirmación
        self.user_states[user_id] = {
            "estado": "esperando_confirmacion",
            "tipo_reunion": "presencial",
            "fecha": "2023-06-15",
            "hora": "10:00",
            "tema_reunion": "Consulta sobre divorcio",
            "datos": {"nombre": "Test User", "email": "test@example.com", "telefono": "612345678"},
            "consulta_caso": {
                "numero_expediente": None,
                "email_cliente": None,
                "caso_encontrado": False
            }
        }
        
        # Rechazar la confirmación
        respuesta1 = generar_respuesta("no, cambiar detalles", user_id, self.user_states)
        self.assertEqual(self.user_states[user_id]["estado"], "esperando_seleccion_cambio")
        
        # Seleccionar cambio de fecha y hora
        respuesta2 = generar_respuesta("Fecha y hora", user_id, self.user_states)
        self.assertEqual(self.user_states[user_id]["estado"], "esperando_preferencia_fecha")
        self.assertIn("¿Cómo te gustaría agendar tu cita?", respuesta2)
    
    def test_cambio_tipo_reunion(self):
        """Prueba la funcionalidad de cambiar el tipo de reunión antes de confirmar."""
        user_id = "test_cambio_tipo"
        
        # Configurar estado para simular cita pendiente de confirmación
        self.user_states[user_id] = {
            "estado": "esperando_confirmacion",
            "tipo_reunion": "presencial",
            "fecha": "2023-06-15",
            "hora": "10:00",
            "tema_reunion": "Consulta laboral",
            "datos": {"nombre": "Test User", "email": "test@example.com", "telefono": "612345678"},
            "consulta_caso": {
                "numero_expediente": None,
                "email_cliente": None,
                "caso_encontrado": False
            }
        }
        
        # Rechazar la confirmación
        generar_respuesta("no, cambiar detalles", user_id, self.user_states)
        
        # Seleccionar cambio de tipo de reunión
        respuesta = generar_respuesta("Tipo de reunión", user_id, self.user_states)
        self.assertEqual(self.user_states[user_id]["estado"], "esperando_tipo_reunion")
        self.assertIn("¿Qué tipo de reunión prefieres?", respuesta)
    
    def test_cambio_tema(self):
        """Prueba la funcionalidad de cambiar el tema de la reunión antes de confirmar."""
        user_id = "test_cambio_tema"
        
        # Configurar estado para simular cita pendiente de confirmación
        self.user_states[user_id] = {
            "estado": "esperando_confirmacion",
            "tipo_reunion": "videoconferencia",
            "fecha": "2023-06-15",
            "hora": "10:00",
            "tema_reunion": "Consulta inicial",
            "datos": {"nombre": "Test User", "email": "test@example.com", "telefono": "612345678"},
            "consulta_caso": {
                "numero_expediente": None,
                "email_cliente": None,
                "caso_encontrado": False
            }
        }
        
        # Rechazar la confirmación
        generar_respuesta("no, cambiar detalles", user_id, self.user_states)
        
        # Seleccionar cambio de tema
        respuesta = generar_respuesta("Tema", user_id, self.user_states)
        self.assertEqual(self.user_states[user_id]["estado"], "esperando_tema_reunion")
        self.assertIn("¿Cuál es el nuevo tema o motivo de la consulta legal?", respuesta)
        
        # Proporcionar nuevo tema
        nuevo_tema = "Consulta sobre contrato de trabajo"
        respuesta2 = generar_respuesta(nuevo_tema, user_id, self.user_states)
        self.assertEqual(self.user_states[user_id]["tema_reunion"], nuevo_tema)
        self.assertEqual(self.user_states[user_id]["estado"], "esperando_preferencia_fecha")
    
    def test_cambio_datos_personales(self):
        """Prueba la funcionalidad de cambiar los datos personales antes de confirmar."""
        user_id = "test_cambio_datos"
        
        # Configurar estado para simular cita pendiente de confirmación
        self.user_states[user_id] = {
            "estado": "esperando_confirmacion",
            "tipo_reunion": "telefonica",
            "fecha": "2023-06-15",
            "hora": "10:00",
            "tema_reunion": "Consulta rápida",
            "datos": {"nombre": "Test User", "email": "test@example.com", "telefono": "612345678"},
            "consulta_caso": {
                "numero_expediente": None,
                "email_cliente": None,
                "caso_encontrado": False
            }
        }
        
        # Rechazar la confirmación
        generar_respuesta("no, cambiar detalles", user_id, self.user_states)
        
        # Seleccionar cambio de datos personales
        respuesta = generar_respuesta("Mis datos personales", user_id, self.user_states)
        self.assertEqual(self.user_states[user_id]["estado"], "esperando_datos")
        self.assertIn("proporciona tus datos de nuevo", respuesta)
        
        # Verificar que los datos se han reseteado
        self.assertIsNone(self.user_states[user_id]["datos"]["nombre"])
        self.assertIsNone(self.user_states[user_id]["datos"]["email"])
        self.assertIsNone(self.user_states[user_id]["datos"]["telefono"])

if __name__ == '__main__':
    unittest.main()