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
            return redirect(url_for('admin.admin_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Rutas de autenticación
@admin_bp.route('/login', methods=['GET', 'POST'], endpoint='admin_login')
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
    session.pop('admin_id', None)
    session.pop('admin_role', None)
    return redirect(url_for('admin.admin_login'))

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
                'type': evento['type'],
                'client': evento['client'],
            }
        }
        
        # Añadir propiedades específicas según el tipo de evento
        if evento['type'] == 'appointment':
            event['extendedProps']['status'] = evento.get('status', 'pendiente')
            event['extendedProps']['tema'] = evento.get('description', '')
        else:
            event['extendedProps']['completed'] = evento.get('completed', False)
            if 'project' in evento:
                event['extendedProps']['project'] = evento['project']
        
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

# Implementación de las rutas faltantes en admin_routes.py

@admin_bp.route('/clientes/<int:cliente_id>')
@login_required
def ver_cliente(cliente_id):
    """Vista detallada de un cliente."""
    try:
        # Obtener cliente de la base de datos
        cliente = db.get_cliente_by_id(cliente_id)
        if not cliente:
            flash('Cliente no encontrado', 'danger')
            return redirect(url_for('admin.clientes'))
        
        # Obtener citas del cliente
        citas = db.get_citas_by_cliente(cliente_id)
        
        # Obtener proyectos del cliente
        proyectos = db.get_proyectos_by_cliente(cliente_id)
        
        return render_template('admin/cliente_detalle.html', 
                              cliente=cliente, 
                              citas=citas,
                              proyectos=proyectos)
    except Exception as e:
        flash(f'Error al cargar cliente: {str(e)}', 'danger')
        return redirect(url_for('admin.clientes'))

@admin_bp.route('/clientes/editar/<int:cliente_id>', methods=['GET', 'POST'])
@login_required
def editar_cliente(cliente_id):
    """Edición de un cliente existente."""
    try:
        # Obtener cliente de la base de datos
        cliente = db.get_cliente_by_id(cliente_id)
        if not cliente:
            flash('Cliente no encontrado', 'danger')
            return redirect(url_for('admin.clientes'))
        
        if request.method == 'POST':
            # Obtener datos del formulario
            nombre = request.form.get('nombre')
            email = request.form.get('email')
            telefono = request.form.get('telefono')
            notas = request.form.get('notas', '')
            
            if not nombre or not email:
                flash('El nombre y email son obligatorios', 'danger')
                return render_template('admin/cliente_editar.html', cliente=cliente)
            
            # Actualizar cliente en la base de datos
            db.update_cliente(cliente_id=cliente_id, 
                             nombre=nombre, 
                             email=email, 
                             telefono=telefono, 
                             notas=notas)
            
            flash('Cliente actualizado correctamente', 'success')
            return redirect(url_for('admin.ver_cliente', cliente_id=cliente_id))
        
        return render_template('admin/cliente_editar.html', cliente=cliente)
    except Exception as e:
        flash(f'Error al editar cliente: {str(e)}', 'danger')
        return redirect(url_for('admin.clientes'))

