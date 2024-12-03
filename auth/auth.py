import os
import functools
from flask import (Blueprint, render_template, request, redirect, session, g ,jsonify, url_for)
from connection.database import execute_query
from werkzeug.security import check_password_hash, generate_password_hash


auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('login', methods = ('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        error = None

        # Consultar usuario en la base de datos
        query = "SELECT id, username, password_hash FROM users WHERE username = %s"
        user = execute_query(query, (username,))

        if not user:
            error = 'Usuario no encontrado'
        elif not check_password_hash(user[0]['password_hash'], password):
            error = 'Contraseña incorrecta'

        # Si no hay errores, inicia sesión
        if error is None:
            session.clear()
            session['user_id'] = user[0]['id']
            return jsonify({'message': 'Datos correctos'}), 200

        return jsonify({'message': error}), 404

    return render_template('login.html')


@auth_bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    print('user_id', user_id)
    if user_id is None:
        g.user = None
    else:
        query = "SELECT id, username FROM users WHERE id = %s"
        user = execute_query(query, (user_id,))
        g.user = user[0]['username'] if user else None


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home.principal'))


def login_require(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role_name = data.get('role', 'user')  # Por defecto, asigna el rol 'user'
    error = None

    # Validaciones
    if not username or not email or not password:
        error = 'Faltan campos obligatorios'
    elif execute_query("SELECT id FROM users WHERE username = %s OR email = %s", (username, email)):
        error = 'El usuario o correo ya existe'

    if error is not None:
        return jsonify({'message': error}), 400

    # Hashear la contraseña
    password_hash = generate_password_hash(password)

    # Insertar usuario en la base de datos
    user_query = """
        INSERT INTO users (username, email, password_hash)
        VALUES (%s, %s, %s) RETURNING id
    """
    user_result = execute_query(user_query, (username, email, password_hash))
    user_id = user_result[0]['id']

    # Obtener el ID del rol
    # roles: admin | user | visitor
    role_query = "SELECT id FROM roles WHERE name = %s"
    role_result = execute_query(role_query, (role_name,))
    if not role_result:
        return jsonify({'message': f'El rol {role_name} no existe'}), 400

    role_id = role_result[0]['id']

    # Asignar rol al usuario
    user_role_query = """
        INSERT INTO user_roles (user_id, role_id)
        VALUES (%s, %s)
    """
    execute_query(user_role_query, (user_id, role_id))

    return jsonify({'message': 'Usuario registrado correctamente', 'user_id': user_id}), 201