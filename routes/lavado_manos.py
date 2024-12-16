import os

from flask import Blueprint, render_template, request, jsonify
from auth.auth import login_require
from connection.database import execute_query
from datetime import datetime
from collections import defaultdict
from .utils.constans import POES
from .utils.constans import MESES_BY_NUM
from .utils.helpers import image_to_base64
from .utils.helpers import generar_reporte
from .utils.helpers import get_cabecera_formato
from .utils.helpers import get_ultimo_dia_laboral_del_mes

########## PARA LAVADO_MANOS.HTML ###################################################################################

lavadoMano = Blueprint('lavado_Manos', __name__)

@lavadoMano.route('/', methods=['GET', 'POST'])
@login_require
def lavado_Manos():
    if request.method == 'GET':
        try:
            # Obtener los registros necesarios
            query_lavado_manos = """SELECT * 
                                    FROM v_lavados_manos 
                                    WHERE estado = 'CREADO' 
                                    ORDER BY fecha DESC, hora DESC;"""
            lavado_manos = execute_query(query_lavado_manos)

            query_trabajadores = "SELECT idtrabajador, CONCAT(nombres, ' ', apellidos) AS nombres FROM trabajadores WHERE estado_trabajador = 'ACTIVO'"
            trabajadores = execute_query(query_trabajadores)

            query_formatos = "SELECT estado FROM lavadosmanos WHERE fk_idtipoformatos = 2 AND estado = 'CREADO'"
            formatos = execute_query(query_formatos)
            
            # Paginación para el historial de lavado de manos
            page = request.args.get('page', 1, type=int)
            per_page = 5
            offset = (page - 1) * per_page
            query_count = "SELECT COUNT(*) AS total FROM public.lavadosmanos WHERE estado = 'CERRADO'"
            
            total_count = execute_query(query_count)[0]['total']
            total_pages = (total_count + per_page - 1) // per_page
            
            query_historialLavadoMano = f"SELECT * FROM v_historial_lavado_manos ORDER BY idlavadomano DESC LIMIT {per_page} OFFSET {offset}"
            historialLavadoMano = execute_query(query_historialLavadoMano)

            return render_template('lavado_manos.html', 
                                    formatos=formatos, 
                                    lavado_manos=lavado_manos, 
                                    trabajadores=trabajadores, 
                                    historialLavadoMano=historialLavadoMano,
                                    page=page,
                                    total_pages=total_pages
                                )
        except Exception as e:
            print(f"Error al obtener datos: {e}")
            return render_template('lavado_manos.html')

    elif request.method == 'POST':
        try:
            # Obtener datos del formulario
            fechaLavado = request.form.get('fechaLavado')
            horaLavado = request.form.get('horaLavado')
            selectTrabajador = request.form.get('selectTrabajador')

            # Verificar si hay un formato 'CREADO' para el tipo de formato 2
            query_formatos = "SELECT idlavadomano FROM lavadosmanos WHERE fk_idtipoformatos = 2 AND estado = 'CREADO'"
            formato = execute_query(query_formatos)

            if not formato:
                return jsonify({'status': 'error', 'message': 'No se encontró un formato válido para registrar el lavado de manos.'}), 400
            
            try:
                # Insertar lavado de manos
                query_insertar_trabajador = """ 
                    INSERT INTO detalle_lavados_manos (fecha, hora, fk_idtrabajador, fk_idlavadomano) 
                    VALUES (%s, %s, %s, %s);
                """
                execute_query(query_insertar_trabajador, (fechaLavado, horaLavado, selectTrabajador, formato[0]['idlavadomano']))
            except Exception as e:
                # Convertir el mensaje de error a string
                return jsonify({'status': 'error', 'message': str(e)}), 500
            
            return jsonify({'status': 'success', 'message': 'Lavado de manos registrado.'}), 200

        except Exception as e:
            print(f"Error al procesar la solicitud POST: {e}")
            return jsonify({'status': 'error', 'message': 'Ocurrió un error al registrar el lavado de manos.'}), 500


@lavadoMano.route('/historial', methods=['GET'])
def historial_lavado_manos():
    try:
        # Paginación para el historial de lavado de manos
        page = request.args.get('page', 1, type=int)
        per_page = 5
        offset = (page - 1) * per_page
        query_count = "SELECT COUNT(*) AS total FROM public.lavadosmanos"
        
        total_count = execute_query(query_count)[0]['total']
        total_pages = (total_count + per_page - 1) // per_page
        
        query_historialLavadoMano = f"SELECT * FROM v_historial_lavado_manos ORDER BY idlavadomano DESC LIMIT {per_page} OFFSET {offset}"
        historialLavadoMano = execute_query(query_historialLavadoMano)

        return render_template('partials/historial_lavado_manos.html', 
                                historialLavadoMano=historialLavadoMano,
                                page=page,
                                total_pages=total_pages)
    except Exception as e:
        print(f"Error al obtener datos: {e}")
        return jsonify({"error": "Error al obtener datos"}), 500


