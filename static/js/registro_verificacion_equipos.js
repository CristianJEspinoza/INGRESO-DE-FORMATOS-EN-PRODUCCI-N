function cargarHistorialPorGrupo(idHeaderFormat) {
    const url = `/verificacion_calibracion_equipos/historial_por_grupo?id_header_format=${idHeaderFormat}`;

    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const tbody = document.getElementById(`tbody-historial-${idHeaderFormat}`);
            tbody.innerHTML = "";

            if (data.error) {
                tbody.innerHTML = `<tr><td colspan="7" class="text-center">${data.error}</td></tr>`;
                return;
            }

            data.forEach(row => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td class="text-center align-middle">${row.equipo}</td>
                    <td class="text-center align-middle">${row.fecha_mantenimiento}</td>
                    <td class="text-center align-middle">${row.fecha_prox_mantenimiento}</td>
                    <td class="text-center align-middle">${row.actividad_realizada}</td>
                    <td class="text-center align-middle">${row.observaciones}</td>
                    <td class="text-center align-middle">${row.responsable}</td>
                    <td class="text-center align-middle">${row.estado}</td>
                `;
                tbody.appendChild(tr);
            });
        })
        .catch(error => {
            console.error("Error al cargar historial:", error);
            const tbody = document.getElementById(`tbody-historial-${idHeaderFormat}`);
            tbody.innerHTML = `<tr><td colspan="7" class="text-center">Error: ${error.message}</td></tr>`;
        });
}

function filterByDate() {
    const mes = document.getElementById("filtrarMesLACLOSE").value;

    if (mes) {
        const [anio, mesNum] = mes.split("-");
        const meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"];
        const nombreMes = meses[parseInt(mesNum) - 1];

        // Redirigir a la misma ruta con los parámetros de mes y año
        window.location.href = `?mes=${nombreMes}&anio=${anio}`;
    }
}
