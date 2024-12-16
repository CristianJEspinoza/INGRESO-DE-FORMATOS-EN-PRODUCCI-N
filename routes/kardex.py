import os
import io
import zipfile
from flask import Blueprint, render_template, request, jsonify, send_file
from auth.auth import login_require
from connection.database import execute_query
from datetime import datetime
from .utils.constans import BPM
from .utils.helpers import image_to_base64
from .utils.helpers import generar_reporte
from .utils.helpers import get_cabecera_formato
from .utils.helpers import get_ultimo_dia_laboral_del_mes

kardex = Blueprint('kardex', __name__)

@kardex.route('/', methods=['GET', 'POST'])
@login_require
def kardex_info():
    if request.method == 'GET':
        try:
            # Obtener a los trabajadores
            query_productos = "SELECT * FROM productos"
            productos = execute_query(query_productos)

            query_kardex = "SELECT * FROM v_kardex WHERE estado = 'CREADO'"
            v_kardex = execute_query(query_kardex)
            
            #Paginación
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
                        'idkardex', idkardex,
                        'mes', mes,
                        'anio', anio,
                        'estado', estado,
                        'descripcion_producto', descripcion_producto
                    )) AS registros
                FROM v_kardex
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
            v_kardex_cerrado = execute_query(query_la_finalizados)
            
            # Si no hay filtro de fecha, contar el total de páginas
            if not filter_mes and not filter_anio:
                query_count = """SELECT COUNT(*) AS total
                                FROM (SELECT DISTINCT mes, anio 
                                    FROM v_kardex 
                                    WHERE estado = 'CERRADO') AS distinct_months_years;"""
                total_count = execute_query(query_count)[0]['total']
                total_pages = (total_count + per_page - 1) // per_page
            else:
                total_pages = 1  # Solo una "página" si estamos en modo de filtro

            return render_template('kardex.html', 
                                    productos=productos, 
                                    v_kardex=v_kardex, 
                                    v_kardex_cerrado=v_kardex_cerrado,
                                    page=page,
                                    total_pages=total_pages)
        except Exception as e:
            print(f"Error al obtener datos: {e}")
            return render_template('kardex.html')
        
    elif request.method == 'POST':
        try:
            producto = request.form.get('selectProducto')
            fecha_actual = datetime.now()

            mes_actual = fecha_actual.month
            anio_actual = fecha_actual.year

            mes_consultar = str(mes_actual)
            anio_consultar = str(anio_actual)
            
            consult_product_kardex_month =  "SELECT * FROM kardex WHERE mes = %s AND anio = %s AND fk_idproducto = %s AND estado = 'CREADO'" 
            verificar_producto = execute_query(consult_product_kardex_month, (mes_consultar, anio_consultar, producto,))
            
            if not verificar_producto:
                query_crear_formato = """
                    INSERT INTO kardex(mes, anio, estado, fk_idproducto, fk_idtipoformatos)
                    VALUES (%s, %s, %s, %s, %s)
                """
                execute_query(query_crear_formato, (mes_actual, anio_actual, 'CREADO', producto, 3))

                return jsonify({'status': 'success', 'message': 'Kardex creado correctamente.'}), 200
            else:
                return jsonify({'status': 'error', 'message': 'El kardex para este producto ya existe para este mes.'}), 500
        except Exception as e:
            print(f"Error al crear el kardex: {e}")
            return jsonify({'status': 'error', 'message': 'Ocurrió un error al crear el kardex.'}), 500

