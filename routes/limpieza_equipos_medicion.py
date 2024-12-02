import os

from flask import Blueprint, render_template, request, jsonify
from auth.auth import login_require
from connection.database import execute_query
from collections import defaultdict
from datetime import datetime
from .utils.constans import POES
from .utils.constans import MESES
from .utils.helpers import image_to_base64
from .utils.helpers import generar_reporte
from .utils.helpers import get_cabecera_formato
from .utils.helpers import get_ultimo_dia_laboral_del_mes


limpieza_equipos_medicion = Blueprint('limpieza_equipos_medicion', __name__)

@limpieza_equipos_medicion.route('/', methods=['GET'])
@login_require
def limpiezaEquiposMedicion():
    try:
        # Obtener las verificaciones en estado creado
        query_equipo_medicion = "SELECT * FROM v_verificaciones_equipos_medicion WHERE estado = 'CREADO' ORDER BY id_verificacion_equipo_medicion DESC"
        formatos_creado = execute_query(query_equipo_medicion)
        
        query_categorias_limpieza_desinfeccion = "SELECT * FROM public.categorias_limpieza_desinfeccion WHERE id_categorias_limpieza_desinfeccion IN (22, 23, 24, 25)"
        categorias_limpieza_desinfeccion = execute_query(query_categorias_limpieza_desinfeccion)
        
        #Paginador
        #obtener el número de página
        page = request.args.get('page', 1, type=int)
        per_page = 5
        offset = (page - 1) * per_page
        
        #Obtener los parámetros de mes y año desde la URL
        filter_mes = request.args.get('mes')
        filter_anio = request.args.get('anio')
        
        #Construimos las condiciones del filtro
        filter_conditions = "WHERE estado = 'CERRADO'"
        
        if filter_mes and filter_anio:
            filter_conditions += f" AND mes = '{filter_mes}' AND anio = '{filter_anio}'"
            limit_offset_clause = ""
        else:
            limit_offset_clause = f"LIMIT {per_page} OFFSET {offset}"
        
        # Obtener las verificaciones en estado cerrado
        query_historial_equipos_medicion = "SELECT * FROM v_verificaciones_equipos_medicion WHERE estado = 'CERRADO' ORDER BY id_verificacion_equipo_medicion DESC"
        historial_formatos_creado = execute_query(query_historial_equipos_medicion)

        query_historial_equipos_medicion = f"""
                                            SELECT DISTINCT mes, anio, id_verificacion_equipo_medicion, estado
                                            FROM v_verificaciones_equipos_medicion
                                            {filter_conditions}
                                            ORDER BY anio DESC, mes DESC
                                            {limit_offset_clause}
                                            """
        historial_formatos_creado = execute_query(query_historial_equipos_medicion)
        
        # Si no hay filtro de fecha, contar el total de páginas
        if not filter_mes and not filter_anio:
            query_count = """SELECT COUNT(*) AS total
                            FROM (SELECT DISTINCT mes, anio 
                                FROM v_verificaciones_equipos_medicion 
                                WHERE estado = 'CERRADO') AS distinct_months_years;"""
            total_count = execute_query(query_count)[0]['total']
            total_pages = (total_count + per_page - 1) // per_page
        else:
            total_pages = 1

        return render_template('limpieza_equipos_medicion.html',
                                formatos_creado=formatos_creado,
                                historial_formatos_creado=historial_formatos_creado,
                                categorias_limpieza_desinfeccion=categorias_limpieza_desinfeccion,
                                page=page,
                                total_pages=total_pages)
    except Exception as e:
        print(f"Error al obtener datos: {e}")
        # Pasar valores por defecto para page y total_pages
        return render_template('limpieza_equipos_medicion.html', 
                            formatos_creado=[], 
                            historial_formatos_creado=[], 
                            categorias_limpieza_desinfeccion=[], 
                            page=1, 
                            total_pages=1)

@limpieza_equipos_medicion.route('/generar_formato_equipos_medicion', methods=['POST'])
def generar_formato_equipos_medicion():
    try:
        fecha_actual = datetime.now()

        mes_actual = fecha_actual.month
        anio_actual = fecha_actual.year

        # Eliminar el registro relacionado en controles_generales_personal
        query_generar_formato = """
            INSERT INTO verificaciones_equipos_medicion(mes,anio,estado,fk_idtipoformatos) VALUES  (%s,%s,%s,%s);
        """
        execute_query(query_generar_formato, (mes_actual,anio_actual,'CREADO',8))

        return jsonify({'status': 'success', 'message': 'Se genero el formato.'}), 200

    except Exception as e:
        print(f"Error al generar el formato: {e}")
        return jsonify({'status': 'error', 'message': 'Hubo un error al generar el formato.'}), 500
    

