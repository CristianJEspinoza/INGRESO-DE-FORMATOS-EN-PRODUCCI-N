-- Creación de vistas para el ingreso de formatos en producción

CREATE OR REPLACE VIEW v_lavados_manos AS
SELECT
    dlv.idmano,
    dlv.hora,
    dlv.fecha,
    CONCAT(
        -- Usamos COALESCE para evitar un valor NULL si no se encuentra el espacio
        COALESCE(
            -- Si se encuentra un espacio, tomamos la subcadena
            SUBSTRING(t.nombres FROM 1 FOR NULLIF(POSITION(' ' IN t.nombres) - 1, -1)),
            -- Si no se encuentra, tomamos todo el nombre
            t.nombres
        ), 
        ' ', 
        -- Toma la inicial del apellido
        SUBSTRING(t.apellidos FROM 1 FOR 1), 
        '.'
    ) AS nombre_formateado,
    lv.idlavadomano,
    lv.fk_idtipoformatos,
    lv.estado
FROM 
    detalle_lavados_manos dlv
JOIN 
    trabajadores t ON t.idtrabajador = dlv.fk_idtrabajador
JOIN
    lavadosmanos lv ON lv.idlavadomano = dlv.fk_idlavadomano
ORDER BY 
    dlv.fecha DESC;


CREATE OR REPLACE VIEW v_historial_lavado_manos AS
SELECT
    TO_CHAR(TO_DATE(f.mes || ' ' || f.anio, 'MM YYYY'), 'TMMonth') AS mes,
    f.anio,
    f.fk_idtipoformatos,
    f.estado,
	f.idlavadomano
FROM
    lavadosmanos f
WHERE 
	f.fk_idtipoformatos = 2 AND estado = 'CERRADO'
ORDER BY
	f.idlavadomano DESC;

CREATE OR REPLACE VIEW v_kardex AS
SELECT
	kr.idkardex,
	TO_CHAR(TO_DATE(kr.mes || ' ' || kr.anio, 'MM YYYY'), 'TMMonth') AS mes,
	kr.anio,
	kr.estado,
	pr.descripcion_producto
FROM
	kardex kr
JOIN
	productos pr ON pr.idproducto = kr.fk_idproducto
ORDER BY
	kr.idkardex
DESC;


SELECT 
	c.idcontrolgeneral,t.idtrabajador, t.dni, t.nombres, t.apellidos, 
	t.fecha_nacimiento, t.direccion, t.celular, 
	t.celular_emergencia, t.fecha_ingreso, 
	t.area, t.cargo, t.fk_idsexo, cn.carnet_salud
FROM 
	trabajadores t 
JOIN 
	controles_generales_personal c ON t.idtrabajador = c.fk_idtrabajador
JOIN
	carnetsalud cn ON c.fk_idcarnetsalud = cn.idcarnetsalud;

CREATE OR REPLACE VIEW v_control_general_personal AS
SELECT
	c.idcontrolgeneral, cs.idcarnetsalud, cs.carnet_salud, t.idtrabajador, t.dni, t.nombres, t.apellidos, t.fecha_nacimiento, 
	t.direccion, t.celular, t.celular_emergencia, t.fecha_ingreso, t.area, t.cargo, t.fk_idsexo
FROM
	controles_generales_personal c
JOIN
	carnetsalud cs ON cs.idcarnetsalud = c.fk_idcarnetsalud
JOIN
	trabajadores t ON t.idtrabajador = c.fk_idtrabajador;

-- CONTROL DE CONDICIONES AMBIENTALES

CREATE OR REPLACE VIEW v_condiciones_ambientales AS
SELECT
	ca.idcondicionambiental, TO_CHAR(TO_DATE(ca.mes || ' ' || ca.anio, 'MM YYYY'), 'TMMonth') AS mes, ca.anio, ca.estado, a.idarea, a.detalle_area
FROM
	condiciones_ambientales ca
JOIN
	areas a ON a.idarea = ca.fk_idarea;


CREATE OR REPLACE VIEW v_detalle_control_CA AS
SELECT
    d.iddetalle_ca,
    d.fecha,
    d.hora,
    d.temperatura,
    d.humedad,
    d.observaciones,
    COALESCE(ac.detalle_accion_correctiva, '-') AS detalle_accion_correctiva,
	ac.idaccion_correctiva,
	ac.estado,
    ca.idcondicionambiental
