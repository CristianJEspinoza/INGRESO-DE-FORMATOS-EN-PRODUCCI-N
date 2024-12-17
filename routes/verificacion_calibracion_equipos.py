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
        # Obtener el formato creado con el id de formato 11
        formato_RCE = execute_query("SELECT * FROM v_verificaciones_calibracion_equipos WHERE estado = 'CREADO'")
        
        #Paginación para el historial
        page = request.args.get('page', 1, type=int)
        per_page = 5
        offset = (page - 1) * per_page
        
        # Obtener los parámetros de mes y año desde la URL
        filter_mes = request.args.get('mes', None)
        filter_anio = request.args.get('anio', None)
        
        # Construir condiciones de filtro
        filter_conditions = "WHERE estado = 'CERRADO' AND fk_idtipoformatos = 14"
        if filter_mes and filter_anio:
            # Si hay filtro de mes y año, solo obtenemos registros que coincidan
            filter_conditions += f" AND mes = '{filter_mes}' AND anio = '{filter_anio}'"
            limit_offset_clause = ""  # Sin paginación cuando hay un filtro
        else:
            # Usar paginación si no hay filtro de fecha
            limit_offset_clause = f" LIMIT {per_page} OFFSET {offset}"
        
        query_finalizados = f"""
                            SELECT * 
                            FROM v_headers_formats 
                            {filter_conditions}
                            ORDER BY 
                                anio::INTEGER DESC,  
                                CASE 
                                    WHEN mes = 'Enero' THEN 1
                                    WHEN mes = 'Febrero' THEN 2
                                    WHEN mes = 'Marzo' THEN 3
                                    WHEN mes = 'Abril' THEN 4
                                    WHEN mes = 'Mayo' THEN 5
                                    WHEN mes = 'Junio' THEN 6
                                    WHEN mes = 'Julio' THEN 7
                                    WHEN mes = 'Agosto' THEN 8
                                    WHEN mes = 'Septiembre' THEN 9
                                    WHEN mes = 'Octubre' THEN 10
                                    WHEN mes = 'Noviembre' THEN 11
                                    WHEN mes = 'Diciembre' THEN 12
                                END DESC
                            {limit_offset_clause}"""
        
        v_finalizados_LA = execute_query(query_finalizados)
        
        query_count = "SELECT COUNT(*) AS total FROM public.v_headers_formats WHERE estado = 'CERRADO' AND fk_idtipoformatos = 14"
        
        total_count = execute_query(query_count)[0]['total']
        total_pages = (total_count + per_page - 1) // per_page
        
        
        return render_template('registro_verificacion_equipos.html', 
                                formato=formato_RCE,
                                page=page,
                                headers_Close=v_finalizados_LA,
                                total_pages=total_pages)

    except Exception as e:
        print(f"Error al obtener datos: {e}")
        return render_template('registro_verificacion_equipos.html')

@verificacion_calibracion_equipos.route('/historial_por_grupo', methods=['GET'])
def historial_por_grupo():
    try:
        id_header_format = request.args.get('id_header_format', type=int)

        if not id_header_format:
            return jsonify({"error": "ID del grupo es requerido"}), 400

        query = f"""
            SELECT equipo, 
                fecha_mantenimiento, 
                fecha_prox_mantenimiento, 
                actividad_realizada, 
                observaciones, 
                responsable, 
                estado
            FROM v_verificaciones_calibracion_equipos
            WHERE id_header_format = {id_header_format}
        """
        historial = execute_query(query)

        if not historial:
            return jsonify({"error": "No hay datos para este grupo"}), 404

        # Formatear fechas
        for record in historial:
            record['fecha_mantenimiento'] = record['fecha_mantenimiento'].strftime('%d/%m/%Y')
            record['fecha_prox_mantenimiento'] = record['fecha_prox_mantenimiento'].strftime('%d/%m/%Y')

        return jsonify(historial)

    except Exception as e:
        print(f"Error en historial_por_grupo: {e}")
        return jsonify({"error": "Error al obtener historial"}), 500


#Para descargar el formato
@verificacion_calibracion_equipos.route('/download_formato', methods=['GET'])
def download_formato():
    # Obtener el id del trabajador de los argumentos de la URL
    print("verificacion_calibracion_equipos...")
    print(request.args)
    id_header_format = request.args.get('formato_id')

    cabecera = get_cabecera_formato_v2(id_header_format)

    print('cabecera', cabecera)

    detalle_registros = execute_query(
        f"""SELECT * FROM v_verificaciones_calibracion_equipos 
        WHERE id_header_format = {id_header_format};"""
    )
    
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

