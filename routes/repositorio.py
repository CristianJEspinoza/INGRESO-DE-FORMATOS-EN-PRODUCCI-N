from flask import Blueprint, render_template, request, jsonify, send_file
from auth.auth import login_require
from connection.azure_storage import upload_file
from connection.Adls import Adls
from dotenv import load_dotenv
import os
import io
import qrcode
import fitz

load_dotenv()

# Instancia de la clase Adls para interactuar con Azure Blob Storage
adls = Adls(type=1, container=os.getenv('container'))

################### REPOSITORIO DE DOCUMENTOS DEL IFP ##########################

repositorioIFP = Blueprint('repositorio_IFP', __name__)

@repositorioIFP.route('/', methods=['GET'])
@login_require
def repositorio_IFP():
    try:
        return render_template('repositorio.html')
    except Exception as e:
        print(f"Error al obtener datos: {e}")
        return render_template('repositorio.html')

def generate_qr_code(url):
    """
    Genera un código QR a partir de una URL.
    """
    qr = qrcode.make(url)
    qr_bytes = io.BytesIO()
    qr.save(qr_bytes, format='PNG')
    qr_bytes.seek(0)
    return qr_bytes

def insert_qr_into_pdf(pdf_data, qr_image):
    """
    Inserta un código QR en todas las páginas de un PDF.
    """
    pdf_bytes = io.BytesIO(pdf_data)
    pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    # Iterar sobre todas las páginas del PDF
    for page in pdf_doc:
        # Tamaño y posición del QR en la página
        qr_rect = fitz.Rect(page.rect.width - 100, page.rect.height - 100, page.rect.width - 10, page.rect.height - 10)
        
        # Insertar la imagen del QR en la página actual
        page.insert_image(qr_rect, stream=qr_image.read())
        
        # Reiniciar el puntero de lectura del QR para la siguiente página
        qr_image.seek(0)
    
    # Guardar el PDF modificado en un BytesIO
    output_pdf = io.BytesIO()
    pdf_doc.save(output_pdf)
    pdf_doc.close()
    output_pdf.seek(0)
    
    return output_pdf.getvalue()

#Guardar los documentos PDF en Azure Storage
@repositorioIFP.route('/send_file_IFP', methods=['POST'])
def send_file_IFP():
    try:
        archivos = request.files.getlist('archivosPDF')
        
        if not archivos:
            return jsonify({'status': 'error', 'message': 'No se cargaron archivos'}), 400

        for file in archivos:
            if file and file.filename:
                file_data = file.read()
                
                if not file_data:
                    print(f"El archivo {file.filename} está vacío.")
                    continue

                # Usar el nombre original del archivo, asegurando que sea seguro para la URL
                file_name = file.filename.replace(" ", "_").strip()

                # Verificar que el nombre del archivo no esté vacío después de limpiar
                if not file_name:
                    print("El nombre del archivo es inválido.")
                    continue
                
                # Subir el archivo a Azure Storage
                upload_success = upload_file(file_data, file_name)

                # if not upload_success:
                #     return jsonify({'status': 'error', 'message': f'Error al subir el documento {file_name}'}), 500
                
                # # Generar la URL del archivo en Azure
                # download_url = adls.generate_sas_url(f"repositorio_IFP/{file_name}", expiration_days=30)
                
                # # Generar el código QR con la URL
                # qr_code_image = generate_qr_code(download_url)
                
                # # Insertar el código QR en todas las páginas del PDF
                # pdf_with_qr = insert_qr_into_pdf(file_data, qr_code_image)
                
                # # Subir el archivo modificado con el QR a Azure Storage
                # upload_success = upload_file(pdf_with_qr, file_name)
                
                if not upload_success:
                    return jsonify({'status': 'error', 'message': f'Error al subir el documento {file_name}'}), 500
        
        return jsonify({'status': 'success', 'message': 'Documentos guardados correctamente'}), 200

    except Exception as e:
        print(f"Error al procesar la solicitud: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Ocurrió un error al procesar los documentos'}), 500
    
@repositorioIFP.route('/list_files', methods=['GET'])
def list_files():
    mes = request.args.get('mes')
    anio = request.args.get('anio')
    
    
    
    try:
        files = adls.list_files_in_directory('repositorio_IFP/')
        
        # Filtrar y agrupar archivos por nombre de formato
        grouped_files = {}
        for file in files:
            # Extraer el nombre, mes y año del archivo
            file_name = file.replace('repositorio_IFP/', '')
            parts = file_name.split('--')
            
            if len(parts) < 3:
                continue

            nombre_formato = parts[0]
            file_mes = parts[1]
            file_anio = parts[2]

            # Filtrar por mes y año
            if mes and anio and (file_mes != mes or file_anio != anio):
                continue

            if nombre_formato not in grouped_files:
                grouped_files[nombre_formato] = []
            grouped_files[nombre_formato].append({'file_name': file_name})

        return jsonify({'status': 'success', 'files': grouped_files}), 200

    except Exception as e:
        print(f"Error al listar los documentos: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500



@repositorioIFP.route('/preview/<filename>', methods=['GET'])
def preview_file(filename):
    """
    Descargar un documento PDF desde Azure Blob Storage para previsualización.
    """
    try:
        # Construir la ruta completa del archivo en Azure Blob Storage
        file_path = f"repositorio_IFP/{filename}"
        print(f"Intentando descargar el archivo desde: {file_path}")

        # Descargar el archivo desde Azure Blob Storage
        file_data = adls.download(file_path)
        
        if not file_data:
            print(f"El archivo '{filename}' no se encontró en Azure Blob Storage.")
            return jsonify({'status': 'error', 'message': 'Documento no encontrado'}), 404
        
        # Devolver el archivo para previsualización
        return send_file(io.BytesIO(file_data), mimetype='application/pdf')
    
    except Exception as e:
        print(f"Error al obtener el documento: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Error al obtener el documento'}), 500

@repositorioIFP.route('/downloadFile/<filename>', methods=['GET'])
def downloadFile(filename):
    """
    Descargar un documento PDF desde Azure Blob Storage.
    """
    try:
        # Construir la ruta completa del archivo en Azure Blob Storage
        file_path = f"repositorio_IFP/{filename}"
        print(f"Intentando descargar el archivo desde: {file_path}")

        # Descargar el archivo desde Azure Blob Storage
        file_data = adls.download(file_path)
        
        if not file_data:
            print(f"El archivo '{filename}' no se encontró en Azure Blob Storage.")
            return jsonify({'status': 'error', 'message': 'Documento no encontrado'}), 404
        
        # Devolver el archivo para descarga directa
        return send_file(
            io.BytesIO(file_data),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        print(f"Error al obtener el documento: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Error al obtener el documento'}), 500