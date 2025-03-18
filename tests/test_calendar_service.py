import unittest
import sys
import os
import datetime
from unittest.mock import patch, MagicMock

# Agregar el directorio raíz del proyecto al path para poder importar módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from handlers.calendar_service import (
    obtener_horarios_disponibles,
    encontrar_proxima_fecha_disponible,
    agendar_en_calendario,
    obtener_dias_disponibles
)

class TestCalendarService(unittest.TestCase):
    
    def setUp(self):
        """Configuración inicial para cada test."""
        # Datos de prueba para cliente
        self.datos_cliente = {
            "nombre": "Usuario Test",
            "email": "test@example.com",
            "telefono": "612345678"
        }
        
        # Fecha y hora de prueba
        self.fecha_test = "2023-06-01"
        self.hora_test = "10:00"
        self.tipo_reunion_test = "presencial"
        self.tema_reunion_test = "Consulta sobre contrato de alquiler"
        
        # Fecha datetime fija para tests
        self.fecha_dt = datetime.datetime(2023, 6, 1, 0, 0, 0)
    
    @patch('handlers.calendar_service._obtener_horarios_simulados')
    @patch('handlers.calendar_service.get_google_calendar_service')
    def test_obtener_horarios_disponibles(self, mock_get_service, mock_obtener_simulados):
        """Prueba la obtención de horarios disponibles."""
        # Configurar el mock para que cause un error y use la versión simulada
        mock_service = MagicMock()
        mock_service.events().list.side_effect = Exception("Error simulado")
        mock_get_service.return_value = mock_service
        
        # Configurar la respuesta simulada
        mock_obtener_simulados.return_value = ["09:00", "10:00", "11:00"]
        
        # Llamar a la función con fecha de prueba
        horarios = obtener_horarios_disponibles(self.fecha_test, self.tipo_reunion_test)
        
        # Verificar que se intentó llamar al servicio pero falló y usó la versión simulada
        mock_service.events().list.assert_called()
        mock_obtener_simulados.assert_called_once()
        
        # Verificar que devuelve la lista simulada
        self.assertEqual(horarios, ["09:00", "10:00", "11:00"])
    
    @patch('handlers.calendar_service._encontrar_proxima_fecha_simulada')
    @patch('handlers.calendar_service.obtener_horarios_disponibles')
    def test_encontrar_proxima_fecha_disponible(self, mock_obtener_horarios, mock_fecha_simulada):
        """Prueba la búsqueda de la próxima fecha disponible."""
        # Configurar el mock para que falle y use la versión simulada
        mock_obtener_horarios.side_effect = Exception("Error simulado")
        mock_fecha_simulada.return_value = ("2023-06-01", "09:00")
        
        # Forzar fecha actual fija para la prueba
        with patch('datetime.datetime') as mock_datetime:
            # Configurar now() para devolver una fecha fija
            mock_dt = MagicMock()
            mock_dt.strftime.return_value = "2023-05-30"
            mock_datetime.now.return_value = mock_dt
            
            # Llamar a la función
            fecha, hora = encontrar_proxima_fecha_disponible(self.tipo_reunion_test)
            
            # Verificar resultado
            mock_fecha_simulada.assert_called_once()
            self.assertEqual(fecha, "2023-06-01")
            self.assertEqual(hora, "09:00")
    
    @patch('handlers.calendar_service._crear_evento_simulado')
    @patch('handlers.calendar_service.get_google_calendar_service')
    def test_agendar_en_calendario(self, mock_get_service, mock_crear_simulado):
        """Prueba el agendamiento de citas en el calendario."""
        # Configurar el mock para que falle y use la versión simulada
        mock_service = MagicMock()
        mock_service.events().insert.side_effect = Exception("Error simulado")
        mock_get_service.return_value = mock_service
        
        # Configurar evento simulado
        evento_simulado = {
            'id': 'evento_simulado_123',
            'summary': f'Consulta Legal - {self.datos_cliente["nombre"]} - {self.tema_reunion_test}',
            'status': 'confirmed'
        }
        mock_crear_simulado.return_value = evento_simulado
        
        # Llamar a la función con datos de prueba
        evento = agendar_en_calendario(
            self.fecha_test,
            self.hora_test,
            self.tipo_reunion_test,
            self.datos_cliente,
            self.tema_reunion_test
        )
        
        # Verificar que se intentó llamar al servicio pero falló y usó la versión simulada
        mock_service.events().insert.assert_called()
        mock_crear_simulado.assert_called_once()
        
        # Verificar que el evento devuelto es el simulado
        self.assertEqual(evento, evento_simulado)
    
    @patch('handlers.calendar_service._obtener_dias_disponibles_simulados')
    def test_obtener_dias_disponibles(self, mock_dias_simulados):
        """Prueba la función para obtener días disponibles en un mes."""
        # Configurar días simulados
        dias_simulados = [1, 3, 5, 8, 10, 12, 15, 17, 19, 22, 24, 26, 29]
        mock_dias_simulados.return_value = dias_simulados
        
        # Llamar a la función con datos de prueba
        mes = 6  # Junio
        anio = 2023
        
        # Forzar un error en obtener_horarios_disponibles para usar la simulación
        with patch('handlers.calendar_service.obtener_horarios_disponibles', side_effect=Exception("Error simulado")):
            dias = obtener_dias_disponibles(mes, anio, self.tipo_reunion_test)
            
            # Verificar que se usó la versión simulada
            mock_dias_simulados.assert_called_once_with(mes, anio, self.tipo_reunion_test)
            
            # Verificar que devuelve los días simulados
            self.assertEqual(dias, dias_simulados)

if __name__ == '__main__':
    unittest.main()