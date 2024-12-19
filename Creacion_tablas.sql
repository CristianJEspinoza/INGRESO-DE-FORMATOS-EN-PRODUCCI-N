-- Definición de las tablas

-- << Trabajadores >> --
-- Tabla para los sexos
CREATE TABLE IF NOT EXISTS public.Sexos(
	idSexo SERIAL PRIMARY KEY,
	Detalle_sexo VARCHAR(12) NOT NULL
);

-- Tabla para los trabajadores de producción
CREATE TABLE IF NOT EXISTS public.Trabajadores (
    idTrabajador SERIAL PRIMARY KEY,
    DNI VARCHAR(8) NOT NULL,
    Nombres VARCHAR(50) NOT NULL,
	Apellidos VARCHAR(50) NOT NULL,
	Fecha_nacimiento DATE NOT NULL,
	Direccion VARCHAR(50) NOT NULL,
	Celular VARCHAR(9) NOT NULL,
	Celular_emergencia VARCHAR(9),
	Fecha_ingreso DATE NOT NULL,
	Area VARCHAR(22) NOT NULL,
	Cargo VARCHAR(45) NOT NULL,
	fk_idSexo INT REFERENCES public.Sexos(idSexo) NOT NULL
);

-- << Formatos >> --
-- Tabla para los tipos de formatos que existen con su detalle
CREATE TABLE IF NOT EXISTS public.TiposFormatos (
	idTipoFormato SERIAL PRIMARY KEY,
	NombreFormato VARCHAR(80) NOT NULL,
	Frecuencia VARCHAR(45),
	Codigo VARCHAR(45)
);

-- Tabla para el formato de lavado de manos
CREATE TABLE IF NOT EXISTS public.LavadosManos (
	idLavadoMano SERIAL PRIMARY KEY,
	Mes VARCHAR(10) NOT NULL,
	anio VARCHAR(4) NOT NULL,
	estado VARCHAR(45) NOT NULL,
	fk_idTipoFormatos INT REFERENCES public.TiposFormatos(idTipoFormato) NOT NULL
);

-- Creación de la tabla para las medidas correctivas asignadas al observador
CREATE TABLE IF NOT EXISTS public.MedidasCorrectivasObservaciones (
	idMedidaCorrectivaOb SERIAL PRIMARY KEY,
	DetalleDeMedidaCorrectiva VARCHAR(100),
	Fecha DATE,
	fk_idLavadoMano INT REFERENCES public.LavadosManos(idLavadoMano) NOT NULL
);

-- Tabla para el detalle de lavado de manos
CREATE TABLE IF NOT EXISTS public.Detalle_lavados_manos (
	idMano SERIAL PRIMARY KEY,
	Fecha DATE NOT NULL,
	Hora TIME NOT NULL,
	medida_correctiva VARCHAR(60),
	fk_idTrabajador INT REFERENCES public.Trabajadores(idTrabajador) NOT NULL,
	fk_idLavadoMano INT REFERENCES public.LavadosManos(idLavadoMano) NOT NULL
);

-- Tabla para el formato carnet de salud
CREATE TABLE IF NOT EXISTS public.CarnetSalud (
	idCarnetSalud SERIAL PRIMARY KEY,
	Carnet_salud BYTEA NOT NULL,
	Fecha_Vencimiento DATE NOT NULL
);

-- Tabla para el formato de control general del personal
CREATE TABLE IF NOT EXISTS public.controles_generales_personal (
	idControlGeneral SERIAL PRIMARY KEY, 
	fk_idCarnetSalud INT REFERENCES public.CarnetSalud(idCarnetSalud) NOT NULL,
	fk_idTrabajador INT REFERENCES public.Trabajadores(idTrabajador) NOT NULL,
	fk_idTipoFormatos INT REFERENCES public.TiposFormatos(idTipoFormato) NOT NULL
);

