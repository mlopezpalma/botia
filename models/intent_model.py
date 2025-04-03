import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import spacy
from config import INTENCIONES

# Intentar descargar recursos de NLTK si no existen

# Descargar recursos necesarios de NLTK 
# Usamos download con quiet=True para evitar mensajes en consola
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('punkt_tab', quiet=True)  # Necesario para el tokenizador

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

# Cargar modelo spaCy
try:
    nlp = spacy.load("es_core_news_md")
except OSError:
    print("ADVERTENCIA: Modelo spaCy 'es_core_news_md' no encontrado. Por favor, instálelo con:")
    print("python -m spacy download es_core_news_md")
    # Fallback básico para usar un modelo más ligero si está disponible
    try:
        nlp = spacy.load("es_core_news_sm")
        print("Usando modelo alternativo es_core_news_sm")
    except OSError:
        print("ERROR: No se ha podido cargar ningún modelo de spaCy")
        # Crear un modelo vacío como último recurso
        nlp = spacy.blank("es")

# Control de nivel de depuración
DEBUG_MODE = False  # Cambiar a True durante desarrollo, False en producción

def debug_print(message):
    """Imprime mensajes de depuración solo si el modo DEBUG está activado."""
    if DEBUG_MODE:
        print(message)

def preprocesar_texto(texto):
    """
    Preprocesa el texto eliminando puntuación, convirtiéndolo a minúsculas
    y eliminando stopwords.
    """
    texto = texto.lower()
    texto = re.sub(r'[^\w\s]', '', texto)
    tokens = word_tokenize(texto)
    stop_words = set(stopwords.words('spanish'))
    tokens = [w for w in tokens if not w in stop_words]
    return " ".join(tokens)

def identificar_intencion(texto):
    """
    Identifica la intención del usuario basándose en el texto proporcionado.
    Utiliza spaCy para calcular similitud entre textos.
    
    Args:
        texto: Texto del usuario
        
    Returns:
        Intención identificada o "desconocido" si no se identifica ninguna
    """
    debug_print(f"DEBUG - spaCy identificando intención para: '{texto}'")
    
    # Manejar caso especial: texto vacío
    if not texto or len(texto.strip()) == 0:
        debug_print(f"DEBUG - Texto vacío, retornando desconocido")
        return "desconocido"
        
    texto_lower = texto.lower().strip()
    
    # Primero comprobar coincidencias exactas
    for intencion, ejemplos in INTENCIONES.items():
        if texto_lower in ejemplos:
            debug_print(f"DEBUG - Coincidencia exacta: '{intencion}'")
            return intencion
    
    # NUEVA SECCIÓN: Detectar despedida o finalización
    palabras_despedida = ["no gracias", "adiós", "adios", "hasta luego", "terminar", 
                         "finalizar", "cerrar", "no quiero", "no deseo", "eso es todo"]
    
    if any(palabra in texto_lower for palabra in palabras_despedida):
        debug_print("DEBUG - Detectada despedida")
        return "despedida"  # Nueva intención para manejar despedidas
    
    # Si no hay coincidencia exacta, usar spaCy
    texto_doc = nlp(texto_lower)
    
    mejor_similitud = 0
    mejor_intencion = None
    
    # Mapeo de palabras clave a intenciones específicas para evitar confusiones
    palabras_claves = {
        "agendar": ["agendar", "cita", "programar", "reservar", "visita"],
        "saludo": ["hola", "buenos", "saludos", "buenas", "qué tal"],
        "dia_especifico": ["semana", "específico", "próxima", "mes"],
        "reunion_presencial": ["presencial", "persona", "cara a cara", "oficina"],
        "reunion_video": ["video", "videoconferencia", "virtual", "online"],
        "reunion_telefonica": ["teléfono", "llamada", "telefonica"],
        "consultar_estado": ["estado", "consultar", "caso", "expediente", "seguimiento"]
    }
    
    # Verificar si el texto contiene palabras clave específicas
    for intencion, palabras in palabras_claves.items():
        for palabra in palabras:
            if palabra in texto_lower:
                # Aumentar la prioridad de esta intención
                for ejemplo in INTENCIONES[intencion]:
                    ejemplo_doc = nlp(ejemplo)
                    # Para textos muy cortos, usar un método alternativo
                    if len(texto_doc) < 2 or len(ejemplo_doc) < 2:
                        if texto_lower in ejemplo or ejemplo in texto_lower:
                            similitud = 0.95  # Alta similitud para subcadenas
                        else:
                            similitud = 0.0
                    else:
                        similitud = texto_doc.similarity(ejemplo_doc) * 1.2  # Aumentar la similitud en un 20%
                    
                    debug_print(f"DEBUG - Similitud entre '{texto_lower}' y '{ejemplo}': {similitud}")
                    
                    if similitud > mejor_similitud:
                        mejor_similitud = similitud
                        mejor_intencion = intencion
    
    # Ahora recorrer todas las intenciones sin aumento de prioridad
    if mejor_similitud < 0.6:  # Solo si no se ha encontrado una alta similitud con palabras clave
        for intencion, ejemplos in INTENCIONES.items():
            for ejemplo in ejemplos:
                ejemplo_doc = nlp(ejemplo)
                # Para textos muy cortos, la similitud puede ser imprecisa
                if len(texto_doc) < 2 or len(ejemplo_doc) < 2:
                    if texto_lower in ejemplo or ejemplo in texto_lower:
                        similitud = 0.9  # Alta similitud para subcadenas
                    else:
                        similitud = 0.0
                else:
                    similitud = texto_doc.similarity(ejemplo_doc)
                
                debug_print(f"DEBUG - Similitud entre '{texto_lower}' y '{ejemplo}': {similitud}")
                
                if similitud > mejor_similitud:
                    mejor_similitud = similitud
                    mejor_intencion = intencion
    
    # Casos especiales
    if "necesito agendar" in texto_lower or "quiero agendar" in texto_lower:
        return "agendar"
    
    if "buenas tardes" in texto_lower or "buenos días" in texto_lower or "buenas noches" in texto_lower:
        if not any(palabra in texto_lower for palabra in ["presencial", "persona", "cara", "video", "telefonica"]):
            return "saludo"
    
    if "para la semana próxima" in texto_lower or "para la próxima semana" in texto_lower:
        return "dia_especifico"
    
    # Umbral de similitud
    if mejor_similitud > 0.6:
        debug_print(f"DEBUG - Mejor intención por similitud ({mejor_similitud}): '{mejor_intencion}'")
        return mejor_intencion
    else:
        debug_print(f"DEBUG - No se encontró intención con suficiente similitud. Mejor: {mejor_intencion} ({mejor_similitud})")
        return "desconocido"