@lavadoMano.route('/generar_formato_lavado', methods=['POST'])
def generar_formato_lavado():
    try:
        fecha_actual = datetime.now()

        mes_actual = fecha_actual.month
        anio_actual = fecha_actual.year

        # Eliminar el registro relacionado en controles_generales_personal
        query_generar_formato = """
            INSERT INTO lavadosmanos(mes,anio,fk_idtipoformatos,estado) VALUES  (%s,%s,%s,%s);
        """
        execute_query(query_generar_formato, (mes_actual,anio_actual,2,'CREADO'))

        return jsonify({'status': 'success', 'message': 'Se genero el formato.'}), 200

    except Exception as e:
        print(f"Error al generar el formato: {e}")
        return jsonify({'status': 'error', 'message': 'Hubo un error al generar el formato.'}), 500
    
@lavadoMano.route('/finalizar_lavado_manos', methods=['POST'])
def finalizar_lavado_manos():
    try:
        # Consulta para obtener el id del formato en estado 'CREADO'
        query_formatos = "SELECT idlavadomano FROM lavadosmanos WHERE fk_idtipoformatos = 2 AND estado = 'CREADO'"
        formato = execute_query(query_formatos)

        # Verificar si se obtuvo un resultado
        if not formato or len(formato) == 0:
            return jsonify({'status': 'error', 'message': 'No se encontró un formato en estado "CREADO".'}), 400

        # Asegurarse de acceder correctamente al ID del formato
        id_formatos = formato[0][0] if isinstance(formato[0], (list, tuple)) else formato[0]['idlavadomano']

        # Actualizar el estado del formato a 'CERRADO'
        query_update_lavado = "UPDATE lavadosmanos SET estado = 'CERRADO' WHERE idlavadomano = %s"
        execute_query(query_update_lavado, (id_formatos,))

        return jsonify({'status': 'success', 'message': 'Se cerró el formato de lavado de manos.'}), 200

    except Exception as e:
        print(f"Error al generar el formato: {e}")
        return jsonify({'status': 'error', 'message': 'Hubo un error al generar el formato.'}), 500

@lavadoMano.route('/obtener_detalle_lavado/<int:id_formatos>', methods=['GET'])
def obtener_detalle_lavado(id_formatos):
    try:
        # Ejecutar la consulta SQL para obtener los detalles
        query = "SELECT * FROM v_lavados_manos WHERE idlavadomano = %s"
        detalles = execute_query(query, (id_formatos,))

        # Verificar si se encontraron resultados
        if not detalles:
            return jsonify({'status': 'error', 'message': 'No se encontraron detalles para el registro.'}), 404

        # Convertir los objetos datetime a string para JSON serialization
        for detalle in detalles:
            detalle['fecha'] = detalle['fecha'].strftime('%Y-%m-%d')  # Formato de fecha
            detalle['hora'] = detalle['hora'].strftime('%H:%M:%S')    # Formato de hora

        # Enviar los detalles de vuelta al frontend
        return jsonify({'status': 'success', 'detalles': detalles}), 200

    except Exception as e:
        print(f"Error al obtener los detalles: {e}")
        return jsonify({'status': 'error', 'message': 'Hubo un error al obtener los detalles.'}), 500

@lavadoMano.route('/registrar_medidas_correctivas', methods=['POST'])
def registrar_medidas_correctivas():
    try:
        data = request.get_json()
        medida_correctiva = data.get('medida_correctiva')
        fecha_actual = datetime.now()
        
        # Ejecuta la consulta para obtener el idlavadomano
        result = execute_query("SELECT idlavadomano FROM lavadosmanos WHERE estado = 'CREADO'")
        
        # Verifica si el resultado no está vacío y si es una lista
        if not result or len(result) == 0:
            return jsonify({'status': 'error', 'message': 'No hay lavados de manos con estado CREADO.'}), 404
        
        # Accede al primer registro de la lista
        idmano = result[0]['idlavadomano'] if isinstance(result[0], dict) else result[0]
        
        # Verifica que los parámetros necesarios estén presentes
        if not idmano or not medida_correctiva:
            return jsonify({'status': 'error', 'message': 'Faltan parámetros necesarios.'}), 400

        # Ejecutar la consulta SQL para insertar la medida correctiva
        query = "INSERT INTO medidascorrectivasobservaciones(detalledemedidacorrectiva, fecha, fk_idlavadomano) VALUES (%s, %s, %s)"
        execute_query(query, (medida_correctiva, fecha_actual, idmano))

        return jsonify({'status': 'success'}), 200

    except Exception as e:
        print(f"Error al registrar la medida correctiva: {e}")
        return jsonify({'status': 'error', 'message': 'Hubo un error.'}), 500