-- << Proveedores >> --
-- Tabla para los representantes legales
CREATE TABLE IF NOT EXISTS public.Representantes_legales (
	idRepresentanteLegal SERIAL PRIMARY KEY,
	DNI VARCHAR(8) NOT NULL,
	RUC VARCHAR(11) NOT NULL,
	Nombres VARCHAR(45) NOT NULL,
	Apellidos VARCHAR(45) NOT NULL,
	Cargo VARCHAR(45) NOT NULL
);

-- Tabla de domicilios legales del proveedor
CREATE TABLE IF NOT EXISTS public.Domicilios_legales (
	idDomicilioLegal SERIAL PRIMARY KEY,
	Departamento VARCHAR(45) NOT NULL,
	Distrito VARCHAR(45) NOT NULL,
	Provincia VARCHAR(45) NOT NULL,
	Celular VARCHAR(9) NOT NULL,
	Calle_pas_av VARCHAR(45) NOT NULL,
	Numero_calle VARCHAR(45) NOT NULL,
	RUC VARCHAR(11) NOT NULL,
	Correo_electronico VARCHAR(45) NOT NULL
);

--Tabla general de proveedores
CREATE TABLE IF NOT EXISTS public.Proveedores (
	idProveedor SERIAL PRIMARY KEY,
	nom_empresa VARCHAR(45) NOT NULL,
	fk_idRepresentanteLegal INT REFERENCES public.Representantes_legales(idRepresentanteLegal) NOT NULL,
	fk_idDomicilioLegal INT REFERENCES public.Domicilios_legales(idDomicilioLegal) NOT NULL
);

-- Crear la tabla para registrar productos
CREATE TABLE IF NOT EXISTS public.productos (
	idproducto SERIAL PRIMARY KEY,
	descripcion_producto VARCHAR(70) NOT NULL,
	Stock INT NOT NULL
);

--Tabla para generar el formato de kardex
CREATE TABLE IF NOT EXISTS public.kardex (
	idkardex SERIAL PRIMARY KEY,
	Mes VARCHAR(10) NOT NULL,
	anio VARCHAR(4) NOT NULL,
	Estado VARCHAR(10) NOT NULL,
	fk_idproducto INT REFERENCES public.productos(idproducto) NOT NULL,
	fk_idTipoFormatos INT REFERENCES public.TiposFormatos(idTipoFormato) NOT NULL
);

-- Tabla de detalles del kardex

CREATE TABLE IF NOT EXISTS public.detalles_kardex (
	iddetallekardex SERIAL PRIMARY KEY,
	fecha DATE NOT NULL,
	lote VARCHAR(15) NOT NULL,
	saldo_inicial INT NOT NULL,
	ingreso INT NOT NULL,
	salida INT NOT NULL,
	saldo_final INT NOT NULL,
	observaciones VARCHAR(80),
	fk_idkardex INT REFERENCES public.kardex(idkardex)
);


-- << Condiciones Ambientales >> --

-- Creación de las áreas para las condiciones ambientales

CREATE TABLE IF NOT EXISTS public.areas (
	idarea SERIAL PRIMARY KEY,
	detalle_area VARCHAR(45) NOT NULL
);

-- Creación de la tabla de condición ambiental

CREATE TABLE IF NOT EXISTS public.condiciones_ambientales (
	idcondicionambiental SERIAL PRIMARY KEY,
	mes VARCHAR(11) NOT NULL,
	anio VARCHAR(4) NOT NULL,
	estado VARCHAR(10) NOT NULL,
	fk_idTipoFormatos INT REFERENCES public.TiposFormatos(idTipoFormato) NOT NULL,
	fk_idArea INT REFERENCES public.areas(idarea) NOT NULL
);

-- Creación de la tabla para las acciones correctivas

CREATE TABLE IF NOT EXISTS public.acciones_correctivas (
	idAccion_correctiva SERIAL PRIMARY KEY,
	detalle_Accion_correctiva VARCHAR(60) NOT NULL,
	estado VARCHAR(30) NOT NULL
);

-- Creación de la tabla del detalle de condiciones ambientales