@limpieza_equipos_medicion.route('/registrar_fecha_limpieza', methods=['POST'])
def registrar_fecha_limpieza():
    try:
        data = request.json
        fecha = data['fecha']
        categoria_id = data['categoria_id']
        
        # Obtener el ID de la verificación en estado "CREADO"
        id_verificacion = execute_query('SELECT id_verificacion_equipo_medicion FROM public.verificaciones_equipos_medicion WHERE estado = %s', ('CREADO',))
        
        if not id_verificacion:
            return jsonify({'status': 'error', 'message': 'No hay verificación en estado CREADO.'}), 400
        
        # Inserción de la fecha de limpieza en la tabla correspondiente
        query = "INSERT INTO detalles_verificaciones_equipos_medicion(fecha, fk_id_categorias_limpieza_desinfeccion, fk_id_verificacion_equipo_medicion, estado_verificacion) VALUES (%s, %s, %s,%s)"
        execute_query(query, (fecha, categoria_id, id_verificacion[0]['id_verificacion_equipo_medicion'], True))

        return jsonify({'status': 'success', 'message': 'Fecha registrada correctamente.'}), 200

    except Exception as e:
        print(f"Error al registrar la fecha de limpieza: {e}")
        return jsonify({'status': 'error', 'message': 'Ocurrió un error al registrar la fecha de limpieza.'}), 500


@limpieza_equipos_medicion.route('/obtener_fechas_limpieza/<int:categoria_id>', methods=['GET'])
def obtener_fechas_limpieza(categoria_id):
    try:
        # Obtener el ID de la verificación en estado "CREADO"
        id_verificacion = execute_query('SELECT id_verificacion_equipo_medicion FROM public.verificaciones_equipos_medicion WHERE estado = %s', ('CREADO',))

        if not id_verificacion:
            return jsonify({'status': 'error', 'message': 'No hay verificación en estado CREADO.'}), 400

        # Consulta para obtener las fechas de limpieza para la categoría y verificación específica
        query = """
            SELECT id_detalle_verificacion_equipos_medicion, fecha, id_verificacion_equipo_medicion, estado_verificacion
            FROM v_detalles_verificaciones_equipos_medicion 
            WHERE id_verificacion_equipo_medicion = %s AND id_categorias_limpieza_desinfeccion = %s 
            ORDER BY fecha
        """
        fechas_resultado = execute_query(query, (id_verificacion[0]['id_verificacion_equipo_medicion'], categoria_id))

        return jsonify({'status': 'success', 'fechas': fechas_resultado}), 200
    
    except Exception as e:
        print(f"Error al obtener las fechas de limpieza: {e}")
        return jsonify({'status': 'error', 'message': 'Ocurrió un error al obtener las fechas de limpieza.'}), 500


@limpieza_equipos_medicion.route('/registrar_no_conforme', methods=['POST'])
def registrar_no_conforme():
    try:
        # Obtener los datos de la solicitud JSON
        data = request.json
        id_detalle = data.get('id_detalle_verificacion_equipos_medicion')
        fecha = data.get('fecha')
        categoria_id = data.get('categoria_id')
        id_verificacion_equipos_medicion = data.get('id_verificacion_equipos_medicion')
        observacion = data.get('observacion')
        accion_correctiva = data.get('accion_correctiva')

        print(id_verificacion_equipos_medicion)

        # Verificar que todos los campos necesarios estén presentes
        if not all([id_detalle, fecha, categoria_id, id_verificacion_equipos_medicion, observacion, accion_correctiva]):
            return jsonify({'status': 'error', 'message': 'Todos los campos son obligatorios.'}), 400

        # Actualizar el estado de la verificación a "No Conforme"
        execute_query(
            'UPDATE detalles_verificaciones_equipos_medicion SET estado_verificacion = %s WHERE id_detalle_verificacion_equipos_medicion = %s',
            (False, id_detalle)
        )

        # Insertar la acción correctiva y retornar su ID
        query_accion_correctiva = """
            INSERT INTO acciones_correctivas (detalle_accion_correctiva, estado)
            VALUES (%s, %s)
            RETURNING idaccion_correctiva
        """
        idaccion_correctiva = execute_query(query_accion_correctiva, (accion_correctiva, 'PENDIENTE'))

        if not idaccion_correctiva or 'idaccion_correctiva' not in idaccion_correctiva[0]:
            return jsonify({'status': 'error', 'message': 'Error al registrar la acción correctiva.'}), 500

        id_accion_correctiva = idaccion_correctiva[0]['idaccion_correctiva']

        # Insertar el registro de "No Conforme" en la base de datos
        query_observacion = """
            INSERT INTO medidascorrectivasobservaciones (detalledemedidacorrectiva, fecha, fk_id_accion_correctiva, fk_id_verificacion_equipo_medicion)
            VALUES (%s, %s, %s, %s)
        """
        execute_query(query_observacion, (observacion, fecha, id_accion_correctiva, id_verificacion_equipos_medicion))

        return jsonify({'status': 'success', 'message': 'Evento "No Conforme" registrado correctamente.'}), 200

    except Exception as e:
        print(f"Error al registrar el evento 'No Conforme': {e}")
        return jsonify({'status': 'error', 'message': 'Ocurrió un error al registrar el evento "No Conforme".'}), 500


