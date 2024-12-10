import os
from flask import Blueprint, render_template, request, jsonify, send_file
from auth.auth import login_require
from datetime import datetime

from connection.database import execute_query
from .utils.constans import MESES
from .utils.constans import POES
from .utils.helpers import image_to_base64
from .utils.helpers import generar_reporte
from .utils.helpers import get_cabecera_formato_v2

import pprint


condiciones_sanitarias_vehiculos = Blueprint('condiciones_sanitarias_vehiculos', __name__)

@condiciones_sanitarias_vehiculos.route('/', methods=['GET', 'POST'])
@login_require
def condicionesSanitariasVehiculos():
    if request.method == 'GET':
        try:
            # Obtener toas las áreas
            query_areas = "SELECT * FROM areas WHERE idarea = 1 OR idarea = 2 OR idarea = 3 OR idarea = 5;"
            areas = execute_query(query_areas)
            
            #Obtener todos los registros activos de este formatos
            query_creados_CSV = "SELECT id_header_format, detalle_area, mes, anio, fk_idarea, estado FROM v_headers_formats WHERE estado = 'CREADO' AND fk_idtipoformatos = 12;"
            headers_formats = execute_query(query_creados_CSV)
            
            #Extraer los motivos para mostrarlos en un selector
            motivos = execute_query("SELECT * FROM motivos_sanitarios_vehiculos")
            
            #Extraer los tipos de vehículos para mostrarlos
            vehiculos = execute_query("SELECT * FROM tipos_vehiculos")
            
            #Paginador
            page = request.args.get('page', 1, type=int)
            per_page = 5
            offset = (page - 1) * per_page
            
            # Obtener los parámetros de mes y año desde la URL
            filter_mes = request.args.get('mes', None)
            filter_anio = request.args.get('anio', None)
            
            # Construir condiciones de filtro
            filter_conditions = "WHERE estado = 'CERRADO' AND fk_idtipoformatos = 12"
            if filter_mes and filter_anio:
                # Si hay filtro de mes y año, solo obtenemos registros que coincidan
                filter_conditions += f" AND mes = '{filter_mes}' AND anio = '{filter_anio}'"
                limit_offset_clause = ""  # Sin paginación cuando hay un filtro
            else:
                # Usar paginación si no hay filtro de fecha
                limit_offset_clause = f" LIMIT {per_page} OFFSET {offset}"

            query_csv_finalizados = f"""
                SELECT
                    mes,
                    anio,
                    json_agg(json_build_object(
                        'id_header_format', id_header_format,
                        'mes', mes,
                        'anio', anio,
                        'estado', estado,
                        'fk_idarea', fk_idarea,
                        'detalle_area', detalle_area
                    )) AS registros
                FROM v_headers_formats
                {filter_conditions}
                GROUP BY mes, anio
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
                {limit_offset_clause}
            """

            v_finalizados_CSV = execute_query(query_csv_finalizados)
            
            # Si no hay filtro de fecha, contar el total de páginas
            if not filter_mes and not filter_anio:
                query_count = """SELECT COUNT(*) AS total
                                FROM (SELECT DISTINCT mes, anio 
                                    FROM v_headers_formats 
                                    WHERE estado = 'CERRADO' AND fk_idtipoformatos = 12) AS distinct_months_years;"""
                total_count = execute_query(query_count)[0]['total']
                total_pages = (total_count + per_page - 1) // per_page
            else:
                total_pages = 1  # Solo una "página" si estamos en modo de filtro

            return render_template('condiciones_sanitarias_vehiculos.html',
                                    areas=areas,
                                    headers_formats=headers_formats,
                                    motivos=motivos,
                                    vehiculos=vehiculos,
                                    v_finalizados_CSV=v_finalizados_CSV,
                                    page=page,
                                    total_pages=total_pages)
        except Exception as e:
                print(f"Error al obtener datos: {e}")
                return render_template('condiciones_sanitarias_vehiculos.html')

    elif request.method == 'POST':
        try:
            area = request.form.get('selectArea')
            print(area)
            fecha_actual = datetime.now()

            mes_actual = fecha_actual.month
            anio_actual = fecha_actual.year

            mes_consultar = str(mes_actual)
            anio_consultar = str(anio_actual)
            
            consult_eviromental_condition_month =  "SELECT * FROM headers_formats WHERE mes = %s AND anio = %s AND fk_idarea = %s AND estado = 'CREADO' AND fk_idtipoformatos = 12" 
            verificar_producto = execute_query(consult_eviromental_condition_month, (mes_consultar, anio_consultar, area))
            
            if not verificar_producto:
                query_crear_formato = """
                    INSERT INTO headers_formats(mes, anio, estado, fk_idarea, fk_idtipoformatos)
                    VALUES (%s, %s, %s, %s, %s)
                """
                execute_query(query_crear_formato, (mes_actual, anio_actual, 'CREADO', area, 12))

                return jsonify({'status': 'success', 'message': 'Control de las condiciones sanitarias de los vehículos de transporte creado.'}), 200
            else:
                return jsonify({'status': 'error', 'message': 'El formato para esta área ya existe para este mes.'}), 500
        except Exception as e:
            print(f"Error al crear el kardex: {e}")
            return jsonify({'status': 'error', 'message': 'Error al crear el Control de las condiciones sanitarias de los vehículos de transporte'}), 500


