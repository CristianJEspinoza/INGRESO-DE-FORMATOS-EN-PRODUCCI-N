import os
from flask import Blueprint, render_template, request, jsonify, send_file
from auth.auth import login_require
from connection.database import execute_query
from datetime import datetime
from .utils.constans import BPM
from .utils.constans import MESES_BY_NUM
from .utils.helpers import image_to_base64
from .utils.helpers import generar_reporte
from .utils.helpers import get_cabecera_formato_v2

control_visitas = Blueprint('control_visitas', __name__)

@control_visitas.route('/')
@login_require
def index():
    try:
        
        evaluaciones_visitas = execute_query("SELECT * FROM evaluaciones_visitas")
        
        control_visitas = execute_query("SELECT * FROM control_visitas ORDER BY idcontrol_visitas DESC")
        
        verificacion_visitas = execute_query("SELECT * FROM asignaciones_evaluaciones_visitas")
        
        return render_template('control_visitas.html', evaluaciones_visitas=evaluaciones_visitas, control_visitas=control_visitas, verificacion_visitas=verificacion_visitas)

    except Exception as e:
        print(f"Error al obtener datos: {e}")
        # return render_template('monitoreo_agua.html')

@control_visitas.route('/registrar_visita', methods=['POST'])
def registrar_visita():
    try:
        data = request.json
        # Extracción de los datos del formulario
        fecha = data.get('fecha')
        nom_apellido = data.get('nom_apellido')
        dni = data.get('dni')
        empresa = data.get('empresa')
        h_ingreso = data.get('h_ingreso')
        h_salida = data.get('h_salida')
        evaluacionesSeleccionadas = data.get('evaluacionesSeleccionadas', [])
        motivo_visita = data.get('motivo_visita')
        observaciones = data.get('observaciones', '')

        # Validar que todos los datos requeridos estén presentes
        if not fecha or not nom_apellido or not dni or not empresa or not h_ingreso or not h_salida or not motivo_visita:
            return jsonify({'status': 'error', 'message': 'Faltan datos obligatorios para el registro de la visita.'}), 400

        # Obtener el ID del registro de monitoreo de visitas en estado "CREADO"
        id_header_visita = execute_query(
            "SELECT id_header_format FROM headers_formats WHERE estado = 'CREADO' AND fk_idtipoformatos = 16"
        )

        if not id_header_visita:
            return jsonify({'status': 'error', 'message': 'No se encontró una cabecera activa para el control de visitas.'}), 404

        id_header_visita_register = id_header_visita[0]['id_header_format']

        # Insertar el registro de visita en `control_visitas`
        resultado_detalle = execute_query(
            """
            INSERT INTO control_visitas (
                fecha, nombres_apellidos, dni, empresa, h_ingreso, h_salida, motivo, observaciones, fk_id_header_format
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING idcontrol_visitas
            """,
            (fecha, nom_apellido, dni, empresa, h_ingreso, h_salida, motivo_visita, observaciones, id_header_visita_register)
        )

        if not resultado_detalle or 'idcontrol_visitas' not in resultado_detalle[0]:
            return jsonify({'status': 'error', 'message': 'Error al registrar los detalles de la visita.'}), 500

        idcontrol_visitas = resultado_detalle[0]['idcontrol_visitas']
        print(evaluacionesSeleccionadas)
        # Insertar evaluaciones seleccionadas
        for evaluacion in evaluacionesSeleccionadas:
            execute_query(
                """
                INSERT INTO asignaciones_evaluaciones_visitas (
                    fk_ididcontrol_visitas, fk_id_evaluacion_visita
                ) VALUES (%s, %s)
                """,
                (idcontrol_visitas, evaluacion)
            )

        return jsonify({'status': 'success', 'message': 'La visita fue registrada correctamente.'}), 200

    except Exception as e:
        print(f"Error al registrar la visita: {e}")
        return jsonify({'status': 'error', 'message': f'Error al registrar la visita: {e}'}), 500




@control_visitas.route('/download_formato', methods=['GET'])
def download_formato():
    try:
        # Obtener la cabecera activa
        id_header_visita = execute_query(
            "SELECT id_header_format FROM headers_formats WHERE estado = 'CREADO' AND fk_idtipoformatos = 16"
        )

        if not id_header_visita:
            return jsonify({'status': 'error', 'message': 'No se encontró una cabecera activa para el control de visitas.'}), 404

        id_header_format = id_header_visita[0]['id_header_format']
        cabecera = get_cabecera_formato_v2(id_header_format)

        # Obtener detalles del control de visitas
        query_registros = """
            SELECT * FROM control_visitas 
            ORDER BY fecha
        """
        detalles = execute_query(query_registros)

        # Obtener las verificaciones para cada detalle
        info = []
        for registro in detalles:
            query_verificaciones = """
                SELECT 
                    fk_ididcontrol_visitas, 
                    fk_id_evaluacion_visita 
                FROM asignaciones_evaluaciones_visitas 
                WHERE fk_ididcontrol_visitas = %s
            """
            verificaciones = execute_query(query_verificaciones, (registro['idcontrol_visitas'],))

            dict_registro = {
                "fecha": registro['fecha'].strftime('%d/%m/%Y'),  # Convertir fecha a dd/mm/yyyy
                "nombres_apellidos": registro['nombres_apellidos'],
                "dni": registro['dni'],
                "empresa": registro['empresa'],
                "h_ingreso": registro['h_ingreso'].strftime('%H:%M'),  # Convertir hora a HH:MM
                "h_salida": registro['h_salida'].strftime('%H:%M'),
                "eva_h": 1 in [verificacion['fk_id_evaluacion_visita'] for verificacion in verificaciones],
                "eva_es": 2 in [verificacion['fk_id_evaluacion_visita'] for verificacion in verificaciones],
                "eva_u": 3 in [verificacion['fk_id_evaluacion_visita'] for verificacion in verificaciones],
                "motivo": registro['motivo'],
                "observaciones": registro['observaciones']
            }
            info.append(dict_registro)

        # Formatear variables de cabecera
        year = datetime.now().year
        month = datetime.now().month
        month_name = MESES_BY_NUM.get(int(month)).capitalize()
        format_code = cabecera[0]['codigo']
        format_frequency = cabecera[0]['frecuencia']
        title_report = cabecera[0]['nombreformato']

        # Generar Template para reporte
        logo_path = os.path.join('static', 'img', 'logo.png')
        logo_base64 = image_to_base64(logo_path)

        # Renderiza la plantilla
        template = render_template(
            "reports/reporte_control_visitas.html",
            title_manual="BPM",  # Ejemplo, ajusta según necesidad
            title_report=title_report,
            format_code_report=format_code,
            frecuencia_registro=format_frequency,
            logo_base64=logo_base64,
            laboratorio=cabecera[0]['laboratorio'],
            info=info
        )

        # Generar el nombre del archivo usando las variables de fecha
        file_name = f"{title_report.replace(' ', '-')}--{month_name}--{year}--F"
        return generar_reporte(template, file_name)

    except Exception as e:
        print(f"Error al descargar formato: {e}")
        return jsonify({'status': 'error', 'message': f'Error al generar el formato: {e}'}), 500
