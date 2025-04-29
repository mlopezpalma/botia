import hashlib
import time
import random
import datetime
import sqlite3
import logging

# Configurar logging
logger = logging.getLogger(__name__)

def generate_token(cita_id):
    """
    Genera un token único para subida de documentos.
    
    Args:
        cita_id: ID de la cita asociada al token
        
    Returns:
        Token generado
    """
    token_base = f"{cita_id}-{time.time()}-{random.randint(1000, 9999)}"
    return hashlib.md5(token_base.encode()).hexdigest()

def store_token(db_file, token, cita_id):
    """
    Almacena un token en la base de datos.
    
    Args:
        db_file: Ruta del archivo de base de datos
        token: Token a almacenar
        cita_id: ID de la cita asociada
        
    Returns:
        True si se almacenó correctamente, False en caso contrario
    """
    # Fechas de creación y expiración
    now = datetime.datetime.now()
    expiration = now + datetime.timedelta(hours=24)
    
    # Guardar en la base de datos
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO upload_tokens (token, cita_id, fecha_creacion, fecha_expiracion, usado) VALUES (?, ?, ?, ?, ?)",
            (token, cita_id, now.strftime("%Y-%m-%d %H:%M:%S"), expiration.strftime("%Y-%m-%d %H:%M:%S"), 0)
        )
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error al guardar token en la base de datos: {str(e)}")
        return False
    finally:
        conn.close()

def validate_token(db_file, token):
    """
    Valida un token y lo marca como usado.
    
    Args:
        db_file: Ruta del archivo de base de datos
        token: Token a validar
        
    Returns:
        ID de la cita asociada o None si el token es inválido
    """
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT cita_id, fecha_expiracion, usado FROM upload_tokens WHERE token = ?", (token,))
        result = cursor.fetchone()
        
        if not result:
            return None
        
        cita_id, fecha_expiracion, usado = result
        
        # Verificar si el token ya fue usado
        if usado:
            return None
        
        # Verificar si el token ha expirado
        expiration = datetime.datetime.strptime(fecha_expiracion, "%Y-%m-%d %H:%M:%S")
        now = datetime.datetime.now()
        
        if now > expiration:
            return None
        
        # Marcar el token como usado
        cursor.execute("UPDATE upload_tokens SET usado = 1 WHERE token = ?", (token,))
        conn.commit()
        
        return cita_id
    except Exception as e:
        logger.error(f"Error al validar token: {str(e)}")
        return None
    finally:
        conn.close()

def create_upload_tokens_table(db_file):
    """
    Crea la tabla para almacenar tokens si no existe.
    
    Args:
        db_file: Ruta del archivo de base de datos
    """
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # Tabla para tokens de carga temporales
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS upload_tokens (
            token TEXT PRIMARY KEY,
            cita_id TEXT NOT NULL,
            fecha_creacion TEXT NOT NULL,
            fecha_expiracion TEXT NOT NULL,
            usado INTEGER DEFAULT 0
        )
        ''')
        
        conn.commit()
    except Exception as e:
        logger.error(f"Error al crear tabla de tokens: {str(e)}")
    finally:
        conn.close()