@limpieza_equipos_medicion.route('/estadoAC/<int:id_ca>', methods=['POST'])
def estadoAC(id_ca):
    try:
        execute_query("UPDATE acciones_correctivas SET estado = %s WHERE idaccion_correctiva = %s", ('SOLUCIONADO', id_ca))
        return jsonify({'status': 'success', 'message': 'Se cambió el estado de esta acción correctiva.'}), 200
    except Exception as e:
        print(f"Error al modificar el estado de la acción correctiva: {e}")
        return jsonify({'status': 'error', 'message': 'No hay acción correctiva para validar.'}), 500


@limpieza_equipos_medicion.route('/obtener_observaciones', methods=['GET'])
def obtener_observaciones():
    try:
        # Obtener el ID de la verificación en estado "CREADO"
        id_verificacion = execute_query('SELECT id_verificacion_equipo_medicion FROM public.verificaciones_equipos_medicion WHERE estado = %s', ('CREADO',))

        if not id_verificacion:
            return jsonify({'status': 'error', 'message': 'No hay verificaciones en estado CREADO.'}), 400

        id_verificacion_equipo_medicion = id_verificacion[0]['id_verificacion_equipo_medicion']

        # Obtener las observaciones correspondientes a la verificación de equipos de medición creada
        observaciones = execute_query("SELECT * FROM v_observaciones_acc_correctivas WHERE fk_id_verificacion_equipo_medicion = %s", (id_verificacion_equipo_medicion,))

        print(observaciones)

        # Convertir la fecha a formato legible
        for observacion in observaciones:
            observacion['fecha'] = observacion['fecha'].strftime('%d/%m/%Y')  # Cambia el formato a dd/mm/yyyy

        return jsonify({'status': 'success', 'observaciones': observaciones}), 200
    except Exception as e:
        print(f"Error al obtener las observaciones: {e}")
        return jsonify({'status': 'error', 'message': 'Error al obtener las observaciones.'}), 500

@limpieza_equipos_medicion.route('/finalizar_estado_equipos_medicion', methods=['POST'])
def finalizar_estado_equipos_medicion():
    try:
        # Obtener los datos del cuerpo de la solicitud
        data = request.json
        id_verificacion_equipo_medicion = data.get('id_verificacion_equipo_medicion')

        if not id_verificacion_equipo_medicion:
            return jsonify({'status': 'error', 'message': 'ID de verificación no proporcionado.'}), 400

        # Actualizar el estado en la tabla verificaciones_equipos_medicion
        execute_query(
            "UPDATE verificaciones_equipos_medicion SET estado = %s WHERE id_verificacion_equipo_medicion = %s",
            ('CERRADO', id_verificacion_equipo_medicion)
        )
        return jsonify({'status': 'success', 'message': 'Se finalizó el registro para este mes.'}), 200
    except Exception as e:
        print(f"Error al cerrar el registro: {e}")
        return jsonify({'status': 'error', 'message': 'No hay registro que cerrar.'}), 500