@lavadoMano.route('/download_formato', methods=['GET'])
def download_formato():

    # Obtener el id del trabajador de los argumentos de la URL
    formato_lavado_id = request.args.get('formato_id')

    # Obtener cabecera
    cabecera = get_cabecera_formato("lavadosmanos", formato_lavado_id)

    # Realizar la consulta para obtener el formato de lavado de mano que corresponda
    detalle_lavado_manos = execute_query(f"SELECT * FROM v_lavados_manos WHERE idlavadomano = {formato_lavado_id} ORDER BY fecha ASC")

    #Realizar una consulta para mostrar las medidas correctivas según corresponda
    medidas_correctivas = execute_query(f"SELECT * FROM medidascorrectivasobservaciones WHERE fk_idlavadomano = {formato_lavado_id}")

    # Estructura de diccionarios anidados
    agrupado_por_fecha = defaultdict(lambda: defaultdict(list))

    # Set fecha, mes y año
    fecha = detalle_lavado_manos[0]['fecha'].strftime("%d/%m/%Y")
    _fecha = datetime.strptime(fecha, '%d/%m/%Y')
    mes=MESES_BY_NUM[_fecha.month].capitalize()
    anio=_fecha.year

    # Rellenar el diccionario anidado con datos formateados
    for registro in detalle_lavado_manos:
        # Formatear la fecha como "DD/MM/YYYY"
        fecha_formateada = registro['fecha'].strftime("%d/%m/%Y")

        # Formatear la hora como "HH:MM"
        hora_formateada = registro['hora'].strftime("%H:%M")

        nombre = registro['nombre_formateado']

        # Agregar los datos formateados al diccionario
        agrupado_por_fecha[fecha_formateada][nombre].append(hora_formateada)
        
    # Ordenar las horas para cada trabajador en cada fecha
    for fecha, nombres in agrupado_por_fecha.items():
        for nombre in nombres:
            nombres[nombre].sort()  # Ordena la lista de horas en orden ascendente

    # Procesar las medidas correctivas
    medidas_correctivas_agrupadas = defaultdict(str)
    for medida in medidas_correctivas:
        fecha_formateada = medida['fecha'].strftime("%d/%m/%Y")
        detalle = medida['detalledemedidacorrectiva']

        # Si ya existe un detalle para esa fecha, agregarlo con una coma
        if medidas_correctivas_agrupadas[fecha_formateada]:
            medidas_correctivas_agrupadas[fecha_formateada] += ', ' + detalle
        else:
            medidas_correctivas_agrupadas[fecha_formateada] = detalle

    # Convertir defaultdict a diccionario regular (opcional)
    agrupado_por_fecha = {fecha: dict(nombres) for fecha, nombres in agrupado_por_fecha.items()}

    # Generar Template para reporte
    logo_path = os.path.join('static', 'img', 'logo.png')
    logo_base64 = image_to_base64(logo_path)

    """
    example
    info
        {
            '04/09/2024':
            {
                'Cristian E.': ['09:18'],
                'LIZBETH P.': ['09:18']
            },
            '03/09/2024':
            {
                'Cristian E.': ['09:18'],
                'LIZBETH P.': ['09:18', '10:19'],
                'Catherine P.': ['09:18', '09:19']
            },
        }
    medidas_correctivas
        {
            '04/09/2024': 'Descripcion de medida correctiva'
        }
    """
    template = render_template(
        "reports/reporte_lavado_de_manos.html",
        title_manual=POES,
        title_report=cabecera[0]['nombreformato'],
        format_code_report=cabecera[0]['codigo'], # "TI-POES-F03-RLM",
        frecuencia_registro=cabecera[0]['frecuencia'],
        logo_base64=logo_base64,
        info=agrupado_por_fecha,
        medidas_correctivas = medidas_correctivas_agrupadas,
        mes=mes,
        anio=anio,
        fecha_periodo=get_ultimo_dia_laboral_del_mes()
    )

    filename=f"REPORTE-DE-LAVADO-DE-MANOS--{mes}--{anio}--F"
    return generar_reporte(template, filename)

