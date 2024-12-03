import os

from flask import Blueprint, render_template, request, jsonify, send_file
from auth.auth import login_require
from connection.database import execute_query
from datetime import datetime
from .utils.constans import POES
from .utils.constans import MESES_BY_NUM
from .utils.helpers import image_to_base64
from .utils.helpers import generar_reporte
from .utils.helpers import get_cabecera_formato
from .utils.helpers import get_ultimo_dia_laboral_del_mes


registro_monitoreo_roedores = Blueprint('registro_monitoreo_roedores', __name__)

@registro_monitoreo_roedores.route('/', methods=['GET'])
@login_require
def registroMonitoreoRoedores():
    try:
        # Obtener las verificaciones en estado creado
        query_control_insectos = "SELECT * FROM v_registros_monitores_insectos_roedores WHERE estado = 'CREADO' AND fk_idtipoformatos = 10 ORDER BY id_registro_monitoreo_insecto_roedor DESC"
        formatos_creado = execute_query(query_control_insectos)

        

        areas = execute_query("SELECT * FROM areas_produccion WHERE id_area_produccion IN (2, 4, 10, 11, 12, 7, 8, 13, 14, 15)")

        query_categorias_limpieza_desinfeccion = "SELECT * FROM public.categorias_limpieza_desinfeccion WHERE id_categorias_limpieza_desinfeccion IN (22, 23, 24, 25)"
        categorias_limpieza_desinfeccion = execute_query(query_categorias_limpieza_desinfeccion)

        # Obtener los registros
        query_registros = "SELECT * FROM v_detalles_registros_monitoreos_insectos_roedores WHERE estado = 'CREADO' AND fk_idtipoformatos = 10 ORDER BY id_detalle_registro_monitoreo_insecto_roedor DESC"
        resgistros_control_insecto = execute_query(query_registros)

        #obtener las asignaciones de las áreas que estan conforme o no conforme
        verificacion_araes_insectos = execute_query('SELECT fk_id_area_produccion, fk_id_detalle_registro_monitoreo_insecto_roedor FROM verificaciones_areas_produccion_insectos_roedores')

        #Paginación para el historial de registro y monitoreo de insectos
        page = request.args.get('page', 1, type=int)
        per_page = 5
        offset = (page - 1) * per_page
        query_count = "SELECT COUNT(*) AS total FROM public.registros_monitores_insectos_roedores WHERE estado = 'CERRADO' AND fk_idtipoformatos = 10"
        
        total_count = execute_query(query_count)[0]['total']
        total_pages = (total_count + per_page - 1) // per_page
        
        # Obtener las verificaciones en estado CERRADO
        query_control_insectos_finalizados = f"SELECT * FROM v_registros_monitores_insectos_roedores WHERE estado = 'CERRADO' AND fk_idtipoformatos = 10 ORDER BY id_registro_monitoreo_insecto_roedor DESC LIMIT {per_page} OFFSET {offset}"
        formatos_finalizados = execute_query(query_control_insectos_finalizados)
        
        return render_template('registro_monitoreo_roedores.html',
                                formatos_creado=formatos_creado,
                                areas=areas,
                                categorias_limpieza_desinfeccion=categorias_limpieza_desinfeccion,
                                resgistros_control_insecto=resgistros_control_insecto,
                                verificacion_araes_insectos=verificacion_araes_insectos,
                                formatos_finalizados=formatos_finalizados,
                                page=page,
                                total_pages=total_pages)
    except Exception as e:
        print(f"Error al obtener datos: {e}")
        return render_template('registro_monitoreo_roedores.html')

