import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Agregar el directorio raíz del proyecto al path para poder importar módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from handlers.conversation import generar_respuesta
from config import casos_db, ESTADOS_CASO
from handlers.calendar_service import obtener_dias_disponibles

class TestNuevasFuncionalidades(unittest.TestCase):
    
    def setUp(self):
        """Configuración inicial para cada test."""
        # Simular estados de usuario para las pruebas
        self.user_states = {}
        
    def test_consulta_estado_caso_numero(self):
        """Prueba la funcionalidad de consulta de estado del caso por número."""
        user_id = "test_consulta_estado"
        
        # Iniciar conversación
        respuesta1 = generar_respuesta("hola", user_id, self.user_states)
        self.assertIn("consultar el estado de tu caso", respuesta1)
        
        # Seleccionar consulta de estado
        respuesta2 = generar_respuesta("Consultar estado de mi caso", user_id, self.user_states)
        self.assertEqual(self.user_states[user_id]["estado"], "esperando_opcion_consulta")
        self.assertIn("Para consultar el estado de tu caso", respuesta2)
        
        # Seleccionar consulta por número de expediente
        respuesta3 = generar_respuesta("Mi número de expediente", user_id, self.user_states)
        self.assertEqual(self.user_states[user_id]["estado"], "esperando_numero_expediente")
        self.assertIn("indícame el número de expediente", respuesta3)
        
        # Proporcionar número de expediente válido (debe existir en casos_db)
        respuesta4 = generar_respuesta("C2023-001", user_id, self.user_states)
        self.assertTrue(self.user_states[user_id]["consulta_caso"]["caso_encontrado"])
        self.assertEqual(self.user_states[user_id]["consulta_caso"]["numero_expediente"], "C2023-001")
        
        # Verificar que la respuesta contiene información del caso
        caso = casos_db["C2023-001"]
        self.assertIn(caso["titulo"], respuesta4)
        self.assertIn(caso["abogado"], respuesta4)
        
        # Verificar que se muestran las notas recientes
        for nota in caso["notas"]:
            self.assertIn(nota["texto"], respuesta4)
    
    def test_consulta_estado_caso_email(self):
        """Prueba la funcionalidad de consulta de estado del caso por email."""
        user_id = "test_consulta_email"
        
        # Configurar estado para prueba
        generar_respuesta("hola", user_id, self.user_states)
        generar_respuesta("Consultar estado de mi caso", user_id, self.user_states)
        
        # Seleccionar consulta por email
        respuesta = generar_respuesta("Mi email para buscar mis casos", user_id, self.user_states)
        self.assertEqual(self.user_states[user_id]["estado"], "esperando_email_cliente")
        self.assertIn("indícame tu dirección de email", respuesta)
        
        # Proporcionar email válido que tenga casos asociados
        email = "juan.perez@example.com"
        respuesta = generar_respuesta(email, user_id, self.user_states)
        self.assertTrue(self.user_states[user_id]["consulta_caso"]["caso_encontrado"])
        self.assertEqual(self.user_states[user_id]["consulta_caso"]["email_cliente"], email)
        
        # Verificar que la respuesta contiene información de los casos
        # Si el cliente tiene varios casos, debería mostrar una lista
        casos_cliente = [caso for numero, caso in casos_db.items() if caso["cliente_email"] == email]
        if len(casos_cliente) > 1:
            self.assertIn(f"Hemos encontrado {len(casos_cliente)} casos asociados a tu email", respuesta)
        # Si solo tiene un caso, debería mostrar los detalles
        elif len(casos_cliente) == 1:
            self.assertIn(casos_cliente[0]["titulo"], respuesta)
    
    @patch('handlers.calendar_service._obtener_dias_disponibles_simulados')
    def test_dias_disponibles_calendario(self, mock_obtener_simulados):
        """Prueba la función para obtener días disponibles para el calendario."""
        # Configurar días simulados
        dias_simulados = [1, 3, 5, 8, 10, 12, 15, 17, 19, 22, 24, 26, 29]
        mock_obtener_simulados.return_value = dias_simulados
        
        mes = 6  # Junio
        anio = 2023
        tipo_reunion = "presencial"
        
        # Forzar un error en obtener_horarios_disponibles para usar la simulación
        with patch('handlers.calendar_service.obtener_horarios_disponibles', side_effect=Exception("Error simulado")):
            # Llamar a la función con valores de prueba
            dias_disponibles = obtener_dias_disponibles(mes, anio, tipo_reunion)
            
            # Verificar que se usó la versión simulada
            mock_obtener_simulados.assert_called_once_with(mes, anio, tipo_reunion)
            
            # Verificar que devuelve la lista simulada
            self.assertEqual(dias_disponibles, dias_simulados)

if __name__ == '__main__':
    unittest.main()