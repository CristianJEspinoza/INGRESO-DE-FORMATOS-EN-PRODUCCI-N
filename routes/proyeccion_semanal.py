from flask import Blueprint, render_template, request, jsonify
from auth.auth import login_require
from connection.database import execute_query
from datetime import datetime, timedelta
from math import ceil

proyeccionsemanal = Blueprint('proyeccion_semanal', __name__)

@proyeccionsemanal.route('/', methods=['GET'])
@login_require
def proyeccion_semanal():
    proyeccion = execute_query("""SELECT * 
                                    FROM v_proyeccion_semanal 
                                    WHERE estado = 'CREADO' 
                                    ORDER BY idproyeccion DESC""") or []
    
    productos = execute_query("SELECT * FROM productos ORDER BY idproducto")

    # Parámetros de paginación
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    
    #contruimos la consulta para obtener los registros finalizados
    query_finalizados = f"""
                    SELECT * FROM v_proyeccion_semanal
                    WHERE estado = 'CERRADO'
                    ORDER BY idproyeccion DESC
                    LIMIT {per_page} OFFSET {offset}
                    """
    proyectEndDetalles = execute_query(query_finalizados) or []
    
    # Contar el total de proyecciones finalizadas
    query_count = "SELECT COUNT(*) AS total FROM v_proyeccion_semanal WHERE estado = 'CERRADO'"
    total_count = execute_query(query_count)[0]['total']
    total_pages = (total_count + per_page - 1) // per_page

    # Obtener los detalles correspondientes para las proyecciones en esta página

    return render_template(
        'proyeccion_semanal.html',
        proyeccion=proyeccion,
        productos=productos,
        proyectEndDetalles=proyectEndDetalles,
        page=page,
        total_pages=total_pages
    )


def obtener_dias_semana():
    fecha_actual = datetime.now()

    # Calcular el lunes de la semana actual
    inicio_semana = fecha_actual - timedelta(days=fecha_actual.weekday())

    # Crear una lista con las fechas de lunes a domingo
    fechas_semana = [(inicio_semana + timedelta(days=i)).date() for i in range(6)]

    return fechas_semana


@proyeccionsemanal.route('/quitar_proyeccion/<int:idproyeccion>', methods=['POST'])
def quitar_proyeccion(idproyeccion):
    try:
        print(f"Proyección a eliminar: {idproyeccion}")
        
        # Ejecutar la consulta para eliminar la proyección
        execute_query("DELETE FROM proyeccion_semanal WHERE idproyeccion = %s", (idproyeccion,))

        return jsonify({'status': 'success', 'message': 'Proyección eliminada correctamente'}), 200
    
    except Exception as e:
        print(f"Error al quitar la proyección: {e}")
        return jsonify({'status': 'error', 'message': 'Hubo un error al eliminar la proyección'}), 500

@proyeccionsemanal.route('/AgregarProducto', methods=['POST'])
def AgregarProducto():
    try:
        # Obtener el valor de 'selectProducto' desde el cuerpo de la solicitud
        data = request.get_json()
        idproducto = data.get('selectProducto')

        if not idproducto:
            return jsonify({'status': 'error', 'message': 'No se seleccionó ningún producto.'}), 400

        # Obtener el stock del producto
        stock_Extract = execute_query("SELECT stock FROM productos WHERE idproducto = %s", (idproducto,))
        stock = int(stock_Extract[0]['stock'])

        # Obtener el máximo por producto
        maximo_und = execute_query("SELECT maximo_und FROM min_max WHERE fk_id_productos = %s", (idproducto,))
        
        if maximo_und:
            maximo_und = int(maximo_und[0]['maximo_und'])
            proyeccion = max(maximo_und - stock, 0)  # Establecer en 0 si la proyección es negativa
        else:
            proyeccion = 0

        # Verificar si el producto ya tiene una proyección en `proyeccion_semanal` para el `id_proyeccion` actual
        producto_existente = execute_query(
            "SELECT 1 FROM proyeccion_semanal WHERE fk_id_productos = %s AND estado = %s",
            (idproducto, 'CREADO')
        )

        if producto_existente:
            return jsonify({'status': 'error', 'message': 'El producto ya existe en la proyección semanal.'}), 400

        # Insertar la proyección en la base de datos si no existe
        execute_query(
            "INSERT INTO proyeccion_semanal(proyeccion, fk_id_productos, estado) VALUES (%s, %s, %s);",
            (proyeccion, idproducto, 'CREADO')
        )

        return jsonify({'status': 'success', 'message': 'Proyección agregada correctamente'}), 200

    except Exception as e:
        print(f"Error al agregar el producto a la proyección: {e}")
        return jsonify({'status': 'error', 'message': 'Hubo un error al agregar el producto a la proyección'}), 500

@proyeccionsemanal.route('/guardar_proyeccion', methods=['POST'])
def guardar_proyeccion():
    try:
        cambios = request.get_json()

        for cambio in cambios:
            if cambio['inicioFecha'] and cambio['finFecha']:
                print(cambio['inicioFecha'], cambio['finFecha'])
                query = """
                    UPDATE proyeccion_semanal
                    SET proyeccion = %s, inicio_date = %s, fin_date = %s
                    WHERE idproyeccion = %s
                """
                params = (cambio['proyeccion_register'], cambio['inicioFecha'], cambio['finFecha'], cambio['idproyeccion'])
                execute_query(query, params)

        return jsonify({'status': 'success', 'message': 'Proyección guardada correctamente'}), 200

    except Exception as e:
        print(f"Error al guardar la proyección: {e}")
        return jsonify({'status': 'error', 'message': 'Hubo un error al guardar la proyección'}), 500


@proyeccionsemanal.route('/register_observation/<int:idproyeccion>', methods=['POST'])
def register_observation(idproyeccion):
    try:
        data = request.get_json()
        observacion = data.get('observacion')
        
        # Ejecutar la consulta para registrar una observación
        execute_query("UPDATE proyeccion_semanal SET observacion = %s WHERE idproyeccion = %s", (observacion, idproyeccion)) 

        return jsonify({'status': 'success', 'message': 'Observación registrada'}), 200
    
    except Exception as e:
        print(f"Error al quitar la proyección: {e}")
        return jsonify({'status': 'error', 'message': 'Hubo un error al registrar la observacion'}), 500