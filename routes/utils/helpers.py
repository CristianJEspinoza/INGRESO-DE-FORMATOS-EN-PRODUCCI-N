import base64
import pdfkit
import calendar
import shutil

from flask import make_response
from connection.database import execute_query
from datetime import datetime, timedelta


def get_cabecera_formato(tabla: str, id_formato: str) -> list:
    """
    Función para obtener la cabecera de un formato dado.

    :param tabla: Nombre de la tabla específica ('lavadosmanos', 'kardex', etc.)
    :param id_formato: Identificador del formato (e.g., idlavadomano, idkardex)
    :return: Resultado de la consulta de la cabecera
    """
    # Mapeo de tablas a sus respectivos IDs
    id_column_map = {
        'lavadosmanos': 'idlavadomano',
        'kardex': 'idkardex',
        'condiciones_ambientales': 'idcondicionambiental',
        'registros_controles_envasados': 'id_registro_control_envasados',
        'controles_higiene_personal': 'id_control_higiene_personal',
        'verificacion_limpieza_desinfeccion_areas': 'id_verificacion_limpieza_desinfeccion_area',
        'verificaciones_equipos_medicion': 'id_verificacion_equipo_medicion',
        'registros_monitores_insectos_roedores': 'id_registro_monitoreo_insecto_roedor'
        # Agrega más mapeos según sea necesario para otros formatos
    }

    # Verificar si la tabla tiene un ID mapeado
    if tabla not in id_column_map:
        raise ValueError(
            f"Tabla '{tabla}' no está configurada correctamente en el mapeo de IDs.")

    # Construir la consulta SQL para la cabecera
    # cabecera = execute_query(f"SELECT tf.idtipoformato, tf.nombreformato, tf.frecuencia, tf.codigo, lm.idlavadomano
    #                            FROM tiposformatos tf
    #                            INNER JOIN lavadosmanos lm ON tf.idtipoformato=lm.fk_idtipoformatos
    #                            WHERE idlavadomano={formato_lavado_id}")
    id_column = id_column_map[tabla]
    query = f"""
        SELECT tf.idtipoformato, tf.nombreformato, tf.frecuencia, tf.codigo, {tabla}.{id_column}
        FROM tiposformatos tf
        INNER JOIN {tabla} ON tf.idtipoformato = {tabla}.fk_idtipoformatos
        WHERE {id_column} = %s
    """

    # Ejecutar la consulta y devolver el resultado
    return execute_query(query, (id_formato,))


def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def generar_reporte(template, filename_report='Reporte_sin_nombre', orientation='portrait'):
    """
    Genera un reporte en formato PDF a partir de una plantilla HTML.

    Args:
        template (str): El contenido HTML de la plantilla a renderizar.
        orientation (str): La orientación del PDF ('portrait' para vertical, 'landscape' para horizontal).

    Returns:
        Flask Response: Una respuesta HTTP con el contenido del PDF generado.
    """
    try:

        # Configuración de pdfkit con la ruta del ejecutable wkhtmltopdf WINDOWS
        wkhtmltopdf_path = "tools/wkhtmltox/bin/wkhtmltopdf.exe"

        # Detecta automáticamente la ruta de wkhtmltopdf en docker
        wkhtmltopdf_path = shutil.which("wkhtmltopdf")

        if wkhtmltopdf_path is None:
            raise FileNotFoundError("No se encontró wkhtmltopdf en el sistema.")

        # Definir opciones para la generación del PDF
        options = {
            'page-size': 'A4',
            'margin-top': '0.4cm',
            'margin-right': '0.4cm',
            'margin-bottom': '1cm',
            'margin-left': '0.4cm',
            'encoding': 'UTF-8',
            'enable-local-file-access': None,
            'orientation': 'landscape' if orientation.lower() == 'landscape' else 'portrait'
        }

        # Configuración de pdfkit con la ruta detectada
        config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

        # Generar el PDF en memoria desde la cadena HTML de la plantilla
        pdf_content = pdfkit.from_string(
            template, False, configuration=config, options=options)

        # Crear la respuesta HTTP con el contenido PDF
        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename={filename_report}.pdf'
        return response
    except Exception as e:
        print(f"Error al generar el reporte: {e}")
        return make_response("Error al generar el reporte.", 500)


def get_ultimo_dia_laboral_del_mes(mes=None, año=None):
    ''' return 30/07/2024 '''
    # Si no se proporciona mes ni año, se toma el mes y año actual
    hoy = datetime.today()
    if mes is None:
        mes = hoy.month
    if año is None:
        año = hoy.year

    # Obtener el último día del mes
    ultimo_dia_mes = calendar.monthrange(año, mes)[1]
    fecha_ultimo_dia = datetime(año, mes, ultimo_dia_mes)

    # Verificar si es domingo
    while fecha_ultimo_dia.weekday() == 6:  # 6 significa domingo
        fecha_ultimo_dia -= timedelta(days=1)

    # Formatear la fecha como dd/mm/yyyy
    return fecha_ultimo_dia.strftime("%d/%m/%Y")

