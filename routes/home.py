from flask import Blueprint, render_template, jsonify, request, send_file
import pandas as pd
from io import BytesIO
from auth.auth import login_require
from connection.database import execute_query

home = Blueprint('home', __name__)

@home.route('/', methods=['GET'])
@login_require
def principal():
    productos = execute_query("""SELECT 
                                    ROW_NUMBER() OVER (ORDER BY idproducto) AS contador,
                                    *
                                FROM productos
                                ORDER BY idproducto;""")
    
    # Asegurarse de que minimo_und sea numérico usando CAST
    min_product = execute_query("SELECT CAST(minimo_und AS INTEGER) AS minimo_und, fk_id_productos FROM public.min_max;")
    
    return render_template('home.html', productos=productos, min_product=min_product)


@home.route('/descargar_inventario', methods=['GET'])
def descargar_inventario():
    try:
        # Consulta para obtener los datos del inventario
        productos = execute_query("""SELECT 
                                        idproducto AS "ID Producto",
                                        descripcion_producto AS "Descripción",
                                        stock AS "Stock"
                                    FROM productos
                                    ORDER BY idproducto;""")
        
        # Crear un DataFrame a partir de los resultados
        df = pd.DataFrame(productos)

        # Generar el archivo Excel en memoria
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Escribir DataFrame en el archivo Excel
            df.to_excel(writer, index=False, startrow=2, sheet_name='Inventario')  # Ajuste: comenzamos en la fila 3

            # Obtener el libro y la hoja de trabajo
            workbook = writer.book
            worksheet = writer.sheets['Inventario']

            # Crear algunos formatos de celda
            bold = workbook.add_format({'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            cell_format = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
            header_format = workbook.add_format({
                'bold': True, 
                'border': 1, 
                'bg_color': '#FFC000',  # Fondo amarillo
                'align': 'center',
                'valign': 'vcenter'
            })
            title_format = workbook.add_format({
                'bold': True,
                'align': 'center',
                'valign': 'vcenter',
                'font_size': 14
            })

            # Fusionar celdas y agregar el título "INVENTARIO DE PRODUCTOS"
            worksheet.merge_range('A1:C1', 'INVENTARIO DE PRODUCTOS', title_format)  # Ajuste: fusionar columnas A-C en la fila 1

            # Aplicar formato a las cabeceras (primera fila de datos, que es la tercera fila en Excel)
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(2, col_num, value, header_format)  # Ajuste: la fila de cabecera es la tercera (índice 2)

            # Aplicar formato a las celdas del contenido
            for row_num in range(3, len(df) + 3):  # Ajuste: empezar desde la cuarta fila
                for col_num in range(len(df.columns)):
                    worksheet.write(row_num, col_num, df.iloc[row_num - 3, col_num], cell_format)

            # Ajustar automáticamente el ancho de las columnas según su contenido
            for col_num, column in enumerate(df.columns):
                max_length = max(df[column].astype(str).map(len).max(), len(column)) + 2
                worksheet.set_column(col_num, col_num, max_length)

        # Asegurarse de mover el puntero al inicio del archivo después de escribir
        output.seek(0)

        # Enviar el archivo Excel al cliente
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                            download_name='Inventario de productos.xlsx', as_attachment=True)
    except Exception as e:
        print(f"Error al descargar el inventario: {e}")
        return jsonify({'status': 'error', 'message': 'Error al descargar el inventario.'}), 500



@home.route('/update', methods=['POST'])
def update_product():
    try:
        # Obtener datos del formulario
        idProducto = request.form.get('idProducto')
        descripcion_producto = request.form.get('descripcion_producto')
        stock = request.form.get('stock')

        print(idProducto, descripcion_producto, stock)

        # Actualizar información del producto en la base de datos
        query_actualizar_producto = """ 
            UPDATE productos 
            SET descripcion_producto=%s, stock=%s
            WHERE idproducto=%s;
        """
        execute_query(query_actualizar_producto, (
            descripcion_producto, stock, idProducto
        ))

        # Siempre devolver una respuesta exitosa
        return jsonify({'status': 'success', 'message': 'Información del producto actualizada correctamente.'}), 200

    except Exception as e:
        print(f"Error al actualizar el producto: {e}")
        return jsonify({'status': 'error', 'message': 'Ocurrió un error al actualizar la información del producto.'}), 500