FROM
    detalle_condiciones_ambientales d
LEFT JOIN
    acciones_correctivas ac ON ac.idaccion_correctiva = d.fk_idaccion_correctiva
JOIN
    condiciones_ambientales ca ON ca.idcondicionambiental = d.fk_idcondicion_ambiental;

SELECT * FROM v_detalle_control_CA

-- REGISTRO Y CONTROL DE ENVASADOS

CREATE OR REPLACE VIEW v_historial_registros_controles_envasados AS
SELECT
	f.id_registro_control_envasados,
	TO_CHAR(f.fecha, 'DD/MM/YYYY') AS fecha,
    TO_CHAR(f.fecha, 'MM') AS mes,
    TO_CHAR(f.fecha, 'YYYY') AS anio,
    TO_CHAR(f.fecha, 'TMMonth') AS month_name,
    f.estado
FROM
    registros_controles_envasados f
WHERE 
    f.fk_idtipoformatos = 5 AND f.estado = 'CERRADO'
ORDER BY
    f.id_registro_control_envasados DESC;

SELECT 
    month_name, 
    anio,
    JSON_AGG(
        JSON_BUILD_OBJECT(
            'id_registro_control_envasados', id_registro_control_envasados,
            'fecha', fecha
        )
    ) AS registros
FROM 
    v_historial_registros_controles_envasados
GROUP BY 
    month_name,mes, anio
ORDER BY 
    anio DESC, 
    mes DESC;

SELECT COUNT(*) AS total
FROM (SELECT DISTINCT mes, anio 
	FROM v_historial_registros_controles_envasados 
	WHERE estado = 'CERRADO') AS distinct_months_years

SELECT * FROM v_historial_registros_controles_envasados

DROP VIEW v_historial_registros_controles_envasados

SELECT * FROM registros_controles_envasados

SELECT * FROM v_historial_registros_controles_envasados

CREATE OR REPLACE VIEW v_registros_controles_envasados AS
SELECT
	ce.id_detalle_registro_controles_envasados,
	t.nombres || ' ' || t.apellidos AS responsable,
	p.idproducto,
	p.codigo_product,
	p.descripcion_producto,
	ce.cantidad_producida,
	pr.nom_empresa,
	ce.lote_proveedor,
	ce.lote_asignado,
	TO_CHAR(ce.fecha_vencimiento, 'DD/MM/YYYY') AS fecha_vencimiento,
	ce.observacion,
	rce.estado,
	rce.fecha AS date_insertion,
	rce.id_registro_control_envasados
FROM
	detalles_registros_controles_envasados ce
JOIN
	trabajadores t ON t.idtrabajador = ce.fk_idtrabajador
JOIN
	productos p ON p.idproducto = ce.fk_idproducto
JOIN
	proveedores pr ON pr.idproveedor = ce.fk_idproveedor
JOIN
	registros_controles_envasados rce ON rce.id_registro_control_envasados = ce.fk_id_registro_control_envasado
ORDER BY
	ce.id_detalle_registro_controles_envasados DESC;

SELECT * FROM v_registros_controles_envasados

DROP VIEW v_registros_controles_envasados

-- CONTROL DE ASEO E HIGIENE PERSONAL --

CREATE OR REPLACE VIEW v_historial_higiene_personal AS
SELECT
    TO_CHAR(TO_DATE(f.mes || ' ' || f.anio, 'MM YYYY'), 'TMMonth') AS mes,
    f.anio,
    f.fk_idtipoformatos,
    f.estado,
	f.id_control_higiene_personal
FROM
    controles_higiene_personal f
WHERE
	f.fk_idtipoformatos = 6 AND estado = 'CERRADO'
ORDER BY
	f.id_control_higiene_personal DESC;

DROP VIEW v_historial_higiene_personal

SELECT * FROM public.asignacion_verificacion_previa_higiene_personal

