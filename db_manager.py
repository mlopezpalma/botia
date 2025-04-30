# Crear un nuevo archivo: db_manager.py

import sqlite3
import os
import json
import datetime

class DatabaseManager:
    def __init__(self, db_file='botia.db'):
        """Inicializa el gestor de base de datos."""
        self.db_file = db_file
        self.initialize_db()
        self.initialize_user_tables()
        self.initialize_document_tables()
    
    def initialize_db(self):
        """Crea las tablas si no existen."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Tabla de clientes
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            telefono TEXT,
            fecha_registro TEXT,
            notas TEXT
        )
        ''')
        
        # Tabla de citas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS citas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            tipo TEXT NOT NULL,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            tema TEXT,
            estado TEXT DEFAULT 'pendiente',
            fecha_creacion TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes (id)
        )
        ''')
        
        # Tabla de casos/proyectos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            titulo TEXT NOT NULL,
            descripcion TEXT,
            estado TEXT DEFAULT 'nuevo',
            abogado TEXT,
            fecha_inicio TEXT,
            ultima_actualizacion TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes (id)
        )
        ''')
        
        # Tabla de eventos críticos de los proyectos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS eventos_proyecto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proyecto_id INTEGER,
            titulo TEXT NOT NULL,
            descripcion TEXT,
            fecha TEXT NOT NULL,
            completado INTEGER DEFAULT 0,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos (id)
        )
        ''')
        
        # Tabla de notas de proyectos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notas_proyecto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proyecto_id INTEGER,
            fecha TEXT NOT NULL,
            texto TEXT NOT NULL,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos (id)
        )
        ''')
        
        conn.commit()
        conn.close()



    def initialize_document_tables(self):
        """Crea las tablas para gestión de documentos si no existen."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        # Tabla de documentos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            tipo TEXT NOT NULL,
            tamano INTEGER NOT NULL,
            fecha_subida TEXT NOT NULL,
            ruta_archivo TEXT NOT NULL,
            hash_md5 TEXT,
            notas TEXT
        )
        ''')
    
        # Tabla de relaciones documentos-cliente
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS documento_cliente (
            documento_id INTEGER,
            cliente_id INTEGER,
            FOREIGN KEY (documento_id) REFERENCES documentos (id),
            FOREIGN KEY (cliente_id) REFERENCES clientes (id),
            PRIMARY KEY (documento_id, cliente_id)
        )
        ''')
    
        # Tabla de relaciones documentos-proyecto
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS documento_proyecto (
            documento_id INTEGER,
            proyecto_id INTEGER,
            FOREIGN KEY (documento_id) REFERENCES documentos (id),
            FOREIGN KEY (proyecto_id) REFERENCES proyectos (id),
            PRIMARY KEY (documento_id, proyecto_id)
        )
        ''')
    
        # Tabla de relaciones documentos-cita
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS documento_cita (
            documento_id INTEGER,
            cita_id INTEGER,
            FOREIGN KEY (documento_id) REFERENCES documentos (id),
            FOREIGN KEY (cita_id) REFERENCES citas (id),
            PRIMARY KEY (documento_id, cita_id)
        )
        ''')
    
        conn.commit()
        conn.close()

    # Métodos para gestión de documentos
    def add_documento(self, nombre, tipo, tamano, ruta_archivo, hash_md5=None, notas=None):
        """
        Añade un nuevo documento a la base de datos.

        Args:
            nombre: Nombre original del documento
            tipo: Tipo MIME o extensión del documento
            tamano: Tamaño en bytes
            ruta_archivo: Ruta donde se almacena el archivo
            hash_md5: Hash MD5 para verificación (opcional)
            notas: Notas sobre el documento (opcional)
    
        Returns:
            ID del documento creado
        """
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        # Usar datetime directamente, sin llamar a datetime.datetime
        fecha_subida = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """INSERT INTO documentos 
               (nombre, tipo, tamano, fecha_subida, ruta_archivo, hash_md5, notas) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (nombre, tipo, tamano, fecha_subida, ruta_archivo, hash_md5, notas)
        )

        documento_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return documento_id

    def relacionar_documento_cliente(self, documento_id, cliente_id):
        """Relaciona un documento con un cliente."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        cursor.execute(
            "INSERT OR IGNORE INTO documento_cliente (documento_id, cliente_id) VALUES (?, ?)",
            (documento_id, cliente_id)
        )
    
        conn.commit()
        conn.close()

    def relacionar_documento_proyecto(self, documento_id, proyecto_id):
        """Relaciona un documento con un proyecto."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        cursor.execute(
            "INSERT OR IGNORE INTO documento_proyecto (documento_id, proyecto_id) VALUES (?, ?)",
            (documento_id, proyecto_id)
        )
    
        conn.commit()
        conn.close()

    def relacionar_documento_cita(self, documento_id, cita_id):
        """Relaciona un documento con una cita."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        cursor.execute(
            "INSERT OR IGNORE INTO documento_cita (documento_id, cita_id) VALUES (?, ?)",
            (documento_id, cita_id)
        )
    
        conn.commit()
        conn.close()

    def get_documentos_cliente(self, cliente_id):
        """Obtiene todos los documentos asociados a un cliente."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        cursor.execute("""
        SELECT d.* FROM documentos d
        JOIN documento_cliente dc ON d.id = dc.documento_id
        WHERE dc.cliente_id = ?
        ORDER BY d.fecha_subida DESC
        """, (cliente_id,))
    
        docs = cursor.fetchall()
        documentos = []
    
        for doc in docs:
            documentos.append({
                'id': doc[0],
                'nombre': doc[1],
                'tipo': doc[2],
                'tamano': doc[3],
                'fecha_subida': doc[4],
                'ruta_archivo': doc[5],
                'hash_md5': doc[6],
                'notas': doc[7]
            })
    
        conn.close()
        return documentos

    def get_documentos_proyecto(self, proyecto_id):
        """Obtiene todos los documentos asociados a un proyecto."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        cursor.execute("""
        SELECT d.* FROM documentos d
        JOIN documento_proyecto dp ON d.id = dp.documento_id
        WHERE dp.proyecto_id = ?
        ORDER BY d.fecha_subida DESC
        """, (proyecto_id,))
    
        docs = cursor.fetchall()
        documentos = []

        for doc in docs:
            documentos.append({
                'id': doc[0],
                'nombre': doc[1],
                'tipo': doc[2],
                'tamano': doc[3],
                'fecha_subida': doc[4],
                'ruta_archivo': doc[5],
                'hash_md5': doc[6],
                'notas': doc[7]
            })
    
        conn.close()
        return documentos

    def get_documentos_cita(self, cita_id):
        """Obtiene todos los documentos asociados a una cita."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        cursor.execute("""
        SELECT d.* FROM documentos d
        JOIN documento_cita dc ON d.id = dc.documento_id
        WHERE dc.cita_id = ?
        ORDER BY d.fecha_subida DESC
        """, (cita_id,))

        docs = cursor.fetchall()
        documentos = []

        for doc in docs:
            documentos.append({
                'id': doc[0],
                'nombre': doc[1],
                'tipo': doc[2],
                'tamano': doc[3],
                'fecha_subida': doc[4],
                'ruta_archivo': doc[5],
                'hash_md5': doc[6],
                'notas': doc[7]
            })
    
        conn.close()
        return documentos

    def get_documento(self, documento_id):
        """Obtiene información detallada de un documento."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM documentos WHERE id = ?", (documento_id,))
        doc = cursor.fetchone()

        if not doc:
            conn.close()
            return None
    
        documento = {
            'id': doc[0],
            'nombre': doc[1],
            'tipo': doc[2],
            'tamano': doc[3],
            'fecha_subida': doc[4],
            'ruta_archivo': doc[5],
            'hash_md5': doc[6],
            'notas': doc[7],
            'clientes': [],
            'proyectos': [],
            'citas': []
        }
    
        # Obtener clientes relacionados
        cursor.execute("""
        SELECT c.id, c.nombre FROM clientes c
        JOIN documento_cliente dc ON c.id = dc.cliente_id
        WHERE dc.documento_id = ?
        """, (documento_id,))
    
        clientes = cursor.fetchall()
        for cliente in clientes:
            documento['clientes'].append({
                'id': cliente[0],
                'nombre': cliente[1]
            })
    
        # Obtener proyectos relacionados
        cursor.execute("""
        SELECT p.id, p.titulo FROM proyectos p
        JOIN documento_proyecto dp ON p.id = dp.proyecto_id
        WHERE dp.documento_id = ?
        """, (documento_id,))
    
        proyectos = cursor.fetchall()
        for proyecto in proyectos:
            documento['proyectos'].append({
                'id': proyecto[0],
                'titulo': proyecto[1]
            })
    
        # Obtener citas relacionadas
        cursor.execute("""
        SELECT c.id, c.fecha, c.hora, c.tipo FROM citas c
        JOIN documento_cita dc ON c.id = dc.cita_id
        WHERE dc.documento_id = ?
        """, (documento_id,))
    
        citas = cursor.fetchall()
        for cita in citas:
            documento['citas'].append({
                'id': cita[0],
                'fecha': cita[1],
                'hora': cita[2],
                'tipo': cita[3]
            })
    
        conn.close()
        return documento

    def delete_documento(self, documento_id):
        """Elimina un documento y sus relaciones."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        # Primero obtenemos la ruta del archivo para eliminarlo del sistema de archivos
        cursor.execute("SELECT ruta_archivo FROM documentos WHERE id = ?", (documento_id,))
        ruta = cursor.fetchone()
    
        if ruta:
            # Eliminar las relaciones
            cursor.execute("DELETE FROM documento_cliente WHERE documento_id = ?", (documento_id,))
            cursor.execute("DELETE FROM documento_proyecto WHERE documento_id = ?", (documento_id,))
            cursor.execute("DELETE FROM documento_cita WHERE documento_id = ?", (documento_id,))
        
            # Eliminar el documento de la base de datos
            cursor.execute("DELETE FROM documentos WHERE id = ?", (documento_id,))

            conn.commit()
        
            # Eliminar el archivo físicamente
            try:
                import os
                if os.path.exists(ruta[0]):
                    os.remove(ruta[0])
            except Exception as e:
                print(f"Error al eliminar archivo: {str(e)}")
    
        conn.close()
        return True



        # Tablas para gestión de usuarios
    def initialize_user_tables(self):
        """Crea las tablas de usuarios si no existen."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        # Tabla de usuarios
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nombre TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            activo INTEGER DEFAULT 1,
            fecha_creacion TEXT,
            ultimo_acceso TEXT
        )
        ''')
    
        # Tabla de roles y permisos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            descripcion TEXT
        )
        ''')
    
        # Tabla de permisos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS permisos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rol_id INTEGER,
            permiso TEXT NOT NULL,
            FOREIGN KEY (rol_id) REFERENCES roles (id)
        )
        ''')
    
        # Comprobar si hay usuarios administradores
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE role='admin'")
        admin_count = cursor.fetchone()[0]
    
        # Si no hay usuarios administradores, crear uno por defecto
        if admin_count == 0:
            # Usar bcrypt para el hash de la contraseña
            import bcrypt
            import datetime
        
            # Contraseña por defecto: admin
            password = 'admin'
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        
            fecha_creacion = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
            cursor.execute(
                "INSERT INTO usuarios (username, password, nombre, email, role, fecha_creacion) VALUES (?, ?, ?, ?, ?, ?)",
                ('admin', hashed_password.decode('utf-8'), 'Administrador', 'admin@example.com', 'admin', fecha_creacion)
            )
        
            # Insertar roles predefinidos
            cursor.execute("INSERT OR IGNORE INTO roles (nombre, descripcion) VALUES (?, ?)",
                          ('admin', 'Administrador con acceso total'))
            cursor.execute("INSERT OR IGNORE INTO roles (nombre, descripcion) VALUES (?, ?)",
                          ('gestor', 'Gestión de clientes y citas'))
            cursor.execute("INSERT OR IGNORE INTO roles (nombre, descripcion) VALUES (?, ?)",
                          ('abogado', 'Acceso solo a sus casos asignados'))
            cursor.execute("INSERT OR IGNORE INTO roles (nombre, descripcion) VALUES (?, ?)",
                          ('recepcion', 'Gestión de citas'))
    
        conn.commit()
        conn.close()

    # Métodos para gestión de usuarios
    def add_usuario(self, username, password, nombre, email, role='user'):
        """Añade un nuevo usuario al sistema."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        import bcrypt
        import datetime
    
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        fecha_creacion = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
        try:
            cursor.execute(
                "INSERT INTO usuarios (username, password, nombre, email, role, fecha_creacion) VALUES (?, ?, ?, ?, ?, ?)",
                (username, hashed_password.decode('utf-8'), nombre, email, role, fecha_creacion)
            )
            conn.commit()
            usuario_id = cursor.lastrowid
            return usuario_id
        except sqlite3.IntegrityError:
            # Si ya existe un usuario con ese username o email
            return None
        finally:
            conn.close()

    def authenticate_user(self, username, password):
        """Autentica un usuario con su username y password."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        import bcrypt
        import datetime
    
        cursor.execute("SELECT id, password, role, activo FROM usuarios WHERE username=?", (username,))
        user = cursor.fetchone()
    
        if user and user[3] == 1:  # Verificar que la cuenta está activa
            stored_password = user[1]
            # Verificar la contraseña
            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                # Actualizar último acceso
                ultimo_acceso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("UPDATE usuarios SET ultimo_acceso=? WHERE id=?", (ultimo_acceso, user[0]))
                conn.commit()
            
                conn.close()
                return {"id": user[0], "role": user[2]}
    
        conn.close()
        return None

    def get_all_usuarios(self):
        """Obtiene todos los usuarios del sistema."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        cursor.execute("SELECT id, username, nombre, email, role, activo, fecha_creacion, ultimo_acceso FROM usuarios")
        usuarios_raw = cursor.fetchall()
    
        conn.close()
    
        usuarios = []
        for u in usuarios_raw:
            usuarios.append({   
                'id': u[0],
                'username': u[1],
                'nombre': u[2],
                'email': u[3],
                'role': u[4],
                'activo': bool(u[5]),
                'fecha_creacion': u[6],
                'ultimo_acceso': u[7]
            })
    
        return usuarios

    def update_usuario(self, usuario_id, **kwargs):
        """Actualiza un usuario existente."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        # Actualizar solo los campos proporcionados
        set_clause = []
        values = []
    
        # Manejar contraseña por separado
        if 'password' in kwargs:
            import bcrypt
            password = kwargs.pop('password')
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
            set_clause.append("password=?")
            values.append(hashed_password.decode('utf-8'))
    
        for key, value in kwargs.items():
            set_clause.append(f"{key}=?")
            values.append(value)
    
        # Añadir ID del usuario
        values.append(usuario_id)
    
        query = f"UPDATE usuarios SET {', '.join(set_clause)} WHERE id=?"
        cursor.execute(query, values)
    
        conn.commit()
        conn.close()
    
        return True

    def get_usuario_by_id(self, usuario_id):
        """Obtiene un usuario por su ID."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        cursor.execute("SELECT id, username, nombre, email, role, activo, fecha_creacion, ultimo_acceso FROM usuarios WHERE id=?", (usuario_id,))
        usuario = cursor.fetchone()
    
        conn.close()
    
        if usuario:
            return {
                'id': usuario[0],
                'username': usuario[1],
                'nombre': usuario[2],
                'email': usuario[3],
                'role': usuario[4],
                'activo': bool(usuario[5]),
                'fecha_creacion': usuario[6],
                'ultimo_acceso': usuario[7]
            }
        return None

    def delete_usuario(self, usuario_id):
        """Elimina un usuario del sistema."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        # Por seguridad, verificar que no es el último administrador
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE role='admin'")
        admin_count = cursor.fetchone()[0]
    
        cursor.execute("SELECT role FROM usuarios WHERE id=?", (usuario_id,))
        user_role = cursor.fetchone()
    
        if admin_count <= 1 and user_role and user_role[0] == 'admin':
            # No permitir eliminar el último administrador
            conn.close()
            return False
    
        # Eliminar el usuario
        cursor.execute("DELETE FROM usuarios WHERE id=?", (usuario_id,))
    
        conn.commit()
        conn.close()
    
        return True




    # Métodos para clientes
    def add_cliente(self, nombre, email, telefono, notas=""):
        """Añade un nuevo cliente a la base de datos."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        fecha_registro = datetime.now().strftime("%Y-%m-%d")
        
        try:
            cursor.execute(
                "INSERT INTO clientes (nombre, email, telefono, fecha_registro, notas) VALUES (?, ?, ?, ?, ?)",
                (nombre, email, telefono, fecha_registro, notas)
            )
            conn.commit()
            cliente_id = cursor.lastrowid
            return cliente_id
        except sqlite3.IntegrityError:
            # Si ya existe un cliente con ese email, actualizarlo
            cursor.execute(
                "UPDATE clientes SET nombre=?, telefono=?, notas=? WHERE email=?",
                (nombre, telefono, notas, email)
            )
            conn.commit()
            cursor.execute("SELECT id FROM clientes WHERE email=?", (email,))
            cliente_id = cursor.fetchone()[0]
            return cliente_id
        finally:
            conn.close()
    
    def get_cliente_by_email(self, email):
        """Obtiene un cliente por su email."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM clientes WHERE email=?", (email,))
        cliente = cursor.fetchone()
        
        conn.close()
        
        if cliente:
            return {
                'id': cliente[0],
                'nombre': cliente[1],
                'email': cliente[2],
                'telefono': cliente[3],
                'fecha_registro': cliente[4],
                'notas': cliente[5]
            }
        return None
    
    def get_cliente_by_telefono(self, telefono):
        """Obtiene un cliente por su teléfono."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM clientes WHERE telefono=?", (telefono,))
        cliente = cursor.fetchone()
        
        conn.close()
        
        if cliente:
            return {
                'id': cliente[0],
                'nombre': cliente[1],
                'email': cliente[2],
                'telefono': cliente[3],
                'fecha_registro': cliente[4],
                'notas': cliente[5]
            }
        return None
    
    def get_all_clientes(self):
        """Obtiene todos los clientes."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM clientes ORDER BY nombre")
        clientes_raw = cursor.fetchall()
        
        conn.close()
        
        clientes = []
        for c in clientes_raw:
            clientes.append({
                'id': c[0],
                'nombre': c[1],
                'email': c[2],
                'telefono': c[3],
                'fecha_registro': c[4],
                'notas': c[5]
            })
        
        return clientes
    
    # Métodos para citas
    def add_cita(self, cliente_id, tipo, fecha, hora, tema=""):
        """Añade una nueva cita."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute(
            "INSERT INTO citas (cliente_id, tipo, fecha, hora, tema, fecha_creacion) VALUES (?, ?, ?, ?, ?, ?)",
            (cliente_id, tipo, fecha, hora, tema, fecha_creacion)
        )
        
        conn.commit()
        cita_id = cursor.lastrowid
        conn.close()
        
        return cita_id
    
    def get_citas_by_cliente(self, cliente_id):
        """Obtiene las citas de un cliente."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM citas WHERE cliente_id=? ORDER BY fecha, hora", (cliente_id,))
        citas_raw = cursor.fetchall()
        
        conn.close()
        
        citas = []
        for c in citas_raw:
            citas.append({
                'id': c[0],
                'cliente_id': c[1],
                'tipo': c[2],
                'fecha': c[3],
                'hora': c[4],
                'tema': c[5],
                'estado': c[6],
                'fecha_creacion': c[7]
            })
        
        return citas
    
    # Métodos para proyectos
    def add_proyecto(self, cliente_id, titulo, descripcion="", abogado="", estado="nuevo"):
        """Añade un nuevo proyecto o caso legal."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        fecha_inicio = datetime.now().strftime("%Y-%m-%d")
        ultima_actualizacion = fecha_inicio
        
        cursor.execute(
            "INSERT INTO proyectos (cliente_id, titulo, descripcion, estado, abogado, fecha_inicio, ultima_actualizacion) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (cliente_id, titulo, descripcion, estado, abogado, fecha_inicio, ultima_actualizacion)
        )
        
        conn.commit()
        proyecto_id = cursor.lastrowid
        conn.close()
        
        return proyecto_id
    
    def update_proyecto(self, proyecto_id, **kwargs):
        """Actualiza un proyecto existente."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Actualizar solo los campos proporcionados
        set_clause = []
        values = []
        
        for key, value in kwargs.items():
            set_clause.append(f"{key}=?")
            values.append(value)
        
        # Añadir fecha de actualización
        set_clause.append("ultima_actualizacion=?")
        values.append(datetime.now().strftime("%Y-%m-%d"))
        
        # Añadir ID del proyecto
        values.append(proyecto_id)
        
        query = f"UPDATE proyectos SET {', '.join(set_clause)} WHERE id=?"
        cursor.execute(query, values)
        
        conn.commit()
        conn.close()
    
    def get_proyecto(self, proyecto_id):
        """Obtiene un proyecto por su ID."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM proyectos WHERE id=?", (proyecto_id,))
        proyecto = cursor.fetchone()
        
        if not proyecto:
            conn.close()
            return None
        
        proyecto_dict = {
            'id': proyecto[0],
            'cliente_id': proyecto[1],
            'titulo': proyecto[2],
            'descripcion': proyecto[3],
            'estado': proyecto[4],
            'abogado': proyecto[5],
            'fecha_inicio': proyecto[6],
            'ultima_actualizacion': proyecto[7],
            'notas': [],
            'eventos': []
        }
        
        # Obtener notas del proyecto
        cursor.execute("SELECT * FROM notas_proyecto WHERE proyecto_id=? ORDER BY fecha DESC", (proyecto_id,))
        notas = cursor.fetchall()
        
        for nota in notas:
            proyecto_dict['notas'].append({
                'id': nota[0],
                'fecha': nota[2],
                'texto': nota[3]
            })
        
        # Obtener eventos del proyecto
        cursor.execute("SELECT * FROM eventos_proyecto WHERE proyecto_id=? ORDER BY fecha", (proyecto_id,))
        eventos = cursor.fetchall()
        
        for evento in eventos:
            proyecto_dict['eventos'].append({
                'id': evento[0],
                'titulo': evento[2],
                'descripcion': evento[3],
                'fecha': evento[4],
                'completado': bool(evento[5])
            })
        
        conn.close()
        return proyecto_dict
    
    def get_proyectos_by_cliente(self, cliente_id):
        """Obtiene los proyectos de un cliente."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        cursor.execute("SELECT * FROM proyectos WHERE cliente_id=? ORDER BY ultima_actualizacion DESC", (cliente_id,))
        proyectos_raw = cursor.fetchall()
    
        # Obtener datos del cliente
        cursor.execute("SELECT nombre, email FROM clientes WHERE id=?", (cliente_id,))
        cliente_data = cursor.fetchone()
        cliente_nombre = cliente_data[0] if cliente_data else "Cliente desconocido"
        cliente_email = cliente_data[1] if cliente_data else ""
    
        proyectos = []
        for p in proyectos_raw:
            proyecto_id = p[0]
            proyecto = {
                'id': proyecto_id,
                'cliente_id': p[1],
                'titulo': p[2],
                'descripcion': p[3],
                'estado': p[4],
                'abogado': p[5],
                'fecha_inicio': p[6],
                'ultima_actualizacion': p[7],
                'cliente_nombre': cliente_nombre,
                'cliente_email': cliente_email,
                'notas': []
            }
        
            # Obtener solo las últimas 2 notas para cada proyecto
            cursor.execute("SELECT * FROM notas_proyecto WHERE proyecto_id=? ORDER BY fecha DESC LIMIT 2", (proyecto_id,))
            notas = cursor.fetchall()
        
            for nota in notas:
                proyecto['notas'].append({
                    'id': nota[0],
                    'fecha': nota[2],
                    'texto': nota[3]
                })
        
            proyectos.append(proyecto)
    
        conn.close()
        return proyectos
    
    # Métodos para eventos de proyectos
    def add_evento_proyecto(self, proyecto_id, titulo, fecha, descripcion=""):
        """Añade un evento crítico a un proyecto."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO eventos_proyecto (proyecto_id, titulo, descripcion, fecha) VALUES (?, ?, ?, ?)",
            (proyecto_id, titulo, descripcion, fecha)
        )
        
        # Actualizar última fecha de actualización del proyecto
        cursor.execute(
            "UPDATE proyectos SET ultima_actualizacion=? WHERE id=?",
            (datetime.now().strftime("%Y-%m-%d"), proyecto_id)
        )
        
        conn.commit()
        evento_id = cursor.lastrowid
        conn.close()
        
        return evento_id
    
    def update_evento_proyecto(self, evento_id, completado=None, **kwargs):
        """Actualiza un evento crítico de proyecto."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Obtener proyecto_id para actualizarlo después
        cursor.execute("SELECT proyecto_id FROM eventos_proyecto WHERE id=?", (evento_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False
        
        proyecto_id = result[0]
        
        # Actualizar solo los campos proporcionados
        set_clause = []
        values = []
        
        for key, value in kwargs.items():
            set_clause.append(f"{key}=?")
            values.append(value)
        
        # Actualizar estado completado si se proporciona
        if completado is not None:
            set_clause.append("completado=?")
            values.append(1 if completado else 0)
        
        # Añadir ID del evento
        values.append(evento_id)
        
        query = f"UPDATE eventos_proyecto SET {', '.join(set_clause)} WHERE id=?"
        cursor.execute(query, values)
        
        # Actualizar última fecha de actualización del proyecto
        cursor.execute(
            "UPDATE proyectos SET ultima_actualizacion=? WHERE id=?",
            (datetime.now().strftime("%Y-%m-%d"), proyecto_id)
        )
        
        conn.commit()
        conn.close()
        return True
    
    # Métodos para notas de proyectos
    def add_nota_proyecto(self, proyecto_id, texto):
        """Añade una nota a un proyecto."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        fecha = datetime.now().strftime("%Y-%m-%d")
        
        cursor.execute(
            "INSERT INTO notas_proyecto (proyecto_id, fecha, texto) VALUES (?, ?, ?)",
            (proyecto_id, fecha, texto)
        )
        
        # Actualizar última fecha de actualización del proyecto
        cursor.execute(
            "UPDATE proyectos SET ultima_actualizacion=? WHERE id=?",
            (fecha, proyecto_id)
        )
        
        conn.commit()
        nota_id = cursor.lastrowid
        conn.close()
        
        return nota_id
    
    # Métodos para sincronización con el dic
    

    # Métodos para importar datos desde los diccionarios en memoria
    def import_from_memory(self, clientes_db, citas_db, casos_db):
        """Importa datos desde los diccionarios en memoria a la base de datos SQLite."""
        # Importar clientes
        for email, cliente_data in clientes_db.items():
            cliente_id = self.add_cliente(
                nombre=cliente_data.get('nombre', ''),
                email=email,
                telefono=cliente_data.get('telefono', '')
            )
            
            # Importar citas del cliente
            for cita_id in cliente_data.get('citas', []):
                if cita_id in citas_db:
                    cita_data = citas_db[cita_id]
                    self.add_cita(
                        cliente_id=cliente_id,
                        tipo=cita_data.get('tipo', ''),
                        fecha=cita_data.get('fecha', ''),
                        hora=cita_data.get('hora', ''),
                        tema=cita_data.get('tema', '')
                    )
        
        # Importar casos/proyectos
        for caso_id, caso_data in casos_db.items():
            email_cliente = caso_data.get('cliente_email', '')
            # Buscar el cliente por email
            cliente = self.get_cliente_by_email(email_cliente)
            if cliente:
                proyecto_id = self.add_proyecto(
                    cliente_id=cliente['id'],
                    titulo=caso_data.get('titulo', ''),
                    descripcion=caso_data.get('descripcion', ''),
                    abogado=caso_data.get('abogado', ''),
                    estado=caso_data.get('estado', 'nuevo')
                )
                
                # Importar notas del caso
                for nota in caso_data.get('notas', []):
                    self.add_nota_proyecto(
                        proyecto_id=proyecto_id,
                        texto=nota.get('texto', '')
                    )
    
    # Métodos para exportar datos a formato JSON
    def export_to_json(self, filename='botia_export.json'):
        """Exporta todos los datos de la base de datos a un archivo JSON."""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row  # Para acceder a columnas por nombre
        cursor = conn.cursor()
        
        export_data = {
            'clientes': [],
            'citas': [],
            'proyectos': [],
            'eventos_proyecto': [],
            'notas_proyecto': []
        }
        
        # Exportar clientes
        cursor.execute("SELECT * FROM clientes")
        for row in cursor.fetchall():
            export_data['clientes'].append(dict(row))
        
        # Exportar citas
        cursor.execute("SELECT * FROM citas")
        for row in cursor.fetchall():
            export_data['citas'].append(dict(row))
        
        # Exportar proyectos
        cursor.execute("SELECT * FROM proyectos")
        for row in cursor.fetchall():
            export_data['proyectos'].append(dict(row))
        
        # Exportar eventos de proyectos
        cursor.execute("SELECT * FROM eventos_proyecto")
        for row in cursor.fetchall():
            export_data['eventos_proyecto'].append(dict(row))
        
        # Exportar notas de proyectos
        cursor.execute("SELECT * FROM notas_proyecto")
        for row in cursor.fetchall():
            export_data['notas_proyecto'].append(dict(row))
        
        conn.close()
        
        # Guardar a archivo JSON
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=4)
        
        return export_data
    
    # Método para obtener todos los eventos del calendario

    # Actualizar el método get_all_calendar_events en db_manager.py

    def get_all_calendar_events(self, start_date=None, end_date=None):
        """
        Obtiene todos los eventos para el calendario en un rango de fechas.
        Incluye citas y eventos críticos de proyectos.
        """
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        events = []
    
        # Construir condiciones de fecha si se proporcionan
        date_condition = ""
        params = []
    
        if start_date:
            date_condition += " AND fecha >= ?"
            params.append(start_date)
    
        if end_date:
            date_condition += " AND fecha <= ?"
            params.append(end_date)
    
        # Obtener citas
        query = f"""
        SELECT c.id, c.fecha, c.hora, c.tipo, c.tema, c.estado, 
               cl.nombre, cl.email, cl.telefono
        FROM citas c
        JOIN clientes cl ON c.cliente_id = cl.id
        WHERE 1=1 {date_condition}
        ORDER BY c.fecha, c.hora
        """
    
        cursor.execute(query, params)
        citas = cursor.fetchall()
    
        for cita in citas:
            events.append({
                'id': f"cita_{cita[0]}",
                'title': f"{cita[3]}: {cita[6]}",
                'start': f"{cita[1]}T{cita[2]}",
                'description': cita[4] or "",
                'type': 'appointment',
                'status': cita[5],
                'client': {
                    'name': cita[6],
                    'email': cita[7],
                    'phone': cita[8]
                }
            })
    
        # Obtener eventos críticos de proyectos
        query = f"""
        SELECT e.id, e.fecha, e.titulo, e.descripcion, e.completado,
               p.id as proyecto_id, p.titulo as proyecto_titulo,
               cl.nombre, cl.email
        FROM eventos_proyecto e
        JOIN proyectos p ON e.proyecto_id = p.id
        JOIN clientes cl ON p.cliente_id = cl.id
        WHERE 1=1 {date_condition}
        ORDER BY e.fecha
        """
    
        cursor.execute(query, params)
        eventos = cursor.fetchall()
    
        for evento in eventos:
            events.append({
                'id': f"evento_{evento[0]}",
                'title': evento[2],
                'start': f"{evento[1]}T00:00:00",
                'description': evento[3] or "",
                'type': 'critical',
                'completed': bool(evento[4]),
                'project': {
                    'id': evento[5],
                    'title': evento[6]
                },
                'client': {
                    'name': evento[7],
                    'email': evento[8]
                }
            })
    
        conn.close()
        return events
    
    # Métodos adicionales a agregar en la clase DatabaseManager en db_manager.py

    def get_cliente_by_id(self, cliente_id):
        """
        Obtiene un cliente por su ID.
    
        Args:
            cliente_id: ID del cliente
        
        Returns:
            Diccionario con los datos del cliente o None si no se encuentra
        """
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        cursor.execute("SELECT * FROM clientes WHERE id=?", (cliente_id,))
        cliente = cursor.fetchone()
    
        conn.close()
    
        if cliente:
            return {
                'id': cliente[0],
                'nombre': cliente[1],
                'email': cliente[2],
                'telefono': cliente[3],
                'fecha_registro': cliente[4],
                'notas': cliente[5]
            }
        return None

    def delete_proyecto(self, proyecto_id):
        """
        Elimina un proyecto y sus datos relacionados.
    
        Args:
            proyecto_id: ID del proyecto a eliminar
        """
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        # Eliminar notas relacionadas
        cursor.execute("DELETE FROM notas_proyecto WHERE proyecto_id=?", (proyecto_id,))
    
        # Eliminar eventos relacionados
        cursor.execute("DELETE FROM eventos_proyecto WHERE proyecto_id=?", (proyecto_id,))
    
        # Eliminar el proyecto
        cursor.execute("DELETE FROM proyectos WHERE id=?", (proyecto_id,))
    
        conn.commit()
        conn.close()

    def delete_nota_proyecto(self, nota_id):
        """
        Elimina una nota de proyecto.
    
        Args:
            nota_id: ID de la nota a eliminar
        """
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        # Obtener proyecto_id para actualizarlo después
        cursor.execute("SELECT proyecto_id FROM notas_proyecto WHERE id=?", (nota_id,))
        result = cursor.fetchone()
        if result:
            proyecto_id = result[0]
        
            # Eliminar la nota
            cursor.execute("DELETE FROM notas_proyecto WHERE id=?", (nota_id,))
        
            # Actualizar última fecha de actualización del proyecto
            from datetime import datetime
            cursor.execute(
                "UPDATE proyectos SET ultima_actualizacion=? WHERE id=?",
                (datetime.now().strftime("%Y-%m-%d"), proyecto_id)
            )
    
        conn.commit()
        conn.close()

    def delete_evento_proyecto(self, evento_id):
        """
        Elimina un evento crítico de proyecto.
    
        Args:
            evento_id: ID del evento a eliminar
        """
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        # Obtener proyecto_id para actualizarlo después
        cursor.execute("SELECT proyecto_id FROM eventos_proyecto WHERE id=?", (evento_id,))
        result = cursor.fetchone()
        if result:
            proyecto_id = result[0]
        
            # Eliminar el evento
            cursor.execute("DELETE FROM eventos_proyecto WHERE id=?", (evento_id,))
        
            # Actualizar última fecha de actualización del proyecto
            from datetime import datetime
            cursor.execute(
                "UPDATE proyectos SET ultima_actualizacion=? WHERE id=?",
                (datetime.now().strftime("%Y-%m-%d"), proyecto_id)
            )
    
        conn.commit()
        conn.close()

    def get_all_citas(self):
        """
        Obtiene todas las citas con información de los clientes.
    
        Returns:
            Lista de diccionarios con información de las citas
        """
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        cursor.execute("""
        SELECT c.id, c.tipo, c.fecha, c.hora, c.tema, c.estado, c.fecha_creacion,
               cl.id as cliente_id, cl.nombre as cliente_nombre, cl.email as cliente_email, cl.telefono as cliente_telefono
        FROM citas c
        JOIN clientes cl ON c.cliente_id = cl.id
        ORDER BY c.fecha DESC, c.hora
        """)
    
        citas_raw = cursor.fetchall()
        conn.close()
    
        citas = []
        for c in citas_raw:
            citas.append({
                'id': c[0],
                'tipo': c[1],
                'fecha': c[2],
                'hora': c[3],
                'tema': c[4],
                'estado': c[5],
                'fecha_creacion': c[6],
                'cliente_nombre': c[8],  # Este campo es importante para la tabla
                'cliente': {
                    'id': c[7],
                    'nombre': c[8],
                    'email': c[9],
                    'telefono': c[10]
                }
            })
    
        return citas

    def get_cita(self, cita_id):
        """
        Obtiene una cita por su ID.
    
        Args:
            cita_id: ID de la cita
        
        Returns:
            Diccionario con los datos de la cita o None si no se encuentra
        """
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        cursor.execute("""
        SELECT c.id, c.tipo, c.fecha, c.hora, c.tema, c.estado, c.fecha_creacion,
               cl.id as cliente_id, cl.nombre as cliente_nombre, cl.email as cliente_email, cl.telefono as cliente_telefono
        FROM citas c
        JOIN clientes cl ON c.cliente_id = cl.id
        WHERE c.id = ?
        """, (cita_id,))
    
        cita = cursor.fetchone()
    
        conn.close()
    
        if cita:
            return {
                'id': cita[0],
                'tipo': cita[1],
                'fecha': cita[2],
                'hora': cita[3],
                'tema': cita[4],
                'estado': cita[5],
                'fecha_creacion': cita[6],
                'cliente': {
                    'id': cita[7],
                    'nombre': cita[8],
                    'email': cita[9],
                    'telefono': cita[10]
                }
            }
        return None

    def update_cita(self, cita_id, **kwargs):
        """
        Actualiza una cita existente.
    
        Args:
            cita_id: ID de la cita
            **kwargs: Campos a actualizar (tipo, fecha, hora, tema, estado)
        """
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        # Actualizar solo los campos proporcionados
        set_clause = []
        values = []
    
        for key, value in kwargs.items():
            if value is not None:  # Solo actualizar si el valor no es None
                set_clause.append(f"{key}=?")
                values.append(value)
    
        if set_clause:
            # Añadir ID de la cita
            values.append(cita_id)
        
            query = f"UPDATE citas SET {', '.join(set_clause)} WHERE id=?"
            cursor.execute(query, values)
        
            conn.commit()
    
        conn.close()

    def delete_cita(self, cita_id):
        """
        Elimina una cita.
    
        Args:
            cita_id: ID de la cita a eliminar
        """
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        # Eliminar la cita
        cursor.execute("DELETE FROM citas WHERE id=?", (cita_id,))
    
        conn.commit()
        conn.close()
    
    def update_cliente(self, cliente_id, nombre, email, telefono, notas=""):
        """
        Actualiza la información de un cliente existente.
    
        Args:
            cliente_id: ID del cliente a actualizar
            nombre: Nombre completo del cliente
            email: Email del cliente
           telefono: Teléfono del cliente
            notas: Notas adicionales sobre el cliente
        """
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        try:
            cursor.execute(
                "UPDATE clientes SET nombre=?, email=?, telefono=?, notas=? WHERE id=?",
                (nombre, email, telefono, notas, cliente_id)
            )
        
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar cliente: {str(e)}")
            return False
        finally:
            conn.close()

    # Añadir a db_manager.py

    def get_consultas_sin_expediante(self):
        """
        Obtiene todas las citas completadas que aún no tienen expediente asociado.
        Útil para convertir consultas en expedientes.
    
        Returns:
            Lista de diccionarios con información de las consultas
        """
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        try:
            # Seleccionar citas completadas
            # Buscamos citas con estado 'completada' o 'confirmada' y fecha pasada
            fecha_actual = datetime.now().strftime("%Y-%m-%d")
        
            query = """
            SELECT c.id, c.tipo, c.fecha, c.hora, c.tema, c.estado, c.fecha_creacion,
                   cl.id as cliente_id, cl.nombre as cliente_nombre, cl.email as cliente_email, 
                   cl.telefono as cliente_telefono, 
                   CASE WHEN COUNT(p.id) > 0 THEN 1 ELSE 0 END as tiene_expediente
            FROM citas c
            JOIN clientes cl ON c.cliente_id = cl.id
            LEFT JOIN proyectos p ON (
                p.cliente_id = cl.id AND 
                p.titulo LIKE '%' || c.tema || '%' AND
                DATE(p.fecha_inicio) >= DATE(c.fecha)
            )
            WHERE (
                (c.estado = 'completada' OR c.estado = 'confirmada') AND
                (DATE(c.fecha) < ?)
            )
            GROUP BY c.id
            HAVING tiene_expediente = 0
            ORDER BY c.fecha DESC
            """
        
            cursor.execute(query, (fecha_actual,))
            citas_raw = cursor.fetchall()
        
            citas = []
            for c in citas_raw:
                citas.append({
                    'id': c[0],
                    'tipo': c[1],
                    'fecha': c[2],
                    'hora': c[3],
                    'tema': c[4],
                    'estado': c[5],
                    'fecha_creacion': c[6],
                    'cliente_id': c[7],
                    'cliente_nombre': c[8],
                    'cliente_email': c[9],
                    'cliente_telefono': c[10]
                })
        
            return citas
        except Exception as e:
            print(f"Error al obtener consultas sin expediente: {str(e)}")
            return []
        finally:
            conn.close()

    def crear_expediente_desde_consulta(self, cita_id, datos_adicionales=None):
        """
        Crea un nuevo expediente a partir de una consulta (cita) existente.
    
        Args:
            cita_id: ID de la cita
            datos_adicionales: Diccionario con datos adicionales para el expediente (opcional)
                - titulo: Título del expediente (por defecto será el tema de la cita)
                - descripcion: Descripción del expediente
                - abogado: Abogado asignado
                - estado: Estado inicial del expediente (por defecto 'nuevo')
    
        Returns:
            ID del nuevo expediente o None si hay error
        """
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
    
        try:
            # Obtener datos de la cita
            cursor.execute("""
            SELECT c.tema, c.fecha, cl.id
            FROM citas c
            JOIN clientes cl ON c.cliente_id = cl.id
            WHERE c.id = ?
            """, (cita_id,))
        
            cita_data = cursor.fetchone()
            if not cita_data:
                print(f"No se encontró la cita con ID {cita_id}")
                return None
        
            tema_cita, fecha_cita, cliente_id = cita_data
        
            # Crear el expediente
            titulo = datos_adicionales.get('titulo', tema_cita) if datos_adicionales else tema_cita
            descripcion = datos_adicionales.get('descripcion', f"Expediente creado a partir de consulta del {fecha_cita}") if datos_adicionales else f"Expediente creado a partir de consulta del {fecha_cita}"
            abogado = datos_adicionales.get('abogado', '') if datos_adicionales else ''
            estado = datos_adicionales.get('estado', 'nuevo') if datos_adicionales else 'nuevo'
        
            fecha_inicio = datetime.now().strftime("%Y-%m-%d")
            ultima_actualizacion = fecha_inicio
        
            cursor.execute(
                "INSERT INTO proyectos (cliente_id, titulo, descripcion, estado, abogado, fecha_inicio, ultima_actualizacion) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (cliente_id, titulo, descripcion, estado, abogado, fecha_inicio, ultima_actualizacion)
            )
        
            # Obtener el ID del expediente creado
            proyecto_id = cursor.lastrowid
        
            # Añadir una nota inicial al expediente con la información de la consulta
            cursor.execute("""
            SELECT c.tipo, c.fecha, c.hora, c.tema
            FROM citas c
            WHERE c.id = ?
            """, (cita_id,))
        
            cita_info = cursor.fetchone()
            if cita_info:
                tipo_cita, fecha_cita, hora_cita, tema_cita = cita_info
            
                nota_texto = f"Expediente creado a partir de una consulta {tipo_cita} realizada el {fecha_cita} a las {hora_cita}.\n"
                nota_texto += f"Tema de la consulta: {tema_cita}\n"
            
                if datos_adicionales and datos_adicionales.get('notas_iniciales'):
                    nota_texto += f"\nNotas iniciales:\n{datos_adicionales['notas_iniciales']}"
            
                cursor.execute(
                    "INSERT INTO notas_proyecto (proyecto_id, fecha, texto) VALUES (?, ?, ?)",
                    (proyecto_id, fecha_inicio, nota_texto)
                )
        
            # Actualizar el estado de la cita si se solicita
            if datos_adicionales and datos_adicionales.get('actualizar_estado_cita'):
                cursor.execute(
                    "UPDATE citas SET estado = 'procesada' WHERE id = ?",
                    (cita_id,)
                )
        
            conn.commit()
            return proyecto_id
    
        except Exception as e:
            print(f"Error al crear expediente desde consulta: {str(e)}")
            conn.rollback()
            return None
        finally:
            conn.close()
