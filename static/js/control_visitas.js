$(document).ready(function() {
    setDefaultFechaKardex();
});

function setDefaultFechaKardex() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('fechaVisita').value = today;
}

function registrarVisita() {
    // Obtener los valores de los elementos del formulario
    const fecha = document.getElementById('fechaVisita').value;
    const nom_apellido = document.getElementById('nom_apellido').value;
    const dni = document.getElementById('dni').value;
    const empresa = document.getElementById('empresa').value;
    const h_ingreso = document.getElementById('h_ingreso').value;
    const h_salida = document.getElementById('h_salida').value;

    // Obtener las evaluaciones seleccionadas
    const evaluacionesSeleccionadas = Array.from(
        document.querySelectorAll('input[name="evaluaciones"]:checked')
    ).map(checkbox => checkbox.value);

    const motivo_visita = document.getElementById('motivo_visita').value;
    const observaciones = document.getElementById('observaciones').value;

    // Crear el objeto con los datos del formulario
    const data = {
        fecha,
        nom_apellido,
        dni,
        empresa,
        h_ingreso,
        h_salida,
        evaluacionesSeleccionadas,
        motivo_visita,
        observaciones
    };

    // Enviar los datos usando fetch
    fetch('/control_visitas/registrar_visita', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                Swal.fire({
                    icon: 'success',
                    title: 'Registrado',
                    text: data.message,
                    showConfirmButton: false,
                    timer: 1500
                }).then(() => {
                    location.reload();
                });
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: data.message || 'Hubo un error al registrar la visita. Por favor, inténtelo nuevamente.',
                });
            }
        })
        .catch(error => {
            Swal.fire({
                icon: 'error',
                title: 'Error en la solicitud',
                text: 'Ocurrió un error al enviar la solicitud: ' + error.message,
            });
            console.error('Error en la solicitud:', error);
        });
}