CREATE OR REPLACE VIEW v_detalle_higiene_personal AS
SELECT
    d.id_detalle_control_higiene_personal,
    d.fecha,
    t.nombres || t.apellidos AS trabajador,
    d.observaciones,
	ac.idaccion_correctiva,
    COALESCE(ac.detalle_accion_correctiva, '-') AS detalle_accion_correctiva,
	COALESCE(ac.estado, '-') AS estado_medida_correctiva,
    d.fk_idcontrol_higiene_personal,
	hp.estado
FROM
    detalles_controles_higiene_personal d
LEFT JOIN
    acciones_correctivas ac ON ac.idaccion_correctiva = d.fk_idaccion_correctiva
JOIN	
	trabajadores t ON t.idtrabajador = d.fk_idtrabajador
JOIN
    controles_higiene_personal hp ON hp.id_control_higiene_personal = d.fk_idcontrol_higiene_personal;

select * from v_detalle_higiene_personal
-- << PARA LIMPIEZA Y DESINFECCIÓN DE LAS ÁREAS >> --

CREATE OR REPLACE VIEW v_verificacion_limpieza_desinfeccion_areas AS
SELECT
	la.id_verificacion_limpieza_desinfeccion_area,
	a.detalle_area_produccion,
	a.id_area_produccion,
	TO_CHAR(TO_DATE(la.mes || ' ' || la.anio, 'MM YYYY'), 'TMMonth') AS mes,
	la.anio,
	la.estado
FROM
	verificacion_limpieza_desinfeccion_areas la
JOIN
	areas_produccion a ON a.id_area_produccion = la.fk_idarea_produccion;

SELECT * FROM v_verificacion_limpieza_desinfeccion_areas

CREATE OR REPLACE VIEW v_detalles_verificacion_limpieza_desinfeccion_areas AS
SELECT
	d.id_detalle_verificacion_limpieza_desinfeccion_area,
	TO_CHAR(d.fecha, 'DD/MM/YYYY') AS fecha,
	v.id_verificacion_limpieza_desinfeccion_area,
	v.fk_idarea_produccion,
	c.id_categorias_limpieza_desinfeccion,
	c.detalles_categorias_limpieza_desinfeccion,
	c.frecuencia
FROM
	detalles_verificacion_limpieza_desinfeccion_areas d
JOIN
	verificacion_limpieza_desinfeccion_areas v ON v.id_verificacion_limpieza_desinfeccion_area = d.fk_id_verificacion_limpieza_desinfeccion_area
JOIN
	categorias_limpieza_desinfeccion c ON c.id_categorias_limpieza_desinfeccion = d.fk_id_categorias_limpieza_desinfeccion;

-- Este
DROP VIEW v_detalles_verificacion_limpieza_desinfeccion_areas

SELECT * FROM v_detalles_verificacion_limpieza_desinfeccion_areas
-- Creación de vista para mostrar las asignaciones de medidas correctivas para la limpieza de las áreas

CREATE OR REPLACE VIEW v_asingaciones_observaciones_acCorrec_limpieza_areas AS
SELECT DISTINCT ON (o.idmedidacorrectivaob)
    o.idmedidacorrectivaob,
    o.detalledemedidacorrectiva,
    TO_CHAR(o.fecha, 'DD/MM/YYYY') AS fecha,
    ac.idaccion_correctiva,
    ac.detalle_accion_correctiva,
    ac.estado
FROM
    asignaciones_medidas_correctivas_limpieza_areas ala
JOIN
    medidascorrectivasobservaciones o ON o.idmedidacorrectivaob = ala.fk_idmedidacorrectivaob
JOIN
    acciones_correctivas ac ON ac.idaccion_correctiva = o.fk_id_accion_correctiva
WHERE
    EXTRACT(MONTH FROM o.fecha) = EXTRACT(MONTH FROM CURRENT_DATE) AND
    EXTRACT(YEAR FROM o.fecha) = EXTRACT(YEAR FROM CURRENT_DATE)
ORDER BY
    o.idmedidacorrectivaob, o.fecha DESC;


SELECT 
	mes, anio, 
	json_agg(json_build_object('id_verificacion_limpieza_desinfeccion_area', id_verificacion_limpieza_desinfeccion_area, 
							   'detalle_area_produccion', detalle_area_produccion,
							   'estado', estado,
							   'id_area_produccion', id_area_produccion)) AS registros