@admin_bp.route('/proyectos/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_proyecto():
    """Creación de un nuevo proyecto."""
    try:
        # Obtener todos los clientes para el selector
        clientes = db.get_all_clientes()
        
        if request.method == 'POST':
            # Obtener datos del formulario
            cliente_id = request.form.get('cliente_id')
            titulo = request.form.get('titulo')
            descripcion = request.form.get('descripcion', '')
            abogado = request.form.get('abogado', '')
            estado = request.form.get('estado', 'nuevo')
            
            if not cliente_id or not titulo:
                flash('El cliente y el título son obligatorios', 'danger')
                return render_template('admin/proyecto_form.html', clientes=clientes)
            
            # Crear proyecto en la base de datos
            proyecto_id = db.add_proyecto(
                cliente_id=int(cliente_id),
                titulo=titulo,
                descripcion=descripcion,
                abogado=abogado,
                estado=estado
            )
            
            flash('Proyecto creado correctamente', 'success')
            return redirect(url_for('admin.ver_proyecto', proyecto_id=proyecto_id))
        
        return render_template('admin/proyecto_form.html', clientes=clientes)
    except Exception as e:
        flash(f'Error al crear proyecto: {str(e)}', 'danger')
        return redirect(url_for('admin.proyectos'))

@admin_bp.route('/proyectos/<int:proyecto_id>')
@login_required
def ver_proyecto(proyecto_id):
    """Vista detallada de un proyecto."""
    try:
        # Obtener proyecto de la base de datos
        proyecto = db.get_proyecto(proyecto_id)
        if not proyecto:
            flash('Proyecto no encontrado', 'danger')
            return redirect(url_for('admin.proyectos'))
        
        # Obtener cliente asociado
        cliente = db.get_cliente_by_id(proyecto['cliente_id'])
        if cliente:
            proyecto['cliente_nombre'] = cliente['nombre']
            proyecto['cliente_email'] = cliente['email']
        
        # Obtener citas del cliente
        citas_cliente = db.get_citas_by_cliente(proyecto['cliente_id'])
        
        return render_template('admin/proyecto_detalle.html', 
                              proyecto=proyecto,
                              citas_cliente=citas_cliente)
    except Exception as e:
        flash(f'Error al cargar proyecto: {str(e)}', 'danger')
        return redirect(url_for('admin.proyectos'))

@admin_bp.route('/proyectos/editar/<int:proyecto_id>', methods=['GET', 'POST'])
@login_required
def editar_proyecto(proyecto_id):
    """Edición de un proyecto existente."""
    try:
        # Obtener proyecto de la base de datos
        proyecto = db.get_proyecto(proyecto_id)
        if not proyecto:
            flash('Proyecto no encontrado', 'danger')
            return redirect(url_for('admin.proyectos'))
        
        # Obtener cliente asociado
        cliente = db.get_cliente_by_id(proyecto['cliente_id'])
        if cliente:
            proyecto['cliente_nombre'] = cliente['nombre']
            proyecto['cliente_email'] = cliente['email']
        
        if request.method == 'POST':
            # Obtener datos del formulario
            titulo = request.form.get('titulo')
            descripcion = request.form.get('descripcion', '')
            abogado = request.form.get('abogado', '')
            estado = request.form.get('estado', 'nuevo')
            
            if not titulo:
                flash('El título es obligatorio', 'danger')
                return render_template('admin/proyecto_editar.html', proyecto=proyecto)
            
            # Actualizar proyecto en la base de datos
            db.update_proyecto(
                proyecto_id=proyecto_id,
                titulo=titulo,
                descripcion=descripcion,
                abogado=abogado,
                estado=estado
            )
            
            flash('Proyecto actualizado correctamente', 'success')
            return redirect(url_for('admin.ver_proyecto', proyecto_id=proyecto_id))
        
        return render_template('admin/proyecto_editar.html', proyecto=proyecto)
    except Exception as e:
        flash(f'Error al editar proyecto: {str(e)}', 'danger')
        return redirect(url_for('admin.proyectos'))

@admin_bp.route('/proyectos/<int:proyecto_id>/notas/nueva', methods=['POST'])
@login_required
def add_nota_proyecto(proyecto_id):
    """Añade una nueva nota a un proyecto."""
    try:
        texto = request.form.get('texto')
        if not texto:
            flash('El texto de la nota es obligatorio', 'danger')
            return redirect(url_for('admin.ver_proyecto', proyecto_id=proyecto_id))
        
        # Añadir nota al proyecto
        db.add_nota_proyecto(proyecto_id, texto)
        
        flash('Nota añadida correctamente', 'success')
        return redirect(url_for('admin.ver_proyecto', proyecto_id=proyecto_id))
    except Exception as e:
        flash(f'Error al añadir nota: {str(e)}', 'danger')
        return redirect(url_for('admin.ver_proyecto', proyecto_id=proyecto_id))

@admin_bp.route('/proyectos/<int:proyecto_id>/eventos/nuevo', methods=['POST'])
@login_required
def add_evento_proyecto(proyecto_id):
    """Añade un nuevo evento crítico a un proyecto."""
    try:
        titulo = request.form.get('titulo')
        fecha = request.form.get('fecha')
        descripcion = request.form.get('descripcion', '')
        
        if not titulo or not fecha:
            flash('El título y la fecha son obligatorios', 'danger')
            return redirect(url_for('admin.ver_proyecto', proyecto_id=proyecto_id))
        
        # Añadir evento al proyecto
        db.add_evento_proyecto(proyecto_id, titulo, fecha, descripcion)
        
        flash('Evento añadido correctamente', 'success')
        return redirect(url_for('admin.ver_proyecto', proyecto_id=proyecto_id))
    except Exception as e:
        flash(f'Error al añadir evento: {str(e)}', 'danger')
        return redirect(url_for('admin.ver_proyecto', proyecto_id=proyecto_id))

@admin_bp.route('/citas/nueva', methods=['GET', 'POST'])
@login_required
def nueva_cita():
    """Creación de una nueva cita."""
    try:
        # Obtener todos los clientes para el selector
        clientes = db.get_all_clientes()
        
        if request.method == 'POST':
            # Obtener datos del formulario
            cliente_id = request.form.get('cliente_id')
            tipo = request.form.get('tipo')
            fecha = request.form.get('fecha')
            hora = request.form.get('hora')
            tema = request.form.get('tema', '')
            
            if not cliente_id or not tipo or not fecha or not hora:
                flash('Cliente, tipo, fecha y hora son obligatorios', 'danger')
                return render_template('admin/cita_form.html', clientes=clientes)
            
            # Crear cita en la base de datos
            cita_id = db.add_cita(
                cliente_id=int(cliente_id),
                tipo=tipo,
                fecha=fecha,
                hora=hora,
                tema=tema
            )
            
            flash('Cita creada correctamente', 'success')
            return redirect(url_for('admin.ver_cita', cita_id=cita_id))
        
        return render_template('admin/cita_form.html', clientes=clientes)
    except Exception as e:
        flash(f'Error al crear cita: {str(e)}', 'danger')
        return redirect(url_for('admin.citas'))

@admin_bp.route('/citas/<int:cita_id>')
@login_required
def ver_cita(cita_id):
    """Vista detallada de una cita."""
    try:
        # Obtener cita de la base de datos
        cita = db.get_cita(cita_id)
        if not cita:
            flash('Cita no encontrada', 'danger')
            return redirect(url_for('admin.citas'))
        
        return render_template('admin/cita_detalle.html', cita=cita)
    except Exception as e:
        flash(f'Error al cargar cita: {str(e)}', 'danger')
        return redirect(url_for('admin.citas'))

@admin_bp.route('/citas/editar/<int:cita_id>', methods=['GET', 'POST'])
@login_required
def editar_cita(cita_id):
    """Edición de una cita existente."""
    try:
        # Obtener cita de la base de datos
        cita = db.get_cita(cita_id)
        if not cita:
            flash('Cita no encontrada', 'danger')
            return redirect(url_for('admin.citas'))
        
        if request.method == 'POST':
            # Obtener datos del formulario
            tipo = request.form.get('tipo')
            fecha = request.form.get('fecha')
            hora = request.form.get('hora')
            tema = request.form.get('tema', '')
            estado = request.form.get('estado', 'pendiente')
            
            if not tipo or not fecha or not hora:
                flash('Tipo, fecha y hora son obligatorios', 'danger')
                return render_template('admin/cita_editar.html', cita=cita)
            
            # Actualizar cita en la base de datos
            db.update_cita(
                cita_id=cita_id,
                tipo=tipo,
                fecha=fecha,
                hora=hora,
                tema=tema,
                estado=estado
            )
            
            flash('Cita actualizada correctamente', 'success')
            return redirect(url_for('admin.ver_cita', cita_id=cita_id))
        
        return render_template('admin/cita_editar.html', cita=cita)
    except Exception as e:
        flash(f'Error al editar cita: {str(e)}', 'danger')
        return redirect(url_for('admin.citas'))

@admin_bp.route('/citas/<int:cita_id>/cancelar', methods=['POST'])
@login_required
def cancelar_cita(cita_id):
    """Cancela una cita existente."""
    try:
        # Actualizar el estado de la cita a cancelada
        db.update_cita(cita_id, estado="cancelada")
        
        # Obtener información de la cita para el mensaje
        cita = db.get_cita(cita_id)
        
        flash(f'Cita del {cita["fecha"]} a las {cita["hora"]} cancelada correctamente', 'success')
        return redirect(url_for('admin.citas'))
    except Exception as e:
        flash(f'Error al cancelar cita: {str(e)}', 'danger')
        return redirect(url_for('admin.ver_cita', cita_id=cita_id))

@admin_bp.route('/citas/<int:cita_id>/recordatorio', methods=['POST'])
@login_required
def enviar_recordatorio(cita_id):
    """Envía un recordatorio de cita al cliente."""
    try:
        # Obtener información de la cita
        cita = db.get_cita(cita_id)
        if not cita:
            flash('Cita no encontrada', 'danger')
            return redirect(url_for('admin.citas'))
        
        # Obtener tipo de recordatorio y mensaje personalizado
        tipo_recordatorio = request.form.get('tipo_recordatorio', 'email')
        mensaje_personalizado = request.form.get('mensaje_recordatorio', '')
        
        # Aquí iría la lógica para enviar el recordatorio por email y/o SMS
        # Utilizamos las funciones de email y SMS existentes en la aplicación
        
        # Para esta demostración, simulamos el envío
        from handlers.email_service import enviar_correo_confirmacion
        
        if tipo_recordatorio in ['email', 'ambos']:
            # Intenta enviar por email
            try:
                enviar_correo_confirmacion(
                    datos_cliente=cita['cliente'],
                    fecha=cita['fecha'],
                    hora=cita['hora'],
                    tipo_reunion=cita['tipo'],
                    tema_reunion=cita['tema']
                )
                flash('Recordatorio enviado por email', 'success')
            except Exception as email_error:
                flash(f'Error al enviar email: {str(email_error)}', 'warning')
        
        if tipo_recordatorio in ['sms', 'ambos']:
            # Intenta enviar por SMS
            try:
                from handlers.email_service import enviar_sms_confirmacion
                
                enviar_sms_confirmacion(
                    telefono=cita['cliente']['telefono'],
                    fecha=cita['fecha'],
                    hora=cita['hora'],
                    tipo_reunion=cita['tipo'],
                    tema_reunion=cita['tema']
                )
                flash('Recordatorio enviado por SMS', 'success')
            except Exception as sms_error:
                flash(f'Error al enviar SMS: {str(sms_error)}', 'warning')
        
        return redirect(url_for('admin.ver_cita', cita_id=cita_id))
    except Exception as e:
        flash(f'Error al enviar recordatorio: {str(e)}', 'danger')
        return redirect(url_for('admin.ver_cita', cita_id=cita_id))

# Rutas para gestión de usuarios a añadir en admin_routes.py

@admin_bp.route('/usuarios')
@login_required
def usuarios():
    """Vista para mostrar todos los usuarios del sistema."""
    try:
        # Verificar que el usuario actual es admin
        if session.get('admin_role') != 'admin':
            flash('No tienes permisos para acceder a esta sección', 'danger')
            return redirect(url_for('admin.dashboard'))
        
        # Obtener todos los usuarios
        usuarios = db.get_all_usuarios()
        
        return render_template('admin/usuarios.html', usuarios=usuarios)
    except Exception as e:
        flash(f'Error al cargar usuarios: {str(e)}', 'danger')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/usuarios/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_usuario():
    """Creación de un nuevo usuario."""
    try:
        # Verificar que el usuario actual es admin
        if session.get('admin_role') != 'admin':
            flash('No tienes permisos para acceder a esta sección', 'danger')
            return redirect(url_for('admin.dashboard'))
        
        if request.method == 'POST':
            # Obtener datos del formulario
            username = request.form.get('username')
            password = request.form.get('password')
            nombre = request.form.get('nombre')
            email = request.form.get('email')
            role = request.form.get('role', 'user')
            
            if not username or not password or not nombre or not email:
                flash('Todos los campos son obligatorios', 'danger')
                return render_template('admin/usuario_form.html')
            
            # Crear usuario en la base de datos
            usuario_id = db.add_usuario(
                username=username,
                password=password,
                nombre=nombre,
                email=email,
                role=role
            )
            
            if usuario_id:
                flash('Usuario creado correctamente', 'success')
                return redirect(url_for('admin.usuarios'))
            else:
                flash('Error al crear el usuario. El nombre de usuario o email ya existe.', 'danger')
                return render_template('admin/usuario_form.html')
        
        return render_template('admin/usuario_form.html')
    except Exception as e:
        flash(f'Error al crear usuario: {str(e)}', 'danger')
        return redirect(url_for('admin.usuarios'))

@admin_bp.route('/usuarios/editar/<int:usuario_id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(usuario_id):
    """Edición de un usuario existente."""
    try:
        # Verificar que el usuario actual es admin
        if session.get('admin_role') != 'admin':
            flash('No tienes permisos para acceder a esta sección', 'danger')
            return redirect(url_for('admin.dashboard'))
        
        # Obtener usuario de la base de datos
        usuario = db.get_usuario_by_id(usuario_id)
        if not usuario:
            flash('Usuario no encontrado', 'danger')
            return redirect(url_for('admin.usuarios'))
        
        if request.method == 'POST':
            # Obtener datos del formulario
            username = request.form.get('username')
            password = request.form.get('password')
            nombre = request.form.get('nombre')
            email = request.form.get('email')
            role = request.form.get('role', 'user')
            activo = request.form.get('activo') == 'on'
            
            if not username or not nombre or not email:
                flash('Username, nombre y email son obligatorios', 'danger')
                return render_template('admin/usuario_editar.html', usuario=usuario)
            
            # Actualizar usuario en la base de datos
            kwargs = {
                'username': username,
                'nombre': nombre,
                'email': email,
                'role': role,
                'activo': 1 if activo else 0
            }
            
            # Solo actualizar contraseña si se proporciona una nueva
            if password:
                kwargs['password'] = password
            
            db.update_usuario(usuario_id, **kwargs)
            
            flash('Usuario actualizado correctamente', 'success')
            return redirect(url_for('admin.usuarios'))
        
        return render_template('admin/usuario_editar.html', usuario=usuario)
    except Exception as e:
        flash(f'Error al editar usuario: {str(e)}', 'danger')
        return redirect(url_for('admin.usuarios'))

@admin_bp.route('/usuarios/eliminar/<int:usuario_id>', methods=['POST'])
@login_required
def eliminar_usuario(usuario_id):
    """Elimina un usuario del sistema."""
    try:
        # Verificar que el usuario actual es admin
        if session.get('admin_role') != 'admin':
            flash('No tienes permisos para acceder a esta sección', 'danger')
            return redirect(url_for('admin.dashboard'))
        
        # No permitir eliminar el propio usuario
        if usuario_id == session.get('admin_id'):
            flash('No puedes eliminar tu propio usuario', 'danger')
            return redirect(url_for('admin.usuarios'))
        
        # Eliminar usuario
        result = db.delete_usuario(usuario_id)
        
        if result:
            flash('Usuario eliminado correctamente', 'success')
        else:
            flash('No se puede eliminar el último administrador del sistema', 'danger')
        
        return redirect(url_for('admin.usuarios'))
    except Exception as e:
        flash(f'Error al eliminar usuario: {str(e)}', 'danger')
        return redirect(url_for('admin.usuarios'))

# Modificar la ruta de login para usar el nuevo sistema de autenticación
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Autenticar usuario con la base de datos
        user = db.authenticate_user(username, password)
        
        if user:
            session['admin_logged_in'] = True
            session['admin_id'] = user['id']
            session['admin_role'] = user['role']
            
            next_page = request.args.get('next', url_for('admin.dashboard'))
            return redirect(next_page)
        else:
            flash('Credenciales incorrectas o usuario desactivado', 'danger')
    
    return render_template('admin/login.html')
