import os

from flask import Blueprint, render_template, request, jsonify, send_file
from connection.database import execute_query
from datetime import datetime
from datetime import time
from .utils.constans import BPM
from .utils.helpers import image_to_base64
from .utils.helpers import generar_reporte
from .utils.helpers import get_cabecera_formato


registro_monitoreo_insectos = Blueprint('registro_monitoreo_insectos', __name__)

@registro_monitoreo_insectos.route('/', methods=['GET'])
def registroMonitoreoInsectos():
    try:
        # Obtener las verificaciones en estado creado
        query_control_insectos = "SELECT * FROM v_registros_monitores_insectos_roedores WHERE estado = 'CREADO' AND fk_id_tipo_formatos = 9 ORDER BY id_registro_monitoreo_insecto_roedor DESC"
        formatos_creado = execute_query(query_control_insectos)

        # Obtener las verificaciones en estado CERRADO
        query_control_insectos_finalizados = "SELECT * FROM v_registros_monitores_insectos_roedores WHERE estado = 'CERRADO' AND fk_id_tipo_formatos = 9 ORDER BY id_registro_monitoreo_insecto_roedor DESC"
        formatos_finalizados = execute_query(query_control_insectos_finalizados)

        areas = execute_query("SELECT * FROM areas_produccion WHERE id_area_produccion IN (2, 4, 10, 11, 12, 7, 8, 13, 14, 15)")

        query_categorias_limpieza_desinfeccion = "SELECT * FROM public.categorias_limpieza_desinfeccion WHERE id_categorias_limpieza_desinfeccion IN (22, 23, 24, 25)"
        categorias_limpieza_desinfeccion = execute_query(query_categorias_limpieza_desinfeccion)

        # Obtener los registros
        query_registros = "SELECT * FROM v_detalles_registros_monitoreos_insectos_roedores WHERE estado = 'CREADO' AND fk_id_tipo_formatos = 9 ORDER BY id_detalle_registro_monitoreo_insecto_roedor DESC"
        resgistros_control_insecto = execute_query(query_registros)

        #obtener las asignaciones de las áreas que estan conforme o no conforme
        verificacion_araes_insectos = execute_query('SELECT fk_id_area_produccion, fk_id_detalle_registro_monitoreo_insecto_roedor FROM verificaciones_areas_produccion_insectos_roedores')

        return render_template('registro_monitoreo_insectos.html',
                               formatos_creado=formatos_creado,
                               areas=areas,
                               categorias_limpieza_desinfeccion=categorias_limpieza_desinfeccion,
                               resgistros_control_insecto=resgistros_control_insecto,
                               verificacion_araes_insectos=verificacion_araes_insectos,
                               formatos_finalizados=formatos_finalizados)
    except Exception as e:
        print(f"Error al obtener datos: {e}")
        return render_template('registro_monitoreo_insectos.html')

@registro_monitoreo_insectos.route('/generar_formato_monitoreo_insecto', methods=['POST'])
def generar_formato_monitoreo_insecto():
    try:
        fecha_actual = datetime.now()
        mes = str(fecha_actual.month)
        anio = str(fecha_actual.year)

        # Intentar ejecutar la consulta y ver si causa un error
        execute_query('INSERT INTO registros_monitores_insectos_roedores(mes, anio, estado, fk_idtipoformatos) VALUES (%s,%s,%s,%s)', (mes, anio, 'CREADO', 9))

        return jsonify({'status': 'success', 'message': 'Formato generado exitosamente.'}), 200

    except Exception as e:
        print(f"Error al generar el formato: {e}")
        return jsonify({'status': 'error', 'message': f'Hubo un error al generar el formato: {e}'}), 500

@registro_monitoreo_insectos.route('/ruta_para_guardar_monitoreo_insectos', methods=['POST'])
def ruta_para_guardar_monitoreo_insectos():
    try:
        data = request.json
        # Extracción de los datos del formulario
        fecha = data.get('fecha')
        hora = data.get('hora')
        areasSeleccionadas = data.get('areas')
        observaciones = data.get('observaciones') or "-"
        accionCorrectiva = data.get('accion_correctiva') or None

        # Validar que todos los datos requeridos estén presentes
        if not fecha or not hora or not areasSeleccionadas:
            return jsonify({'status': 'error', 'message': 'Datos incompletos: fecha, hora y áreas son obligatorios.'}), 400

        # Insertar la acción correctiva si existe
        id_accion_correctiva = None
        if accionCorrectiva:
            resultado_accion = execute_query(
                "INSERT INTO acciones_correctivas(detalle_accion_correctiva, estado) VALUES (%s, %s) RETURNING idaccion_correctiva", 
                (accionCorrectiva, 'PENDIENTE')
            )
            if resultado_accion and 'idaccion_correctiva' in resultado_accion[0]:
                id_accion_correctiva = resultado_accion[0]['idaccion_correctiva']

        # Obtener el ID del registro de monitoreo de insectos en estado "CREADO"
        id_registro_monitoreo_resultado = execute_query(
            "SELECT id_registro_monitoreo_insecto_roedor FROM registros_monitores_insectos_roedores WHERE estado = 'CREADO' AND fk_id_tipo_formatos = 9"
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

    
@registro_monitoreo_insectos.route('/estadoAC/<int:id_ca>', methods=['POST'])
def estadoAC(id_ca):
    try:
        execute_query("UPDATE acciones_correctivas SET estado = %s WHERE idaccion_correctiva = %s", ('SOLUCIONADO', id_ca))
        return jsonify({'status': 'success', 'message': 'Se cambió el estado de esta acción correctiva.'}), 200
    
    except Exception as e:
        print(f"Error al modificar el estado de la acción correctiva: {e}")
        return jsonify({'status': 'error', 'message': 'No hay acción correctiva para validar.'}), 500
    
@registro_monitoreo_insectos.route('/finalizar_monitoreo_insectos', methods=['POST'])
def finalizar_monitoreo_insectos():
    try:
        execute_query("UPDATE registros_monitores_insectos_roedores SET estado = %s WHERE estado = %s AND fk_id_tipo_formatos = 9", ('CERRADO', 'CREADO'))
        return jsonify({'status': 'success', 'message': 'Se cambió el estado de esta acción correctiva.'}), 200
    
    except Exception as e:
        print(f"Error al finalizar el registro de control de higiene personal: {e}")
        return jsonify({'status': 'error', 'message': 'Error al finalizar el registro de control de higiene personal.'}), 500