FROM v_verificacion_limpieza_desinfeccion_areas 
WHERE estado = 'CERRADO' 
GROUP BY mes, anio
ORDER BY anio DESC, mes DESC


-- LIMPIEZA Y EQUIPOS DE MEDICIÓN

CREATE OR REPLACE VIEW v_verificaciones_equipos_medicion AS
SELECT
	em.id_verificacion_equipo_medicion,
	TO_CHAR(TO_DATE(em.mes || ' ' || em.anio, 'MM YYYY'), 'TMMonth') AS mes,
	em.anio,
	em.estado,
	em.fk_idtipoformatos
FROM
	verificaciones_equipos_medicion em;  


CREATE OR REPLACE VIEW v_detalles_verificaciones_equipos_medicion AS
SELECT
    d.id_detalle_verificacion_equipos_medicion,
    TO_CHAR(d.fecha, 'DD/MM/YYYY') AS fecha,
    d.estado_verificacion,
    c.id_categorias_limpieza_desinfeccion,
    c.detalles_categorias_limpieza_desinfeccion,
    c.frecuencia,
    v.id_verificacion_equipo_medicion,
    v.mes,
    v.anio,
    v.estado,
    v.fk_idtipoformatos
FROM
    detalles_verificaciones_equipos_medicion d
JOIN
    categorias_limpieza_desinfeccion c ON c.id_categorias_limpieza_desinfeccion = d.fk_id_categorias_limpieza_desinfeccion
JOIN
    verificaciones_equipos_medicion v ON v.id_verificacion_equipo_medicion = d.fk_id_verificacion_equipo_medicion;

DROP VIEW v_verificaciones_equipos_medicion

CREATE OR REPLACE VIEW v_observaciones_acc_correctivas AS
SELECT
	ob.idmedidacorrectivaob,
	ob.detalledemedidacorrectiva,
	ob.fecha,
	ob.fk_id_verificacion_equipo_medicion,
	ac.idaccion_correctiva,
	ac.detalle_accion_correctiva,
	ac.estado
FROM
	public.medidascorrectivasobservaciones ob
JOIN
	public.acciones_correctivas ac ON ac.idaccion_correctiva = ob.fk_id_accion_correctiva;


-- PARA EL FORMATO DE CONTROL DE INSECTOS

SELECT * FROM public.registros_monitores_insectos_roedores

SELECT * FROM tiposformatos

CREATE OR REPLACE VIEW v_registros_monitores_insectos_roedores AS
SELECT
	ri.id_registro_monitoreo_insecto_roedor,
	TO_CHAR(TO_DATE(ri.mes || ' ' || ri.anio, 'MM YYYY'), 'TMMonth') AS mes,
	ri.anio,
	ri.estado,
	ri.fk_idtipoformatos
FROM
	registros_monitores_insectos_roedores ri;

SELECT * FROM v_detalles_registros_monitoreos_insectos_roedores

CREATE OR REPLACE VIEW v_detalles_registros_monitoreos_insectos_roedores AS
SELECT
	d.id_detalle_registro_monitoreo_insecto_roedor,
	d.fecha,
	d.hora,
	d.observacion,
	ac.idaccion_correctiva,
	COALESCE(ac.detalle_accion_correctiva, '-') AS detalle_accion_correctiva,
	ac.estado AS estado_accion_correctiva,
	r.id_registro_monitoreo_insecto_roedor,
	r.mes,
	r.anio,
	r.estado,
	r.fk_idtipoformatos
FROM
	detalles_registros_monitoreos_insectos_roedores d
LEFT JOIN
	acciones_correctivas ac ON ac.idaccion_correctiva = d.fk_id_accion_correctiva
JOIN
	registros_monitores_insectos_roedores r ON r.id_registro_monitoreo_insecto_roedor = d.fk_id_registro_monitoreo_insecto_roedor
ORDER BY
	d.id_detalle_registro_monitoreo_insecto_roedor
DESC;



SELECT * FROM public.trabajadores
SELECT 
	c.idcontrolgeneral,t.idtrabajador, t.dni, t.nombres, t.apellidos, 
	t.fecha_nacimiento, t.direccion, t.celular, 
	t.celular_emergencia, t.fecha_ingreso, 
	t.area, t.cargo, t.fk_idsexo, cn.carnet_salud,
	t.estado_trabajador
