import os
from flask import Flask, redirect
from dotenv import load_dotenv

# Rutas
from auth.auth import auth_bp
from routes.home import home
from routes.lavado_manos import lavadoMano
from routes.control_general_personal import controlGeneral
from routes.kardex import kardex
from routes.control_condiciones_ambientales import condiciones_ambientales
from routes.registro_control_envasados import controlEnvasados
from routes.higiene_personal import higienePersona
from routes.limpieza_areas import limpieza_areas
from routes.limpieza_equipos_medicion import limpieza_equipos_medicion
from routes.registro_monitoreo_insectos import registro_monitoreo_insectos
from routes.registro_monitoreo_roedores import registro_monitoreo_roedores
from routes.min_max import minmax
from routes.proyeccion_semanal import proyeccionsemanal
from routes.repositorio import repositorioIFP
from routes.control_cloro_residual_agua import controlCloroResidual
from routes.condiciones_sanitarias_vehiculos import condiciones_sanitarias_vehiculos
from routes.monitoreo_calidad_agua import monitoreoAgua
from routes.control_recepcion_materia_prima import control_recepcion_materia_prima

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Llamar a las rutas
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(home, url_prefix="/home")
app.register_blueprint(lavadoMano, url_prefix = "/lavado_Manos")
app.register_blueprint(controlGeneral, url_prefix='/control_general')
app.register_blueprint(kardex, url_prefix='/kardex')
app.register_blueprint(condiciones_ambientales, url_prefix='/condiciones_ambientales')
app.register_blueprint(controlEnvasados, url_prefix='/control_envasados')
app.register_blueprint(higienePersona, url_prefix='/higiene_personal')
app.register_blueprint(limpieza_areas, url_prefix='/limpieza_areas')
app.register_blueprint(limpieza_equipos_medicion, url_prefix='/limpieza_equipos_medicion')
app.register_blueprint(registro_monitoreo_insectos, url_prefix = '/registro_monitoreo_insectos')
app.register_blueprint(registro_monitoreo_roedores, url_prefix = '/registro_monitoreo_roedores')
app.register_blueprint(minmax, url_prefix = '/min_max')
app.register_blueprint(proyeccionsemanal, url_prefix = '/proyeccion_semanal')
app.register_blueprint(repositorioIFP, url_prefix = '/repositorio_IFP')
app.register_blueprint(controlCloroResidual, url_prefix = '/control_cloro_residual')
app.register_blueprint(condiciones_sanitarias_vehiculos, url_prefix = '/condiciones_sanitarias_vehiculos')
app.register_blueprint(monitoreoAgua, url_prefix = '/monitoreo_agua')
app.register_blueprint(control_recepcion_materia_prima, url_prefix = '/control_recepcion_materia_prima')

# Definiendo la ruta por defecto
@app.route('/')
def default():
    return redirect('/home')

if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=5000, debug=True)
    app.run()