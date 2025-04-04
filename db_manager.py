# Crear un nuevo archivo: db_manager.py

import sqlite3
import os
import json
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_file='botia.db'):
        """Inicializa el gestor de base de datos."""
        self.db_file = db_file
        self.initialize_db()
    
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