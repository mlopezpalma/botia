import unittest
import sys
import os

# Agregar el directorio raíz del proyecto al path para poder importar módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar todos los tests
from tests.test_data_extraction import TestDataExtraction
from tests.test_intent_model import TestIntentModel
from tests.test_helpers import TestHelpers
from tests.test_conversation import TestConversation
from tests.test_calendar_service import TestCalendarService
from tests.test_events import TestEventos

def run_tests():
    """Ejecuta todos los tests unitarios y de integración."""
    
    # Crear un test suite
    test_suite = unittest.TestSuite()
    
    # Agregar todas las clases de test
    test_suite.addTest(unittest.makeSuite(TestDataExtraction))
    test_suite.addTest(unittest.makeSuite(TestIntentModel))
    test_suite.addTest(unittest.makeSuite(TestHelpers))
    test_suite.addTest(unittest.makeSuite(TestConversation))
    test_suite.addTest(unittest.makeSuite(TestCalendarService))
    test_suite.addTest(unittest.makeSuite(TestEventos))
    
    # Ejecutar los tests
    print("\n== Ejecutando tests del Bot de Agendamiento de Citas Legales ==\n")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    print("\n== Resumen de Tests ==")
    print(f"Tests ejecutados: {result.testsRun}")
    print(f"Tests exitosos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Tests fallidos: {len(result.failures)}")
    print(f"Tests con error: {len(result.errors)}")
    
    return result

if __name__ == '__main__':
    result = run_tests()
    
    # Códigos de salida para integración continua
    if len(result.failures) > 0 or len(result.errors) > 0:
        sys.exit(1)  # Falló al menos un test
    else:
        sys.exit(0)  # Todos los tests pasaron