@kardex.route('/get_stock', methods=['POST'])
def get_stock():
    try:
        # Obtener el JSON enviado desde el frontend
        data = request.get_json()
        
        # Asegurarse de que el idkardex esté presente en los datos
        if 'idkardex' not in data:
            return jsonify({'status': 'error', 'message': 'idkardex no proporcionado.'}), 400

        idkardex = data['idkardex']

        # Consulta para obtener el stock asociado al idkardex
        query_stock = """
            SELECT stock 
            FROM productos 
            WHERE idproducto = (
                SELECT fk_idproducto 
                FROM public.kardex 
                WHERE idkardex = %s
            )
        """
        result = execute_query(query_stock, (idkardex,))
        stock = result[0]['stock'] if result else 0

        query_lote = """ 
                    SELECT id_detalle_registro_controles_envasados, lote_asignado
                    FROM public.detalles_registros_controles_envasados
                    WHERE fk_idproducto = (
                        SELECT fk_idproducto 
                        FROM public.kardex 
                        WHERE idkardex = %s
                    )   
                    ORDER BY id_detalle_registro_controles_envasados DESC
                    LIMIT 4;
                    """
        lotes = execute_query(query_lote, (idkardex,))

        # Si hay lotes, seleccionar el más reciente (el primer resultado)
        if lotes:
            lote_mas_reciente = lotes[0]['lote_asignado']
            lista_lotes = [lote['lote_asignado'] for lote in lotes]
        else:
            lote_mas_reciente = None
            lista_lotes = []

        # Retornar el stock y los lotes en formato JSON
        return jsonify({
            'status': 'success',
            'stock': stock,
            'lote': lote_mas_reciente,  # El lote más reciente
            'lotes': lista_lotes  # Todos los lotes
        }), 200

    except Exception as e:
        print(f"Error al obtener el stock: {e}")
        return jsonify({'status': 'error', 'message': 'Ocurrió un error al obtener el stock.'}), 500


@kardex.route('/agregar_producto', methods = ['POST'])
def agregar_producto():
    try:
        detalle_producto = request.form.get('descripcionProducto')
        stock_producto = request.form.get('stockProducto')

        query_insert_product = "INSERT INTO productos (descripcion_producto,stock) VALUES (%s,%s)"
        execute_query(query_insert_product, (detalle_producto,stock_producto,))

        return jsonify({'status': 'success', 'message': 'Se registro el producto correctamente.'}), 200

    except Exception as e:
        print(f"Error al agregar un producto: {e}")
        return jsonify({'status': 'error', 'message': 'Ocurrió un error registrar el producto.'}), 500 
    
@kardex.route('/detalles_kardex/<int:id_kardex>', methods=['GET'])
def detalles_kardex(id_kardex):
    try:
        query_detalles = "SELECT * FROM detalle_kardex WHERE fk_idkardex = %s"
        detalles = execute_query(query_detalles, (id_kardex,))

        detalles_json = []
        for detalle in detalles:
            detalles_json.append({
                'fecha': detalle['fecha'],
                'lote': detalle['lote'],
                'saldo_inicial': detalle['saldo_inicial'],
                'salida': detalle['salida'],
                'saldo_final': detalle['saldo_final'],
                'observaciones': detalle['observaciones']
            })

        return jsonify(detalles_json), 200

    except Exception as e:
        print(f"Error al obtener los detalles del kardex: {e}")
        return jsonify({'status': 'error', 'message': 'Ocurrió un error al obtener los detalles del kardex.'}), 500

    
@kardex.route('/registrar_lote_kardex', methods=['POST'])
def registrar_lote_kardex():
    try:
        data = request.json
        # Extracción de los datos del formulario
        id_kardex = data['idkardex']
        fecha = data['fecha']
        ingreso = data['ingreso']
        lote = data['lote']
        saldo_inicial = data['saldo_inicial']
        salida = data['salida']
        observaciones = data['observaciones']

        # Validación de datos
        if not all([id_kardex, fecha, saldo_inicial]):
            return jsonify({'status': 'error', 'message': 'Todos los campos son obligatorios.'}), 400
        
        # Convertir a números si es necesario
        saldo_inicial = float(saldo_inicial)
        salida = float(salida)

        saldo_final = saldo_inicial + ingreso - salida

        if not observaciones:
            observaciones = "-"

        query_update_stock = "UPDATE productos SET stock = %s WHERE idproducto = (SELECT fk_idproducto FROM kardex WHERE idkardex = %s)"
        execute_query(query_update_stock, (saldo_final,id_kardex))

        if not ingreso:
            ingreso = 0

        query_insert_detalle_kardex = """
            INSERT INTO detalles_kardex 
            (fecha, lote, saldo_inicial, ingreso, salida, saldo_final, observaciones, fk_idkardex) 
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """
        
        execute_query(query_insert_detalle_kardex, (fecha, lote, saldo_inicial, ingreso, salida, saldo_final, observaciones, id_kardex))

        return jsonify({'status': 'success', 'message': 'Se registró el producto correctamente.'}), 200

    except Exception as e:
        print(f"Error al agregar detalle de kardex: {e}")
        return jsonify({'status': 'error', 'message': 'Ocurrió un error al registrar el producto.'}), 500
    