CREATE TABLE IF NOT EXISTS public.detalle_condiciones_ambientales(
	idDetalle_ca SERIAL PRIMARY KEY,
	fecha DATE NOT NULL,
	Hora TIME NOT NULL,
	observaciones VARCHAR(50) NULL,
	temperatura VARCHAR(10) NOT NULL,
	humedad VARCHAR(10) NOT NULL,
	fk_idAccion_correctiva INT REFERENCES public.acciones_correctivas(idAccion_correctiva) NULL,
	fk_idCondicion_ambiental INT REFERENCES public.condiciones_ambientales(idcondicionambiental) NULL
);

-- CREACIÓN DE LA TABLA DE VERIFICACIÓN PREVIA

CREATE TABLE IF NOT EXISTS public.Verificacion_previa(
	idVerificacion_Previa SERIAL PRIMARY KEY,
	detalle_verificacion_previa VARCHAR(50) NOT NULL
);

-- RELACIÓN DE MUCHOS A MUCHOS ENTRE LA VERIFICACIÓN PREVIA Y EL DETALLE DE LA CONDICÓN AMBIENTAL

CREATE TABLE IF NOT EXISTS public.asignacion_verificacion_previa_condicion_ambiental (
	idAsignacion_verificacion_previa SERIAL PRIMARY KEY,
	fk_idDetalle_condicion_ambiental INT REFERENCES public.detalle_condiciones_ambientales(iddetalle_ca),
	fk_idVerificacion_previa INT REFERENCES public.Verificacion_previa(idVerificacion_Previa)
);


-- << REGISTRO Y CONTROL DE ENVASADOS >>

