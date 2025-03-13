import unittest
import sys
import os
import datetime

# Agregar el directorio raíz del proyecto al path para poder importar módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.helpers import (
    format_fecha, 
    format_hora, 
    get_proximos_dias, 
    validar_email, 
    validar_telefono,
    generar_id_unico
)

class TestHelpers(unittest.TestCase):
    
    def test_format_fecha(self):
        """Prueba el formateo de fechas."""
        # Probar diferentes formatos
        self.assertEqual(format_fecha("2023-05-15", "DD/MM/YYYY"), "15/05/2023")
        self.assertEqual(format_fecha("2023-05-15", "YYYY/MM/DD"), "2023/05/15")
        self.assertEqual(format_fecha("2023-05-15", "DD-MM-YYYY"), "15-05-2023")
        self.assertEqual(format_fecha("2023-05-15", "YYYY-MM-DD"), "2023-05-15")
        
        # Probar con formato incluyendo día de la semana
        # 15/05/2023 fue lunes
        self.assertEqual(format_fecha("2023-05-15", "DD/MM/YYYY (DIA)"), "15/05/2023 (Lunes)")
        
        # Probar con fecha inválida
        self.assertEqual(format_fecha("fecha-invalida"), "fecha-invalida")
    
    def test_format_hora(self):
        """Prueba el formateo de horas."""
        # Probar formato 24h
        self.assertEqual(format_hora("9:30", "24h"), "09:30")
        self.assertEqual(format_hora("15:45", "24h"), "15:45")
        
        # Probar formato 12h
        self.assertEqual(format_hora("0:00", "12h"), "12:00 AM")
        self.assertEqual(format_hora("9:30", "12h"), "9:30 AM")
        self.assertEqual(format_hora("12:00", "12h"), "12:00 PM")
        self.assertEqual(format_hora("15:45", "12h"), "3:45 PM")
        self.assertEqual(format_hora("23:59", "12h"), "11:59 PM")
        
        # Probar con hora inválida
        self.assertEqual(format_hora("hora-invalida"), "hora-invalida")
    
    def test_get_proximos_dias(self):
        """Prueba la obtención de próximos días."""
        # Obtener 5 días excluyendo fines de semana
        dias = get_proximos_dias(5, incluir_fines_semana=False)
        
        # Comprobar que devuelve 5 días
        self.assertEqual(len(dias), 5)
        
        # Comprobar que ninguno es fin de semana
        for dia in dias:
            self.assertFalse(dia["es_fin_semana"])
        
        # Obtener 7 días incluyendo fines de semana
        dias = get_proximos_dias(7, incluir_fines_semana=True)
        
        # Comprobar que devuelve 7 días
        self.assertEqual(len(dias), 7)
        
        # Comprobar que el primer día es hoy
        hoy = datetime.datetime.now().strftime("%Y-%m-%d")
        self.assertEqual(dias[0]["fecha"], hoy)
    
    def test_validar_email(self):
        """Prueba la validación de emails."""
        # Emails válidos
        self.assertTrue(validar_email("usuario@dominio.com"))
        self.assertTrue(validar_email("usuario.nombre@empresa.co.uk"))
        self.assertTrue(validar_email("usuario_123@servidor.net"))
        
        # Emails inválidos
        self.assertFalse(validar_email("usuario@"))
        self.assertFalse(validar_email("@dominio.com"))
        self.assertFalse(validar_email("usuario@dominio"))
        self.assertFalse(validar_email("usuario.dominio.com"))
        self.assertFalse(validar_email(""))
    
    def test_validar_telefono(self):
        """Prueba la validación de teléfonos."""
        # Teléfonos válidos para España
        self.assertTrue(validar_telefono("612345678", "ES"))
        self.assertTrue(validar_telefono("+34 612345678", "ES"))
        self.assertTrue(validar_telefono("912345678", "ES"))
        self.assertTrue(validar_telefono("712345678", "ES"))
        
        # Teléfonos inválidos para España
        self.assertFalse(validar_telefono("12345678", "ES"))  # No empieza por 6, 7 o 9
        self.assertFalse(validar_telefono("61234567", "ES"))  # Muy corto
        self.assertFalse(validar_telefono("6123456789", "ES"))  # Muy largo
        
        # Teléfonos genéricos (cuando no se especifica país)
        self.assertTrue(validar_telefono("12345678", ""))  # 8 dígitos
        self.assertTrue(validar_telefono("123456789", ""))  # 9 dígitos
    
    def test_generar_id_unico(self):
        """Prueba la generación de IDs únicos."""
        # Generar dos IDs y comprobar que son diferentes
        id1 = generar_id_unico()
        id2 = generar_id_unico()
        
        self.assertNotEqual(id1, id2)
        
        # Comprobar el formato (timestamp_random)
        self.assertRegex(id1, r'^\d+_\d{4}$')
        self.assertRegex(id2, r'^\d+_\d{4}$')

if __name__ == '__main__':
    unittest.main()
