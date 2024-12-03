from flask import Blueprint, render_template, request, jsonify
from auth.auth import login_require
from connection.database import execute_query

minmax = Blueprint('min_max', __name__)

@minmax.route('/', methods=['GET'])
@login_require
def min_max():
    min_max = execute_query("SELECT * FROM v_min_max ORDER BY id_min_max")
    return render_template('min_max.html', min_max=min_max)

@minmax.route('/guardar_cambios', methods=['POST'])
def guardar_cambios():
    try:
        # Obtener los datos enviados desde el frontend
        cambios = request.get_json()

        # Actualizar cada fila en la tabla min_max
        for cambio in cambios:
            query = """
                UPDATE min_max
                SET minimo_und = %s, maximo_und = %s, conversion_und = %s, equivalencia = %s, unidad_equivalencia = %s, unidades_por_equivalencia = %s
                WHERE id_min_max = %s
            """
            params = (cambio['minimo_und'], cambio['maximo_und'], cambio['conversion_und'], cambio['equivalencia'], cambio['unidad_equivalencia'], cambio['unidades_por_equivalencia'] ,cambio['id_min_max'])
            execute_query(query, params)

        return jsonify({'status': 'success', 'message': 'Cambios guardados correctamente'}), 200

    except Exception as e:
        print(f"Error al guardar los cambios: {e}")
        return jsonify({'status': 'error', 'message': 'Hubo un error al guardar los cambios'}), 500

