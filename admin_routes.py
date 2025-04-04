# admin_routes.py - Rutas para el panel de administración

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from db_manager import DatabaseManager
import os
from functools import wraps
from datetime import datetime, timedelta
import json

# Inicializar blueprint para el panel de administración
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Inicializar el gestor de base de datos
db = DatabaseManager()

# Función para requerir autenticación
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Rutas de autenticación
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # En producción, usar un sistema de autenticación más seguro
        # Como ejemplo simple, usamos credenciales fijas
        admin_user = os.environ.get('ADMIN_USER', 'admin')
        admin_pass = os.environ.get('ADMIN_PASSWORD', 'password')
        
        if username == admin_user and password == admin_pass:
            session['admin_logged_in'] = True
            next_page = request.args.get('next', url_for('admin.dashboard'))
            return redirect(next_page)
        else:
            flash('Credenciales incorrectas', 'error')
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin.login'))

# Panel principal
@admin_bp.route('/')
@login_required
def dashboard():
    # Obtener estadísticas para el dashboard
    clientes = db.get_all_clientes()
    
    stats = {
        'total_clientes': len(clientes),
        'citas_proximas': 0,
        'eventos_proximos': 0,
        'proyectos_activos': 0
    }
    
    # Obtener eventos del calendario próximos (7 días)
    hoy = datetime.now().strftime("%Y-%m-%d")
    proxima_semana = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    eventos = db.get_all_calendar_events(hoy, proxima_semana)
    
    # Contar citas y eventos críticos
    for evento in eventos:
        if evento['type'] == 'appointment':
            stats['citas_proximas'] += 1
        elif evento['type'] == 'critical':
            stats['eventos_proximos'] += 1
    
    # Los últimos 5 clientes agregados
    ultimos_clientes = sorted(clientes, key=lambda x: x.get('fecha_registro', ''), reverse=True)[:5]
    
    # Próximos eventos del calendario
    proximos_eventos = sorted(eventos, key=lambda x: x['start'])[:10]
    
    return render_template('admin/dashboard.html', 
                          stats=stats, 
                          ultimos_clientes=ultimos_clientes,
                          proximos_eventos=proximos_eventos)

# Gestión de clientes
@admin_bp.route('/clientes')
@login_required
def clientes():
    clientes = db.get_all_clientes()
    return render_template('admin/clientes.html', clientes=clientes)

