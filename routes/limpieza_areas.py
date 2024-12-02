import os
import pprint

from flask import Blueprint, render_template, request, jsonify
from connection.database import execute_query
from collections import defaultdict
from datetime import datetime
from .utils.constans import POES
from .utils.constans import MESES
from .utils.helpers import image_to_base64
from .utils.helpers import generar_reporte
from .utils.helpers import get_cabecera_formato
from .utils.helpers import get_ultimo_dia_laboral_del_mes


limpieza_areas = Blueprint('limpieza_areas', __name__)

@limpieza_areas.route('/', methods=['GET'])
def limpiezaAreas():
    try:
        # Obtener todas las áreas
        query_areas = "SELECT * FROM areas_produccion WHERE id_area_produccion BETWEEN 2 AND 9"
        areas = execute_query(query_areas)

        # Obtener los registros de verificación de limpieza y desinfección creados
        query_vista_limpieza_areas = "SELECT * FROM v_verificacion_limpieza_desinfeccion_areas WHERE estado = 'CREADO' ORDER BY id_verificacion_limpieza_desinfeccion_area DESC"
        v_limpieza_areas = execute_query(query_vista_limpieza_areas)
        
        # Parámetros de paginación
        page = request.args.get('page', 1, type=int)
        per_page = 5
        offset = (page - 1) * per_page
        
        # Obtener los parámetros de mes y año desde la URL
        filter_mes = request.args.get('mes', None)
        filter_anio = request.args.get('anio', None)
        
        # Construir condiciones de filtro
        filter_conditions = "WHERE estado = 'CERRADO'"
        if filter_mes and filter_anio:
            # Si hay filtro de mes y año, solo obtenemos registros que coincidan
            filter_conditions += f" AND mes = '{filter_mes}' AND anio = '{filter_anio}'"
            limit_offset_clause = ""  # Sin paginación cuando hay un filtro
        else:
            # Usar paginación si no hay filtro de fecha
            limit_offset_clause = f" LIMIT {per_page} OFFSET {offset}"
        
        # Construir la consulta para obtener registros finalizados
        query_la_finalizados = f"""
            SELECT 
                mes, 
                anio, 
                json_agg(json_build_object(
                    'id_verificacion_limpieza_desinfeccion_area', id_verificacion_limpieza_desinfeccion_area, 
                    'detalle_area_produccion', detalle_area_produccion,
                    'estado', estado,
                    'id_area_produccion', id_area_produccion
                )) AS registros
            FROM v_verificacion_limpieza_desinfeccion_areas 
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
        v_finalizados_LA = execute_query(query_la_finalizados)
        
        # Si no hay filtro de fecha, contar el total de páginas
        if not filter_mes and not filter_anio:
            query_count = """SELECT COUNT(*) AS total
                            FROM (SELECT DISTINCT mes, anio 
                                FROM v_verificacion_limpieza_desinfeccion_areas 
                                WHERE estado = 'CERRADO') AS distinct_months_years;"""
            total_count = execute_query(query_count)[0]['total']
            total_pages = (total_count + per_page - 1) // per_page
        else:
            total_pages = 1  # Solo una "página" si estamos en modo de filtro

        # Obtener las observaciones y acciones correctivas
        asignacion_observaciones_limpieza_areas = execute_query("SELECT * FROM v_asingaciones_observaciones_acCorrec_limpieza_areas")

        # Renderizar la plantilla con los datos obtenidos
        return render_template('limpieza_areas.html', 
                                areas=areas, 
                                v_limpieza_areas=v_limpieza_areas, 
                                v_finalizados_LA=v_finalizados_LA, 
                                asignacion_observaciones_limpieza_areas=asignacion_observaciones_limpieza_areas,
                                page=page,
                                total_pages=total_pages,
                                filter_mes=filter_mes,
                                filter_anio=filter_anio)
    except Exception as e:
        print(f"Error al obtener datos: {e}")
        return render_template('limpieza_areas.html')

@limpieza_areas.route('/agregar_registro_limpieza_areas/<int:selectArea>', methods=['POST'])
def agregar_registro_limpieza_areas(selectArea):
    try:
        fecha_actual = datetime.now()

        mes = fecha_actual.month
        anio = fecha_actual.year

        mes_consultar = str(mes)
        anio_consultar = str(anio)

        consult_eviromental_condition_month =  "SELECT * FROM verificacion_limpieza_desinfeccion_areas WHERE mes = %s AND anio = %s AND fk_idarea_produccion = %s AND estado = 'CREADO'" 
        verificar_limpieza_area = execute_query(consult_eviromental_condition_month, (mes_consultar, anio_consultar,selectArea))
        if not verificar_limpieza_area:
            execute_query("INSERT INTO verificacion_limpieza_desinfeccion_areas(mes, anio, estado, fk_idarea_produccion, fk_idtipoformatos) VALUES (%s,%s,%s,%s,%s)", (mes, anio, 'CREADO', selectArea, 7))
            return jsonify({'status': 'success', 'message': 'Se registro una verificación de limpieza y desinfección para esta área.'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'El formato para esta área ya existe para este mes.'}), 500
    except Exception as e:
        print(f"Error al registrar una verificación de limpieza: {e}")
        return jsonify({'status': 'error', 'message': 'No se registro una verificación de limpieza y desinfección para esta área.'}), 500

@limpieza_areas.route('/detalles_limpieza_areas/<int:id_verificacion_limpieza_desinfeccion_area>', methods=['GET'])
def detalles_limpieza_areas(id_verificacion_limpieza_desinfeccion_area):

    # Obtener los detalles de la condición ambiental
    query_detalle_limpieza_areas = "SELECT * FROM v_detalles_verificacion_limpieza_desinfeccion_areas WHERE id_verificacion_limpieza_desinfeccion_area = %s"
    detalle_limpieza_areas = execute_query(query_detalle_limpieza_areas, (id_verificacion_limpieza_desinfeccion_area,))


    return jsonify(detalle_limpieza_areas)

@limpieza_areas.route('/obtener_categorias_area/<int:id_area>', methods=['GET'])
def obtener_categorias_area(id_area):
    try:
        # Consulta para obtener categorías específicas para un área dada
        if id_area == 2:
            query_categorias = """SELECT * 
                                    FROM categorias_limpieza_desinfeccion 
                                    WHERE id_categorias_limpieza_desinfeccion IN (1, 2, 3, 4, 5, 6, 7);"""
            categorias = execute_query(query_categorias, (id_area,))
            return jsonify({'status': 'success', 'categorias': categorias}), 200
        elif id_area == 3:
            query_categorias = """SELECT * 
                                    FROM categorias_limpieza_desinfeccion 
                                    WHERE id_categorias_limpieza_desinfeccion IN (1, 2, 3, 4, 5, 7, 8, 9);"""
            categorias = execute_query(query_categorias, (id_area,))
            return jsonify({'status': 'success', 'categorias': categorias}), 200
        elif id_area == 4:
            query_categorias = """SELECT * 
                                    FROM categorias_limpieza_desinfeccion 
                                    WHERE id_categorias_limpieza_desinfeccion IN (1, 2, 3, 4, 5, 6);"""
            categorias = execute_query(query_categorias, (id_area,))
            return jsonify({'status': 'success', 'categorias': categorias}), 200
        elif id_area == 5:
            query_categorias = """SELECT * 
                                    FROM categorias_limpieza_desinfeccion 
                                    WHERE id_categorias_limpieza_desinfeccion IN (1, 2, 3, 4, 5, 10, 9);"""
            categorias = execute_query(query_categorias, (id_area,))
            return jsonify({'status': 'success', 'categorias': categorias}), 200
        elif id_area == 6:
            query_categorias = """SELECT * 
                                    FROM categorias_limpieza_desinfeccion 
                                    WHERE id_categorias_limpieza_desinfeccion IN (1, 2, 3, 4, 11, 7, 12, 13, 10, 9);"""
            categorias = execute_query(query_categorias, (id_area,))
            return jsonify({'status': 'success', 'categorias': categorias}), 200
        elif id_area == 7:
            query_categorias = """SELECT * 
                                    FROM categorias_limpieza_desinfeccion 
                                    WHERE id_categorias_limpieza_desinfeccion IN (1, 2, 3, 14, 4, 5, 15, 16, 17, 9);"""
            categorias = execute_query(query_categorias, (id_area,))
            return jsonify({'status': 'success', 'categorias': categorias}), 200
        elif id_area == 8:
            query_categorias = """SELECT * 
                                    FROM categorias_limpieza_desinfeccion 
                                    WHERE id_categorias_limpieza_desinfeccion IN (1, 2, 18, 19, 3, 4, 5, 20, 9);"""
            categorias = execute_query(query_categorias, (id_area,))
            return jsonify({'status': 'success', 'categorias': categorias}), 200
        elif id_area == 9:
            query_categorias = """SELECT * 
                                    FROM categorias_limpieza_desinfeccion 
                                    WHERE id_categorias_limpieza_desinfeccion IN (1, 2, 3, 4, 5, 21);"""
            categorias = execute_query(query_categorias, (id_area,))
            return jsonify({'status': 'success', 'categorias': categorias}), 200
    except Exception as e:
        print(f"Error al obtener las categorías para el área: {e}")
        return jsonify({'status': 'error', 'message': 'No se pudieron obtener las categorías para el área especificada.'}), 500

@limpieza_areas.route('/registrar_fecha_limpieza', methods=['POST'])
def registrar_fecha_limpieza():
    try:
        # Obtener datos de la solicitud
        data = request.get_json()
        fecha = data.get('fecha')
        categoria_id = data.get('categoria_id')
        id_verificacion = data.get('id_verificacion')



        # Validar que todos los datos estén presentes
        if not fecha or not categoria_id or not id_verificacion:
            return jsonify({'status': 'error', 'message': 'Faltan datos para registrar la fecha de limpieza.'}), 400
        
        verificiacion_fecha = execute_query("SELECT id_detalle_verificacion_limpieza_desinfeccion_area FROM detalles_verificacion_limpieza_desinfeccion_areas WHERE fecha = %s AND fk_id_verificacion_limpieza_desinfeccion_area = %s AND fk_id_categorias_limpieza_desinfeccion = %s", (fecha, id_verificacion, categoria_id))

        if verificiacion_fecha:
            return jsonify({'status': 'error', 'message': 'Esta fecha ya esta registrada.'}), 400
        else:
            # Insertar el registro de limpieza en la tabla detalles_verificacion_limpieza_desinfeccion_areas
            query = """
                INSERT INTO detalles_verificacion_limpieza_desinfeccion_areas 
                (fecha, fk_id_verificacion_limpieza_desinfeccion_area, fk_id_categorias_limpieza_desinfeccion) 
                VALUES (%s, %s, %s)
            """
            execute_query(query, (fecha, id_verificacion, categoria_id))

        # Responder con éxito
        return jsonify({'status': 'success', 'message': 'La fecha de limpieza ha sido registrada correctamente.'}), 200

    except Exception as e:
        print(f"Error al registrar la fecha de limpieza: {e}")
        return jsonify({'status': 'error', 'message': 'Ocurrió un error al registrar la fecha de limpieza.'}), 500

@limpieza_areas.route('/obtener_fechas_limpieza/<int:id_verificacion>/<int:id_area>', methods=['GET'])
def obtener_fechas_limpieza(id_verificacion,id_area):
    try:
        query_fechas = """SELECT * 
                        FROM v_detalles_verificacion_limpieza_desinfeccion_areas 
                        WHERE id_verificacion_limpieza_desinfeccion_area = %s 
                        AND id_categorias_limpieza_desinfeccion = %s
                        ORDER BY fecha DESC"""
        fechas = execute_query(query_fechas, (id_verificacion,id_area,))
        return jsonify({'status': 'success', 'fechas': fechas}), 200
    except Exception as e:
        print(f"Error al obtener las fechas: {e}")
        return jsonify({'status': 'error', 'message': 'No se pudieron obtener las fechas.'}), 500
    
@limpieza_areas.route('/finalizar_limpieza_areas/<int:id_verificacion>', methods=['POST'])
def finalizar_limpieza_areas(id_verificacion):
    try:
        execute_query("UPDATE verificacion_limpieza_desinfeccion_areas SET estado = 'CERRADO'  WHERE id_verificacion_limpieza_desinfeccion_area = %s", (id_verificacion,))
        # Responder con éxito
        return jsonify({'status': 'success', 'message': 'Se finalizo la verificación de la limpieza y desinfección de esta área.'}), 200
    except Exception as e:
        print(f"Error al registrar la fecha de limpieza: {e}")
        return jsonify({'status': 'error', 'message': 'Ocurrió un error al finalizar la verificación de la limpieza y desinfección de esta área.'}), 500
    

    

@limpieza_areas.route('/registrar_observaciones_limpieza_area', methods=['POST'])
def registrar_observaciones_limpieza_area():
    try:
        fecha_actual = datetime.now()
        mes = fecha_actual.month
        mes_format = str(mes)
        data = request.json
        
        # Extracción de los datos del formulario
        observacionLimpiezaAreas = data.get('observacionLimpiezaAreas')
        accionCorrectivaLimpiezaAreas = data.get('accionCorrectivaLimpiezaAreas')
        
        # Verificar que todos los campos estén presentes
        if not observacionLimpiezaAreas or not accionCorrectivaLimpiezaAreas:
            return jsonify({'status': 'error', 'message': 'Faltan datos para registrar la observación.'}), 400

        # Ingresar la acción correctiva y retornar su ID
        query_accion_correctiva = "INSERT INTO acciones_correctivas(detalle_accion_correctiva, estado) VALUES (%s, %s) RETURNING idaccion_correctiva"
        accion_correctiva_result = execute_query(query_accion_correctiva, (accionCorrectivaLimpiezaAreas, 'PENDIENTE'))
        
        # Verificar que se haya obtenido el ID de la acción correctiva
        if not accion_correctiva_result or 'idaccion_correctiva' not in accion_correctiva_result[0]:
            return jsonify({'status': 'error', 'message': 'Error al registrar la acción correctiva.'}), 500
        
        id_accion_correctiva = accion_correctiva_result[0]['idaccion_correctiva']

        # Ingresar la observación y retornar su ID
        query_observacion = "INSERT INTO medidascorrectivasobservaciones(detalledemedidacorrectiva, fecha, fk_id_accion_correctiva) VALUES (%s, %s, %s) RETURNING idmedidacorrectivaob"
        observacion_result = execute_query(query_observacion, (observacionLimpiezaAreas, fecha_actual, id_accion_correctiva))
        
        # Verificar que se haya obtenido el ID de la observación
        if not observacion_result or 'idmedidacorrectivaob' not in observacion_result[0]:
            return jsonify({'status': 'error', 'message': 'Error al registrar la observación.'}), 500

        id_observacion = observacion_result[0]['idmedidacorrectivaob']

        # Obtener las verificaciones de limpieza y desinfección de las áreas activas
        limpieza_areas = execute_query("SELECT id_verificacion_limpieza_desinfeccion_area FROM verificacion_limpieza_desinfeccion_areas WHERE mes = %s", (mes_format,))
        
        # Asignar las observaciones a cada registro de limpieza de área para el mes actual
        for la in limpieza_areas:
            execute_query("INSERT INTO asignaciones_medidas_correctivas_limpieza_areas(fk_id_verificacion_limpieza_desinfeccion_area, fk_idmedidacorrectivaob) VALUES (%s, %s)", (la['id_verificacion_limpieza_desinfeccion_area'], id_observacion))

        return jsonify({'status': 'success', 'message': 'Se registró la observación y medida correctiva correctamente.'}), 200

    except Exception as e:
        print(f"Error al registrar la observación y medida correctiva: {e}")
        return jsonify({'status': 'error', 'message': 'Ocurrió un error al registrar la observación y medida correctiva.'}), 500

@limpieza_areas.route('/estadoAC/<int:id_ca>', methods=['POST'])
def estadoAC(id_ca):
    try:
        execute_query("UPDATE acciones_correctivas SET estado = %s WHERE idaccion_correctiva = %s", ('SOLUCIONADO', id_ca))
        return jsonify({'status': 'success', 'message': 'Se cambió el estado de esta acción correctiva.'}), 200
    except Exception as e:
        print(f"Error al modificar el estado de la acción correctiva: {e}")
        return jsonify({'status': 'error', 'message': 'No hay acción correctiva para validar.'}), 500

@limpieza_areas.route('/get_observaciones_limpieza_areas', methods=['GET'])
def get_observaciones_limpieza_areas():
    try:
        # Consulta para obtener todas las observaciones con sus acciones correctivas y estados
        asignacion_observaciones_limpieza_areas = execute_query("SELECT * FROM v_asingaciones_observaciones_acCorrec_limpieza_areas")

        # Asegúrate de retornar las observaciones correctamente en el formato esperado por el frontend
        return jsonify({'status': 'success', 'observaciones': asignacion_observaciones_limpieza_areas}), 200
    except Exception as e:
        print(f"Error al obtener observaciones: {e}")
        return jsonify({'status': 'error', 'message': 'Error al obtener observaciones.'}), 500


@limpieza_areas.route('/download_formato', methods=['GET'])
def download_formato():

    # Obtener el id del trabajador de los argumentos de la URL
    formato_id=1 # request.args.get('formato_id') # Por el momento cumple para todos los reportes
    nombre_mes=request.args.get('mes')
    anio=request.args.get('anio')
    mes=MESES.get(nombre_mes.lower(), 0)

    cabecera=get_cabecera_formato("verificacion_limpieza_desinfeccion_areas", formato_id)

    # Realizar la consulta para todos los registros y controles de envasados finalizados
    registros = execute_query(f"""SELECT id_verificacion_limpieza_desinfeccion_area, detalle_area_produccion, id_area_produccion, mes, anio, estado
	FROM public.v_verificacion_limpieza_desinfeccion_areas
	WHERE mes = '{nombre_mes.capitalize()}' AND anio = '{anio}' AND estado = 'CERRADO'""")

    # Crear un diccionario para mapear cada 'id_area_produccion' con su 'detalle_area_produccion'
    areas = {registro['id_area_produccion']: registro['detalle_area_produccion'] for registro in registros}

    # pprint.pprint(areas)

    # Crear un diccionario info para almacenar los datos
    info = defaultdict(lambda: defaultdict(lambda: {"dias": [], "frecuencia": ""}))

    for id_area, detalle_area in areas.items():
        # Realizar una consulta para obtener los detalles específicos de cada área
        detalles_limpieza_area = execute_query(f"""SELECT id_detalle_verificacion_limpieza_desinfeccion_area, fecha, id_verificacion_limpieza_desinfeccion_area, fk_idarea_produccion, id_categorias_limpieza_desinfeccion, detalles_categorias_limpieza_desinfeccion, frecuencia
        FROM public.v_detalles_verificacion_limpieza_desinfeccion_areas
        WHERE fk_idarea_produccion={id_area} AND EXTRACT(MONTH FROM TO_DATE(fecha, 'DD/MM/YYYY')) = {mes}""")

        # Crear el subdiccionario para esta área
        sub_info = defaultdict(lambda: {"dias": [], "frecuencia": ""})
        # Procesar cada registro en 'detalles' para llenar 'sub_info'
        for detalle in detalles_limpieza_area:
            categoria = detalle['detalles_categorias_limpieza_desinfeccion']
            fecha = detalle['fecha']
            dia = datetime.strptime(fecha, '%d/%m/%Y').day
            frecuencia = detalle['frecuencia']

            # Agregar el día a la lista de días de esta categoría
            sub_info[categoria]["dias"].append(dia)
            # Establecer la frecuencia si aún no se ha asignado
            if not sub_info[categoria]["frecuencia"]:
                sub_info[categoria]["frecuencia"] = frecuencia.lower()

        # Agregar el subdiccionario al diccionario principal 'info'
        info[detalle_area] = dict(sub_info)

    # Mostrar el resultado
    # pprint.pprint(info)

    # Generar Template para reporte
    logo_path = os.path.join('static', 'img', 'logo.png')
    logo_base64 = image_to_base64(logo_path)
    title_report = cabecera[0]['nombreformato']

    # Renderiza la plantilla
    template = render_template(
        "reports/reporte_limpieza_desinfeccion_areas.html",
        title_manual=POES,
        title_report=title_report,
        format_code_report=cabecera[0]['codigo'],
        frecuencia_registro=cabecera[0]['frecuencia'],
        logo_base64=logo_base64,
        info=info,
        mes=registros[0]['mes'],
        anio=registros[0]['anio']
    )

    file_name = f"{title_report.replace(' ','-')}--{registros[0]['mes']}--{anio}--F"
    return generar_reporte(template, file_name)


@limpieza_areas.route('/download_formato_obs', methods=['GET'])
def download_formato_obs():

    # Obtener el id del trabajador de los argumentos de la URL
    formato_id=1  # request.args.get('formato_id')
    nombre_mes=request.args.get('mes').lower()
    mes=MESES.get(nombre_mes, 0) # 9
    anio=request.args.get('anio')
    # Validar que el mes sea correcto
    if mes == 0:
        raise ValueError(f"Nombre de mes inválido: {nombre_mes}")

    cabecera = get_cabecera_formato("verificacion_limpieza_desinfeccion_areas", formato_id)

    # Realizar la consulta para todos los registros y controles de envasados finalizados
    registros = execute_query(f"""SELECT DISTINCT ON (o.idmedidacorrectivaob)
        o.idmedidacorrectivaob,
        o.detalledemedidacorrectiva,
        to_char(o.fecha::timestamp with time zone, 'DD/MM/YYYY') AS fecha,
        ac.detalle_accion_correctiva,
        ac.estado
    FROM asignaciones_medidas_correctivas_limpieza_areas ala
    JOIN medidascorrectivasobservaciones o
        ON o.idmedidacorrectivaob = ala.fk_idmedidacorrectivaob
    JOIN acciones_correctivas ac
        ON ac.idaccion_correctiva = o.fk_id_accion_correctiva
    WHERE EXTRACT(MONTH FROM o.fecha) = {mes}
    AND EXTRACT(YEAR FROM o.fecha) = {anio}
    ORDER BY o.idmedidacorrectivaob, o.fecha DESC;""")

    # Generar Template para reporte
    logo_path = os.path.join('static', 'img', 'logo.png')
    logo_base64 = image_to_base64(logo_path)
    title_report = f"{cabecera[0]['nombreformato']} - OBSERVACIONES"

    # Renderiza la plantilla
    template = render_template(
        "reports/reporte_limpieza_desinfeccion_areas_obs.html",
        title_manual=POES,
        title_report=title_report,
        format_code_report=cabecera[0]['codigo'],
        frecuencia_registro=cabecera[0]['frecuencia'],
        logo_base64=logo_base64,
        info=registros,
        fecha_periodo=get_ultimo_dia_laboral_del_mes()
    )

    file_name = f"{title_report}--{nombre_mes}--{anio}--F"
    return generar_reporte(template, file_name)