@registro_monitoreo_roedores.route('/historial', methods=['GET'])
def historial_monitoreo_insectos():
    try:
        #Paginación para el historial de registro y monitoreo de insectos
        page = request.args.get('page', 1, type=int)
        per_page = 5
        offset = (page - 1) * per_page
        query_count = "SELECT COUNT(*) AS total FROM public.registros_monitores_insectos_roedores WHERE estado = 'CERRADO' AND fk_idtipoformatos = 10"
        
        total_count = execute_query(query_count)[0]['total']
        total_pages = (total_count + per_page - 1) // per_page
        
        # Obtener las verificaciones en estado CERRADO
        query_control_insectos_finalizados = f"SELECT * FROM v_registros_monitores_insectos_roedores WHERE estado = 'CERRADO' AND fk_idtipoformatos = 10 ORDER BY id_registro_monitoreo_insecto_roedor DESC LIMIT {per_page} OFFSET {offset}"
        formatos_finalizados = execute_query(query_control_insectos_finalizados)

        return render_template('partials/historial_registro_monitoreo_roedores.html',
                                formatos_finalizados=formatos_finalizados,
                                page=page,
                                total_pages=total_pages)
    except Exception as e:
            print(f"Error al obtener datos: {e}")
            return jsonify({"error": "Error al obtener datos"}), 500


@registro_monitoreo_roedores.route('/generar_formato_monitoreo_insecto', methods=['POST'])
def generar_formato_monitoreo_insecto():
    try:
        fecha_actual = datetime.now()
        mes = str(fecha_actual.month)
        anio = str(fecha_actual.year)

        # Intentar ejecutar la consulta y ver si causa un error
        execute_query('INSERT INTO registros_monitores_insectos_roedores(mes, anio, estado, fk_idtipoformatos) VALUES (%s,%s,%s,%s)', (mes, anio, 'CREADO', 10))

        return jsonify({'status': 'success', 'message': 'Formato generado exitosamente.'}), 200

    except Exception as e:
        print(f"Error al generar el formato: {e}")
        return jsonify({'status': 'error', 'message': f'Hubo un error al generar el formato: {e}'}), 500

@registro_monitoreo_roedores.route('/ruta_para_guardar_monitoreo_insectos', methods=['POST'])
def ruta_para_guardar_monitoreo_insectos():
    try:
        data = request.json
        # Extracción de los datos del formulario
        fecha = data.get('fecha')
        hora = data.get('hora')
        areasSeleccionadas = data.get('areas')
        observaciones = data.get('observaciones') or "-"
        accionCorrectiva = data.get('accion_correctiva')

        # Validar que todos los datos requeridos estén presentes
        if not fecha or not hora or not areasSeleccionadas:
            return jsonify({'status': 'error', 'message': 'Datos incompletos: fecha, hora y áreas son obligatorios.'}), 400

        # Insertar la acción correctiva si existe
        id_accion_correctiva = None
        if accionCorrectiva and accionCorrectiva.strip():
            resultado_accion = execute_query(
                "INSERT INTO acciones_correctivas(detalle_accion_correctiva, estado) VALUES (%s, %s) RETURNING idaccion_correctiva",
                (accionCorrectiva, 'PENDIENTE')
            )
            if resultado_accion and 'idaccion_correctiva' in resultado_accion[0]:
                id_accion_correctiva = resultado_accion[0]['idaccion_correctiva']

        # Obtener el ID del registro de monitoreo de insectos en estado "CREADO"
        id_registro_monitoreo_resultado = execute_query(
            "SELECT id_registro_monitoreo_insecto_roedor FROM registros_monitores_insectos_roedores WHERE estado = 'CREADO' AND fk_idtipoformatos = 10"
        )

        if not id_registro_monitoreo_resultado:
            return jsonify({'status': 'error', 'message': 'No se encontró un formato de monitoreo de insectos en estado "CREADO".'}), 404

        id_registro_monitoreo_insecto_roedor = id_registro_monitoreo_resultado[0]['id_registro_monitoreo_insecto_roedor']

        # Insertar el detalle del registro de monitoreo
        resultado_detalle = execute_query(
            "INSERT INTO detalles_registros_monitoreos_insectos_roedores(fecha, hora, observacion, fk_id_accion_correctiva, fk_id_registro_monitoreo_insecto_roedor) VALUES (%s,%s,%s,%s,%s) RETURNING id_detalle_registro_monitoreo_insecto_roedor",
            (fecha, hora, observaciones, id_accion_correctiva, id_registro_monitoreo_insecto_roedor)
        )

        if not resultado_detalle or 'id_detalle_registro_monitoreo_insecto_roedor' not in resultado_detalle[0]:
            return jsonify({'status': 'error', 'message': 'Error al registrar el detalle de monitoreo.'}), 500

        id_detalle_registro_monitoreo_insecto_roedor = resultado_detalle[0]['id_detalle_registro_monitoreo_insecto_roedor']

        # Insertar cada área seleccionada
        for area in areasSeleccionadas:
            execute_query(
                "INSERT INTO verificaciones_areas_produccion_insectos_roedores(fk_id_area_produccion, fk_id_detalle_registro_monitoreo_insecto_roedor) VALUES (%s,%s)",
                (area, id_detalle_registro_monitoreo_insecto_roedor)
            )

        return jsonify({'status': 'success', 'message': 'Se registró correctamente el monitoreo de insectos.'}), 200

    except Exception as e:
        print(f"Error al generar el formato: {e}")
        return jsonify({'status': 'error', 'message': f'Hubo un error al generar el formato: {e}'}), 500



