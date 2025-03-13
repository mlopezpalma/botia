import datetime
import re

def format_fecha(fecha_str, formato="DD/MM/YYYY"):
    """
    Formatea una fecha en el formato deseado.
    
    Args:
        fecha_str: Fecha en formato "YYYY-MM-DD"
        formato: Formato deseado (DD/MM/YYYY, YYYY/MM/DD, etc.)
        
    Returns:
        Fecha formateada según el formato especificado
    """
    try:
        fecha = datetime.datetime.strptime(fecha_str, "%Y-%m-%d")
        
        if formato == "DD/MM/YYYY":
            return fecha.strftime("%d/%m/%Y")
        elif formato == "YYYY/MM/DD":
            return fecha.strftime("%Y/%m/%d")
        elif formato == "DD-MM-YYYY":
            return fecha.strftime("%d-%m-%Y")
        elif formato == "YYYY-MM-DD":
            return fecha.strftime("%Y-%m-%d")
        elif formato == "DD/MM/YYYY (DIA)":
            # Con nombre del día de la semana
            dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            dia_semana = dias[fecha.weekday()]
            return f"{fecha.strftime('%d/%m/%Y')} ({dia_semana})"
        else:
            return fecha.strftime("%d/%m/%Y")  # Formato por defecto
    except ValueError:
        return fecha_str  # Devolver la entrada original si hay error

def format_hora(hora_str, formato="24h"):
    """
    Formatea una hora en el formato deseado.
    
    Args:
        hora_str: Hora en formato "HH:MM"
        formato: Formato deseado (24h, 12h)
        
    Returns:
        Hora formateada según el formato especificado
    """
    try:
        # Extraer horas y minutos
        match = re.match(r'^(\d{1,2}):(\d{2})$', hora_str)
        if not match:
            return hora_str  # Devolver la entrada original si no coincide con el patrón
        
        hora = int(match.group(1))
        minutos = match.group(2)
        
        if formato == "24h":
            return f"{hora:02d}:{minutos}"
        elif formato == "12h":
            # Convertir a formato 12h (AM/PM)
            if hora == 0:
                return f"12:{minutos} AM"
            elif hora < 12:
                return f"{hora}:{minutos} AM"
            elif hora == 12:
                return f"12:{minutos} PM"
            else:
                return f"{hora-12}:{minutos} PM"
        else:
            return hora_str  # Devolver la entrada original si el formato no es reconocido
    except (ValueError, AttributeError):
        return hora_str  # Devolver la entrada original si hay error

def get_proximos_dias(num_dias=7, incluir_fines_semana=False):
    """
    Obtiene una lista de las próximas fechas a partir de hoy.
    
    Args:
        num_dias: Número de días a obtener
        incluir_fines_semana: Si se deben incluir los fines de semana
        
    Returns:
        Lista de diccionarios con {fecha: "YYYY-MM-DD", dia_semana: "Lunes", ...}
    """
    hoy = datetime.datetime.now()
    dias = []
    dias_obtenidos = 0
    dias_comprobados = 0
    
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    
    while dias_obtenidos < num_dias and dias_comprobados < 30:  # Límite de 30 días para evitar bucles infinitos
        fecha_check = hoy + datetime.timedelta(days=dias_comprobados)
        dias_comprobados += 1
        
        # Saltar fines de semana si se especifica
        if not incluir_fines_semana and fecha_check.weekday() >= 5:  # 5=Sábado, 6=Domingo
            continue
        
        dia_semana = dias_semana[fecha_check.weekday()]
        
        dias.append({
            "fecha": fecha_check.strftime("%Y-%m-%d"),
            "fecha_formateada": fecha_check.strftime("%d/%m/%Y"),
            "dia_semana": dia_semana,
            "es_fin_semana": fecha_check.weekday() >= 5
        })
        
        dias_obtenidos += 1
    
    return dias

def validar_email(email):
    """
    Valida si un email tiene un formato válido.
    
    Args:
        email: Dirección de email a validar
        
    Returns:
        True si el email es válido, False en caso contrario
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True
    return False

def validar_telefono(telefono, pais="ES"):
    """
    Valida si un número de teléfono tiene un formato válido.
    
    Args:
        telefono: Número de teléfono a validar
        pais: Código de país para validar según sus reglas (ES=España)
        
    Returns:
        True si el teléfono es válido, False en caso contrario
    """
    # Eliminar espacios, guiones y paréntesis
    telefono_limpio = re.sub(r'[\s\-\(\)]', '', telefono)
    
    if pais == "ES":
        # Formatos válidos para España: +34XXXXXXXXX, 6XXXXXXXX, 7XXXXXXXX, 9XXXXXXXX
        pattern = r'^(?:\+34)?[679]\d{8}$'
        if re.match(pattern, telefono_limpio):
            return True
    else:
        # Validación genérica para otros países
        if len(telefono_limpio) >= 8 and telefono_limpio.isdigit():
            return True
    
    return False

def generar_id_unico():
    """
    Genera un ID único basado en timestamp y valores aleatorios.
    
    Returns:
        String con ID único
    """
    import time
    import random
    
    # Usar formato simple que coincida con la expresión regular en el test
    timestamp = int(time.time())
    random_part = random.randint(1000, 9999)
    
    return f"{timestamp}_{random_part}"
