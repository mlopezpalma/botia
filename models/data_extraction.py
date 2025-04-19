import re
import datetime

def identificar_fecha(texto):
    """
    Identifica fechas en el texto proporcionado.
    
    Args:
        texto: Texto del usuario
        
    Returns:
        Fecha identificada en formato "YYYY-MM-DD" o None si no se identifica
    """
    hoy = datetime.datetime.now()
    texto_lower = texto.lower()
    
    # Buscar patrones de fecha como DD/MM/YYYY
    fecha_pattern = r'(\d{1,2})\/(\d{1,2})\/(\d{4})'
    fecha_match = re.search(fecha_pattern, texto)
    if fecha_match:
        dia = int(fecha_match.group(1))
        mes = int(fecha_match.group(2))
        año = int(fecha_match.group(3))
        
        try:
            fecha_dt = datetime.datetime(año, mes, dia)
            return fecha_dt.strftime("%Y-%m-%d")
        except ValueError:
            pass  # Fecha inválida, continuar con otros métodos
    
    # Patrones para fechas en formato texto
    if "hoy" in texto_lower:
        return hoy.strftime("%Y-%m-%d")
    elif "mañana" in texto_lower:
        manana = hoy + datetime.timedelta(days=1)
        return manana.strftime("%Y-%m-%d")
    elif "próxima semana" in texto_lower or "proxima semana" in texto_lower:
        prox_semana = hoy + datetime.timedelta(days=7)
        return prox_semana.strftime("%Y-%m-%d")
    
    # Identificar días específicos
    dias = {"lunes": 0, "martes": 1, "miércoles": 2, "miercoles": 2, 
            "jueves": 3, "viernes": 4, "sábado": 5, "sabado": 5, "domingo": 6}
    
    for dia, num in dias.items():
        if dia in texto_lower:
            # Calcular días hasta el próximo día de la semana mencionado
            dias_hasta = (num - hoy.weekday()) % 7
            if dias_hasta == 0:
                dias_hasta = 7  # Si hoy es el día mencionado, ir a la próxima semana
            fecha = hoy + datetime.timedelta(days=dias_hasta)
            return fecha.strftime("%Y-%m-%d")
    
    # Buscar fechas con patrón "el XX de [mes]" o "XX de [mes]"
    meses = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
        "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
        "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
    }
    
    for mes_nombre, mes_num in meses.items():
        # Patrones como "el 15 de enero" o "15 de enero"
        patron = r'(?:el\s+)?(\d{1,2})\s+de\s+' + mes_nombre
        match = re.search(patron, texto_lower)
        
        if match:
            dia = int(match.group(1))
            try:
                # Si el mes ya pasó este año, asumimos que se refiere al próximo año
                año = hoy.year
                fecha_candidata = datetime.datetime(año, mes_num, dia)
                
                if fecha_candidata < hoy:
                    año += 1
                    fecha_candidata = datetime.datetime(año, mes_num, dia)
                
                return fecha_candidata.strftime("%Y-%m-%d")
            except ValueError:
                # Fecha inválida (ej: 31 de febrero)
                continue
    
    return None