FROM 
	trabajadores t 
JOIN 
	controles_generales_personal c ON t.idtrabajador = c.fk_idtrabajador
JOIN
	carnetsalud cn ON c.fk_idcarnetsalud = cn.idcarnetsalud
WHERE
	t.estado_trabajador = 'ACTIVO'

SELECT 
	c.idcontrolgeneral,
	t.idtrabajador, 
	t.dni, 
	t.nombres, 
	t.apellidos, 
	DATE_FORMAT(t.fecha_nacimiento, '%d/%m/%Y') AS fecha_nacimiento, 
	t.direccion, 
	t.celular, 
	t.celular_emergencia, 
	DATE_FORMAT(t.fecha_ingreso, '%d/%m/%Y') AS fecha_ingreso, 
	t.area, 
	t.cargo, 
	t.fk_idsexo, 
	cn.carnet_salud,
	t.estado_trabajador
FROM 
	trabajadores t 
JOIN 
	controles_generales_personal c ON t.idtrabajador = c.fk_idtrabajador
JOIN
	carnetsalud cn ON c.fk_idcarnetsalud = cn.idcarnetsalud
WHERE
	t.estado_trabajador = 'ACTIVO'



CREATE OR REPLACE VIEW v_min_max AS
SELECT
    m.id_min_max,
    m.minimo_und,
    m.maximo_und,
    m.conversion_und,
	ROUND(CAST(m.minimo_und AS NUMERIC) * CAST(m.conversion_und AS NUMERIC), 2)::TEXT || ' ' || 'KG' AS transformed_minimo, 
	ROUND(CAST(m.maximo_und AS NUMERIC) * CAST(m.conversion_und AS NUMERIC), 2)::TEXT || ' ' || 'KG' AS transformed_maximo,
	m.equivalencia,
	m.unidad_equivalencia,
    p.idproducto,
    p.descripcion_producto,
	p.stock,
	m.unidades_por_equivalencia
FROM
    min_max m
JOIN
    productos p ON p.idproducto = m.fk_id_productos;

DROP VIEW v_min_max
SELECT * FROM v_min_max
	
SELECT * FROM public.proyeccion_semanal

CREATE OR REPLACE VIEW v_proyeccion_semanal AS
SELECT
    p.idproyeccion,
    p.proyeccion,
    p.producido,
    pro.idproducto,
    pro.descripcion_producto,
    pro.stock,
	m.minimo_und,
	m.maximo_und,
    CEIL(CAST(m.equivalencia AS NUMERIC) * CAST(p.proyeccion AS NUMERIC))::TEXT || ' ' || m.unidad_equivalencia AS equivalencia_unidades,
    CAST(m.conversion_und AS NUMERIC) AS kgs,
    m.equivalencia,
    CAST(m.unidades_por_equivalencia AS NUMERIC) AS unidades,
	CEIL((CAST(m.equivalencia AS NUMERIC) * CAST(p.proyeccion AS NUMERIC))) AS equivalenciauni,
	p.dia,
	p.inicio_date,
	p.fin_date,
	p.estado,
	p.producido_en_periodo,
	p.producido_fuera_periodo,
	COALESCE(p.observacion, ' ') AS observacion
FROM
    proyeccion_semanal p
JOIN
    productos pro ON pro.idproducto = p.fk_id_productos
JOIN
    min_max m ON pro.idproducto = m.fk_id_productos
ORDER BY
    p.idproyeccion;

SELECT * FROM v_proyeccion_semanal

DROP VIEW v_proyeccion_semanal

SELECT COUNT(*) AS total
FROM (SELECT DISTINCT mes, anio 
	FROM v_historial_registros_controles_envasados 
	WHERE estado = 'CERRADO') AS distinct_months_years

SELECT 
	mes, 
	anio, 
	json_agg(json_build_object(
		'id_verificacion_limpieza_desinfeccion_area', id_verificacion_limpieza_desinfeccion_area, 
		'detalle_area_produccion', detalle_area_produccion,
		'estado', estado,
		'id_area_produccion', id_area_produccion
	)) AS registros