@condiciones_sanitarias_vehiculos.route('/detalles_condiciones_sanitarias_vehiculos/<int:id_header_format>', methods=['GET'])
def detalles_condiciones_ambientales(id_header_format):
    # Obtener los detalles de la condición ambiental
    query_detalle_CA = "SELECT * FROM v_detalle_condiciones_vehiculos WHERE fk_id_header_format = %s ORDER BY fecha DESC"
    detalle_CSV = execute_query(query_detalle_CA, (id_header_format,))

    print(detalle_CSV)
    # Obtener las asignaciones de verificación previa para cada detalle
    detalles_formateados = []

    for detalle in detalle_CSV:
        # Formatear la fecha
        detalle['fecha'] = detalle['fecha'].strftime('%d/%m/%Y')  # Formatear la fecha a DD/MM/YYYY

        # Obtener las asignaciones de verificación previa para cada detalle
        query_asignaciones = "SELECT fk_id_verificion_vehiculos FROM asignacion_detalles_condiciones_sanitarias_vehiculos WHERE fk_id_detalle_condicion_sanitaria_vehiculo = %s"
        asignaciones = execute_query(query_asignaciones, (detalle['id_detalle_condicion_sanitaria_vehiculo_transporte'],))

        verificacion = {1: False, 2: False, 3: False, 4: False, 5: False, 6: False, 7: False}
        
        for asig in asignaciones:
            if asig['fk_id_verificion_vehiculos'] in verificacion:
                verificacion[asig['fk_id_verificion_vehiculos']] = True

        # Añadir las asignaciones al detalle
        detalle['verificacion_vehiculos'] = verificacion
        detalles_formateados.append(detalle)

    pprint.pprint(detalles_formateados)
    return jsonify(detalles_formateados)

