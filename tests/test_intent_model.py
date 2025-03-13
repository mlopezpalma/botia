import unittest
import sys
import os

# Agregar el directorio raíz del proyecto al path para poder importar módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.intent_model import identificar_intencion, preprocesar_texto

class TestIntentModel(unittest.TestCase):
    
    def test_preprocesar_texto(self):
        """Prueba el preprocesamiento de texto."""
        # Texto con puntuación y mayúsculas
        texto_original = "¡Hola! ¿Cómo estás? Quiero agendar una cita."
        texto_preprocesado = preprocesar_texto(texto_original)
        
        # Comprobar que elimina puntuación y pasa a minúsculas
        self.assertNotIn("¡", texto_preprocesado)
        self.assertNotIn("!", texto_preprocesado)
        self.assertNotIn("¿", texto_preprocesado)
        self.assertNotIn("?", texto_preprocesado)
        self.assertNotIn(".", texto_preprocesado)
        self.assertEqual(texto_preprocesado, texto_preprocesado.lower())
    
    def test_identificar_intencion_saludo(self):
        """Prueba la identificación de intenciones de saludo."""
        self.assertEqual(identificar_intencion("hola"), "saludo")
        self.assertEqual(identificar_intencion("buenos días"), "saludo")
        self.assertEqual(identificar_intencion("buenas tardes a todos"), "saludo")
        self.assertEqual(identificar_intencion("hola, ¿cómo estás?"), "saludo")
    
    def test_identificar_intencion_agendar(self):
        """Prueba la identificación de intenciones de agendar cita."""
        self.assertEqual(identificar_intencion("quiero una cita"), "agendar")
        self.assertEqual(identificar_intencion("necesito agendar una visita"), "agendar")
        self.assertEqual(identificar_intencion("quisiera programar una reunión"), "agendar")
        self.assertEqual(identificar_intencion("reservar un horario para consulta"), "agendar")
    
    def test_identificar_intencion_tipo_reunion(self):
        """Prueba la identificación de intenciones sobre tipo de reunión."""
        self.assertEqual(identificar_intencion("presencial"), "reunion_presencial")
        self.assertEqual(identificar_intencion("quiero que sea en persona"), "reunion_presencial")
        self.assertEqual(identificar_intencion("por teléfono"), "reunion_telefonica")
        self.assertEqual(identificar_intencion("prefiero una videoconferencia"), "reunion_video")
    
    def test_identificar_intencion_preferencia_fecha(self):
        """Prueba la identificación de intenciones sobre preferencia de fecha."""
        self.assertEqual(identificar_intencion("lo antes posible"), "antes_posible")
        self.assertEqual(identificar_intencion("cuanto antes mejor"), "antes_posible")
        self.assertEqual(identificar_intencion("quiero ver el calendario"), "ver_calendario")
        self.assertEqual(identificar_intencion("para la semana próxima"), "dia_especifico")
    
    def test_identificar_intencion_confirmacion_negacion(self):
        """Prueba la identificación de intenciones de confirmación y negación."""
        self.assertEqual(identificar_intencion("sí, confirmo"), "confirmacion")
        self.assertEqual(identificar_intencion("de acuerdo"), "confirmacion")
        self.assertEqual(identificar_intencion("no, quiero otra fecha"), "negacion")
        self.assertEqual(identificar_intencion("cancelar"), "negacion")
    
    def test_identificar_intencion_desconocida(self):
        """Prueba la identificación de intenciones desconocidas."""
        self.assertEqual(identificar_intencion("xyz abc 123"), "desconocido")
        self.assertEqual(identificar_intencion(""), "desconocido")

if __name__ == '__main__':
    unittest.main()