def identificar_hora(texto):
    """
    Identifica horas en el texto proporcionado.
    
    Args:
        texto: Texto del usuario
        
    Returns:
        Hora identificada en formato "HH:MM" o None si no se identifica
    """
    # Buscar patrones de hora en el texto (formato 24h)
    patron_24h = r'(\d{1,2}):(\d{2})'
    match_24h = re.search(patron_24h, texto)
    if match_24h:
        hora = int(match_24h.group(1))
        minutos = match_24h.group(2)
        # Asegurar que la hora es válida
        if 0 <= hora <= 23:
            return f"{hora:02d}:{minutos}"
    
    # Buscar patrones como "a las X" o "las X"
    patron_a_las = r'(?:a\s+)?las\s+(\d{1,2})(?::(\d{2}))?(?:\s+(am|pm))?'
    match_a_las = re.search(patron_a_las, texto.lower())
    if match_a_las:
        hora = int(match_a_las.group(1))
        minutos = match_a_las.group(2) if match_a_las.group(2) else "00"
        ampm = match_a_las.group(3)
        
        if ampm:
            if ampm.lower() == 'pm' and hora < 12:
                hora += 12
            elif ampm.lower() == 'am' and hora == 12:
                hora = 0
        else:
            # Sin AM/PM, asumimos hora en formato 24h
            if hora < 8:  # Asumimos PM para horas entre 1-7 sin AM/PM
                hora += 12
        
        # Asegurar que la hora es válida
        if 0 <= hora <= 23:
            return f"{hora:02d}:{minutos}"
    
    # Buscar patrones como "X am/pm"
    patron_ampm = r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)'
    match_ampm = re.search(patron_ampm, texto.lower())
    if match_ampm:
        hora = int(match_ampm.group(1))
        minutos = match_ampm.group(2) if match_ampm.group(2) else "00"
        ampm = match_ampm.group(3)
        
        if ampm.lower() == 'pm' and hora < 12:
            hora += 12
        elif ampm.lower() == 'am' and hora == 12:
            hora = 0
            
        # Asegurar que la hora es válida
        if 0 <= hora <= 23:
            return f"{hora:02d}:{minutos}"
    
    return None

def identificar_tipo_reunion(texto):
    """
    Identifica el tipo de reunión en el texto proporcionado.
    
    Args:
        texto: Texto del usuario
        
    Returns:
        Tipo de reunión identificado o None si no se identifica

    """


    print(f"DEBUG - identificar_tipo_reunion recibió: '{texto}'")
    texto_original = texto
    texto = texto.lower().strip()
    
    print(f"DEBUG - Texto original: '{texto_original}'")
    print(f"DEBUG - Texto normalizado: '{texto}'")
    
    # Verificar coincidencias exactas primero
    if texto == "presencial":
        print("DEBUG - Coincidencia exacta: presencial")
        return "presencial"
    elif texto in ["videoconferencia", "video"]:
        print("DEBUG - Coincidencia exacta: videoconferencia")
        return "videoconferencia"
    elif texto in ["telefonica", "telefónica", "teléfono", "telefono", "por telefono"]:
        print("DEBUG - Coincidencia exacta: telefonica")
        return "telefonica"
    print(f"DEBUG - No se encontraron coincidencias exactas para '{texto}'")
    
    # Verificar explícitamente "por teléfono mejor" y similares
    if "por teléfono" in texto or "por telefono" in texto or "teléfono mejor" in texto or "telefono mejor" in texto:
        print(f"DEBUG - Detectada referencia a teléfono: '{texto}'")
        return "telefonica"
    
    # Si no es una palabra exacta, buscar en el texto completo
    # Comprobar si hay términos negativos que indiquen ambigüedad (mejorada para evitar falsos positivos)
    if " no " in " "+texto+" " or "pero no" in texto or texto.startswith("no "):
        print("DEBUG - Detectada negación, retornando None")
        # Si hay negación, es ambiguo y retornamos None
        return None
    
    # Patrones para tipos de reunión específicos
    patrones_presencial = ["presencial", "en persona", "cara a cara", "oficina"]
    patrones_video = ["video", "virtual", "online", "videollamada", "videoconferencia"]
    patrones_telefonica = ["telefónica", "teléfono", "telefonica", "telefono", "llamada"]
    
    # Verificar cada patrón en el texto
    for patron in patrones_presencial:
        if patron in texto:
            print(f"DEBUG - Detectado patrón presencial: '{patron}'")
            return "presencial"
            
    for patron in patrones_video:
        if patron in texto:
            print(f"DEBUG - Detectado patrón videoconferencia: '{patron}'")
            return "videoconferencia"
            
    for patron in patrones_telefonica:
        if patron in texto:
            print(f"DEBUG - Detectado patrón telefonica: '{patron}'")
            return "telefonica"
            
    # No se encontró ningún patrón reconocible
    print("DEBUG - No se detectó ningún patrón, retornando None")
    return None

