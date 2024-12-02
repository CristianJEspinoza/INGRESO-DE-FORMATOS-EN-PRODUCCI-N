from flask import Blueprint, render_template, request, jsonify, send_file
from auth.auth import login_require
from connection.database import execute_query
import psycopg2
import base64
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer, Frame, PageTemplate, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io


controlGeneral = Blueprint('control_general', __name__)

@controlGeneral.route('/', methods=['GET', 'POST'])
@login_require
def control_general():
    if request.method == 'GET':
        try:
            # Obtener a los trabajadores
            query_trabajador = """SELECT 
                                    c.idcontrolgeneral,
                                    t.idtrabajador, 
                                    t.dni, 
                                    t.nombres, 
                                    t.apellidos, 
                                    t.fecha_nacimiento, 
                                    t.direccion, 
                                    t.celular, 
                                    t.celular_emergencia, 
                                    t.fecha_ingreso,
                                    t.area, 
                                    t.cargo, 
                                    t.fk_idsexo, 
                                    cn.carnet_salud,
                                    t.estado_trabajador,
                                    t.status
                                FROM 
                                    trabajadores t 
                                JOIN 
                                    controles_generales_personal c ON t.idtrabajador = c.fk_idtrabajador
                                JOIN
                                    carnetsalud cn ON c.fk_idcarnetsalud = cn.idcarnetsalud
                                WHERE
                                    t.estado_trabajador = 'ACTIVO'
                                    """
            trabajadores = execute_query(query_trabajador)

            query_genero = "SELECT * FROM sexos"
            genero = execute_query(query_genero)

            # Convertir la imagen en Base64 para ser mostrada en el frontend
            for trabajador in trabajadores:
                if trabajador['carnet_salud']:
                    trabajador['carnet_salud'] = base64.b64encode(trabajador['carnet_salud']).decode('utf-8')

            return render_template('control_general_persona.html', trabajadores=trabajadores, genero=genero)
        except Exception as e:
            print(f"Error al obtener datos: {e}")
            return render_template('control_general_persona.html', trabajadores=[], genero=[]), 500


    elif request.method == 'POST':
        try:
            # Obtener datos del formulario
            dniTrabajador = request.form.get('dniTrabajador')
            nombresTrabajador = request.form.get('nombresTrabajador')
            apellidosTrabajador = request.form.get('apellidosTrabajador')
            fechaNacimiento = request.form.get('fechaNacimiento')
            direccionTrabajador = request.form.get('direccionTrabajador')
            celularTrabajador = request.form.get('celularTrabajador')
            celularEmergenciaTrabajador = request.form.get('celularEmergenciaTrabajador')
            fechaIngreso = request.form.get('fechaIngreso')
            areaTrabajador = request.form.get('areaTrabajador')
            cargoTrabajador = request.form.get('cargoTrabajador')
            genero_seleccionar = request.form.get('genero_seleccionar')

            # Manejo del archivo
            carnetSaludTrabajador = request.files.get('carnetSaludTrabajador')
            if not carnetSaludTrabajador:
                return jsonify({'status': 'error', 'message': 'El carnet de salud es obligatorio.'}), 400
            
            file_data = carnetSaludTrabajador.read()

            dni_creado = execute_query("SELECT dni FROM trabajadores WHERE dni = %s", (dniTrabajador,))
            if dni_creado and len(dni_creado) > 0:
                return jsonify({'status': 'error', 'message': 'El DNI ya existe.'}), 400
            else:
                # Insertar trabajador en la base de datos
                query_insertar_trabajador = """ 
                    INSERT INTO trabajadores (dni, nombres, apellidos, fecha_nacimiento, direccion, celular, 
                    celular_emergencia, fecha_ingreso, area, cargo, fk_idsexo, estado_trabajador) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING idtrabajador;
                """
                result = execute_query(query_insertar_trabajador, (
                    dniTrabajador, nombresTrabajador, apellidosTrabajador, fechaNacimiento,
                    direccionTrabajador, celularTrabajador, celularEmergenciaTrabajador, fechaIngreso,
                    areaTrabajador, cargoTrabajador, genero_seleccionar,'ACTIVO'
                ))

                if result and len(result) > 0:
                    idTrabajador = result[0]['idtrabajador']

                    # Insertar el carnet de salud y devolver el id generado
                    query_carnet_salud = """
                        INSERT INTO carnetsalud (carnet_salud) 
                        VALUES (%s) 
                        RETURNING idcarnetsalud;
                    """
                    
                    # Ejecutamos la consulta y obtenemos el id del nuevo carnet
                    idcarnet_result = execute_query(query_carnet_salud, (psycopg2.Binary(file_data),))
                    idcarnet = idcarnet_result[0]['idcarnetsalud']

                    # Insertar control general personal con el id del carnet y el id del trabajador
                    query_insertar_control = """ 
                        INSERT INTO controles_generales_personal (fk_idcarnetsalud, fk_idtrabajador, fk_idtipoformatos) 
                        VALUES (%s, %s, %s);
                    """
                    execute_query(query_insertar_control, (idcarnet, idTrabajador, 1))

                    return jsonify({'status': 'success', 'message': 'Trabajador registrado exitosamente.'}), 200
                else:
                    return jsonify({'status': 'error', 'message': 'Error al insertar el trabajador en la base de datos.'}), 500

        except Exception as e:
            print(f"Error al procesar la solicitud POST: {e}")
            return jsonify({'status': 'error', 'message': 'Ocurrió un error al procesar la solicitud.'}), 500