@admin_bp.route('/clientes/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_cliente():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        telefono = request.form.get('telefono')
        notas = request.form.get('notas', '')
        
        if not nombre or not email:
            flash('El nombre y email son obligatorios', 'error')
            return render_template('admin/cliente_form.html')
        
        db.add_cliente(nombre, email, telefono, notas)
        flash('Cliente agregado correctamente', 'success')
        return redirect(url_for('admin.clientes'))
    
    return render_template('admin/cliente_form.html')

@admin_bp.route('/clientes/editar/<int:cliente_id>', methods=['GET', 'POST'])
@login_required
def editar_cliente(cliente_id):
    # Obtener cliente de la base de datos
    # Implementar edición
    pass

@admin_bp.route('/clientes/<int:cliente_id>')
@login_required
def ver_cliente(cliente_id):
    # Obtener cliente y sus citas/proyectos
    # Implementar vista detallada del cliente
    pass

# Gestión de proyectos
@admin_bp.route('/proyectos')
@login_required
def proyectos():
    """Vista para mostrar todos los proyectos."""
    try:
        # Obtener todos los proyectos (simplificado)
        proyectos = []
        clientes = db.get_all_clientes()
        
        # Para cada cliente, obtener sus proyectos
        for cliente in clientes:
            proyectos_cliente = db.get_proyectos_by_cliente(cliente['id'])
            proyectos.extend(proyectos_cliente)
        
        # Ordenar por actualización más reciente
        proyectos = sorted(proyectos, key=lambda p: p.get('ultima_actualizacion', ''), reverse=True)
        
        return render_template('admin/proyectos.html', proyectos=proyectos)
    except Exception as e:
        flash(f'Error al cargar proyectos: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/proyectos/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_proyecto():
    # Formulario para crear nuevo proyecto
    # Seleccionar cliente existente
    pass

@admin_bp.route('/proyectos/<int:proyecto_id>')
@login_required
def ver_proyecto(proyecto_id):
    # Vista detallada del proyecto con notas y eventos
    pass

@admin_bp.route('/proyectos/editar/<int:proyecto_id>', methods=['GET', 'POST'])
@login_required
def editar_proyecto(proyecto_id):
    # Edición de proyecto
    pass

# Gestión de calendario
@admin_bp.route('/calendario')
@login_required
def calendario():
    return render_template('admin/calendario.html')

@admin_bp.route('/api/eventos', methods=['GET'])
@login_required
def api_eventos():
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    # Obtener eventos para el calendario
    eventos = db.get_all_calendar_events(start_date, end_date)
    
    # Formatear para FullCalendar
    calendar_events = []
    for evento in eventos:
        event = {
            'id': evento['id'],
            'title': evento['title'],
            'start': evento['start'],
            'description': evento['description'],
            'extendedProps': {
                'type': evento['type']
            }
        }
        
        # Diferentes colores según el tipo
        if evento['type'] == 'appointment':
            event['backgroundColor'] = '#3788d8'  # Azul para citas
        else:
            # Eventos críticos: verde si completados, rojo si pendientes
            if evento.get('completed'):
                event['backgroundColor'] = '#28a745'  # Verde
            else:
                event['backgroundColor'] = '#dc3545'  # Rojo
        
        calendar_events.append(event)
    
    return jsonify(calendar_events)

@admin_bp.route('/api/eventos/<event_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_evento(event_id):
    # Implementar operaciones CRUD para eventos individuales
    pass

# Gestión de citas
@admin_bp.route('/citas')
@login_required
def citas():
    """Vista para mostrar todas las citas."""
    try:
        # Obtener todas las citas
        todas_citas = []
        
        # Para cada cliente, obtener sus citas
        clientes = db.get_all_clientes()
        for cliente in clientes:
            citas_cliente = db.get_citas_by_cliente(cliente['id'])
            todas_citas.extend(citas_cliente)
        
        # Ordenar por fecha más reciente
        todas_citas = sorted(todas_citas, key=lambda c: (c.get('fecha', ''), c.get('hora', '')))
        
        return render_template('admin/citas.html', citas=todas_citas)
    except Exception as e:
        flash(f'Error al cargar citas: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))
@admin_bp.route('/citas/nueva', methods=['GET', 'POST'])
@login_required
def nueva_cita():
    # Formulario para nueva cita
    pass

# Integramos el blueprint en la aplicación principal
def register_admin_blueprint(app):
    app.register_blueprint(admin_bp)
    
    # Configurar ruta para archivos estáticos del admin
    @app.route('/admin/static/<path:filename>')
    def admin_static(filename):
        return send_from_directory('static/admin', filename)
    
# API para gestión de proyectos
@admin_bp.route('/api/proyectos', methods=['GET'])
@login_required
def api_proyectos():
    """API para obtener todos los proyectos"""
    try:
        # Obtenemos todos los clientes primero para tener sus datos
        clientes = db.get_all_clientes()
        clientes_dict = {cliente['id']: cliente for cliente in clientes}
        
        # Ahora obtenemos todos los proyectos
        all_proyectos = []
        for cliente in clientes:
            proyectos_cliente = db.get_proyectos_by_cliente(cliente['id'])
            for proyecto in proyectos_cliente:
                proyecto['cliente_nombre'] = cliente['nombre']
                proyecto['cliente_email'] = cliente['email']
                all_proyectos.append(proyecto)
        
        return jsonify({
            'success': True,
            'proyectos': all_proyectos
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/api/proyectos/<int:proyecto_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_proyecto(proyecto_id):
    """API para gestionar un proyecto específico"""
    try:
        if request.method == 'GET':
            proyecto = db.get_proyecto(proyecto_id)
            if not proyecto:
                return jsonify({
                    'success': False,
                    'error': 'Proyecto no encontrado'
                }), 404
            
            # Obtener datos del cliente
            cliente = db.get_cliente_by_id(proyecto['cliente_id'])
            if cliente:
                proyecto['cliente_nombre'] = cliente['nombre']
                proyecto['cliente_email'] = cliente['email']
            
            return jsonify({
                'success': True,
                'proyecto': proyecto
            })
        
        elif request.method == 'PUT':
            data = request.json
            
            # Validar campos requeridos
            required_fields = ['titulo', 'estado']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': f'Campo requerido: {field}'
                    }), 400
            
            # Actualizar proyecto
            db.update_proyecto(
                proyecto_id,
                titulo=data['titulo'],
                descripcion=data.get('descripcion', ''),
                estado=data['estado'],
                abogado=data.get('abogado', '')
            )
            
            return jsonify({
                'success': True,
                'message': 'Proyecto actualizado correctamente'
            })
        
        elif request.method == 'DELETE':
            # Verificar si el proyecto existe
            proyecto = db.get_proyecto(proyecto_id)
            if not proyecto:
                return jsonify({
                    'success': False,
                    'error': 'Proyecto no encontrado'
                }), 404
            
            # Eliminar el proyecto
            db.delete_proyecto(proyecto_id)
            
            return jsonify({
                'success': True,
                'message': 'Proyecto eliminado correctamente'
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# API para gestión de notas de proyectos
@admin_bp.route('/api/proyectos/<int:proyecto_id>/notas', methods=['POST'])
@login_required
def api_add_nota(proyecto_id):
    """API para añadir una nota a un proyecto"""
    try:
        data = request.json
        texto = data.get('texto', '')
        
        if not texto:
            return jsonify({
                'success': False,
                'error': 'El texto de la nota es requerido'
            }), 400
        
        # Añadir nota
        nota_id = db.add_nota_proyecto(proyecto_id, texto)
        
        return jsonify({
            'success': True,
            'nota_id': nota_id,
            'message': 'Nota añadida correctamente'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/api/notas/<int:nota_id>', methods=['DELETE'])
@login_required
def api_delete_nota(nota_id):
    """API para eliminar una nota"""
    try:
        # Eliminar la nota
        db.delete_nota_proyecto(nota_id)
        
        return jsonify({
            'success': True,
            'message': 'Nota eliminada correctamente'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# API para gestión de eventos críticos
@admin_bp.route('/api/proyectos/<int:proyecto_id>/eventos', methods=['POST'])
@login_required
def api_add_evento(proyecto_id):
    """API para añadir un evento crítico a un proyecto"""
    try:
        data = request.json
        
        # Validar campos requeridos
        if not data.get('titulo') or not data.get('fecha'):
            return jsonify({
                'success': False,
                'error': 'Título y fecha son requeridos'
            }), 400
        
        # Añadir evento
        evento_id = db.add_evento_proyecto(
            proyecto_id=proyecto_id,
            titulo=data['titulo'],
            fecha=data['fecha'],
            descripcion=data.get('descripcion', '')
        )
        
        return jsonify({
            'success': True,
            'evento_id': evento_id,
            'message': 'Evento añadido correctamente'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/api/eventos/<int:evento_id>', methods=['PUT', 'DELETE'])
@login_required
def api_evento_crud(evento_id):
    """API para actualizar o eliminar un evento crítico"""
    try:
        if request.method == 'PUT':
            data = request.json
            
            # Actualizar evento
            kwargs = {}
            if 'titulo' in data:
                kwargs['titulo'] = data['titulo']
            if 'fecha' in data:
                kwargs['fecha'] = data['fecha']
            if 'descripcion' in data:
                kwargs['descripcion'] = data['descripcion']
            
            # Manejar el estado completado separadamente
            completado = data.get('completado')
            
            db.update_evento_proyecto(evento_id, completado, **kwargs)
            
            return jsonify({
                'success': True,
                'message': 'Evento actualizado correctamente'
            })
        
        elif request.method == 'DELETE':
            # Eliminar el evento
            db.delete_evento_proyecto(evento_id)
            
            return jsonify({
                'success': True,
                'message': 'Evento eliminado correctamente'
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# API para gestión de citas
@admin_bp.route('/api/citas', methods=['GET'])
@login_required
def api_citas():
    """API para obtener todas las citas"""
    try:
        # Obtener todas las citas con sus respectivos clientes
        citas = db.get_all_citas()
        
        return jsonify({
            'success': True,
            'citas': citas
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/api/citas/<int:cita_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_cita(cita_id):
    """API para gestionar una cita específica"""
    try:
        if request.method == 'GET':
            cita = db.get_cita(cita_id)
            if not cita:
                return jsonify({
                    'success': False,
                    'error': 'Cita no encontrada'
                }), 404
            
            return jsonify({
                'success': True,
                'cita': cita
            })
        
        elif request.method == 'PUT':
            data = request.json
            
            # Actualizar cita
            db.update_cita(
                cita_id,
                tipo=data.get('tipo'),
                fecha=data.get('fecha'),
                hora=data.get('hora'),
                tema=data.get('tema'),
                estado=data.get('estado')
            )
            
            return jsonify({
                'success': True,
                'message': 'Cita actualizada correctamente'
            })
        
        elif request.method == 'DELETE':
            # Eliminar la cita
            db.delete_cita(cita_id)
            
            return jsonify({
                'success': True,
                'message': 'Cita eliminada correctamente'
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Métodos adicionales necesarios para el gestor de base de datos (db_manager.py)

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