@kardex.route('/detalle_kardex_table/<int:id_kardex>', methods=['GET'])
def detalle_kardex_table(id_kardex):
    query_detalle_kardex = "SELECT * FROM detalles_kardex WHERE fk_idkardex = %s ORDER BY iddetallekardex DESC"
    detalle_kardex = execute_query(query_detalle_kardex, (id_kardex,))

    # Convertir la fecha al formato deseado antes de enviarlo al frontend
    detalles_formateados = []
    for detalle in detalle_kardex:
        detalle['fecha'] = detalle['fecha'].strftime('%d/%m/%Y')  # Formatear la fecha a DD/MM/YYYY
        detalles_formateados.append(detalle)

    return jsonify(detalles_formateados)


@kardex.route('/descargar_formato_kardex/<int:id_kardex>', methods=['GET'])
def descargar_formato_kardex(id_kardex):
    id_kardex = int(id_kardex)

    cabecera = get_cabecera_formato("kardex", id_kardex)

    # Consulta para obtener el kardex
    query_kardex = "SELECT * FROM v_kardex WHERE idkardex = %s"
    kardex = execute_query(query_kardex, (id_kardex,))

    # Consulta para obtener los detalles del kardex
    query_detalle_kardex = "SELECT * FROM detalles_kardex WHERE fk_idkardex = %s"
    detalle_kardex = execute_query(query_detalle_kardex, (id_kardex,))

    # Formatear la fecha en los detalles
    detalles_formateados = []
    for detalle in detalle_kardex:
        detalle['fecha'] = detalle['fecha'].strftime('%d/%m/%Y')  # Formato DD/MM/YYYY
        detalles_formateados.append(detalle)

    # Generar Template para reporte
    logo_path = os.path.join('static', 'img', 'logo.png')
    logo_base64 = image_to_base64(logo_path)
    title_report=cabecera[0]['nombreformato']

    # Renderiza la plantilla de Kardex
    template = render_template(
        "reports/reporte_kardex.html",
        title_manual=BPM,
        title_report=title_report,
        format_code_report=cabecera[0]['codigo'],
        frecuencia_registro=cabecera[0]['frecuencia'],
        logo_base64=logo_base64,
        info=detalles_formateados,
        kardex=kardex[0],
        fecha_periodo=get_ultimo_dia_laboral_del_mes()
    )

    file_name=f"{title_report}--{kardex[0]['mes']}--{kardex[0]['anio']}--{kardex[0]['descripcion_producto'].replace(' ', '-')}--F"
    return generar_reporte(template, file_name)


@kardex.route('/finalizar_kardex', methods=['POST'])
def finalizar_kardex():
    try:
        # Extracción de los datos del formulario
        data = request.json
        id_kardex = data['idKardex']

        query_update_estado_kardex = "UPDATE kardex SET estado = %s WHERE idkardex = %s"
        execute_query(query_update_estado_kardex,('CERRADO', id_kardex))
        return jsonify({'status': 'success', 'message': 'Se finalizo correctamente el Kardex'}), 200

    except Exception as e:
        print(f"Error al agregar detalle de kardex: {e}")
        return jsonify({'status': 'error', 'message': 'Ocurrió un error al registrar el producto.'}), 500
    
from datetime import datetime
from flask import jsonify

@kardex.route('/agregar_todos_productos_kardex', methods=['POST'])
def agregar_todos_productos_kardex():
    try:
        productos = execute_query("SELECT idproducto, descripcion_producto FROM productos")
        fecha_actual = datetime.now()

        registrados_correctamente = []
        list_productos_registrados = []

        mes_actual = str(fecha_actual.month)
        anio_actual = str(fecha_actual.year)

        # Consulta para verificar si ya existen registros en el kardex para el mes actual
        consult_product_kardex_month = """
            SELECT fk_idproducto 
            FROM kardex 
            WHERE mes = %s AND anio = %s AND estado = 'CREADO'
        """
        productos_registrados = execute_query(consult_product_kardex_month, (mes_actual, anio_actual))
        productos_registrados_ids = {p['fk_idproducto'] for p in productos_registrados}

        # Insertar solo los productos que no están registrados
        for p in productos:
            product_id = p['idproducto']
            descripcion_producto = p['descripcion_producto']

            if product_id not in productos_registrados_ids:
                query_crear_formato = """
                    INSERT INTO kardex(mes, anio, estado, fk_idproducto, fk_idtipoformatos)
                    VALUES (%s, %s, %s, %s, %s)
                """
                execute_query(query_crear_formato, (mes_actual, anio_actual, 'CREADO', product_id, 3))
                registrados_correctamente.append(descripcion_producto)
            else:
                list_productos_registrados.append(descripcion_producto)

        # Crear respuesta con productos registrados y ya existentes
        return jsonify({
            'status': 'success',
            'message': 'Proceso completado.',
            'productos_registrados': list_productos_registrados,
            'productos_nuevos': registrados_correctamente
        }), 200

    except Exception as e:
        print(f"Error al crear el kardex: {e}")
        return jsonify({'status': 'error', 'message': 'Ocurrió un error al crear el kardex.'}), 500

