import os
import datetime

from flask import Blueprint, render_template, request, jsonify
from auth.auth import login_require
from connection.database import execute_query
from .utils.constans import POES
from .utils.helpers import image_to_base64
from .utils.helpers import generar_reporte
from .utils.helpers import get_cabecera_formato_v2


controlCloroResidual = Blueprint('control_cloro_residual', __name__)

@controlCloroResidual.route('/', methods=['GET', 'POST'])
@login_require
def control_cloro_residual():
    if request.method == 'GET':
        try:
            # Obtener el formato creado con el id de formato 11
            formato_CCR = execute_query("SELECT * FROM public.headers_formats WHERE estado = 'CREADO' AND fk_idtipoformatos = 11")
            
            # Obtener el detalle del formato creado
            detalle_CCA = execute_query("""SELECT 
                                            fecha, 
                                            hora, 
                                            lectura, 
                                            observacion,
                                            idaccion_correctiva,
                                            detalle_accion_correctiva, 
                                            estado_accion_correctiva
                                            FROM v_detalles_controles_cloro_residual_agua 
                                            WHERE estado_formato = 'CREADO'
                                            ORDER BY fecha DESC""")
            
            detalles_formateados = []
            
            for detalle in detalle_CCA:
                # Asegúrate de que los valores son accesibles como diccionario
                detalle_formateado = {}
                
                # Formatear la fecha
                if 'fecha' in detalle and isinstance(detalle['fecha'], (datetime.date, datetime.datetime)):
                    detalle_formateado['fecha'] = detalle['fecha'].strftime('%d/%m/%Y')
                else:
                    detalle_formateado['fecha'] = detalle['fecha']  # Dejar como está si no es una fecha válida

                # Formatear la hora
                if 'hora' in detalle and isinstance(detalle['hora'], datetime.time):
                    detalle_formateado['hora'] = detalle['hora'].strftime('%H:%M:%S')
                else:
                    detalle_formateado['hora'] = detalle['hora']  # Dejar como está si no es una hora válida

                # Copiar los demás campos directamente
                detalle_formateado.update({
                    'lectura': detalle.get('lectura'),
                    'observacion': detalle.get('observacion'),
                    'idaccion_correctiva': detalle.get('idaccion_correctiva'),
                    'detalle_accion_correctiva': detalle.get('detalle_accion_correctiva'),
                    'estado_accion_correctiva': detalle.get('estado_accion_correctiva'),
                })
                
                detalles_formateados.append(detalle_formateado)
                
            #Paginación para el historial
            page = request.args.get('page', 1, type=int)
            per_page = 5
            offset = (page - 1) * per_page
            query_count = "SELECT COUNT(*) AS total FROM public.headers_formats WHERE estado = 'CERRADO' AND fk_idtipoformatos = 11"
            
            total_count = execute_query(query_count)[0]['total']
            total_pages = (total_count + per_page - 1) // per_page
            
            query_historialCCA = f"""
                                    SELECT 
                                        id_header_format,
                                        mes,
                                        anio
                                    FROM
                                    v_headers_formats
                                    WHERE fk_idtipoformatos = 11
                                    AND estado = 'CERRADO'
                                    LIMIT {per_page} OFFSET {offset}
                                """
            historial_CCA = execute_query(query_historialCCA)
            
            return render_template('control_cloro_residual_agua.html', 
                                    formato_CCR=formato_CCR, 
                                    detalle_CCA=detalles_formateados,
                                    historialCCA=historial_CCA,
                                    page=page,
                                    total_pages=total_pages)
        except Exception as e:
            print(f"Error al obtener datos: {e}")
            return render_template('control_cloro_residual_agua.html')
    
    elif request.method == 'POST':
        try:
            # Obtener datos del formulario
            fecha = request.form.get('fechaCCA')
            hora = request.form.get('horaCCA')
            lectura = str(request.form.get('lecturaCCA'))
            observacion = request.form.get('observacionCCA')
            accion_correctiva = request.form.get('acCCA')
            
            print(fecha, hora, lectura, observacion, accion_correctiva)

            # Verificar si hay un formato 'CREADO' para el tipo de formato 11
            formato_CCR = execute_query("SELECT id_header_format FROM public.headers_formats WHERE estado = 'CREADO' AND fk_idtipoformatos = 11")

            print(formato_CCR)
            
            if not formato_CCR or len(formato_CCR) == 0:
                return jsonify({'status': 'error', 'message': 'No se encontró un formato válido para registrar el control de cloro residual.'}), 400

            #Ingresar la acción correctiva
            if accion_correctiva:
                query_insertar_accion_correctiva = """
                        INSERT INTO acciones_correctivas(detalle_accion_correctiva, estado) 
                        VALUES (%s, %s) 
                        RETURNING idaccion_correctiva
                    """
                id_Accion_correctiva = execute_query(query_insertar_accion_correctiva, (accion_correctiva, 'PENDIENTE'))
            
            id_accion_correctiva = id_Accion_correctiva[0]['idaccion_correctiva'] if accion_correctiva else None
            
            observacion = observacion if observacion else None
            
            # Insertar control de cloro residual
            query_insertar_control = """ 
                INSERT INTO detalles_controles_cloro_residual_agua (fecha, hora, lectura, observacion, fk_id_accion_correctiva, fk_id_header_format) 
                VALUES (%s, %s, %s, %s, %s, %s);
            """
            execute_query(query_insertar_control, (fecha, hora, lectura, observacion, id_accion_correctiva, formato_CCR[0]['id_header_format']))

            return jsonify({'status': 'success', 'message': 'Control de cloro residual registrado.'}), 200

        except Exception as e:
            print(f"Error al procesar la solicitud POST: {e}")
            return jsonify({'status': 'error', 'message': 'Ocurrió un error al registrar el control de cloro residual.'}), 500