@controlGeneral.route('/toggle_status', methods=['POST'])
def toggle_status():
    data = request.get_json()
    trabajador_id = data.get('id')
    new_status = data.get('status')

    try:
        # Actualizar el estado del trabajador en la base de datos
        query_update_status = "UPDATE trabajadores SET status = %s WHERE idtrabajador = %s"
        execute_query(query_update_status, (new_status, trabajador_id))

        return jsonify({'status': 'success', 'message': 'Estado actualizado correctamente'}), 200
    except Exception as e:
        print(f"Error al actualizar el estado: {e}")
        return jsonify({'status': 'error', 'message': 'Ocurrió un error al actualizar el estado.'}), 500


@controlGeneral.route('/update', methods=['POST'])
def update_trabajador():
    try:
        # Obtener datos del formulario
        idTrabajador = request.form.get('idTrabajador')
        dniTrabajador = request.form.get('dniTrabajador')
        nombresTrabajador = request.form.get('nombresTrabajador')
        apellidosTrabajador = request.form.get('apellidosTrabajador')
        fechaNacimiento = request.form.get('fechaNacimiento')
        direccionTrabajador = request.form.get('direccionTrabajador')
        celularTrabajador = request.form.get('celularTrabajador')
        celularEmergenciaTrabajador = request.form.get('celularEmergenciaTrabajador')
        fechaIngreso = request.form.get('fechaIngreso')
        areaTrabajador = request.form.get('areaTrabajador')
        cargoTrabajador = request.form.get('cargoTrabajador')
        genero_seleccionar = request.form.get('genero_seleccionar')

        # Manejo del archivo
        carnetSaludTrabajador = request.files.get('carnetSaludTrabajador')
        file_data = None

        if carnetSaludTrabajador:
            file_data = carnetSaludTrabajador.read()

        # Actualizar información del trabajador en la base de datos
        query_actualizar_trabajador = """ 
            UPDATE trabajadores 
            SET dni=%s, nombres=%s, apellidos=%s, fecha_nacimiento=%s, direccion=%s, 
                celular=%s, celular_emergencia=%s, fecha_ingreso=%s, area=%s, cargo=%s, fk_idsexo=%s
            WHERE idtrabajador=%s;
        """
        execute_query(query_actualizar_trabajador, (
            dniTrabajador, nombresTrabajador, apellidosTrabajador, fechaNacimiento,
            direccionTrabajador, celularTrabajador, celularEmergenciaTrabajador, fechaIngreso,
            areaTrabajador, cargoTrabajador, genero_seleccionar, idTrabajador
        ))

        if file_data:
            # Actualizar el carnet de salud si se subió un nuevo archivo
            query_obtener_carnet = """ 
                SELECT fk_idcarnetsalud FROM controles_generales_personal WHERE fk_idtrabajador = %s
            """
            # Ejecuta la consulta y obtén la fila de resultados
            idCarnet_result = execute_query(query_obtener_carnet, (idTrabajador,))
            
            # Asegúrate de que se obtuvo un resultado y extrae el valor correcto
            if idCarnet_result and 'fk_idcarnetsalud' in idCarnet_result[0]:
                idCarnet = idCarnet_result[0]['fk_idcarnetsalud']

                # Actualizar el carnet de salud con el archivo subido
                query_actualizar_carnet = "UPDATE carnetsalud SET carnet_salud = %s WHERE idcarnetsalud = %s"
                execute_query(query_actualizar_carnet, (file_data, idCarnet))
            else:
                # Manejo si no se encuentra un carnet asociado
                return jsonify({'status': 'error', 'message': 'No se encontró un carnet de salud para el trabajador.'}), 404

        # Siempre devolver una respuesta exitosa
        return jsonify({'status': 'success', 'message': 'Información del trabajador actualizada correctamente.'}), 200

    except Exception as e:
        print(f"Error al actualizar el trabajador: {e}")
        return jsonify({'status': 'error', 'message': 'Ocurrió un error al actualizar la información del trabajador.'}), 500

    