FROM v_verificacion_limpieza_desinfeccion_areas
GROUP BY mes, anio

SELECT * FROM v_kardex WHERE estado = 'CERRADO'

SELECT
	mes,
	anio,
	json_agg(json_build_object(
		'idkardex', idkardex,
		'mes', mes,
		'anio', anio,
		'estado', estado,
		'descripcion_producto', descripcion_producto
	)) AS registros
FROM v_kardex
WHERE estado = 'CERRADO'
GROUP BY mes, anio

SELECT COUNT(*) AS total
FROM (SELECT DISTINCT mes, anio 
	FROM v_kardex 
	WHERE estado = 'CERRADO') AS distinct_months_years;
	
SELECT * FROM detalles_controles_cloro_residual_agua

CREATE OR REPLACE VIEW v_detalles_controles_cloro_residual_agua AS
SELECT
	d.id_detalle_control_cloro_residual_agua,
	d.fecha,
	d.hora,
	d.lectura,
	COALESCE(d.observacion, '-') AS observacion,
	a.idaccion_correctiva,
	COALESCE(a.detalle_accion_correctiva, '-') AS detalle_accion_correctiva,
	COALESCE(a.estado, '-') AS estado_accion_correctiva,
	h.id_header_format,
	h.estado AS estado_formato
FROM
	detalles_controles_cloro_residual_agua d
JOIN
	headers_formats h ON h.id_header_format = d.fk_id_header_format
LEFT JOIN
	acciones_correctivas a ON a.idaccion_correctiva = d.fk_id_accion_correctiva;

drop view v_proyeccion_semanal

SELECT fecha, hora, lectura, observacion, detalle_accion_correctiva, estado_Accion_correctiva 
FROM v_detalles_controles_cloro_residual_agua 
WHERE estado_formato = 'CREADO'

CREATE OR REPLACE VIEW v_headers_formats AS
SELECT
	f.id_header_format,
    TO_CHAR(TO_DATE(f.mes || ' ' || f.anio, 'MM YYYY'), 'TMMonth') AS mes,
    f.anio,
	f.estado,
	f.fk_idtipoformatos,
	f.empresa_monitoreo_calidad_agua,
	f.fk_idarea,
	a.detalle_area
FROM
    headers_formats f
LEFT JOIN
	areas a ON f.fk_idarea = a.idarea
ORDER BY
	f.anio DESC, f.mes DESC;

SELECT * FROM motivos_sanitarios_vehiculos

SELECT * FROM v_headers_formats

SELECT COUNT(*) AS total
FROM (SELECT DISTINCT mes, anio 
	FROM v_headers_formats 
	WHERE estado = 'CERRADO' AND fk_idtipoformatos = 12) AS distinct_months_years
	
SELECT * FROM public.detalles_condiciones_sanitarias_vehiculos_transporte

-- VISTA PARA LAS CONDICIONE SANITARIAS DE VEHICULOS DE TRANSPORTE
CREATE OR REPLACE VIEW v_detalle_condiciones_vehiculos AS
SELECT
	dv.id_detalle_condicion_sanitaria_vehiculo_transporte,
	dv.fecha,
	mv.detalle_motivo_vehiculo,
	dv.documento_referencia,
	dv.total_bultos,
	tv.detalle_tipo_vehiculo,
	dv.num_placa_vehiculo,
	dv.fk_id_header_format,
	COALESCE(dv.observacion, '-') AS observacion,
	ac.idaccion_correctiva,
	COALESCE(ac.detalle_accion_correctiva, '-') AS detalle_accion_correctiva,
	ac.estado AS estado_ac
FROM
	detalles_condiciones_sanitarias_vehiculos_transporte dv
JOIN
	motivos_sanitarios_vehiculos mv ON mv.id_motivo_sanitario_vehiculo = dv.fk_id_motivo_sanitario_vehiculo
JOIN
	tipos_vehiculos tv ON tv.id_tipo_vehiculo = dv.fk_id_tipo_vehiculo
LEFT JOIN
	acciones_correctivas ac ON ac.idaccion_correctiva = dv.fk_id_accion_correctiva;

SELECT id_header_format 
FROM headers_formats 
WHERE estado = 'CREADO' AND headers_formats.fk_idtipoformatos = 11
	