@condiciones_sanitarias_vehiculos.route('/registrar_condiciones_vehiculos', methods=['POST'])
def registrar_condiciones_vehiculos():
    try:
        data = request.json
        # Extracción de los datos del formulario
        idCSV_hidden = data['idCSV_hidden']
        fecha = data['fecha']
        motivo = data['motivo']
        documento_referencia = data['documento_referencia']
        cantida_bultos = data['cantida_bultos']
        tipo_vehiculo = data['tipo_vehiculo']
        num_placa = data['num_placa']
        
        areaCargaHermetica = data.get('areaCargaHermetica') == 'true'
        noTransportaPersonas = data.get('noTransportaPersonas') == 'true'
        transporteExclusivo = data.get('transporteExclusivo') == 'true'
        pisoTechoLimpio = data.get('pisoTechoLimpio') == 'true'
        paredesLimpias = data.get('paredesLimpias') == 'true'
        libreOlores = data.get('libreOlores') == 'true'
        productoProtegido = data.get('productoProtegido') == 'true'
        
        print(areaCargaHermetica, noTransportaPersonas, transporteExclusivo, pisoTechoLimpio, paredesLimpias, libreOlores, productoProtegido)
        observaciones = data['observaciones'] or None
        accionesCorrectivas = data['accionesCorrectivas'] or None
        
        print(observaciones, accionesCorrectivas)
        idaccion_correctiva = None
        if accionesCorrectivas != None:
            result_accion_correctiva = execute_query("INSERT INTO acciones_correctivas(detalle_accion_correctiva, estado) VALUES (%s,%s) RETURNING idaccion_correctiva", 
                                                    (accionesCorrectivas, 'PENDIENTE'))
            idaccion_correctiva = result_accion_correctiva[0]['idaccion_correctiva']

        # Inserción de detalles_condiciones_sanitarias_vehiculos_transporte
        query_insert_detalle_CSV = """
            INSERT INTO detalles_condiciones_sanitarias_vehiculos_transporte 
            (fecha,
            fk_id_motivo_sanitario_vehiculo,
            documento_referencia,
            total_bultos,
            fk_id_tipo_vehiculo,
            num_placa_vehiculo,
            fk_id_header_format,
            observacion,
            fk_id_accion_correctiva)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id_detalle_condicion_sanitaria_vehiculo_transporte
        """
        
        result_detalle = execute_query(query_insert_detalle_CSV, 
                                        (fecha, motivo, 
                                        documento_referencia, 
                                        cantida_bultos, 
                                        tipo_vehiculo, 
                                        num_placa, 
                                        idCSV_hidden, 
                                        observaciones, 
                                        idaccion_correctiva))

        id_detalle = result_detalle[0]['id_detalle_condicion_sanitaria_vehiculo_transporte']

        # Inserciones para verificación previa
        if areaCargaHermetica:
            execute_query("INSERT INTO asignacion_detalles_condiciones_sanitarias_vehiculos(fk_id_detalle_condicion_sanitaria_vehiculo, fk_id_verificion_vehiculos) VALUES (%s,%s)", 
                        (id_detalle, 1))
        if noTransportaPersonas:
            execute_query("INSERT INTO asignacion_detalles_condiciones_sanitarias_vehiculos(fk_id_detalle_condicion_sanitaria_vehiculo, fk_id_verificion_vehiculos) VALUES (%s, %s)",
                        (id_detalle, 2))
        if transporteExclusivo:
            execute_query("INSERT INTO asignacion_detalles_condiciones_sanitarias_vehiculos(fk_id_detalle_condicion_sanitaria_vehiculo, fk_id_verificion_vehiculos) VALUES (%s, %s)",
                        (id_detalle, 3))
        if pisoTechoLimpio:
            execute_query("INSERT INTO asignacion_detalles_condiciones_sanitarias_vehiculos(fk_id_detalle_condicion_sanitaria_vehiculo, fk_id_verificion_vehiculos) VALUES (%s, %s)",
                        (id_detalle, 4))
        if paredesLimpias:
            execute_query("INSERT INTO asignacion_detalles_condiciones_sanitarias_vehiculos(fk_id_detalle_condicion_sanitaria_vehiculo, fk_id_verificion_vehiculos) VALUES (%s, %s)",
                        (id_detalle, 5))
        if libreOlores:
            execute_query("INSERT INTO asignacion_detalles_condiciones_sanitarias_vehiculos(fk_id_detalle_condicion_sanitaria_vehiculo, fk_id_verificion_vehiculos) VALUES (%s, %s)",
                        (id_detalle, 6))
        if productoProtegido:
            execute_query("INSERT INTO asignacion_detalles_condiciones_sanitarias_vehiculos(fk_id_detalle_condicion_sanitaria_vehiculo, fk_id_verificion_vehiculos) VALUES (%s, %s)",
                        (id_detalle, 7))

        return jsonify({'status': 'success', 'message': 'Se registró el Control de las condiciones sanitarias de los vehículos de transporte.'}), 200

    except Exception as e:
        print(f"Error al agregar detalle de condiciones ambientales: {e}")
        return jsonify({'status': 'error', 'message': 'Ocurrió un error al registrar el Control de las condiciones sanitarias de los vehículos de transporte.'}), 500


@condiciones_sanitarias_vehiculos.route('/estadoAC/<int:id_ca>', methods=['POST'])
def estadoAC(id_ca):
    try:
        execute_query("UPDATE acciones_correctivas SET estado = %s WHERE idaccion_correctiva = %s", ('SOLUCIONADO', id_ca))
        return jsonify({'status': 'success', 'message': 'Se cambió el estado de esta acción correctiva.'}), 200
    except Exception as e:
        print(f"Error al modificar el estado de la acción correctiva: {e}")
        return jsonify({'status': 'error', 'message': 'No hay acción correctiva para validar.'}), 500

