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
    # Obtener todos los proyectos con datos básicos del cliente
    # Implementar vista de proyectos
    pass

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
    # Listar todas las citas
    pass

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