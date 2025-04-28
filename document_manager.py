import os
import hashlib
import datetime
import logging
import mimetypes
from werkzeug.utils import secure_filename

# Configurar logging
logger = logging.getLogger(__name__)

class DocumentManager:
    """Clase para gestionar documentos: subida, descarga, almacenamiento, etc."""
    
    def __init__(self, upload_dir='uploads', db_manager=None):
        """
        Inicializa el gestor de documentos.
        
        Args:
            upload_dir: Directorio base para almacenar los archivos
            db_manager: Instancia de DatabaseManager para operaciones en BD
        """
        self.upload_dir = upload_dir
        self.db_manager = db_manager
        
        # Crear directorios si no existen
        self.create_directories()
    
    def create_directories(self):
        """Crea los directorios necesarios para almacenar documentos."""
        try:
            # Crear directorio base si no existe
            if not os.path.exists(self.upload_dir):
                os.makedirs(self.upload_dir)
            
            # Crear subdirectorios por tipo
            subdirs = ['clientes', 'proyectos', 'citas']
            for subdir in subdirs:
                path = os.path.join(self.upload_dir, subdir)
                if not os.path.exists(path):
                    os.makedirs(path)
                    
            logger.info(f"Directorios de documentos creados en {self.upload_dir}")
        except Exception as e:
            logger.error(f"Error al crear directorios para documentos: {str(e)}")
            raise
    
    def get_secure_filename(self, filename):
        """
        Genera un nombre de archivo seguro y único.
        
        Args:
            filename: Nombre original del archivo
            
        Returns:
            Nombre de archivo seguro y único
        """
        # Obtener un nombre base seguro
        secure_name = secure_filename(filename)
        
        # Añadir timestamp para hacerlo único
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Separar nombre y extensión
        name, ext = os.path.splitext(secure_name)
        
        # Crear nombre único combinando nombre base, timestamp y extensión
        unique_name = f"{name}_{timestamp}{ext}"
        
        return unique_name
    
    def calculate_md5(self, file_path):
        """
        Calcula el hash MD5 de un archivo.
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            Hash MD5 en formato hexadecimal
        """
        hash_md5 = hashlib.md5()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
                
        return hash_md5.hexdigest()
    
    def get_mime_type(self, filename):
        """
        Obtiene el tipo MIME de un archivo.
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            Tipo MIME o "application/octet-stream" si no se puede determinar
        """
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or "application/octet-stream"
    
    def upload_documento(self, file, entity_type, entity_id, notas=None):
        """
        Sube un documento y lo asocia a una entidad.
        
        Args:
            file: Objeto de archivo (e.j. request.files['file'])
            entity_type: Tipo de entidad ('cliente', 'proyecto', 'cita')
            entity_id: ID de la entidad
            notas: Notas sobre el documento (opcional)
            
        Returns:
            ID del documento creado o None si hay error
        """
        try:
            if not file:
                logger.error("No se proporcionó ningún archivo")
                return None
            
            # Verificar tipo de entidad
            if entity_type not in ['cliente', 'proyecto', 'cita']:
                logger.error(f"Tipo de entidad no válido: {entity_type}")
                return None
            
            # Generar nombre seguro
            original_filename = file.filename
            secure_name = self.get_secure_filename(original_filename)
            
            # Crear ruta para guardar el archivo
            subdir = f"{entity_type}s"  # clientes, proyectos, citas
            entity_dir = os.path.join(self.upload_dir, subdir, str(entity_id))
            
            # Crear directorio si no existe
            if not os.path.exists(entity_dir):
                os.makedirs(entity_dir)
            
            # Ruta completa del archivo
            file_path = os.path.join(entity_dir, secure_name)
            
            # Guardar el archivo
            file.save(file_path)
            
            # Obtener información del archivo
            file_size = os.path.getsize(file_path)
            file_type = self.get_mime_type(original_filename)
            file_hash = self.calculate_md5(file_path)
            
            # Registrar en base de datos
            if self.db_manager:
                # Guardar documento en la tabla de documentos
                doc_id = self.db_manager.add_documento(
                    nombre=original_filename,
                    tipo=file_type,
                    tamano=file_size,
                    ruta_archivo=file_path,
                    hash_md5=file_hash,
                    notas=notas
                )
                
                # Asociar el documento con la entidad correspondiente
                if entity_type == 'cliente':
                    self.db_manager.relacionar_documento_cliente(doc_id, entity_id)
                elif entity_type == 'proyecto':
                    self.db_manager.relacionar_documento_proyecto(doc_id, entity_id)
                elif entity_type == 'cita':
                    self.db_manager.relacionar_documento_cita(doc_id, entity_id)
                
                return doc_id
            else:
                logger.warning("No se proporcionó gestor de base de datos, el documento no se registró")
                return None
                
        except Exception as e:
            logger.error(f"Error al subir documento: {str(e)}")
            return None
    
    def download_documento(self, documento_id):
        """
        Prepara un documento para descarga.
        
        Args:
            documento_id: ID del documento a descargar
            
        Returns:
            Tupla (ruta_archivo, nombre_original, tipo_mime) o None si hay error
        """
        try:
            if not self.db_manager:
                logger.error("No se proporcionó gestor de base de datos")
                return None
            
            # Obtener información del documento
            documento = self.db_manager.get_documento(documento_id)
            
            if not documento:
                logger.error(f"Documento con ID {documento_id} no encontrado")
                return None
            
            # Verificar que el archivo existe
            if not os.path.exists(documento['ruta_archivo']):
                logger.error(f"Archivo no encontrado en disco: {documento['ruta_archivo']}")
                return None
            
            return (documento['ruta_archivo'], documento['nombre'], documento['tipo'])
            
        except Exception as e:
            logger.error(f"Error al preparar documento para descarga: {str(e)}")
            return None
    
    def delete_documento_file(self, file_path):
        """
        Elimina un archivo del sistema de archivos.
        
        Args:
            file_path: Ruta al archivo a eliminar
            
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            logger.error(f"Error al eliminar archivo: {str(e)}")
            return False