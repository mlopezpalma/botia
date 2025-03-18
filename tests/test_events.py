import unittest
import sys
import os
import datetime

# Agregar el directorio raíz del proyecto al path para poder importar módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar configuración y módulos relacionados con eventos
from config import citas_db, clientes_db
from handlers.conversation import _confirmar_cita, reset_conversacion
from handlers.calendar_service import agendar_en_calendario
from handlers.email_service import enviar_correo_confirmacion

class TestEventos(unittest.TestCase):
    
    def setUp(self):
        """Configuración inicial para cada test."""
        # Limpiar las bases de datos simuladas antes de cada prueba
        citas_db.clear()
        clientes_db.clear()
        
        # Estado de usuario simulado para pruebas
        self.user_id = "test_user_events"
        self.user_states = {}
        
        # Crear un estado de usuario para las pruebas
        self.estado_usuario = {
            "estado": "esperando_confirmacion",
            "tipo_reunion": "presencial",
            "fecha": "2023-06-15",
            "hora": "10:00",
            "tema_reunion": "Consulta sobre contrato de arrendamiento",
            "datos": {
                "nombre": "Usuario Prueba",
                "email": "usuario.prueba@example.com",
                "telefono": "612345678"
            },
            "consulta_caso": {
                "numero_expediente": None,
                "email_cliente": None,
                "caso_encontrado": False
            }
        }
        
        # Agregar el estado al diccionario de estados
        self.user_states[self.user_id] = self.estado_usuario
    
    def test_confirmacion_cita(self):
        """Prueba la confirmación de una cita y su almacenamiento en la BD."""
        # Ejecutar la función de confirmación
        mensaje = _confirmar_cita(self.estado_usuario, self.user_id, self.user_states)
        
        # Verificar que el mensaje contiene la información relevante
        self.assertIn("Cita confirmada con éxito", mensaje)
        self.assertIn(self.estado_usuario["tipo_reunion"], mensaje)
        self.assertIn(self.estado_usuario["hora"], mensaje)
        self.assertIn(self.estado_usuario["tema_reunion"], mensaje)
        
        # Verificar que se ha guardado la cita en la BD
        self.assertEqual(len(citas_db), 1)
        
        # Obtener la cita guardada (debería haber solo una)
        cita_id = list(citas_db.keys())[0]
        cita = citas_db[cita_id]
        
        # Verificar los datos de la cita
        self.assertEqual(cita["tipo"], self.estado_usuario["tipo_reunion"])
        self.assertEqual(cita["fecha"], self.estado_usuario["fecha"])
        self.assertEqual(cita["hora"], self.estado_usuario["hora"])
        self.assertEqual(cita["tema"], self.estado_usuario["tema_reunion"])
        self.assertEqual(cita["cliente"]["nombre"], self.estado_usuario["datos"]["nombre"])
        self.assertEqual(cita["cliente"]["email"], self.estado_usuario["datos"]["email"])
        
        # Verificar que se ha guardado el cliente en la BD
        cliente_id = self.estado_usuario["datos"]["email"]
        self.assertIn(cliente_id, clientes_db)
        
        # Verificar los datos del cliente
        cliente = clientes_db[cliente_id]
        self.assertEqual(cliente["nombre"], self.estado_usuario["datos"]["nombre"])
        self.assertEqual(cliente["email"], self.estado_usuario["datos"]["email"])
        self.assertEqual(cliente["telefono"], self.estado_usuario["datos"]["telefono"])
        
        # Verificar que la cita está asociada al cliente
        self.assertIn(cita_id, cliente["citas"])
    
    def test_reset_conversacion(self):
        """Prueba que el reseteo de la conversación funciona correctamente."""
        # Ejecutar la función de reseteo
        reset_conversacion(self.user_id, self.user_states)
        
        # Verificar que el estado se ha reiniciado correctamente
        estado_reseteado = self.user_states[self.user_id]
        self.assertEqual(estado_reseteado["estado"], "inicial")
        self.assertIsNone(estado_reseteado["tipo_reunion"])
        self.assertIsNone(estado_reseteado["fecha"])
        self.assertIsNone(estado_reseteado["hora"])
        self.assertIsNone(estado_reseteado["tema_reunion"])
        self.assertIsNone(estado_reseteado["datos"]["nombre"])
        self.assertIsNone(estado_reseteado["datos"]["email"])
        self.assertIsNone(estado_reseteado["datos"]["telefono"])
        self.assertFalse(estado_reseteado["consulta_caso"]["caso_encontrado"])

if __name__ == '__main__':
    unittest.main()