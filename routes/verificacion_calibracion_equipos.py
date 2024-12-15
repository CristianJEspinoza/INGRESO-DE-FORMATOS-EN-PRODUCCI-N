import os
from flask import Blueprint, render_template, request, jsonify, send_file
from auth.auth import login_require
from connection.database import execute_query
from datetime import datetime
from .utils.constans import MESES_BY_NUM
from .utils.constans import BPM
from .utils.helpers import image_to_base64
from .utils.helpers import generar_reporte
from .utils.helpers import get_cabecera_formato_v2

verificacion_calibracion_equipos = Blueprint('verificacion_calibracion_equipos', __name__)

@verificacion_calibracion_equipos.route('/')
# @login_require
def index():
    try:
        print("Home verificacion_calibracion_equipos")

    except Exception as e:
        print(f"Error al obtener datos: {e}")
        return render_template('monitoreo_agua.html')


#Para descargar el formato
@verificacion_calibracion_equipos.route('/download_formato', methods=['GET'])
def download_formato():
    # Obtener el id del trabajador de los argumentos de la URL
    print("verificacion_calibracion_equipos...")
    print(request.args)
    id_header_format = request.args.get('formato_id')

    cabecera = get_cabecera_formato_v2(id_header_format)

    print('cabecera', cabecera)

    # Realizar la consulta para el detalle de todos los registros y controles de envasados finalizados
    # detalle_registros = execute_query(
    #     f"""SELECT
    #         resultado, observaciones, detalle_control, unidad, estado, fecha
    #     FROM v_detalles_monitoreos_calidad_agua WHERE id_header_format = {id_header_format} AND estado = 'CERRADO' ORDER BY fecha;"""
    # )

    detalle_registros = [
        {
            'equipo': 'Equipo 1',
            'fecha_mantenimiento': '2024-12-01',
            'fecha_proximo_mantenimiento': '2025-03-01',
            'actividad_realizada': 'Actividad 1',
            'observacion': 'Observación 1',
            'responsable': 'Responsable 1'
        }
    ]
    # Extraer datos de la cabecera
    month=cabecera[0]['mes']
    month_name=MESES_BY_NUM.get(int(month)).capitalize()
    year=cabecera[0]['anio']
    format_code=cabecera[0]['codigo']
    format_frequency=cabecera[0]['frecuencia']

    # Generar Template para reporte
    logo_path = os.path.join('static', 'img', 'logo.png')
    logo_base64 = image_to_base64(logo_path)
    title_report = cabecera[0]['nombreformato']

    # Renderiza la plantilla
    template = render_template(
        "reports/reporte_verificacion_calibracion_equipos.html",
        title_manual=BPM,
        title_report=title_report,
        format_code_report=format_code,
        frecuencia_registro=format_frequency,
        logo_base64=logo_base64,
        laboratorio=cabecera[0]['laboratorio'],
        info=detalle_registros
    )

    # Generar el nombre del archivo usando las variables de fecha
    file_name = f"{title_report.replace(' ', '-')}--{month_name}--{year}--F"
    return generar_reporte(template, file_name)