@limpieza_equipos_medicion.route('/obtener_fechas_limpieza_finalizados/<int:categoria_id>/<int:id_verificacion_equipo_medicion>', methods=['GET'])
def obtener_fechas_limpieza_finalizados(categoria_id, id_verificacion_equipo_medicion):
    try:
        # Consulta para obtener las fechas de limpieza para la categoría y verificación específica
        query = """
            SELECT id_detalle_verificacion_equipos_medicion, fecha, id_verificacion_equipo_medicion, estado_verificacion
            FROM v_detalles_verificaciones_equipos_medicion 
            WHERE id_verificacion_equipo_medicion = %s AND id_categorias_limpieza_desinfeccion = %s 
            ORDER BY fecha
        """
        fechas_resultado = execute_query(query, (id_verificacion_equipo_medicion, categoria_id))

        return jsonify({'status': 'success', 'fechas': fechas_resultado}), 200
    
    except Exception as e:
        print(f"Error al obtener las fechas de limpieza: {e}")
        return jsonify({'status': 'error', 'message': 'Ocurrió un error al obtener las fechas de limpieza.'}), 500


@limpieza_equipos_medicion.route('/download_formato', methods=['GET'])
def download_formato():

    id_formato=1 # request.args.get('formato_id') # Por el momento cumple para todos los reportes
    nombre_mes=request.args.get('mes').lower()
    mes=MESES.get(nombre_mes, 0) # 9

    cabecera = get_cabecera_formato("verificaciones_equipos_medicion", id_formato)

    # Realizar una consulta para obtener los detalles específicos de cada área
    detalles_equipos_medicion = execute_query(f"""
                                SELECT
                                    id_detalle_verificacion_equipos_medicion,
                                    fecha,
                                    estado_verificacion,
                                    id_categorias_limpieza_desinfeccion,
                                    detalles_categorias_limpieza_desinfeccion,
                                    frecuencia,
                                    id_verificacion_equipo_medicion,
                                    mes,
                                    anio,
                                    estado,
                                    fk_idtipoformatos
                                FROM public.v_detalles_verificaciones_equipos_medicion
                                WHERE mes = '{mes}';
                                """)
    # pprint.pprint(detalles_equipos_medicion)

    # Consulta para obtener Observaciones
    observaciones = execute_query(f"""
                                SELECT
                                    detalledemedidacorrectiva,
                                    fecha,
                                    detalle_accion_correctiva,
                                    estado
	                            FROM public.v_observaciones_acc_correctivas
                                WHERE fk_id_verificacion_equipo_medicion = {id_formato};
                                """)

    # Crear el subdiccionario para esta área
    info = defaultdict(lambda: {"dias": [], "frecuencia": ""})
    anio=detalles_equipos_medicion[0]['anio']

    # Procesar cada registro en 'detalles' para llenar 'info'
    for detalle in detalles_equipos_medicion:
        categoria = detalle['detalles_categorias_limpieza_desinfeccion']
        fecha = detalle['fecha']
        dia = datetime.strptime(fecha, '%d/%m/%Y').day
        frecuencia = detalle['frecuencia']
        # Agregar el día a la lista de días de esta categoría
        info[categoria]["dias"].append(dia)
        # Establecer la frecuencia si aún no se ha asignado
        if not info[categoria]["frecuencia"]:
            info[categoria]["frecuencia"] = frecuencia.lower()
    # pprint.pprint(info)

    """ Example
        info {
                "Balanzas": {
                    "dias": [15],
                    "frecuencia": "mensual",
                },
                "Insectolocutores":  {
                    "dias": [25],
                    "frecuencia": "mensual",
                }
        }
        info_observaciones [
            {
                "detalledemedidacorrectiva": "Observación 1",
                "fecha": "01/09/2023",
                "detalle_accion_correctiva": "detalle_accion_correctiva 2",
                "estado": "SOLUCIONADO"
            },
        ]
    """

    # Generar Template para reporte equipos
    logo_path = os.path.join('static', 'img', 'logo.png')
    logo_base64 = image_to_base64(logo_path)
    title_report = f"{cabecera[0]['nombreformato']}"

    # Renderiza la plantilla
    template = render_template(
        "reports/reporte_limpieza_desinfeccion_equipos_medicion.html",
        title_manual=POES,
        title_report=title_report,
        format_code_report=cabecera[0]['codigo'],
        frecuencia_registro=cabecera[0]['frecuencia'],
        logo_base64=logo_base64,
        mes=nombre_mes,
        anio=anio,
        info=info,
        info_observaciones=observaciones,
        fecha_periodo=get_ultimo_dia_laboral_del_mes()
    )

    file_name = f"{title_report.replace(' ','-')}--{nombre_mes.strip().capitalize()}--{anio}--F"
    return generar_reporte(template, file_name, orientation='landscape')