#Finalizar el formato
@condiciones_sanitarias_vehiculos.route('/finalizar_Detalles_CSV', methods=['POST'])
def finalizar_Detalles_CSV():
    try:
        data = request.json
        # Extracción de los datos del formulario
        id_header_format = data['id_header_format']

        execute_query("UPDATE headers_formats SET estado = %s WHERE id_header_format = %s", ('CERRADO', id_header_format))
        return jsonify({'status': 'success', 'message': 'Se finalizo correctamente el formato.'}), 200

    except Exception as e:
        print(f"Error al agregar detalle de kardex: {e}")
        return jsonify({'status': 'error', 'message': 'Ocurrió un error al registrar el formato.'}), 500


@condiciones_sanitarias_vehiculos.route('/download_formato', methods=['GET'])
def download_formato():
    # Obtener el id del trabajador de los argumentos de la URL
    month_name = request.args.get('month')
    month = MESES[month_name.lower()]

    query_header_and_area = f"""SELECT id_header_format, a.detalle_area
                                FROM public.headers_formats hf 	LEFT JOIN areas a ON hf.fk_idarea = a.idarea
                                WHERE fk_idtipoformatos = 12 AND mes = '%s'"""
    list_header_formats_with_area = execute_query(query_header_and_area, (month,))

    id_header_format_to_cabecera=list_header_formats_with_area[0]['id_header_format']
    cabecera = get_cabecera_formato_v2(id_header_format_to_cabecera)

    info = {}
    # list_header_formats = [ RealDictRow([('id_header_format', 14), ('detalle_area', 'Materias Primas')]), RealDictRow([('id_header_format', 2), ('detalle_area', 'Envases y Embalajes')])]
    for row in list_header_formats_with_area:
        name = row['detalle_area']
        id_header_format = row['id_header_format']

        query_detalle_CA = "SELECT * FROM v_detalle_condiciones_vehiculos WHERE fk_id_header_format = %s ORDER BY fecha DESC"
        detalle_CSV = execute_query(query_detalle_CA, (id_header_format,))

        # Obtener las asignaciones de verificación previa para cada detalle
        detalles_formateados = []

        for detalle in detalle_CSV:
            # Formatear la fecha
            detalle['fecha'] = detalle['fecha'].strftime('%d/%m/%Y')  # Formatear la fecha a DD/MM/YYYY

            # Obtener las asignaciones de verificación previa para cada detalle
            query_asignaciones = "SELECT fk_id_verificion_vehiculos FROM asignacion_detalles_condiciones_sanitarias_vehiculos WHERE fk_id_detalle_condicion_sanitaria_vehiculo = %s"
            asignaciones = execute_query(query_asignaciones, (detalle['id_detalle_condicion_sanitaria_vehiculo_transporte'],))

            verificacion = {1: False, 2: False, 3: False, 4: False, 5: False, 6: False, 7: False}

            for asig in asignaciones:
                if asig['fk_id_verificion_vehiculos'] in verificacion:
                    verificacion[asig['fk_id_verificion_vehiculos']] = True

            # Añadir las asignaciones al detalle
            detalle['verificacion_vehiculos'] = verificacion
            detalles_formateados.append(detalle)
        info[name] = detalles_formateados
    # pprint.pprint(info)

    # Extraer datos de la cabecera
    year=cabecera[0]['anio']
    format_code=cabecera[0]['codigo']
    format_frequency=cabecera[0]['frecuencia']

    # Generar Template para reporte
    logo_path = os.path.join('static', 'img', 'logo.png')
    logo_base64 = image_to_base64(logo_path)
    title_report = cabecera[0]['nombreformato']

    # Renderiza la plantilla
    template = render_template(
        "reports/reporte_control_condiciones_sanitarias_vehiculos.html",
        title_manual=POES,
        title_report=title_report,
        format_code_report=format_code,
        frecuencia_registro=format_frequency,
        logo_base64=logo_base64,
        info=info,
        month=month_name.capitalize(),
        year=year
    )

    # Generar el nombre del archivo usando las variables de fecha
    file_name = f"{title_report.replace(' ', '-')}--{month_name}--{year}--F"
    return generar_reporte(template, file_name, orientation="landscape")