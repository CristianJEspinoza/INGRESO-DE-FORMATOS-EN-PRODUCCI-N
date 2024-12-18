import os
from flask import Blueprint, render_template, request, jsonify, send_file
from auth.auth import login_require
from connection.database import execute_query
from datetime import datetime
from .utils.constans import MESES_BY_NUM
from .utils.constans import BPM
from .utils.helpers import image_to_base64
from .utils.helpers import generar_reporte
from .utils.helpers import get_cabecera_formato_v2

proveedores = Blueprint('proveedores', __name__)

@proveedores.route('/')
@login_require
def index():
    try:
        # Obtener datos de proveedores
        proveedores = execute_query(
            """SELECT * FROM v_proveedores WHERE estado = 'CREADO'"""
        )
        
        # Obtener detalles de los productos ofrecidos
        detalles_productos_proveedores = execute_query(
            """SELECT * FROM v_detalles_productos_proveedores;"""
        )
        
        historial_proveedores = execute_query(
            """SELECT * FROM v_proveedores WHERE estado = 'CERRADO' ORDER BY anio DESC"""
        )
        
        return render_template('proveedores.html', 
                                proveedores=proveedores, 
                                detalles_productos_proveedores=detalles_productos_proveedores,
                                historial_proveedores=historial_proveedores)
    
    except Exception as e:
        print(f"Error al obtener datos: {e}")
        return render_template('proveedores.html')


#Para descargar el formato
@proveedores.route('/download_formato', methods=['GET'])
def download_formato():
    # Obtener el id del trabajador de los argumentos de la URL
    print("Reporte proveedores...")
    print(request.args)
    id_header_format = request.args.get('formato_id')

    cabecera = get_cabecera_formato_v2(id_header_format)

    # print('cabecera', cabecera)

    # Realizar la consulta para el detalle de todos los registros y controles de envasados finalizados
    registro = execute_query(
        f"""SELECT
                id_asignacion_proveedores,
                fk_id_proveedor,
                nom_empresa,
                departamento,
                distrito,
                provincia,
                celular,
                calle_pas_av,
                numero_calle,
                ruc_domicilio,
                correo_electronico,
                dni,
                ruc_representante,
                nombres,
                apellidos,
                cargo,
                status,
                comercial,
                industrial,
                tipo_empresa,
                fk_id_header_format,
                anio,
                estado
            FROM
            v_proveedores
        WHERE fk_id_header_format = {id_header_format};"""
    )

    # Consulta para obtener los detalles de productos por registro
    detalle_productos_por_registro = execute_query(
        f"""SELECT
                iddetalle_producto_proveedor,
                cantidad,
                frecuencia,
                producto_proveedor,
                fk_id_asignacion_header,
                id_header_format
            FROM public.v_detalles_productos_proveedores
            WHERE id_header_format = {id_header_format};"""
    )

    # Transformar `registro` en un diccionario (si es necesario)
    if isinstance(registro, list) and registro:
        registro = registro[0]  # Suponiendo que siempre obtienes un solo registro

    # Agregar detalle de productos al diccionario
    registro['detalle_productos'] = detalle_productos_por_registro

    # Construir el diccionario de información final
    info = {
        'nom_empresa': registro.get('nom_empresa', ''),
        'departamento': registro.get('departamento', '').strip(),
        'distrito': registro.get('distrito', '').strip(),
        'provincia': registro.get('provincia', '').strip(),
        'telefono': registro.get('telefono', ''),
        'calle_pas_av': registro.get('calle_pas_av', ''),
        'numero_calle': registro.get('numero_calle', ''),
        'ruc_domicilio': registro.get('ruc_domicilio', ''),
        'correo': registro.get('correo', ''),
        'representante': f"{registro.get('nombres', '')}  {registro.get('apellidos', '')}",
        'cargo': registro.get('cargo', ''),
        'dni': registro.get('dni', ''),
        'ruc_representante': registro.get('ruc_representante', ''),
        'comercial': registro.get('comercial', ''),
        'industrial': registro.get('industrial', ''),
        'tipo_empresa': registro.get('tipo_empresa', ''),
        'detalle_productos': registro.get('detalle_productos', [])
    }

    year=datetime.now().year
    month=datetime.now().month
    month_name = MESES_BY_NUM.get(int(month)).capitalize()
    # Extraer datos de la cabecera
    format_code=cabecera[0]['codigo']
    format_frequency=cabecera[0]['frecuencia']

    # Generar Template para reporte
    logo_path = os.path.join('static', 'img', 'logo.png')
    logo_base64 = image_to_base64(logo_path)
    title_report = cabecera[0]['nombreformato']

    # Renderiza la plantilla
    template = render_template(
        "reports/reporte_ficha_tecnica_proveedor.html",
        title_manual=BPM,
        title_report=title_report,
        format_code_report=format_code,
        frecuencia_registro=format_frequency,
        logo_base64=logo_base64,
        info=info
    )

    # Generar el nombre del archivo usando las variables de fecha
    file_name = f"{title_report.replace(' ', '-')}--{month_name}--{year}--F"
    return generar_reporte(template, file_name)


@proveedores.route('/download_formato_lista', methods=['GET'])
def download_formato_list():
    # DEPRECATED by unused
    # Obtener el id del trabajador de los argumentos de la URL
    print("Reporte lista proveedores...")
    print(request.args)
    id_header_format = request.args.get('formato_id')

    cabecera = get_cabecera_formato_v2(id_header_format)

    print('cabecera', cabecera)

    # Realizar la consulta para el detalle de todos los registros y controles de envasados finalizados
    # detalle_registros = execute_query(
    #     f"""SELECT
    #         resultado, observaciones, detalle_control, unidad, estado, fecha
    #     FROM v_detalles_monitoreos_calidad_agua WHERE id_header_format = {id_header_format} AND estado = 'CERRADO' ORDER BY fecha;"""
    # )

    detalle_registros = [{
            'producto': 'producto 1',
            'razon_social': 'razon social',
            'contacto': 'Contacto 1',
            'celular': '942568547',
            'correo': 'prov@gmail.com',
            'ruc': '20475896852',
            'direccion': 'direccion 1',
        }]
    # Extraer datos de la cabecera
    month=cabecera[0]['mes']
    month_name=MESES_BY_NUM.get(int(month)).capitalize()
    year=cabecera[0]['anio']
    format_code=cabecera[0]['codigo']
    format_frequency=cabecera[0]['frecuencia']

    # Generar Template para reporte
    logo_path = os.path.join('static', 'img', 'logo.png')
    logo_base64 = image_to_base64(logo_path)
    title_report = cabecera[0]['nombreformato']

    # Renderiza la plantilla
    template = render_template(
        "reports/reporte_lista_proveedores.html",
        title_manual=BPM,
        title_report=title_report,
        format_code_report=format_code,
        frecuencia_registro=format_frequency,
        logo_base64=logo_base64,
        info=detalle_registros
    )

    # Generar el nombre del archivo usando las variables de fecha
    file_name = f"{title_report.replace(' ', '-')}--{month_name}--{year}--F"
    return generar_reporte(template, file_name)