SELECT SUM(salida) AS total_salidas
FROM public.detalles_kardex
WHERE fecha = '2024-11-21'::date;

CREATE OR REPLACE VIEW v_detalles_monitoreos_calidad_agua AS
SELECT
	mc.iddetalle_monitoreo_calidad_agua,
	mc.resultado,
	COALESCE(mc.observaciones, '-') AS observaciones,
	mc.fk_id_tipo_control_calidad_agua,
	tc.detalle_control,
	tc.unidad,
	tc.detection_limit,
	hf.id_header_format,
	hf.estado,
	hf.fecha
FROM
	detalles_monitoreos_calidad_agua mc
JOIN
	headers_formats hf ON mc.fk_id_header_format = hf.id_header_format
JOIN
	public.tipos_controles_calidad_agua tc ON mc.fk_id_tipo_control_calidad_agua = tc.id_tipo_control_calidad_agua;


SELECT
    fecha,
    estado,
    json_agg(
        json_build_object(
            'iddetalle_monitoreo_calidad_agua', iddetalle_monitoreo_calidad_agua,
            'detalle_control', detalle_control,
            'unidad', unidad,
            'detection_limit', detection_limit,
            'resultado', resultado
        )
    ) AS registros
FROM v_detalles_monitoreos_calidad_agua
WHERE estado = 'CERRADO'
GROUP BY fecha, estado
ORDER BY fecha;

	
SELECT COUNT(*) AS total
FROM (SELECT DISTINCT fecha 
	FROM v_detalles_monitoreos_calidad_agua
	WHERE estado = 'CERRADO') AS distinct_date;


CREATE OR REPLACE VIEW v_verificaciones_calibracion_equipos AS
SELECT
	v.idverificacion_equipo, v.equipo, v.fecha_mantenimiento, v.fecha_prox_mantenimiento, v.actividad_realizada, 
	COALESCE(v.observaciones, '-') AS observaciones, v.responsable, h.estado, h.id_header_format
FROM
	verificaciones_calibracion_equipos v
JOIN
	headers_formats h ON v.fk_id_header_format = h.id_header_format;

-- PARA EL FORMATO DE PROVEEDORES

SELECT * FROM public.proveedores

SELECT * FROM public.asignaciones_provedores_header

CREATE OR REPLACE VIEW v_proveedores AS 
SELECT
	a.id_asignacion_proveedores,
	a.fk_id_proveedor,
	p.nom_empresa,
	d.departamento,
	d.distrito,
	d.provincia,
	d.celular,
	d.calle_pas_av,
	d.numero_calle,
	d.ruc AS ruc_domicilio,
	d.correo_electronico,
	r.dni,
	r.ruc AS ruc_representante,
	r.nombres,
	r.apellidos,
	r.cargo,
	p.status,
	p.comercial,
	p.industrial,
	p.tipo_empresa,
	a.fk_id_header_format,
	h.anio,
	h.estado
FROM
	asignaciones_provedores_header a
JOIN
	proveedores p ON p.idproveedor = a.fk_id_proveedor
JOIN
	headers_formats h ON h.id_header_format = a.fk_id_header_format
JOIN
	domicilios_legales d ON d.iddomiciliolegal = p.fk_iddomiciliolegal
JOIN
	representantes_legales r ON r.idrepresentantelegal = p.fk_idrepresentantelegal;
	

DROP VIEW v_proveedores
	
SELECT * FROM v_proveedores

SELECT * FROM public.headers_formats

SELECT * FROM public.detalles_productos_proveedores

CREATE OR REPLACE VIEW v_detalles_productos_proveedores AS
SELECT
	d.iddetalle_producto_proveedor,
	d.cantidad,
	d.frecuencia,
	d.producto_proveedor,
	d.fk_id_asignacion_header,
	h.id_header_format
FROM 
	public.detalles_productos_proveedores d
JOIN
	public.asignaciones_provedores_header a ON d.fk_id_asignacion_header = a.id_asignacion_proveedores
JOIN
	public.headers_formats h ON h.id_header_format = a.fk_id_header_format;

SELECT * FROM v_detalles_productos_proveedores

SELECT * FROM public.productos
