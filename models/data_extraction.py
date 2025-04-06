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
    
    # Palabras que no deben considerarse nombres
    palabras_a_ignorar = [
        "no", "si", "sí", "hola", "buenas", "buenos", "quiero", "quisiera", 
        "necesito", "confirmar", "cancelar", "el", "la", "los", "las",
        "presencial", "videoconferencia", "telefonica", "telefónica", 
        "consulta", "cita", "reunion", "reunión", "agendar", "legal",
        "tema", "asunto", "motivo", "porque", "sobre", "para", "como", 
        "por", "favor", "gracias", "deseo", "prefiero", "mejor"
    ]
    
    # Buscar nombre (patrones mejorados con más casos)
    nombre_patterns = [
        # Patrones explícitos - estos son prioritarios
        r'me llamo\s+([A-Za-záéíóúüñÁÉÍÓÚÜÑ]+(?:\s+[A-Za-záéíóúüñÁÉÍÓÚÜÑ]+){0,3})',
        r'mi nombre es\s+([A-Za-záéíóúüñÁÉÍÓÚÜÑ]+(?:\s+[A-Za-záéíóúüñÁÉÍÓÚÜÑ]+){0,3})',
        r'soy\s+([A-Za-záéíóúüñÁÉÍÓÚÜÑ]+(?:\s+[A-Za-záéíóúüñÁÉÍÓÚÜÑ]+){0,3})',
        r'nombre[:\s]+([A-Za-záéíóúüñÁÉÍÓÚÜÑ]+(?:\s+[A-Za-záéíóúüñÁÉÍÓÚÜÑ]+){0,3})'
    ]
    
    # Buscar primero patrones explícitos
    for pattern in nombre_patterns:
        nombre_match = re.search(pattern, texto, re.IGNORECASE)
        if nombre_match:
            nombre_candidato = nombre_match.group(1).strip()
            
            # Verificar que no sea una palabra o frase a ignorar
            palabras_nombre = nombre_candidato.lower().split()
            if not all(palabra in palabras_a_ignorar for palabra in palabras_nombre):
                # Verificar que no sea solo una palabra común
                if len(palabras_nombre) > 1 or (len(palabras_nombre) == 1 and len(palabras_nombre[0]) > 3):
                    # Filtrar conectores y preposiciones si hay más de 2 palabras
                    if len(palabras_nombre) > 2:
                        conectores = ["y", "e", "de", "del", "la", "el", "los", "las"]
                        # Si el nombre tiene muchas palabras, verificar que no sean solo conectores
                        if not all(palabra in conectores for palabra in palabras_nombre):
                            datos["nombre"] = nombre_candidato
                            break
                    else:
                        datos["nombre"] = nombre_candidato
                        break
    
    # Si no se encontró nombre con los patrones explícitos, buscar nombres propios
    if datos["nombre"] is None:
        # Buscar segmentos que parezcan nombres propios (primera letra mayúscula)
        # Pero solo después de frases como "soy" o "me llamo" si existen
        for prefix in ["soy ", "me llamo ", "llamame ", "mi nombre es "]:
            if prefix in texto_lower:
                # Buscar después del prefijo
                start_idx = texto_lower.find(prefix) + len(prefix)
                remaining_text = texto[start_idx:]
                
                # Buscar palabras que comiencen con mayúscula
                posibles_nombres = re.findall(r'(?:^|\s)([A-Z][a-záéíóúüñ]+(?:\s+[A-Z][a-záéíóúüñ]+){0,2})(?:\s|$|,|\.|;)', remaining_text)
                for posible_nombre in posibles_nombres:
                    # Verificar que no sea una palabra común o a ignorar
                    palabras = posible_nombre.lower().split()
                    if not any(palabra in palabras_a_ignorar for palabra in palabras):
                        # Verificar que tiene al menos 3 caracteres para evitar siglas o iniciales sueltas
                        if len(posible_nombre) >= 3:
                            datos["nombre"] = posible_nombre
                            break
                
                if datos["nombre"]:
                    break
    
    # Verificación final: asegurarse de que el nombre identificado no es un tipo de reunión
    if datos["nombre"]:
        tipos_reunion = ["presencial", "videoconferencia", "telefonica", "telefónica"]
        if datos["nombre"].lower() in tipos_reunion:
            datos["nombre"] = None
    
    return datos