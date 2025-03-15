import unittest
import datetime
import sys
import os

# Agregar el directorio raíz del proyecto al path para poder importar módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.data_extraction import (
    identificar_fecha, 
    identificar_hora, 
    identificar_tipo_reunion, 
    identificar_datos_personales
)

class TestDataExtraction(unittest.TestCase):
    
    def test_identificar_fecha_formatos_especificos(self):
        """Prueba la identificación de fechas en formatos específicos."""
        # Probar con formato DD/MM/YYYY
        self.assertIsNotNone(identificar_fecha("quiero una cita el 12/3/2025"))
        self.assertIsNotNone(identificar_fecha("el 15/04/2024 estaría bien"))
        
        # Probar con días
        hoy = datetime.datetime.now()
        fecha_hoy = hoy.strftime("%Y-%m-%d")
        self.assertEqual(identificar_fecha("quiero una cita hoy"), fecha_hoy)
        
        fecha_manana = (hoy + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        self.assertEqual(identificar_fecha("mañana me vendría bien"), fecha_manana)
        
        # Calcular el próximo lunes
        dias_hasta_lunes = (0 - hoy.weekday()) % 7
        if dias_hasta_lunes == 0:
            dias_hasta_lunes = 7  # Si hoy es lunes, ir al próximo
        fecha_lunes = (hoy + datetime.timedelta(days=dias_hasta_lunes)).strftime("%Y-%m-%d")
        self.assertEqual(identificar_fecha("el próximo lunes"), fecha_lunes)
    
    def test_identificar_hora(self):
        """Prueba la identificación de horas en diferentes formatos."""
        self.assertEqual(identificar_hora("a las 10:30"), "10:30")
        self.assertEqual(identificar_hora("a las 3pm"), "15:00")
        self.assertEqual(identificar_hora("a las 8 de la mañana"), "08:00")
        self.assertEqual(identificar_hora("15:45"), "15:45")
        self.assertEqual(identificar_hora("a las 7 de la tarde"), "19:00")
        
        # Casos que deberían devolver None o un valor específico
        self.assertIsNone(identificar_hora("no hay hora aquí"))
        self.assertIsNone(identificar_hora("a las veintitrés horas"))  # No maneja horas en texto
    
    def test_identificar_tipo_reunion(self):
        """Prueba la identificación de tipos de reunión."""
        self.assertEqual(identificar_tipo_reunion("presencial"), "presencial")
        self.assertEqual(identificar_tipo_reunion("telefonica"), "telefonica")
        self.assertEqual(identificar_tipo_reunion("videoconferencia"), "videoconferencia")
        self.assertEqual(identificar_tipo_reunion("quiero una cita en persona"), "presencial")
        self.assertEqual(identificar_tipo_reunion("preferiblemente por video"), "videoconferencia")
        self.assertEqual(identificar_tipo_reunion("por teléfono mejor"), "telefonica")
        
        # Casos que deberían devolver None
        self.assertIsNone(identificar_tipo_reunion("no especifico tipo"))
        self.assertIsNone(identificar_tipo_reunion("virtual pero no videollamada"))  # Ambiguo
    
    def test_identificar_datos_personales(self):
        """Prueba la identificación de datos personales."""
        # Prueba de nombre
        datos = identificar_datos_personales("me llamo Juan Pérez")
        self.assertEqual(datos["nombre"], "Juan Pérez")
        
        datos = identificar_datos_personales("mi nombre es Maria García")
        self.assertEqual(datos["nombre"], "Maria García")
        
        # Prueba de email
        datos = identificar_datos_personales("mi email es ejemplo@correo.com")
        self.assertEqual(datos["email"], "ejemplo@correo.com")
        
        # Prueba de teléfono
        datos = identificar_datos_personales("mi teléfono es 612345678")
        self.assertEqual(datos["telefono"], "612345678")
        
        datos = identificar_datos_personales("pueden contactarme al +34 912345678")
        self.assertEqual(datos["telefono"], "+34 912345678")
        
        # Prueba con múltiples datos en el mismo texto
        datos = identificar_datos_personales(
            "Soy Ana Rodríguez, mi email es ana@example.com y mi teléfono 654321987"
        )
        self.assertEqual(datos["nombre"], "Ana Rodríguez")
        self.assertEqual(datos["email"], "ana@example.com")
        self.assertEqual(datos["telefono"], "654321987")
        
        # Casos que no deberían identificar datos
        datos = identificar_datos_personales("xyz 123 abc")
        self.assertIsNone(datos["nombre"])
        self.assertIsNone(datos["email"])
        self.assertIsNone(datos["telefono"])

if __name__ == '__main__':
    unittest.main()