@registro_monitoreo_roedores.route('/estadoAC/<int:id_ca>', methods=['POST'])
def estadoAC(id_ca):
    try:
        execute_query("UPDATE acciones_correctivas SET estado = %s WHERE idaccion_correctiva = %s", ('SOLUCIONADO', id_ca))
        return jsonify({'status': 'success', 'message': 'Se cambió el estado de esta acción correctiva.'}), 200

    except Exception as e:
        print(f"Error al modificar el estado de la acción correctiva: {e}")
        return jsonify({'status': 'error', 'message': 'No hay acción correctiva para validar.'}), 500

@registro_monitoreo_roedores.route('/finalizar_monitoreo_insectos', methods=['POST'])
def finalizar_monitoreo_insectos():
    try:
        execute_query("UPDATE registros_monitores_insectos_roedores SET estado = %s WHERE estado = %s AND fk_idtipoformatos = 10", ('CERRADO', 'CREADO'))
        return jsonify({'status': 'success', 'message': 'Se cambió el estado de esta acción correctiva.'}), 200

    except Exception as e:
        print(f"Error al finalizar el registro de control de higiene personal: {e}")
        return jsonify({'status': 'error', 'message': 'Error al finalizar el registro de control de higiene personal.'}), 500

@registro_monitoreo_roedores.route('/obtener_detalle_monitoreo_insectos/<int:id_formatos>', methods=['GET'])
def obtener_detalle_monitoreo_insectos(id_formatos):
    try:
        # Consulta de detalles de monitoreo de insectos
        query_registros = """
            SELECT
                id_detalle_registro_monitoreo_insecto_roedor,
                fecha,
                hora,
                observacion,
                detalle_accion_correctiva,
                estado_accion_correctiva,
                idaccion_correctiva
            FROM v_detalles_registros_monitoreos_insectos_roedores
            WHERE id_registro_monitoreo_insecto_roedor = %s
            ORDER BY fecha, hora
        """
        detalles = execute_query(query_registros, (id_formatos,))

        # Consulta para obtener las verificaciones de áreas por detalle
        query_verificaciones = """
            SELECT
                fk_id_area_produccion,
                fk_id_detalle_registro_monitoreo_insecto_roedor
            FROM verificaciones_areas_produccion_insectos_roedores
            WHERE fk_id_detalle_registro_monitoreo_insecto_roedor IN %s
        """
        detalle_ids = tuple([detalle['id_detalle_registro_monitoreo_insecto_roedor'] for detalle in detalles])
        verificaciones = execute_query(query_verificaciones, (detalle_ids,)) if detalle_ids else []

        # Convertir los objetos datetime y time a string para JSON serialization
        for detalle in detalles:
            detalle['fecha'] = detalle['fecha'].strftime('%d/%m/%Y')  # Convertir fecha a string
            detalle['hora'] = detalle['hora'].strftime('%H:%M')  # Convertir hora a string

        # Verificar si se encontraron resultados
        if not detalles:
            return jsonify({'status': 'error', 'message': 'No se encontraron detalles para el registro.'}), 404

        # Enviar los detalles y las verificaciones de vuelta al frontend
        return jsonify({'status': 'success', 'detalles': detalles, 'verificaciones': verificaciones}), 200

    except Exception as e:
        print(f"Error al obtener los detalles: {e}")
        return jsonify({'status': 'error', 'message': 'Hubo un error al obtener los detalles.'}), 500


