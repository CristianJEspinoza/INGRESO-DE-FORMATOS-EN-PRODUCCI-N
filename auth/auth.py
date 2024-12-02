import functools
from flask import (Blueprint, render_template, request, redirect, session, g ,jsonify, url_for)


auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('login', methods = ('GET', 'POST'))
def login():
    print("Entro login", request.method)
    if request.method == 'POST':
        # username = request.form['username']
        password = request.form['password']
        print(password)
        error = None
        #validar datos
        if not password == "1234": # os.getenv('PASSWORD_ADMIN'):
            print('go index home')
            error = 'Contraseña incorrecta'
        #Iniciar sesión
        if error is None:
            session.clear()
            session['user_id'] = 2 # Con BD - model: user.id
            # return redirect(url_for('home.principal'))
            return jsonify({ 'message': 'Datos correctos' }), 200
        print('error'*10, error);
        return jsonify({ 'message': error }), 404
    return render_template('login.html')

@auth_bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    print('user_id', user_id)
    if user_id is None:
        g.user = None
    else:
        # g.user = User.query.get_or_404(user_id) # Si fuera con BD
        g.user = 'admin'

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