@kardex.route('/finalizar_todos_productos_kardex', methods=['POST'])
def finalizar_todos_productos_kardex():
    try:
        kardex_creados = execute_query("SELECT idkardex FROM kardex WHERE estado = 'CREADO'")
        for k in kardex_creados:
            execute_query("UPDATE kardex SET estado = 'CERRADO' WHERE idkardex = %s", (k['idkardex'], ))
        return jsonify({'status': 'success', 'message': 'Se finalizaron todos los Kardex'}), 200
    except Exception as e:
        print(f"Error al finalizar el kardex: {e}")
        return jsonify({'status': 'error', 'message': 'Ocurrió un error al finalizar el kardex.'}), 500

@kardex.route('/download_formats', methods=['GET'])
def download_formats():
    try:
        # Obtenemos el mes y año
        mes = request.args.get('mes')
        anio = request.args.get('anio')
        
        # Obtenemos el id_kardex de todos los formatos del mes y año que se quieren descargar
        id_kardex_return = execute_query(f"SELECT idkardex FROM v_kardex WHERE mes = '{mes}' AND anio = '{anio}'")
        
        # Lista para almacenar los PDFs generados temporalmente
        pdf_files = []
        
        # Recorremos cada id_kardex encontrado
        for id in id_kardex_return:
            id_kardex = int(id['idkardex'])
            
            # Obtenemos la cabecera y detalles
            cabecera = get_cabecera_formato("kardex", id_kardex)
            query_kardex = "SELECT * FROM v_kardex WHERE idkardex = %s"
            kardex = execute_query(query_kardex, (id_kardex,))
            query_detalle_kardex = "SELECT * FROM detalles_kardex WHERE fk_idkardex = %s"
            detalle_kardex = execute_query(query_detalle_kardex, (id_kardex,))
            
            # Formateamos la fecha en los detalles
            detalles_formateados = []
            for detalle in detalle_kardex:
                detalle['fecha'] = detalle['fecha'].strftime('%d/%m/%Y')
                detalles_formateados.append(detalle)
            
            # Renderizamos la plantilla HTML
            logo_path = os.path.join('static', 'img', 'logo.png')
            logo_base64 = image_to_base64(logo_path)
            title_report = cabecera[0]['nombreformato']
            template = render_template(
                "reports/reporte_kardex.html",
                title_manual=BPM,
                title_report=title_report,
                format_code_report=cabecera[0]['codigo'],
                frecuencia_registro=cabecera[0]['frecuencia'],
                logo_base64=logo_base64,
                info=detalles_formateados,
                kardex=kardex[0],
                fecha_periodo=get_ultimo_dia_laboral_del_mes()
            )
            
            # Generamos el PDF usando la función generar_reporte
            file_name=f"{title_report}--{kardex[0]['mes']}--{kardex[0]['anio']}--{kardex[0]['descripcion_producto'].replace(' ', '-')}--F.pdf"
            pdf_response = generar_reporte(template, file_name)
            
            # Extraemos el contenido del PDF de la respuesta
            pdf_content = pdf_response.get_data()
            pdf_files.append((file_name, pdf_content))
        
        # Crear un archivo ZIP en memoria
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_name, pdf_data in pdf_files:
                zip_file.writestr(file_name, pdf_data)
        
        # Preparar el archivo ZIP para su descarga
        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype="application/zip",
            as_attachment=True,
            download_name=f"Kardex_{mes}_{anio}.zip"
        )

    except Exception as e:
        print(f"Error al obtener los kardex: {e}")
        return jsonify({'status': 'error', 'message': 'Ocurrió un error al obtener los kardex.'}), 500