@controlCloroResidual.route('/historial', methods=['GET'])
def historial():
    try:
        # Paginación para el historial
        page = request.args.get('page', 1, type=int)
        per_page = 5
        offset = (page - 1) * per_page
        query_count = "SELECT COUNT(*) AS total FROM public.headers_formats WHERE estado = 'CERRADO' AND fk_idtipoformatos = 11"
        
        total_count = execute_query(query_count)[0]['total']
        total_pages = (total_count + per_page - 1) // per_page
        
        query_historialCCA = f"""
                                SELECT * FROM 
                                v_headers_formats
                                WHERE fk_idtipoformatos = 11
                                AND estado = 'CERRADO'
                                LIMIT {per_page} OFFSET {offset}
                            """
        historial_CCA = execute_query(query_historialCCA)

        return render_template('partials/historial_control_cloro_residual_agua.html', 
                                historialCCA=historial_CCA,
                                page=page,
                                total_pages=total_pages)
    except Exception as e:
        print(f"Error al obtener datos: {e}")
        return jsonify({"error": "Error al obtener datos"}), 500

@controlCloroResidual.route('/generar_formato_CCA', methods=['POST'])
def generar_formato_CCA():
    try:
        #Obtener la fecha actual
        fecha_actual = datetime.datetime.now()
        #Obtener el mes y el año
        mes = fecha_actual.month
        anio = fecha_actual.year
        
        #Generando un nuevo formato
        execute_query("INSERT INTO headers_formats (mes, anio, estado, fk_idtipoformatos) VALUES (%s,%s,%s,%s)", (mes, anio, 'CREADO', 11 ))
        return jsonify({'status': 'success', 'message': 'Se genero el formato.'}), 200
    except Exception as e:
        print(f"Error al generar formato: {e}")
        return jsonify({'error': 'Error al generar formato'}), 500
    
@controlCloroResidual.route('/obtener_detalle_CCA/<int:id_formatos>', methods=['GET'])
def obtener_detalle_CCA(id_formatos):
    try:
        # Ejecutar la consulta SQL para obtener los detalles
        query = "SELECT fecha, hora, lectura, observacion, detalle_accion_correctiva, estado_accion_correctiva FROM v_detalles_controles_cloro_residual_agua WHERE id_header_format = %s ORDER BY fecha"
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

    
#Modificar el estado de la acción correctiva
@controlCloroResidual.route('/modificar_estado_CCA/<int:id_ca>', methods=['POST'])
def estadoAC(id_ca):
    try:
        execute_query("UPDATE acciones_correctivas SET estado = %s WHERE idaccion_correctiva = %s", ('SOLUCIONADO', id_ca))
        return jsonify({'status': 'success', 'message': 'Se cambió el estado de esta acción correctiva.'}), 200
    except Exception as e:
        print(f"Error al modificar el estado de la acción correctiva: {e}")
        return jsonify({'status': 'error', 'message': 'No hay acción correctiva para validar.'}), 500
    
#PAra descargar el formato
@controlCloroResidual.route('/download_formato', methods=['GET'])
def download_formato():
    # Obtener el id del trabajador de los argumentos de la URL
    print(request.args)
    id_header_format = request.args.get('formato_id')

    cabecera = get_cabecera_formato_v2(id_header_format)

    print('cabecera', cabecera)

    # Realizar la consulta para el detalle de todos los registros y controles de envasados finalizados
    detalle_registros = execute_query(
        f"""SELECT
            fecha, hora, lectura, observacion, detalle_accion_correctiva, estado_accion_correctiva
        FROM v_detalles_controles_cloro_residual_agua WHERE id_header_format = {id_header_format} ORDER BY fecha;"""
    )

    # Extraer datos de la cabecera
    month=cabecera[0]['mes']
    year=cabecera[0]['anio']
    format_code=cabecera[0]['codigo']
    format_frequency=cabecera[0]['frecuencia']

    # Generar Template para reporte
    logo_path = os.path.join('static', 'img', 'logo.png')
    logo_base64 = image_to_base64(logo_path)
    title_report = cabecera[0]['nombreformato']

    # Renderiza la plantilla
    template = render_template(
        "reports/reporte_control_cloro_residual_agua.html",
        title_manual=POES,
        title_report=title_report,
        format_code_report=format_code,
        frecuencia_registro=format_frequency,
        logo_base64=logo_base64,
        info=detalle_registros
    )

    # Generar el nombre del archivo usando las variables de fecha
    file_name = f"{title_report.replace(' ', '-')}--{month}--{year}--F"
    return generar_reporte(template, file_name)


#Para finalizar el registro
@controlCloroResidual.route('/finalizar_registro_CCA', methods=['POST'])
def finalizar_registro_CCA():
    try:
        # Obtener el id del formato
        id_formato = execute_query("SELECT id_header_format FROM public.headers_formats WHERE estado = 'CREADO' AND fk_idtipoformatos = 11")[0]['id_header_format']

        # Actualizar el estado del formato a 'CERRADO'
        execute_query("UPDATE headers_formats SET estado = %s WHERE id_header_format = %s", ('CERRADO', id_formato))

        return jsonify({'status': 'success', 'message': 'Se finalizó el registro.'}), 200
    except Exception as e:
        print(f"Error al finalizar el registro: {e}")
        return jsonify({'status': 'error', 'message': 'No se pudo finalizar el registro.'}), 500