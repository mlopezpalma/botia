# admin_routes.py - Rutas para el panel de administración

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from db_manager import DatabaseManager
import os
import re  # Import necesario para las funciones de calendario
from functools import wraps
from datetime import datetime, timedelta
import json
import logging

# Configurar logging
logger = logging.getLogger(__name__)

# Inicializar blueprint para el panel de administración
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Inicializar el gestor de base de datos
db = DatabaseManager()

# Ubicar al inicio del archivo, antes de las rutas
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.admin_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(roles):
    """
    Decorador para requerir uno o varios roles específicos
    Args:
        roles: String o lista de strings con los roles permitidos
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('admin_logged_in'):
                return redirect(url_for('admin.admin_login', next=request.url))
            
            if isinstance(roles, str):
                allowed_roles = [roles]
            else:
                allowed_roles = roles
                
            # Admin siempre tiene acceso a todo
            if session.get('admin_role') == 'admin':
                return f(*args, **kwargs)
                
            if session.get('admin_role') not in allowed_roles:
                flash('No tienes permisos para acceder a esta sección', 'danger')
                return redirect(url_for('admin.dashboard'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Rutas de autenticación
@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Autenticar usuario con la base de datos
        user = db.authenticate_user(username, password)
        
        if user:
            session['admin_logged_in'] = True
            session['admin_id'] = user['id']
            session['admin_role'] = user['role']
            session['admin_name'] = user['nombre'] if 'nombre' in user else username
            
            flash(f'Bienvenido, {session["admin_name"]}', 'success')
            next_page = request.args.get('next', url_for('admin.dashboard'))
            return redirect(next_page)
        else:
            flash('Credenciales incorrectas o usuario desactivado', 'danger')
    
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
    
    # Obtener consultas sin expediente
    consultas_pendientes = db.get_consultas_sin_expediante()
    
    stats = {
        'total_clientes': len(clientes),
        'citas_proximas': 0,
        'eventos_proximos': 0,
        'proyectos_activos': 0,
        'consultas_pendientes': len(consultas_pendientes)
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
    
    # Últimas consultas sin expediente (top 5)
    ultimas_consultas = consultas_pendientes[:5]
    
    return render_template('admin/dashboard.html', 
                          stats=stats, 
                          ultimos_clientes=ultimos_clientes,
                          proximos_eventos=proximos_eventos,
                          ultimas_consultas=ultimas_consultas)

# Gestión de clientes
@admin_bp.route('/clientes')
@role_required(['admin', 'gestor', 'recepcion'])
def clientes():
    # Solo admin, gestor y recepción pueden ver clientes
    clientes = db.get_all_clientes()
    return render_template('admin/clientes.html', clientes=clientes)

@admin_bp.route('/clientes/nuevo', methods=['GET', 'POST'])
@role_required(['admin', 'gestor', 'recepcion'])
def nuevo_cliente():
    # Solo admin, gestor y recepción pueden añadir clientes
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

@admin_bp.route('/clientes/<int:cliente_id>')
@role_required(['admin', 'gestor', 'recepcion', 'abogado'])
def ver_cliente(cliente_id):
    # Todos los roles pueden ver detalles de un cliente
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

@admin_bp.route('/clientes/editar/<int:cliente_id>', methods=['GET', 'POST'])
@role_required(['admin', 'gestor', 'recepcion'])
def editar_cliente(cliente_id):
    # Solo admin, gestor y recepción pueden editar clientes
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


# Gestión de proyectos
@admin_bp.route('/proyectos')
@role_required(['admin', 'gestor', 'abogado'])
def proyectos():
    """Vista para mostrar todos los expedientes."""
    try:
        # Admin, gestor y abogado pueden ver expedientes
        # Obtener todos los expedientes con información del cliente
        proyectos = []
        clientes = db.get_all_clientes()
        
        # Crear un diccionario para acceso rápido a clientes por ID
        clientes_dict = {cliente['id']: cliente for cliente in clientes}
        
        # Para cada cliente, obtener sus expedientes
        for cliente in clientes:
            proyectos_cliente = db.get_proyectos_by_cliente(cliente['id'])
            
            # Añadir el nombre del cliente a cada expediente
            for proyecto in proyectos_cliente:
                proyecto['cliente_nombre'] = cliente['nombre']
                proyecto['cliente_email'] = cliente['email']
            
            proyectos.extend(proyectos_cliente)
        
        # Ordenar por actualización más reciente
        proyectos = sorted(proyectos, key=lambda p: p.get('ultima_actualizacion', ''), reverse=True)
        
        return render_template('admin/proyectos.html', proyectos=proyectos)
    except Exception as e:
        flash(f'Error al cargar expedientes: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/proyectos/nuevo', methods=['GET', 'POST'])
@role_required(['admin', 'gestor', 'abogado'])
def nuevo_proyecto():
    """Creación de un nuevo proyecto."""
    try:
        # Admin, gestor y abogado pueden crear expedientes
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
            
            flash('Expediente creado correctamente', 'success')
            return redirect(url_for('admin.ver_proyecto', proyecto_id=proyecto_id))
        
        return render_template('admin/proyecto_form.html', clientes=clientes)
    except Exception as e:
        flash(f'Error al crear expediente: {str(e)}', 'danger')
        return redirect(url_for('admin.proyectos'))

@admin_bp.route('/proyectos/<int:proyecto_id>')
@role_required(['admin', 'gestor', 'abogado'])
def ver_proyecto(proyecto_id):
    """Vista detallada de un proyecto."""
    try:
        # Admin, gestor y abogado pueden ver expedientes
        # Obtener proyecto de la base de datos
        proyecto = db.get_proyecto(proyecto_id)
        if not proyecto:
            flash('Expediente no encontrado', 'danger')
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
        flash(f'Error al cargar expediente: {str(e)}', 'danger')
        return redirect(url_for('admin.proyectos'))

@admin_bp.route('/proyectos/editar/<int:proyecto_id>', methods=['GET', 'POST'])
@role_required(['admin', 'gestor', 'abogado'])
def editar_proyecto(proyecto_id):
    """Edición de un proyecto existente."""
    try:
        # Admin, gestor y abogado pueden editar expedientes
        # Obtener proyecto de la base de datos
        proyecto = db.get_proyecto(proyecto_id)
        if not proyecto:
            flash('Expediente no encontrado', 'danger')
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
            
            flash('Expediente actualizado correctamente', 'success')
            return redirect(url_for('admin.ver_proyecto', proyecto_id=proyecto_id))
        
        return render_template('admin/proyecto_editar.html', proyecto=proyecto)
    except Exception as e:
        flash(f'Error al editar expediente: {str(e)}', 'danger')
        return redirect(url_for('admin.proyectos'))

@admin_bp.route('/proyectos/<int:proyecto_id>/notas/nueva', methods=['POST'])
@role_required(['admin', 'gestor', 'abogado'])
def add_nota_proyecto(proyecto_id):
    """Añade una nueva nota a un proyecto."""
    try:
        # Admin, gestor y abogado pueden agregar notas
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
@role_required(['admin', 'gestor', 'abogado'])
def add_evento_proyecto(proyecto_id):
    """Añade un nuevo evento crítico a un proyecto."""
    try:
        # Admin, gestor y abogado pueden agregar eventos críticos
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


# Gestión de calendario
@admin_bp.route('/calendario')
@role_required(['admin', 'gestor', 'recepcion', 'abogado'])
def calendario():
    """Vista del calendario con estado de conexión a Google Calendar."""
    try:
        # Verificar si Google Calendar está conectado
        google_calendar_connected = os.path.exists('credentials.json') and os.path.exists('token.pickle')
        
        return render_template('admin/calendario.html', 
                             google_calendar_connected=google_calendar_connected)
    except Exception as e:
        flash(f'Error al cargar calendario: {str(e)}', 'danger')
        return redirect(url_for('admin.dashboard'))
# Actualizar el método api_eventos en admin_routes.py

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
            # Asegurarse de incluir la información del proyecto
            if 'project' in evento:
                event['extendedProps']['project'] = evento['project']
            else:
                # Si no viene en el evento, intentar obtenerlo
                try:
                    evento_id = evento['id'].replace('evento_', '')
                    conn = sqlite3.connect(db.db_file)
                    cursor = conn.cursor()
                    cursor.execute("""
                    SELECT proyecto_id, p.titulo 
                    FROM eventos_proyecto e
                    JOIN proyectos p ON e.proyecto_id = p.id
                    WHERE e.id = ?
                    """, (evento_id,))
                    result = cursor.fetchone()
                    conn.close()
                    if result:
                        event['extendedProps']['project'] = {
                            'id': result[0],
                            'title': result[1]
                        }
                except Exception as e:
                    logger.error(f"Error al obtener proyecto para evento {evento['id']}: {e}")
        
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

@admin_bp.route('/calendario/sincronizar', methods=['POST'])
@role_required(['admin', 'gestor'])
def sincronizar_calendario():
    """Sincroniza manualmente el calendario con Google."""
    try:
        # Solo admin y gestor pueden sincronizar el calendario
        from handlers.calendar_service import sincronizar_calendario_bd
        
        exito, mensaje = sincronizar_calendario_bd()
        
        if exito:
            flash(mensaje, 'success')
        else:
            flash(mensaje, 'danger')
        
        return redirect(url_for('admin.calendario'))
    except Exception as e:
        flash(f'Error al sincronizar calendario: {str(e)}', 'danger')
        return redirect(url_for('admin.calendario'))

# Gestión de citas
@admin_bp.route('/citas')
@role_required(['admin', 'gestor', 'recepcion', 'abogado'])
def citas():
    """Vista para mostrar todas las citas."""
    try:
        # Todos los roles pueden ver citas
        # Obtener todas las citas con información completa de clientes
        todas_citas = db.get_all_citas()
        
        # Si la función get_all_citas no incluye el nombre del cliente, lo añadimos aquí
        for cita in todas_citas:
            if 'cliente_nombre' not in cita and 'cliente' in cita and 'nombre' in cita['cliente']:
                cita['cliente_nombre'] = cita['cliente']['nombre']
        
        # Ordenar por fecha y hora
        todas_citas = sorted(todas_citas, key=lambda c: (c.get('fecha', ''), c.get('hora', '')))
        
        return render_template('admin/citas.html', citas=todas_citas)
    except Exception as e:
        flash(f'Error al cargar citas: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/citas/nueva', methods=['GET', 'POST'])
@role_required(['admin', 'gestor', 'recepcion'])
def nueva_cita():
    """Creación de una nueva cita."""
    try:
        # Admin, gestor y recepción pueden crear citas
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
@role_required(['admin', 'gestor', 'recepcion', 'abogado'])
def ver_cita(cita_id):
    """Vista detallada de una cita."""
    try:
        # Todos los roles pueden ver detalles de citas
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
@role_required(['admin', 'gestor', 'recepcion'])
def editar_cita(cita_id):
    """Edición de una cita existente."""
    try:
        # Admin, gestor y recepción pueden editar citas
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
@role_required(['admin', 'gestor', 'recepcion'])
def cancelar_cita(cita_id):
    """Cancela una cita existente."""
    try:
        # Admin, gestor y recepción pueden cancelar citas
        # Obtener motivo de cancelación si existe
        motivo = request.form.get('motivo', None)
        
        # Obtener información de la cita antes de actualizarla
        cita = db.get_cita(cita_id)
        if not cita:
            flash('Cita no encontrada', 'danger')
            return redirect(url_for('admin.citas'))
        
        # Guardar datos para notificaciones
        datos_cliente = cita['cliente']
        fecha = cita['fecha']
        hora = cita['hora']
        tipo = cita['tipo']
        
        # Actualizar el estado de la cita a cancelada
        db.update_cita(cita_id, estado="cancelada")
        
        # Enviar notificaciones
        from handlers.email_service import enviar_correo_cancelacion, enviar_sms_cancelacion
        
        # Enviar email
        try:
            enviar_correo_cancelacion(datos_cliente, fecha, hora, tipo, motivo)
        except Exception as e:
            print(f"Error al enviar correo de cancelación: {str(e)}")
        
        # Enviar SMS si hay teléfono
        if datos_cliente.get('telefono'):
            try:
                enviar_sms_cancelacion(datos_cliente['telefono'], fecha, hora, tipo, motivo)
            except Exception as e:
                print(f"Error al enviar SMS de cancelación: {str(e)}")
        
        flash(f'Cita del {fecha} a las {hora} cancelada correctamente', 'success')
        
        # Redireccionar según origen
        if request.args.get('from') == 'calendar':
            return redirect(url_for('admin.calendario'))
        else:
            return redirect(url_for('admin.citas'))
    except Exception as e:
        flash(f'Error al cancelar cita: {str(e)}', 'danger')
        return redirect(url_for('admin.ver_cita', cita_id=cita_id))

@admin_bp.route('/citas/<int:cita_id>/recordatorio', methods=['POST'])
@role_required(['admin', 'gestor', 'recepcion'])
def enviar_recordatorio(cita_id):
    """Envía un recordatorio de cita al cliente."""
    try:
        # Admin, gestor y recepción pueden enviar recordatorios
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



# consultas  
#     
@admin_bp.route('/consultas')
@role_required(['admin', 'gestor', 'abogado'])
def consultas():
    """Vista para mostrar todas las consultas sin expediente asociado."""
    try:
        # Admin, gestor y abogado pueden ver consultas pendientes
        # Obtener todas las consultas sin expediente
        consultas = db.get_consultas_sin_expediante()
        
        return render_template('admin/consultas.html', consultas=consultas)
    except Exception as e:
        flash(f'Error al cargar consultas: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/consultas/<int:cita_id>/crear-expediente', methods=['GET', 'POST'])
@role_required(['admin', 'gestor', 'abogado'])
def crear_expediente_desde_consulta(cita_id):
    """Crea un nuevo expediente a partir de una consulta."""
    try:
        # Admin, gestor y abogado pueden crear expedientes desde consultas
        # Obtener detalles de la cita
        cita = db.get_cita(cita_id)
        if not cita:
            flash('Consulta no encontrada', 'danger')
            return redirect(url_for('admin.consultas'))
        
        if request.method == 'POST':
            # Procesar formulario
            datos_expediente = {
                'titulo': request.form.get('titulo'),
                'descripcion': request.form.get('descripcion'),
                'abogado': request.form.get('abogado'),
                'estado': request.form.get('estado', 'nuevo'),
                'notas_iniciales': request.form.get('notas_iniciales', ''),
                'actualizar_estado_cita': request.form.get('actualizar_estado_cita') == 'on'
            }
            
            # Crear expediente
            expediente_id = db.crear_expediente_desde_consulta(cita_id, datos_expediente)
            
            if expediente_id:
                flash('Expediente creado correctamente', 'success')
                return redirect(url_for('admin.ver_proyecto', proyecto_id=expediente_id))
            else:
                flash('Error al crear el expediente', 'danger')
                return render_template('admin/crear_expediente_form.html', cita=cita)
        
        return render_template('admin/crear_expediente_form.html', cita=cita)
    except Exception as e:
        flash(f'Error al procesar la consulta: {str(e)}', 'danger')
        return redirect(url_for('admin.consultas'))
    

# Rutas para gestión de usuarios a añadir en admin_routes.py

@admin_bp.route('/usuarios')
@role_required('admin')
def usuarios():
    """Vista para mostrar todos los usuarios del sistema."""
    try:
        # Solo admin puede gestionar usuarios
        # Obtener todos los usuarios
        usuarios = db.get_all_usuarios()
        
        return render_template('admin/usuarios.html', usuarios=usuarios)
    except Exception as e:
        flash(f'Error al cargar usuarios: {str(e)}', 'danger')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/usuarios/nuevo', methods=['GET', 'POST'])
@role_required('admin')
def nuevo_usuario():
    """Creación de un nuevo usuario."""
    try:
        # Solo admin puede crear usuarios
        if request.method == 'POST':
            # Obtener datos del formulario
            username = request.form.get('username')
            password = request.form.get('password')
            nombre = request.form.get('nombre')
            email = request.form.get('email')
            role = request.form.get('role', 'user')
            
            if not username or not password or not nombre or not email:
                flash('Todos los campos son obligatorios', 'danger')
                return render_template('admin/usuarios_form.html')
            
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
                return render_template('admin/usuarios_form.html')
        
        return render_template('admin/usuarios_form.html')
    except Exception as e:
        flash(f'Error al crear usuario: {str(e)}', 'danger')
        return redirect(url_for('admin.usuarios'))

@admin_bp.route('/usuarios/editar/<int:usuario_id>', methods=['GET', 'POST'])
@role_required('admin')
def editar_usuario(usuario_id):
    """Edición de un usuario existente."""
    try:
        # Solo admin puede editar usuarios
        # Obtener usuario de la base de datos
        usuario = db.get_usuario_by_id(usuario_id)
        if not usuario:
            flash('Usuario no encontrado', 'danger')
            return redirect(url_for('admin.usuarios'))
        
        if request.method == 'POST':
            # Obtener datos del formulario
            nombre = request.form.get('nombre')
            email = request.form.get('email')
            role = request.form.get('role', 'user')
            activo = request.form.get('activo') == 'on'
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            if not nombre or not email:
                flash('Nombre y email son obligatorios', 'danger')
                return render_template('admin/usuarios_form.html', usuario=usuario)
            
            # Verificar que las contraseñas coincidan si se proporciona una nueva
            if password and password != confirm_password:
                flash('Las contraseñas no coinciden', 'danger')
                return render_template('admin/usuarios_form.html', usuario=usuario)
            
            # Preparar datos para actualización
            kwargs = {
                'nombre': nombre,
                'email': email,
                'role': role,
                'activo': 1 if activo else 0
            }
            
            # Solo actualizar contraseña si se proporciona una nueva
            if password:
                kwargs['password'] = password
            
            # Actualizar usuario en la base de datos
            db.update_usuario(usuario_id, **kwargs)
            
            flash('Usuario actualizado correctamente', 'success')
            return redirect(url_for('admin.usuarios'))
        
        return render_template('admin/usuarios_form.html', usuario=usuario)
    except Exception as e:
        flash(f'Error al editar usuario: {str(e)}', 'danger')
        return redirect(url_for('admin.usuarios'))

@admin_bp.route('/usuarios/eliminar/<int:usuario_id>', methods=['POST'])
@role_required('admin')
def eliminar_usuario(usuario_id):
    """Elimina un usuario del sistema."""
    try:
        # Solo admin puede eliminar usuarios
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


# Api sincronizacion

@admin_bp.route('/api/sync_database', methods=['POST'])
@role_required('admin')
def sync_database():
    """
    Sincroniza los datos entre las estructuras en memoria y la base de datos SQLite.
    Esta ruta se puede llamar periódicamente o después de cambios importantes.
    """
    try:
        # Solo admin puede sincronizar la base de datos
        from config import clientes_db, citas_db, casos_db
        db.import_from_memory(clientes_db, citas_db, casos_db)
        return jsonify({"success": True, "message": "Base de datos sincronizada correctamente"})
    except Exception as e:
        logger.error(f"Error al sincronizar base de datos: {str(e)}")
        return jsonify({"success": False, "message": f"Error al sincronizar: {str(e)}"})

@admin_bp.route('/api/proyectos', methods=['GET'])
@login_required
def api_proyectos():
    """API para obtener todos los proyectos"""
    try:
        # Cualquier usuario autenticado puede acceder a la API
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
@role_required(['admin', 'gestor', 'abogado'])
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
            # Solo admin, gestor y abogado pueden actualizar proyectos
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
            # Solo admin puede eliminar proyectos
            if session.get('admin_role') != 'admin':
                return jsonify({
                    'success': False,
                    'error': 'No tienes permisos para eliminar proyectos'
                }), 403
                
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
@role_required(['admin', 'gestor', 'recepcion'])
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
            # Solo admin, gestor y recepción pueden actualizar citas
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
            # Solo admin puede eliminar citas
            if session.get('admin_role') != 'admin':
                return jsonify({
                    'success': False,
                    'error': 'No tienes permisos para eliminar citas'
                }), 403
                
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


#perfil de usuario 

@admin_bp.route('/perfil')
@login_required
def admin_perfil():
    """Muestra el perfil del usuario actual"""
    user_id = session.get('admin_id')
    if not user_id:
        return redirect(url_for('admin.admin_login'))
    
    try:
        # Obtener datos del usuario
        usuario = db.get_usuario_by_id(user_id)
        if not usuario:
            flash('Información de usuario no encontrada', 'danger')
            return redirect(url_for('admin.dashboard'))
        
        return render_template('admin/perfil.html', usuario=usuario)
    except Exception as e:
        flash(f'Error al cargar perfil: {str(e)}', 'danger')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/perfil/cambiar-password', methods=['POST'])
@login_required
def cambiar_password():
    """Permite al usuario cambiar su propia contraseña"""
    user_id = session.get('admin_id')
    if not user_id:
        return redirect(url_for('admin.admin_login'))
    
    try:
        # Obtener datos del formulario
        password_actual = request.form.get('password_actual')
        password_nueva = request.form.get('password_nueva')
        password_confirmar = request.form.get('password_confirmar')
        
        # Verificar que todos los campos estén completos
        if not password_actual or not password_nueva or not password_confirmar:
            flash('Todos los campos son obligatorios', 'danger')
            return redirect(url_for('admin.admin_perfil'))
        
        # Verificar que las contraseñas nuevas coincidan
        if password_nueva != password_confirmar:
            flash('Las contraseñas nuevas no coinciden', 'danger')
            return redirect(url_for('admin.admin_perfil'))
        
        # Verificar la contraseña actual
        import bcrypt
        usuario = db.get_usuario_by_id(user_id)
        
        if not bcrypt.checkpw(password_actual.encode('utf-8'), usuario['password'].encode('utf-8')):
            flash('La contraseña actual es incorrecta', 'danger')
            return redirect(url_for('admin.admin_perfil'))
        
        # Actualizar contraseña
        db.update_usuario(user_id, password=password_nueva)
        
        flash('Contraseña actualizada correctamente', 'success')
        return redirect(url_for('admin.admin_perfil'))
    except Exception as e:
        flash(f'Error al cambiar contraseña: {str(e)}', 'danger')
        return redirect(url_for('admin.admin_perfil'))
    
#editar eventos
@admin_bp.route('/eventos/editar/<int:evento_id>', methods=['GET', 'POST'])
@role_required(['admin', 'gestor', 'abogado'])
def editar_evento(evento_id):
    """Edición de un evento crítico."""
    try:
        # Obtener evento de la base de datos
        conn = sqlite3.connect(db.db_file)
        cursor = conn.cursor()
        
        # Obtener información del evento con datos del proyecto y cliente
        cursor.execute("""
        SELECT e.id, e.titulo, e.descripcion, e.fecha, e.completado,
               p.id as proyecto_id, p.titulo as proyecto_titulo,
               cl.id as cliente_id, cl.nombre as cliente_nombre
        FROM eventos_proyecto e
        JOIN proyectos p ON e.proyecto_id = p.id
        JOIN clientes cl ON p.cliente_id = cl.id
        WHERE e.id = ?
        """, (evento_id,))
        
        evento_data = cursor.fetchone()
        conn.close()
        
        if not evento_data:
            flash('Evento no encontrado', 'danger')
            return redirect(url_for('admin.calendario'))
        
        # Estructurar datos del evento
        evento = {
            'id': evento_data[0],
            'titulo': evento_data[1],
            'descripcion': evento_data[2],
            'fecha': evento_data[3],
            'completado': bool(evento_data[4]),
            'proyecto': {
                'id': evento_data[5],
                'titulo': evento_data[6]
            },
            'cliente': {
                'id': evento_data[7],
                'nombre': evento_data[8]
            }
        }
        
        if request.method == 'POST':
            # Obtener datos del formulario
            titulo = request.form.get('titulo')
            fecha = request.form.get('fecha')
            descripcion = request.form.get('descripcion', '')
            completado = request.form.get('completado') == 'on'
            
            if not titulo or not fecha:
                flash('El título y la fecha son obligatorios', 'danger')
                return render_template('admin/evento_editar.html', evento=evento)
            
            # Actualizar evento en la base de datos
            db.update_evento_proyecto(
                evento_id=evento_id,
                completado=completado,
                titulo=titulo,
                fecha=fecha,
                descripcion=descripcion
            )
            
            flash('Evento actualizado correctamente', 'success')
            
            # Redireccionar según origen
            next_url = request.args.get('next', url_for('admin.ver_proyecto', proyecto_id=evento['proyecto']['id']))
            return redirect(next_url)
        
        return render_template('admin/evento_editar.html', evento=evento)
    except Exception as e:
        flash(f'Error al editar evento: {str(e)}', 'danger')
        return redirect(url_for('admin.calendario'))
    

# sincronizacion google  calendar

@admin_bp.route('/configuracion')
@role_required('admin')
def configuracion():
    """Vista para configurar integración con Google Calendar."""
    try:
        # Verificar si existe credentials.json y token.pickle
        google_calendar_connected = os.path.exists('credentials.json') and os.path.exists('token.pickle')
        
        # Obtener configuración de sincronización automática
        # Aquí deberías obtener los valores de una base de datos o archivo de configuración
        sync_auto_enabled = False  # Valor por defecto
        sync_interval = 15  # Valor por defecto en minutos
        
        return render_template('admin/configuracion.html', 
                             google_calendar_connected=google_calendar_connected,
                             sync_auto_enabled=sync_auto_enabled,
                             sync_interval=sync_interval)
    except Exception as e:
        flash(f'Error al cargar configuración: {str(e)}', 'danger')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/configuracion/upload_credentials', methods=['POST'])
@role_required('admin')
def upload_google_credentials():
    """Subir credenciales de Google para configurar Calendar."""
    try:
        if 'credentials_file' not in request.files:
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(url_for('admin.configuracion'))
        
        file = request.files['credentials_file']
        
        if file.filename == '':
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(url_for('admin.configuracion'))
        
        if file and file.filename.endswith('.json'):
            # Guardar el archivo de credenciales
            file.save('credentials.json')
            
            # Eliminar token.pickle existente para forzar nueva autenticación
            if os.path.exists('token.pickle'):
                os.remove('token.pickle')
            
            flash('Credenciales de Google subidas correctamente. Ahora intenta sincronizar para autenticar.', 'success')
            return redirect(url_for('admin.configuracion'))
        else:
            flash('Por favor, sube un archivo JSON válido', 'danger')
            return redirect(url_for('admin.configuracion'))
        
    except Exception as e:
        flash(f'Error al subir credenciales: {str(e)}', 'danger')
        return redirect(url_for('admin.configuracion'))

@admin_bp.route('/configuracion/desconectar_google', methods=['POST'])
@role_required('admin')
def desconectar_google_calendar():
    """Desconectar la integración con Google Calendar."""
    try:
        # Eliminar token.pickle
        if os.path.exists('token.pickle'):
            os.remove('token.pickle')
            flash('Google Calendar desconectado correctamente', 'success')
        else:
            flash('No hay conexión activa con Google Calendar', 'warning')
        
        return redirect(url_for('admin.configuracion'))
    except Exception as e:
        flash(f'Error al desconectar Google Calendar: {str(e)}', 'danger')
        return redirect(url_for('admin.configuracion'))

@admin_bp.route('/configuracion/sync_auto', methods=['POST'])
@role_required('admin')
def configurar_sync_auto():
    """Configurar sincronización automática."""
    try:
        sync_auto = request.form.get('sync_auto') == 'on'
        sync_interval = int(request.form.get('sync_interval', 15))
        
        # Aquí deberías guardar esta configuración en la base de datos o archivo de configuración
        # Por simplicidad, solo mostraremos un mensaje
        
        if sync_auto:
            flash(f'Sincronización automática activada cada {sync_interval} minutos', 'success')
        else:
            flash('Sincronización automática desactivada', 'success')
        
        return redirect(url_for('admin.configuracion'))
    except Exception as e:
        flash(f'Error al configurar sincronización automática: {str(e)}', 'danger')
        return redirect(url_for('admin.configuracion'))

@admin_bp.route('/calendario/sincronizar', methods=['POST'])
@role_required(['admin', 'gestor'])
def sincronizar_calendario():
    """Sincroniza manualmente el calendario con Google."""
    try:
        from handlers.calendar_service import sincronizar_calendario_bd
        
        # Verificar si tenemos credenciales
        if not os.path.exists('credentials.json'):
            flash('No se han configurado las credenciales de Google Calendar. Por favor, configúralas primero.', 'warning')
            return redirect(url_for('admin.configuracion'))
        
        # Si no existe token.pickle, esto iniciará el flujo de autenticación de Google
        exito, mensaje = sincronizar_calendario_bd()
        
        if exito:
            flash(mensaje, 'success')
        else:
            flash(mensaje, 'danger')
        
        return redirect(url_for('admin.calendario'))
    except Exception as e:
        flash(f'Error al sincronizar calendario: {str(e)}', 'danger')
        return redirect(url_for('admin.calendario'))
    