@controlGeneral.route('/delete', methods=['POST'])
def delete_trabajador():
    try:
        data = request.json
        idTrabajador = data.get('idTrabajador')

        print(idTrabajador)

        # Eliminar el registro relacionado en controles_generales_personal
        query_eliminar_control = """
            UPDATE trabajadores SET estado_trabajador = %s WHERE idtrabajador = %s;
        """
        execute_query(query_eliminar_control, ('INACTIVO',idTrabajador,))
        
        return jsonify({'status': 'success', 'message': 'Registro eliminado.'}), 200

    except Exception as e:
        print(f"Error al eliminar el trabajador: {e}")
        return jsonify({'status': 'error', 'message': 'Hubo un error al eliminar el trabajador.'}), 500
    

def generar_pdf_formato_generales_personal(detalle_control_general):
    try:
        # Usar los datos del trabajador correctamente, asumiendo que 'trabajador' es un diccionario o RealDictRow
        nombre_trabajador = detalle_control_general['nombres']
        apellido_trabajador = detalle_control_general['apellidos']
        fecha_nacimiento_trabajador = detalle_control_general['fecha_nacimiento'].strftime('%d/%m/%Y')
        sexo_trabajador = 'Femenino' if detalle_control_general['fk_idsexo'] == 1 else 'Masculino' 
        direccion = detalle_control_general['direccion']
        celular = detalle_control_general['celular']
        celularEmergencia = detalle_control_general['celular_emergencia']
        dni = detalle_control_general['dni']
        fechaIngreso = detalle_control_general['fecha_ingreso'].strftime('%d/%m/%Y')
        area = detalle_control_general['area']
        cargo = detalle_control_general['cargo']
        carnet_salud_data = detalle_control_general['carnet_salud']

        # Crear un buffer en memoria
        pdf_buffer = io.BytesIO()

        # Configurar el documento PDF
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, topMargin=20)

        # Lista de elementos para el PDF
        elements = []

        # Estilos para el texto
        styles = getSampleStyleSheet()
        header_style = ParagraphStyle(
            'header_style',
            parent=styles['Title'],
            fontSize=16,
            spaceAfter=12,
            alignment=1  # Centrado
        )
        normal_style = ParagraphStyle(name='Normal', parent=styles['Normal'], fontSize=10)
        personal_text_style = ParagraphStyle(
            'personal_text_style',
            fontName='Helvetica-Bold',  # Fuente en negrita
            fontSize=14,                # Tamaño de fuente 16
            alignment=1,                # Centrado
            spaceAfter=10               # Espacio después del párrafo (opcional)
        )
        header_nombre_apellido_style = ParagraphStyle(
            'header_nombre_apellido_style',
            fontName='Helvetica-Bold',
            fontSize=10,
            alignment=0
        )


        # Encabezado
        header = [Paragraph("MANUAL DE BUENAS PRÁCTICAS DE MANUFACTURA", header_style)]
        table_header = [[header[0]]]

        # Información del encabezado
        table_header.append([
            Paragraph('CAPÍTULO V: FORMATOS', normal_style),
            Paragraph('CONTROL GENERAL DEL PERSONAL', normal_style)
        ])
        table_header.append([
            Paragraph('Edición: 01', normal_style),
            Paragraph('Revisión: 0', normal_style),
            Paragraph('Fecha de Aprobación: Febrero 2023', normal_style),
            Paragraph('Código: TI-BPM-F07-CGP', normal_style)
        ])

        # Definir la tabla y los estilos
        table = Table(table_header, colWidths=[1.3 * inch, 1 * inch, 2.5 * inch, 1.8 * inch])
        table.setStyle(TableStyle([
            ('SPAN', (0, 0), (-1, 0)),  
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('SPAN', (0, 1), (0, 1)),  
            ('SPAN', (1, 1), (-1, 1)),  
            ('ALIGN', (0, 1), (0, 1), 'LEFT'),  
            ('ALIGN', (1, 1), (-1, 1), 'CENTER'),  
            ('VALIGN', (1, 1), (-1, 1), 'MIDDLE'),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, 1), 12),
            ('BACKGROUND', (0, 1), (-1, 1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, 1), colors.black),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 8),
            ('ALIGN', (0, 2), (-1, 2), 'CENTER'),
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica'),
            ('FONTSIZE', (0, 2), (-1, 2), 10),
            ('BACKGROUND', (0, 2), (-1, 2), colors.white),
            ('TEXTCOLOR', (0, 2), (-1, 2), colors.black),
            ('BOTTOMPADDING', (0, 2), (-1, 2), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))

        # Cargar la imagen y ajustar el tamaño
        image_path = 'static/img/logo.png'  # Reemplaza con la ruta de tu imagen
        imagen = Image(image_path, width=1 * inch, height=0.5 * inch)

        # Crear una tabla con la imagen y la tabla de contenido
        combined_table = Table([[imagen, table]], colWidths=[1.2 * inch, 6.6 * inch])
        combined_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
            ('VALIGN', (1, 0), (1, 0), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))

        elements.append(combined_table)
        elements.append(Spacer(1, 6))

        # Crear y agregar tabla de datos del personal
        personal_text = Paragraph('1. DATOS DEL PERSONAL', personal_text_style)
        personal_table = Table([[personal_text]], colWidths=[7.8 * inch])
        personal_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'CENTER'), 
            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (0, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(personal_table)
        elements.append(Spacer(1, 6))

        # Crear tabla con nombres y apellidos
        header_nombre_apellido_table = [[
            Paragraph("NOMBRES:", header_nombre_apellido_style), 
            Paragraph("APELLIDOS:", header_nombre_apellido_style)
        ]]
        header_nombre_apellido_table.append([
            Paragraph(nombre_trabajador, normal_style),
            Paragraph(apellido_trabajador, normal_style)
        ])
        table_nombre_apellido = Table(header_nombre_apellido_table, colWidths=[3.9 * inch, 3.9 * inch])
        table_nombre_apellido.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(table_nombre_apellido)



        # Crear tabla con fecha de nacimiento y sexo 
        header_fecha_nacimiento_table = [[
            Paragraph("FECHA DE NACIMIENTO:", header_nombre_apellido_style), 
            Paragraph("SEXO:", header_nombre_apellido_style)
        ]]
        header_fecha_nacimiento_table.append([
            Paragraph(fecha_nacimiento_trabajador, normal_style),
            Paragraph(sexo_trabajador, normal_style)
        ])
        table_fecha_sexo = Table(header_fecha_nacimiento_table, colWidths=[3.9 * inch, 3.9 * inch])
        table_fecha_sexo.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(table_fecha_sexo)


        # Crear tabla con dirección, celular y celular de emergencia
        header_direc_telefono_table = [[
            Paragraph("DIRECCIÓN:", header_nombre_apellido_style), 
            Paragraph("TELEFONO/CELULAR:", header_nombre_apellido_style),
            Paragraph("CELULAR DE EMERGENCIA:", header_nombre_apellido_style)
        ]]
        header_direc_telefono_table.append([
            Paragraph(direccion, normal_style),
            Paragraph(celular, normal_style),
            Paragraph(celularEmergencia, normal_style)
        ])
        table_direc_telefono = Table(header_direc_telefono_table, colWidths=[3.9 * inch, 1.95 * inch, 1.95 * inch])
        table_direc_telefono.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(table_direc_telefono)


        # Crear tabla con dni y fecha de ingreso
        header_dni_fecha_ingreso_table = [[
            Paragraph("DNI:", header_nombre_apellido_style), 
            Paragraph("FECHA DE INGRESO:", header_nombre_apellido_style)
        ]]
        header_dni_fecha_ingreso_table.append([
            Paragraph(dni, normal_style),
            Paragraph(fechaIngreso, normal_style)
        ])
        table_dni_fecha_ingreso = Table(header_dni_fecha_ingreso_table, colWidths=[3.9 * inch, 3.9 * inch])
        table_dni_fecha_ingreso.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(table_dni_fecha_ingreso)

        # Crear tabla con area y cargo
        header_area_cargo_table = [[
            Paragraph("ÁREA:", header_nombre_apellido_style), 
            Paragraph("CARGO:", header_nombre_apellido_style)
        ]]
        header_area_cargo_table.append([
            Paragraph(area, normal_style),
            Paragraph(cargo, normal_style)
        ])
        table_area_cargo = Table(header_area_cargo_table, colWidths=[3.9 * inch, 3.9 * inch])
        table_area_cargo.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(table_area_cargo)

        # Agrupar la imagen y su marco con KeepTogether para evitar saltos de página
        carnet_section = []

        # Añadir un espacio antes de la imagen
        carnet_section.append(Spacer(1, 33))

        # Crear la sección del carnet de salud
        if carnet_salud_data:
            # Convertir los datos binarios en un flujo de bytes
            carnet_image_stream = io.BytesIO(carnet_salud_data)

            # Agregar la imagen al PDF usando el flujo de bytes directamente
            carnet_image_element = Image(carnet_image_stream, width=5 * inch, height=3 * inch)
            # Crear un marco alrededor de la imagen
            carnet_table = Table([[carnet_image_element]], colWidths=[5 * inch], rowHeights=[3 * inch])
            carnet_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            carnet_section.append(carnet_table)
        else:
            # Mostrar el marcador de posición si no hay carnet de salud
            carnet_placeholder = Table(
                [['Pegar Carnet de Salud Vigente']],
                colWidths=[5 * inch], rowHeights=[3 * inch]
            )
            carnet_placeholder.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            carnet_section.append(carnet_placeholder)

        # Añadir la sección agrupada con KeepTogether para evitar salto de página
        elements.append(KeepTogether(carnet_section))

        # Definir el pie de página
        def add_footer(canvas, doc):
            canvas.saveState()
            width, height = letter
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(colors.black)

            # Línea en el pie de página
            canvas.line(0.75 * inch, 0.75 * inch, width - 0.75 * inch, 0.75 * inch)

            # Texto en el pie de página
            footer_text = "Se prohíbe la reproducción total o parcial del presente documento sin la autorización de la GG"
            text_width = canvas.stringWidth(footer_text, 'Helvetica', 8)
            canvas.drawString((width - text_width) / 2, 0.5 * inch, footer_text)
            canvas.restoreState()

        # Agregar el template con el pie de página
        doc.addPageTemplates([
            PageTemplate(id='footer', frames=[
                Frame(
                    doc.leftMargin,
                    doc.bottomMargin + 1.5 * inch, 
                    doc.width, 
                    doc.height - 1.5 * inch, 
                    id='main'
                )
            ], onPage=add_footer)
        ])

        # Construir el PDF
        doc.build(elements)

        # Regresar el buffer del PDF
        pdf_buffer.seek(0)
        return pdf_buffer

    except Exception as e:
        print(f"Error al generar el PDF: {e}")
        return jsonify({'status': 'error', 'message': 'Error al generar el PDF.'}), 500

@controlGeneral.route('/download_formato', methods=['GET'])
def download_formato():
    # Obtener el id del trabajador de los argumentos de la URL
    trabajador_id = request.args.get('trabajador_id')

    # Realizar la consulta para obtener detalles del trabajador utilizando el ID
    detalle_trabajador = execute_query(f"SELECT * FROM trabajadores WHERE idtrabajador = {trabajador_id}")
    

    # Verificar si se obtuvieron resultados
    if not detalle_trabajador:
        return jsonify({'status': 'error', 'message': 'No se encontró el trabajador.'}), 404

    # Obtener el primer resultado de la lista de detalles del trabajador
    trabajador = detalle_trabajador[0]

    # Realizar la consulta para obtener el control general del trabajador
    detalle_control_general = execute_query(f"SELECT * FROM v_control_general_personal WHERE idtrabajador = {trabajador_id}")

    # Asegurarse de que se obtuvieron resultados y acceder correctamente a los datos
    if detalle_control_general:
        detalle_control_general = detalle_control_general[0]  # Acceder al primer elemento
    else:
        return jsonify({'status': 'error', 'message': 'No se encontró información de control general.'}), 404

    # Generar el PDF con la información del trabajador
    pdf_buffer = generar_pdf_formato_generales_personal(detalle_control_general)

    return send_file(pdf_buffer, as_attachment=True, download_name="Formato_Control_General_Personal.pdf", mimetype='application/pdf')