@registro_monitoreo_roedores.route('/download_formato', methods=['GET'])
def download_formato():

    # Obtener el id del trabajador de los argumentos de la URL
    id_formato=request.args.get('id_formato')
    mes=request.args.get('mes')
    print(id_formato, mes)
    cabecera=get_cabecera_formato("registros_monitores_insectos_roedores", id_formato)

    # Realizar la consulta para todos los registros para el monitoreo de roedores
    registros = execute_query(f"""SELECT
                id_detalle_registro_monitoreo_insecto_roedor,
                to_char(fecha::timestamp with time zone, 'DD/MM/YYYY'::text) AS fecha,
                hora,
                observacion,
                detalle_accion_correctiva,
                estado_accion_correctiva,
                idaccion_correctiva
            FROM v_detalles_registros_monitoreos_insectos_roedores
            WHERE id_registro_monitoreo_insecto_roedor = {id_formato}
            ORDER BY fecha, hora""")

    info=[]
    for registro in registros:
        # Obtener las verificaciones de áreas por detalle
        verificaciones = execute_query("""
            SELECT
                fk_id_area_produccion,
                fk_id_detalle_registro_monitoreo_insecto_roedor
            FROM verificaciones_areas_produccion_insectos_roedores
            WHERE fk_id_detalle_registro_monitoreo_insecto_roedor = %s
        """, (registro['id_detalle_registro_monitoreo_insecto_roedor'],))

        ids_areas = [verificacion['fk_id_area_produccion'] for verificacion in verificaciones]
        dict_registro = {
            "fecha": registro['fecha'],
            "hora": registro['hora'],
            "area_m_prima": 2 in ids_areas,
            "alm_p_terminado": 4 in ids_areas,
            "alm_proceso": 10 in ids_areas,
            "vestuarios": 11 in ids_areas,
            "lav_de_manos": 12 in ids_areas,
            "sshh": 7 in ids_areas,
            "oficinas": 8 in ids_areas,
            "pasadizos": 13 in ids_areas,
            "a_empaque": 14 in ids_areas,
            "a_lavado": 15 in ids_areas,
            "acciones_correctivas": registro['detalle_accion_correctiva']
        }
        info.append(dict_registro)

### REGISTRO Y MONITOREO DE ROEDORES
    """ Exampl info
    info [
            {
                "fecha": registros['fecha'],
                "hora": "09:05",
                "area_m_prima": True,
                "alm_p_terminado": False,
                "alm_proceso": "",
                "vestuarios": True,
                "sshh": True,
                "oficinas": True,
                "pasadizos": False,
                "a_empaque": True,
                "a_lavado": True,
                "acciones_correctivas": "Se volverá a revisar el almacen de productos terminados y pasadizos"
            },
        ]
    """

    # Generar Template
    logo_path = os.path.join('static', 'img', 'logo.png')
    logo_base64 = image_to_base64(logo_path)
    title_report = f"{cabecera[0]['nombreformato']}"

    # Establecer mes y año
    num_mes=datetime.strptime(registros[0]['fecha'], '%d/%m/%Y').month
    mes=MESES_BY_NUM[num_mes].upper()
    anio=datetime.strptime(registros[0]['fecha'], '%d/%m/%Y').year

    # Renderiza la plantilla
    template = render_template(
        "reports/reporte_registro_monitoreo_roedores.html",
        title_manual=POES,
        title_report=title_report,
        format_code_report=cabecera[0]['codigo'],
        frecuencia_registro=cabecera[0]['frecuencia'],
        logo_base64=logo_base64,
        mes=mes,
        anio=anio,
        info=info,
        fecha_periodo=get_ultimo_dia_laboral_del_mes()
    )

    file_name = f"{title_report.replace(' ', '-')}--{mes.strip().capitalize()}--{anio}--F"
    return generar_reporte(template, file_name, orientation='landscape')