CREATE TABLE IF NOT EXISTS public.Registros_Controles_Envasados (
	id_Registro_Control_Envasados SERIAL PRIMARY KEY,
	fecha DATE NULL,
	estado VARCHAR(20) NULL,
	fk_idTipoFormato INT REFERENCES public.TiposFormatos(idTipoFormato) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.Detalles_Registros_Controles_Envasados (
	id_detalle_registro_controles_envasados SERIAL PRIMARY KEY,
	fk_idTrabajador INT REFERENCES public.trabajadores(idtrabajador) NOT NULL,
	fk_idproducto INT REFERENCES public.productos(idproducto) NOT NULL,
	cantidad_producida INT NOT NULL,
	fk_idProveedor INT REFERENCES public.proveedores(idproveedor) NOT NULL,
	Lote_proveedor VARCHAR(15) NOT NULL,
	Lote_asignado VARCHAR(15) NOT NULL,
	fecha_vencimiento DATE NOT NULL,
	Observacion VARCHAR(60) NULL, 
	fk_id_registro_control_envasado INT REFERENCES public.Registros_Controles_Envasados(id_Registro_Control_Envasados)
);

-- << CONTROL DE HIGIENE PERSONAL >> --

CREATE TABLE IF NOT EXISTS public.Controles_higiene_personal (
	id_control_higiene_personal SERIAL PRIMARY KEY,
	mes VARCHAR(11) NOT NULL,
	anio VARCHAR(4) NOT NULL,
	estado VARCHAR(30) NULL,
	fk_idTipoFormato INT REFERENCES public.TiposFormatos(idTipoFormato) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.Detalles_controles_higiene_personal (
	id_detalle_control_higiene_personal SERIAL PRIMARY KEY,
	fecha DATE NOT NULL,
	fk_idtrabajador INT REFERENCES public.trabajadores(idtrabajador) NOT NULL,
	observaciones VARCHAR(60) NULL,
	fk_idaccion_correctiva INT REFERENCES public.acciones_correctivas(idaccion_correctiva) NULL,
	fk_idControl_higiene_personal INT REFERENCES public.Controles_higiene_personal(id_control_higiene_personal) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.asignacion_verificacion_previa_higiene_personal (
	id_asignacion_verificacion_previa_higiene_personal SERIAL PRIMARY KEY,
	fk_idVerificacion_previa INT REFERENCES public.verificacion_previa(idverificacion_previa) NOT NULL,
	fk_idDetalle_control_higiene_personal INT REFERENCES public.Detalles_controles_higiene_personal(id_detalle_control_higiene_personal) NOT NULL
);


-- << PARA VERIFICACIÓN DE LIMPIEZA Y DESINFECCIÓN DE LAS ÁREAS >> --

CREATE TABLE IF NOT EXISTS public.areas_produccion (
	id_area_produccion SERIAL PRIMARY KEY,
	detalle_area_produccion VARCHAR(45)
);

CREATE TABLE IF NOT EXISTS public.verificacion_limpieza_desinfeccion_areas (
	id_verificacion_limpieza_desinfeccion_area SERIAL PRIMARY KEY,
	mes VARCHAR(2) NOT NULL,
	anio VARCHAR(4) NOT NULL,
	fk_idarea_produccion INT REFERENCES public.areas_produccion(id_area_produccion) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.categorias_limpieza_desinfeccion (
	id_categorias_limpieza_desinfeccion SERIAL PRIMARY KEY,
	detalles_categorias_limpieza_desinfeccion VARCHAR(45) NOT NULL,
	frecuencia VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS public.detalles_verificacion_limpieza_desinfeccion_areas (
	id_detalle_verificacion_limpieza_desinfeccion_area SERIAL PRIMARY KEY,
	fecha DATE NOT NULL,
	fk_id_verificacion_limpieza_desinfeccion_area INT REFERENCES public.verificacion_limpieza_desinfeccion_areas(id_verificacion_limpieza_desinfeccion_area),
	fk_id_categorias_limpieza_desinfeccion INT REFERENCES public.categorias_limpieza_desinfeccion(id_categorias_limpieza_desinfeccion)
);

ALTER TABLE public.MedidasCorrectivasObservaciones
ADD COLUMN fk_id_accion_correctiva INT REFERENCES public.acciones_correctivas(idaccion_correctiva) NULL;

ALTER TABLE public.verificacion_limpieza_desinfeccion_areas
ADD COLUMN fk_idarea_produccion INT REFERENCES public.areas_produccion(id_area_produccion) NOT NULL;

CREATE TABLE IF NOT EXISTS public.asignaciones_medidas_correctivas_limpieza_areas (
	id_asignacion_medida_correctiva_limpieza_area SERIAL PRIMARY KEY,
	fk_id_verificacion_limpieza_desinfeccion_area INT REFERENCES public.verificacion_limpieza_desinfeccion_areas(id_verificacion_limpieza_desinfeccion_area) NOT NULL,
	fk_idmedidacorrectivaob INT REFERENCES public.medidascorrectivasobservaciones(idmedidacorrectivaob) NOT NULL
);


ALTER TABLE public.verificacion_limpieza_desinfeccion_areas
ADD COLUMN fk_idtipoformato INT REFERENCES public.tiposformatos(idtipoformato) NULL;


-- PARA LIMPIEZA DE EQUIPOS DE MEDICIÓN

CREATE TABLE IF NOT EXISTS public.verificaciones_equipos_medicion (
	id_verificacion_equipo_medicion SERIAL PRIMARY KEY,
	mes VARCHAR(2) NOT NULL,
	anio VARCHAR(4) NOT NULL,
	estado VARCHAR(20) NOT NULL,
	fk_id_tipo_formato INT REFERENCES public.tiposformatos(idtipoformato) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.detalles_verificaciones_equipos_medicion (
	id_detalle_verificacion_equipos_medicion SERIAL PRIMARY KEY,
	fecha DATE NOT NULL,
	fk_id_categorias_limpieza_desinfeccion INT REFERENCES public.categorias_limpieza_desinfeccion(id_categorias_limpieza_desinfeccion) NOT NULL,
	fk_id_verificacion_equipo_medicion INT REFERENCES public.verificaciones_equipos_medicion(id_verificacion_equipo_medicion) NOT NULL
);

-- MONITOREO DE INSECTOS Y ROEDORES

CREATE TABLE IF NOT EXISTS public.registros_monitores_insectos_roedores (
	id_registro_monitoreo_insecto_roedor SERIAL PRIMARY KEY,
	mes VARCHAR(2) NOT NULL,
	anio VARCHAR(4) NOT NULL,
	estado VARCHAR(20) NOT NULL,
	fk_id_tipo_formato INT REFERENCES public.tiposformatos(idtipoformato) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.detalles_registros_monitoreos_insectos_roedores (
	id_detalle_registro_monitoreo_insecto_roedor SERIAL PRIMARY KEY,
	fecha DATE NOT NULL,
	hora TIME NOT NULL,
	observacion VARCHAR(80) NULL,
	fk_id_accion_correctiva INT REFERENCES public.acciones_correctivas(idaccion_correctiva) NULL,
	fk_id_registro_monitoreo_insecto_roedor INT REFERENCES public.registros_monitores_insectos_roedores(id_registro_monitoreo_insecto_roedor) NOT NULL
);

CREATE TABLE IF NOT EXISTS verificaciones_areas_produccion_insectos_roedores (
	id_verificacion_area_produccion_insecto SERIAL PRIMARY KEY,
	fk_id_area_produccion INT REFERENCES public.areas_produccion(id_area_produccion) NOT NULL,
	fk_id_detalle_registro_monitoreo_insecto_roedor INT REFERENCES public.detalles_registros_monitoreos_insectos_roedores(id_detalle_registro_monitoreo_insecto_roedor) NOT NULL
);

ALTER TABLE public.medidascorrectivasobservaciones
ADD COLUMN fk_id_verificacion_equipo_medicion INT REFERENCES public.verificaciones_equipos_medicion(id_verificacion_equipo_medicion) NULL;


CREATE TABLE IF NOT EXISTS min_max (
	id_min_max SERIAL PRIMARY KEY,
	minimo_und VARCHAR(5) NULL,
	maximo_und VARCHAR(5) NULL,
	conversion_und VARCHAR(5) NULL,
	unidades VARCHAR(15) NULL,
	fk_id_productos INT REFERENCES public.productos(idproducto) NOT NULL
);

SELECT * FROM detalles_kardex

CREATE TABLE IF NOT EXISTS proyeccion (
	idprojection SERIAL PRIMARY KEY,
	estado VARCHAR(15) NOT NULL,
	semana VARCHAR(45) NULL
);

CREATE TABLE IF NOT EXISTS proyeccion_semanal (
    idProyeccion SERIAL PRIMARY KEY,
    proyeccion DOUBLE PRECISION NOT NULL,
    producido DOUBLE PRECISION NULL,
	dia VARCHAR(10) NULL,
    fk_id_productos INT REFERENCES public.productos(idproducto) NOT NULL,
	fk_proyeccion INT REFERENCES public.proyeccion(idprojection) NOT NULL
);

-- CREACIÓN DE UNA CABECERA PARA LOS NUEVOS FORMATOS
CREATE TABLE IF NOT EXISTS headers_formats (
	id_header_format SERIAL PRIMARY KEY,
	mes VARCHAR(2) NOT NULL,
	anio VARCHAR(4) NOT NULL,
	estado VARCHAR(20) NOT NULL,
	fk_id_tipo_formato INT REFERENCES public.tiposformatos(idtipoformato) NOT NULL,
	empresa_monitoreo_calidad_agua VARCHAR(30) NULL
);

CREATE TABLE IF NOT EXISTS detalles_controles_cloro_residual_agua (
	id_detalle_control_cloro_residual_agua SERIAL PRIMARY KEY,
	fecha DATE NOT NULL,
	hora TIME NOT NULL,
	lectura DOUBLE PRECISION NOT NULL,
	Observacion VARCHAR(50) NULL,
	fk_id_accion_correctiva INT REFERENCES public.acciones_correctivas(idaccion_correctiva) NULL,
	fk_id_header_format INT REFERENCES public.headers_formats(id_header_format) NOT NULL,
	fk_idarea INT REFERENCES public.areas(idarea) NULL
);

ALTER TABLE public.headers_formats
ADD COLUMN fk_idarea INT REFERENCES public.areas(idarea) NULL;


-- PARA EL FORMATO DE CONDICIONES SANITARIAS DE VEHÍCULOS DE TRANSPORTE

CREATE TABLE IF NOT EXISTS motivos_sanitarios_vehiculos (
	id_motivo_sanitario_vehiculo SERIAL PRIMARY KEY,
	detalle_motivo_vehiculo VARCHAR(10) NOT NULL
);

CREATE TABLE IF NOT EXISTS tipos_vehiculos (
	id_tipo_vehiculo SERIAL PRIMARY KEY,
	detalle_tipo_vehiculo VARCHAR(10) NOT NULL
);

CREATE TABLE IF NOT EXISTS verificaciones_vehiculos (
	id_verificion_vehiculos SERIAL PRIMARY KEY,
	detalle_verificacion_vehiculos VARCHAR(45) NOT NULL
);

CREATE TABLE IF NOT EXISTS detalles_condiciones_sanitarias_vehiculos_transporte (
	id_detalle_condicion_sanitaria_vehiculo_transporte SERIAL PRIMARY KEY,
	fecha DATE NOT NULL,
	fk_id_motivo_sanitario_vehiculo INT REFERENCES motivos_sanitarios_vehiculos(id_motivo_sanitario_vehiculo) NOT NULL,
	documento_referencia VARCHAR(30) NOT NULL,
	total_bultos DOUBLE PRECISION NOT NULL,
	fk_id_tipo_vehiculo INT REFERENCES tipos_vehiculos(id_tipo_vehiculo) NOT NULL,
	num_placa_vehiculo VARCHAR(10) NOT NULL,
	fk_id_header_format INT REFERENCES public.headers_formats(id_header_format) NOT NULL,
	observacion VARCHAR(80) NULL,
	fk_id_accion_correctiva INT REFERENCES public.acciones_correctivas(idaccion_correctiva) NULL
);

CREATE TABLE IF NOT EXISTS asignacion_detalles_condiciones_sanitarias_vehiculos (
	id_asignacion_detalle_condicion_sanitaria_vehiculo SERIAL PRIMARY KEY,
	fk_id_detalle_condicion_sanitaria_vehiculo INT REFERENCES detalles_condiciones_sanitarias_vehiculos_transporte(id_detalle_condicion_sanitaria_vehiculo_transporte) NOT NULL,
	fk_id_verificion_vehiculos INT REFERENCES verificaciones_vehiculos(id_verificion_vehiculos) NOT NULL
);

-- Para el formato "Monitoreo de la calidad de agua"

CREATE TABLE IF NOT EXISTS tipos_controles_calidad_agua (
	id_tipo_Control_calidad_agua SERIAL PRIMARY KEY,
	detalle_control VARCHAR(45) NOT NULL,
	unidad VARCHAR(10) NOT NULL,
	detection_limit DOUBLE PRECISION NOT NULL
);

CREATE TABLE IF NOT EXISTS detalles_monitoreos_calidad_agua (
	idDetalle_monitoreo_calidad_agua SERIAL PRIMARY KEY,
	Resultado DOUBLE PRECISION NOT NULL,
	observaciones VARCHAR(80) NULL,
	fk_id_tipo_Control_calidad_agua INT REFERENCES tipos_controles_calidad_agua(id_tipo_Control_calidad_agua) NOT NULL,
	fk_id_header_format INT REFERENCES public.headers_formats(id_header_format) NOT NULL
);

-- FORMATO DE REGISTRO DE VERIFICACIÓN DE EQUIPOS

CREATE TABLE IF NOT EXISTS verificaciones_calibracion_equipos (
	idverificacion_equipo SERIAL PRIMARY KEY,
	equipo VARCHAR(45) NOT NULL,
	fecha_mantenimiento DATE NOT NULL,
	fecha_prox_mantenimiento DATE NOT NULL,
	actividad_realizada VARCHAR(100) NOT NULL,
	observaciones VARCHAR(45) NULL,
	responsable VARCHAR(45) NOT NULL,
	fk_id_header_format INT REFERENCES public.headers_formats(id_header_format) NOT NULL
);

-- PARA EL FORMATO DE FICHA TÉCNICA DEL PROVEEDOR

ALTER TABLE public.proveedores
ADD COLUMN status VARCHAR(20) NULL,
ADD COLUMN comercial VARCHAR(45) NULL,
ADD COLUMN industrial VARCHAR(45) NULL,
ADD COLUMN tipo_empresa VARCHAR(45) NULL;

CREATE TABLE IF NOT EXISTS asignaciones_provedores_header (
	id_asignacion_proveedores SERIAL PRIMARY KEY,
	fk_id_proveedor INT REFERENCES public.proveedores(idproveedor) NOT NULL,
	fk_id_header_format INT REFERENCES public.headers_formats(id_header_format) NOT NULL
)

CREATE TABLE IF NOT EXISTS detalles_productos_proveedores (
	iddetalle_producto_proveedor SERIAL PRIMARY KEY,
	cantidad VARCHAR(45) NOT NULL,
	frecuencia VARCHAR(45) NOT NULL,
	producto_proveedor VARCHAR(60) NOT NULL,
	fk_id_asignacion_header INT REFERENCES asignaciones_provedores_header(id_asignacion_proveedores) NOT NULL
);

SELECT * FROM v_proveedores WHERE estado = 'CERRADO' ORDER BY anio

SELECT * FROM public.headers_formats
	
ALTER TABLE public.detalles_productos_proveedores
ADD COLUMN fk_id_asignacion_header INT REFERENCES asignaciones_provedores_header(id_asignacion_proveedores) NULL

CREATE TABLE IF NOT EXISTS recepciones_materias_primas (
	id_recepcion_materia_prima SERIAL PRIMARY KEY,
	producto_recibido VARCHAR(100) NOT NULL,
	razon_social VARCHAR(14) NOT NULL,
	factura VARCHAR(25) NOT NULL,
	lote VARCHAR(30) NULL,
	cantidad_recibida VARCHAR(20) NOT NULL,
	f_produccion DATE NULL,
	f_vencimiento DATE NULL,
	observaciones VARCHAR(100) NULL,
	fk_id_header_format INT REFERENCES public.headers_formats(id_header_format) NOT NULL
);

CREATE TABLE IF NOT EXISTS controles_calidad_mat_primas (
	id_control_calidad SERIAL PRIMARY KEY,
	detalle_control VARCHAR(10) NOT NULL
);

CREATE TABLE IF NOT EXISTS asignaciones_controles_mat_primas(
	id_asignacion_control_mat_prima SERIAL PRIMARY KEY,
	fk_id_recepcion_materia_prima INT REFERENCES recepciones_materias_primas(id_recepcion_materia_prima) NOT NULL,
	fk_id_control_calidad INT REFERENCES controles_calidad_mat_primas(id_control_calidad) NOT NULL,
	estado VARCHAR(15) NOT NULL
);

CREATE TABLE IF NOT EXISTS control_visitas (
	idcontrol_visitas SERIAL PRIMARY KEY,
	fecha DATE NOT NULL,
	nombres_apellidos VARCHAR(100) NOT NULL,
	dni VARCHAR(8) NOT NULL,
	empresa VARCHAR(100) NOT NULL,
	h_ingreso TIME NOT NULL,
	h_salida TIME NOT NULL,
	motivo VARCHAR(150) NOT NULL,
	observaciones VARCHAR(150) NULL,
	fk_id_header_format INT REFERENCES public.headers_formats(id_header_format) NOT NULL
);

CREATE TABLE IF NOT EXISTS evaluaciones_visitas (
	id_evaluacion_visita SERIAL PRIMARY KEY,
	detalle_evaluacion VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS asignaciones_evaluaciones_visitas (
	id_asignacion_evaluacion_visita SERIAL PRIMARY KEY,
	fk_ididcontrol_visitas INT REFERENCES control_visitas(idcontrol_visitas) NOT NULL,
	fk_id_evaluacion_visita INT REFERENCES evaluaciones_visitas(id_evaluacion_visita) NOT NULL
);