# Modificaciones para mejorar la extracción de datos personales en models/data_extraction.py

def identificar_datos_personales(texto):
    """
    Identifica datos personales en el texto proporcionado.
    Versión mejorada para evitar confusiones con temas o tipos de reunión.
    
    Args:
        texto: Texto del usuario
        
    Returns:
        Diccionario con los datos personales identificados
    """
    datos = {"nombre": None, "email": None, "telefono": None}
    texto_lower = texto.lower()
    
    # Buscar email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_match = re.search(email_pattern, texto)
    if email_match:
        datos["email"] = email_match.group(0)
    
    # Buscar teléfono (formatos comunes en España)
    telefono_pattern = r'\b(?:\+34\s?)?(?:6\d{8}|7[1-9]\d{7}|9\d{8})\b'
    telefono_match = re.search(telefono_pattern, texto)
    if telefono_match:
        # Extraer el teléfono completo con prefijo si existe
        num_telefono = telefono_match.group(0)
        # Restaurar el prefijo +34 si el teléfono empieza con 9, 6 o 7 y no tiene prefijo
        if not num_telefono.startswith('+') and (num_telefono.startswith('9') or num_telefono.startswith('6') or num_telefono.startswith('7')):
            # Si el teléfono en el texto necesita el prefijo pero no lo tiene, añadirlo
            if "+34" in texto and "+34" not in num_telefono:
                num_telefono = "+34 " + num_telefono
        datos["telefono"] = num_telefono
    
    # Lista expandida de palabras que no deben considerarse nombres
    palabras_a_ignorar = [
        # Palabras comunes
        "no", "si", "sí", "hola", "buenos", "buenas", "quiero", "quisiera", 
        "necesito", "confirmar", "cancelar", "el", "la", "los", "las",
        "le", "les", "un", "una", "unos", "unas", "por", "favor", "gracias",
        "deseo", "prefiero", "mejor", "esta", "este", "ese", "esa", "mi", 
        # Tipos de reunión y servicios
        "presencial", "videoconferencia", "telefonica", "telefónica", 
        "virtual", "online", "cita", "consulta", "reunion", "reunión", 
        "agendar", "legal", "abogado", "despacho", "oficina",
        # Términos relacionados con el servicio
        "tema", "asunto", "motivo", "porque", "sobre", "para", "como", 
        "sobre", "servicio", "servicios", "quiero", "quisiera", "día", "hora", 
        "disponible", "horario", "fecha", "antes", "posible", "mañana", "hoy",
        "semana", "mes", "lunes", "martes", "miércoles", "jueves", "viernes",
        # Palabras relacionadas con el contexto legal
        "caso", "expediente", "demanda", "contrato", "juicio", "derecho",
        "ley", "legislación", "normativa"
    ]
    
    # Buscar nombre (patrones mejorados)
    nombre_patterns = [
        # Patrones explícitos - estos son prioritarios
        r'me llamo\s+([A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+(?:\s+[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+){0,3})',
        r'mi nombre es\s+([A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+(?:\s+[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+){0,3})',
        r'soy\s+([A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+(?:\s+[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+){0,3})',
        r'nombre[:\s]+([A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+(?:\s+[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+){0,3})',
        r'llamarme\s+([A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+(?:\s+[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+){0,3})',
        r'\blláma\w*\s+([A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+(?:\s+[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+){0,3})',
        # Patrón para "hola, soy [Nombre]" o variantes
        r'(?:hola|buenos días|buenas tardes)[,\s]+(?:soy|me llamo)\s+([A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+(?:\s+[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+){0,3})',
        # Patrón para detectar nombres al final del mensaje, seguidos de punto o en nueva línea
        r'\b([A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+(?:\s+[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+){0,3})(?:\.|$)',
        # Patrón para detectar saludos directos: "saludos, [Nombre]" o similar
        r'(?:saludos|atentamente|cordialmente)[,\s]+([A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+(?:\s+[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+){0,3})'
    ]
    
    # Función auxiliar para validar nombres candidatos
    def validar_nombre_candidato(nombre_candidato):
        if not nombre_candidato:
            return False
            
        # Verificar que no sea una palabra a ignorar
        palabras_nombre = nombre_candidato.lower().split()
        if all(palabra in palabras_a_ignorar for palabra in palabras_nombre):
            return False
        
        # Verificar que al menos una palabra comience con mayúscula
        if not any(palabra[0].isupper() for palabra in nombre_candidato.split()):
            return False
        
        # Verificar la longitud del nombre
        if len(nombre_candidato) < 3 or len(nombre_candidato) > 50:
            return False
            
        # Verificar que no sea una frase completa (más de 5 palabras probablemente no es un nombre)
        if len(palabras_nombre) > 5:
            return False
            
        # Verificar que no contenga números
        if any(char.isdigit() for char in nombre_candidato):
            return False
            
        # Verificar que no sean tipos de reunión
        tipos_reunion = ["presencial", "videoconferencia", "telefonica", "telefónica", "virtual", "online"]
        if any(tipo in nombre_candidato.lower() for tipo in tipos_reunion):
            return False
            
        return True
    
    # Buscar primero patrones explícitos
    for pattern in nombre_patterns:
        nombre_match = re.search(pattern, texto, re.IGNORECASE)
        if nombre_match:
            nombre_candidato = nombre_match.group(1).strip()
            
            if validar_nombre_candidato(nombre_candidato):
                datos["nombre"] = nombre_candidato
                break
    
    # Si no se encontró nombre con los patrones explícitos, buscar nombres propios
    if datos["nombre"] is None:
        # Buscar palabras que comiencen con mayúscula y que formen una secuencia coherente
        palabras = texto.split()
        for i, palabra in enumerate(palabras):
            # Verificar si es el inicio de un nombre propio (palabra con mayúscula inicial)
            if palabra[0].isupper() and len(palabra) > 1:
                nombre_candidato = palabra
                
                # Comprobar si las siguientes palabras también pueden ser parte del nombre
                j = i + 1
                while j < len(palabras) and j < i + 4:  # Limitamos a 4 palabras máximo
                    siguiente_palabra = palabras[j]
                    
                    # Si la siguiente palabra es una inicial (capital seguida de punto)
                    if siguiente_palabra[0].isupper() and len(siguiente_palabra) == 2 and siguiente_palabra[1] == '.':
                        nombre_candidato += " " + siguiente_palabra
                    # Si es una palabra que comienza con mayúscula
                    elif siguiente_palabra[0].isupper() and len(siguiente_palabra) > 1:
                        nombre_candidato += " " + siguiente_palabra
                    # Si es un conector común en nombres (de, la, del, etc.)
                    elif siguiente_palabra.lower() in ["de", "del", "la", "los", "las", "y", "e"]:
                        nombre_candidato += " " + siguiente_palabra
                    else:
                        break
                    j += 1
                
                # Validar el nombre candidato
                if validar_nombre_candidato(nombre_candidato):
                    # Verificar que no esté en medio de una oración que lo invalide
                    if i > 0:
                        palabra_anterior = palabras[i-1].lower()
                        # Si la palabra anterior invalida que sea un nombre, continuar
                        if palabra_anterior in ["tipo", "cita", "quiero", "presencial", "telefónica", "videoconferencia"]:
                            continue
                    
                    datos["nombre"] = nombre_candidato
                    break
    
    # Verificación final: asegurarse de que el nombre identificado no es un tipo de reunión o término del servicio
    if datos["nombre"]:
        nombre_lower = datos["nombre"].lower()
        invalidos = ["presencial", "videoconferencia", "telefonica", "telefónica", "virtual", "online", 
                    "consulta", "cita", "reunión", "reunion", "legal", "abogado"]
        
        if any(invalido in nombre_lower for invalido in invalidos):
            datos["nombre"] = None
    
    return datos