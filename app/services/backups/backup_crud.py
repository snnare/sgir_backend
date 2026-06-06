from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.backup_models import (
    RutaRespaldo, PoliticaRespaldo, AsignacionPoliticaBD, Respaldo,
    TipoRespaldo, TipoAlmacenamiento
)
from app.schemas import (
    RutaRespaldoCreate, RutaRespaldoUpdate,
    PoliticaRespaldoCreate, PoliticaRespaldoUpdate,
    RespaldoCreate, AsignacionPoliticaBDCreate,
    TipoRespaldoCreate, TipoAlmacenamientoCreate
)

# --- Catálogos ---

def create_tipo_respaldo(db: Session, tipo: TipoRespaldoCreate) -> TipoRespaldo:
    db_tipo = TipoRespaldo(**tipo.model_dump())
    db.add(db_tipo)
    db.commit()
    db.refresh(db_tipo)
    return db_tipo

def get_tipos_respaldo(db: Session) -> List[TipoRespaldo]:
    return db.query(TipoRespaldo).all()

def delete_tipo_respaldo(db: Session, id_tipo: int) -> bool:
    db_tipo = db.query(TipoRespaldo).filter(TipoRespaldo.id_tipo_respaldo == id_tipo).first()
    if db_tipo:
        db.delete(db_tipo)
        db.commit()
        return True
    return False

def create_tipo_almacenamiento(db: Session, tipo: TipoAlmacenamientoCreate) -> TipoAlmacenamiento:
    db_tipo = TipoAlmacenamiento(**tipo.model_dump())
    db.add(db_tipo)
    db.commit()
    db.refresh(db_tipo)
    return db_tipo

def get_tipos_almacenamiento(db: Session) -> List[TipoAlmacenamiento]:
    return db.query(TipoAlmacenamiento).all()

def delete_tipo_almacenamiento(db: Session, id_tipo: int) -> bool:
    db_tipo = db.query(TipoAlmacenamiento).filter(TipoAlmacenamiento.id_tipo_almacenamiento == id_tipo).first()
    if db_tipo:
        db.delete(db_tipo)
        db.commit()
        return True
    return False

# --- Rutas de Respaldo ---

def create_ruta_respaldo(db: Session, ruta: RutaRespaldoCreate) -> RutaRespaldo:
    db_ruta = RutaRespaldo(**ruta.model_dump())
    db.add(db_ruta)
    db.commit()
    db.refresh(db_ruta)
    return db_ruta

def get_rutas_respaldo(db: Session) -> List[RutaRespaldo]:
    return db.query(RutaRespaldo).all()

def get_rutas_respaldo_by_servidor(db: Session, id_servidor: int) -> List[RutaRespaldo]:
    return db.query(RutaRespaldo).filter(RutaRespaldo.id_servidor == id_servidor).all()

def get_ruta_respaldo(db: Session, id_ruta: int) -> Optional[RutaRespaldo]:
    return db.query(RutaRespaldo).filter(RutaRespaldo.id_ruta == id_ruta).first()

def update_ruta_respaldo(db: Session, id_ruta: int, ruta_update: RutaRespaldoUpdate) -> Optional[RutaRespaldo]:
    db_ruta = get_ruta_respaldo(db, id_ruta)
    if not db_ruta:
        return None
    for key, value in ruta_update.model_dump(exclude_unset=True).items():
        setattr(db_ruta, key, value)
    db.commit()
    db.refresh(db_ruta)
    return db_ruta

def delete_ruta_respaldo(db: Session, id_ruta: int) -> bool:
    db_ruta = get_ruta_respaldo(db, id_ruta)
    if db_ruta:
        db.delete(db_ruta)
        db.commit()
        return True
    return False

# --- Políticas de Respaldo ---

def create_politica_respaldo(db: Session, politica: PoliticaRespaldoCreate) -> PoliticaRespaldo:
    db_politica = PoliticaRespaldo(**politica.model_dump())
    db.add(db_politica)
    db.commit()
    db.refresh(db_politica)
    return db_politica

def get_politicas_respaldo(db: Session) -> List[PoliticaRespaldo]:
    return db.query(PoliticaRespaldo).all()

def get_politica_respaldo(db: Session, id_politica: int) -> Optional[PoliticaRespaldo]:
    return db.query(PoliticaRespaldo).filter(PoliticaRespaldo.id_politica == id_politica).first()

def update_politica_respaldo(db: Session, id_politica: int, politica_update: PoliticaRespaldoUpdate) -> Optional[PoliticaRespaldo]:
    db_politica = get_politica_respaldo(db, id_politica)
    if not db_politica:
        return None
    for key, value in politica_update.model_dump(exclude_unset=True).items():
        setattr(db_politica, key, value)
    db.commit()
    db.refresh(db_politica)
    return db_politica

def delete_politica_respaldo(db: Session, id_politica: int) -> bool:
    db_politica = get_politica_respaldo(db, id_politica)
    if db_politica:
        db.delete(db_politica)
        db.commit()
        return True
    return False

def get_politica_assets_grouped(db: Session, id_politica: int) -> Optional[dict]:
    """
    Obtiene el detalle de una política y sus bases de datos asociadas,
    agrupándolas por servidor y motor DBMS.
    """
    from sqlalchemy.orm import joinedload
    from app.models.infrastructure_models import DBMS, Servidor, InstanciaDBMS, BaseDeDatos
    from app.models.backup_models import PoliticaRespaldo

    politica = db.query(PoliticaRespaldo).options(
        joinedload(PoliticaRespaldo.bases_datos)
        .joinedload(BaseDeDatos.instancia)
        .joinedload(InstanciaDBMS.servidor),
        joinedload(PoliticaRespaldo.bases_datos)
        .joinedload(BaseDeDatos.instancia)
        .joinedload(InstanciaDBMS.dbms)
    ).filter(PoliticaRespaldo.id_politica == id_politica).first()

    if not politica:
        return None

    # Agrupar por servidor
    grupos = {}
    for db_obj in politica.bases_datos:
        instancia = db_obj.instancia
        servidor = instancia.servidor
        motor = instancia.dbms
        
        server_key = (servidor.direccion_ip, f"{motor.nombre_dbms} {motor.version}")
        
        if server_key not in grupos:
            grupos[server_key] = []
            
        grupos[server_key].append({
            "id_base_datos": db_obj.id_base_datos,
            "nombre_base": db_obj.nombre_base,
            "tamano_mb": float(db_obj.tamano_mb or 0),
            "estado": "ACTIVO" if db_obj.id_estado_bd == 1 else "INACTIVO"
        })

    # Transformar a formato de respuesta
    servidores_vinculados = []
    for (ip, motor_str), dbs in grupos.items():
        servidores_vinculados.append({
            "ip": ip,
            "motor": motor_str,
            "databases": dbs
        })

    return {
        "id_politica": politica.id_politica,
        "nombre_politica": politica.nombre_politica,
        "descripcion": politica.descripcion,
        "frecuencia_horas": politica.frecuencia_horas,
        "retencion_dias": politica.retencion_dias,
        "servidores_vinculados": servidores_vinculados
    }

# --- Asignaciones ---

def asignar_politica_a_bd(db: Session, asignacion: AsignacionPoliticaBDCreate) -> AsignacionPoliticaBD:
    db_asignacion = AsignacionPoliticaBD(**asignacion.model_dump())
    db.add(db_asignacion)
    db.commit()
    db.refresh(db_asignacion)
    return db_asignacion

def eliminar_asignacion_politica(db: Session, id_base_datos: int, id_politica: int) -> bool:
    db_asignacion = db.query(AsignacionPoliticaBD).filter(
        AsignacionPoliticaBD.id_base_datos == id_base_datos,
        AsignacionPoliticaBD.id_politica == id_politica
    ).first()
    if db_asignacion:
        db.delete(db_asignacion)
        db.commit()
        return True
    return False

# --- Registros de Respaldo (Auditoría) ---

def create_registro_respaldo(db: Session, respaldo: RespaldoCreate) -> Respaldo:
    """
    Registra el resultado de una verificación (Éxito/Fallo).
    """
    db_respaldo = Respaldo(**respaldo.model_dump())
    db.add(db_respaldo)
    db.commit()
    db.refresh(db_respaldo)
    return db_respaldo

def get_historial_respaldos(db: Session, id_base_datos: Optional[int] = None) -> List[Respaldo]:
    query = db.query(Respaldo)
    if id_base_datos:
        query = query.filter(Respaldo.id_base_datos == id_base_datos)
    return query.order_by(Respaldo.fecha_inicio.desc()).all()

def get_rutas_respaldo_detalladas(db: Session) -> List[dict]:
    """
    Retorna todas las rutas de respaldo detalladas con IP del servidor, path, descripción y nombre del estado.
    """
    from app.models.user_models import UserStatus
    from app.models.infrastructure_models import Servidor
    
    results = db.query(RutaRespaldo, Servidor, UserStatus).join(
        Servidor, RutaRespaldo.id_servidor == Servidor.id_servidor
    ).join(
        UserStatus, RutaRespaldo.id_estado_ruta == UserStatus.id_estado
    ).all()
    
    return [
        {
            "ip": srv.direccion_ip,
            "path": ruta.path,
            "descripcion": ruta.descripcion_ruta,
            "estado": estado.nombre_estado
        }
        for ruta, srv, estado in results
    ]

def get_politicas_resumen_global(db: Session) -> List[dict]:
    """
    Retorna un resumen global de todas las políticas de respaldo y las bases de datos / servidores asignados.
    """
    from app.models.infrastructure_models import BaseDeDatos, InstanciaDBMS, Servidor, DBMS
    from sqlalchemy.sql import func
    
    query = db.query(
        PoliticaRespaldo.nombre_politica.label("politica"),
        Servidor.direccion_ip.label("ip_servidor"),
        func.concat(DBMS.nombre_dbms, " (", DBMS.version, ")").label("tipo_rdbms"),
        BaseDeDatos.nombre_base.label("base_de_datos"),
        BaseDeDatos.tamano_mb
    ).select_from(PoliticaRespaldo)\
     .join(BaseDeDatos.politicas)\
     .join(InstanciaDBMS, BaseDeDatos.id_instancia == InstanciaDBMS.id_instancia)\
     .join(DBMS, InstanciaDBMS.id_dbms == DBMS.id_dbms)\
     .join(Servidor, InstanciaDBMS.id_servidor == Servidor.id_servidor)\
     .order_by(PoliticaRespaldo.nombre_politica, Servidor.direccion_ip, BaseDeDatos.nombre_base)
     
    resultados = query.all()
    
    return [
        {
            "politica": r.politica,
            "ip_servidor": r.ip_servidor,
            "tipo_rdbms": r.tipo_rdbms,
            "base_de_datos": r.base_de_datos,
            "tamano_mb": float(r.tamano_mb or 0)
        }
        for r in resultados
    ]


def auto_associate_policy_to_databases(db: Session, payload: "AutoAsignarPoliticaRequest", user_id: int):
    from fastapi import HTTPException
    import re
    from app.models.infrastructure_models import Servidor, InstanciaDBMS, BaseDeDatos
    from app.models.audit_model import Bitacora
    from app.schemas import AutoAsignarPoliticaRequest

    # 1. Validar que la política exista
    politica = db.query(PoliticaRespaldo).filter(PoliticaRespaldo.id_politica == payload.id_politica).first()
    if not politica:
        raise HTTPException(status_code=404, detail="La política de respaldo especificada no existe.")

    # 2. Validar que el servidor exista
    servidor = db.query(Servidor).filter(Servidor.id_servidor == payload.id_servidor).first()
    if not servidor:
        raise HTTPException(status_code=404, detail="El servidor especificado no existe.")

    # 3. Procesar y normalizar el listado de bases de datos
    db_names_requested = [
        name.strip() for name in re.split(r'[,\n\r]+', payload.bases_datos_raw) 
        if name.strip()
    ]
    
    if not db_names_requested:
        raise HTTPException(status_code=400, detail="El listado de bases de datos está vacío.")

    # 4. Obtener todas las BDs reales asociadas al servidor
    dbs_in_server = db.query(BaseDeDatos).join(
        InstanciaDBMS, BaseDeDatos.id_instancia == InstanciaDBMS.id_instancia
    ).filter(
        InstanciaDBMS.id_servidor == payload.id_servidor
    ).all()

    # Mapeamos a minúsculas
    server_dbs_map = {bd.nombre_base.lower(): bd for bd in dbs_in_server}

    # 5. Validar pertenencia y existencia
    missing_dbs = []
    valid_db_ids = []
    
    for name in db_names_requested:
        name_lower = name.lower()
        if name_lower in server_dbs_map:
            valid_db_ids.append(server_dbs_map[name_lower].id_base_datos)
        else:
            missing_dbs.append(name)

    if missing_dbs:
        raise HTTPException(
            status_code=400, 
            detail={
                "message": "Algunas bases de datos no existen o no están registradas en este servidor.",
                "missing_databases": missing_dbs
            }
        )

    # 6. Guardar relaciones (limpiando asignaciones anteriores de estas BDs)
    db.query(AsignacionPoliticaBD).filter(
        AsignacionPoliticaBD.id_base_datos.in_(valid_db_ids)
    ).delete(synchronize_session=False)

    # Crear nuevas asignaciones
    for db_id in valid_db_ids:
        nueva_asignacion = AsignacionPoliticaBD(
            id_base_datos=db_id,
            id_politica=payload.id_politica
        )
        db.add(nueva_asignacion)

    # 7. Registrar en bitácora de auditoría
    nueva_bitacora = Bitacora(
        entidad_afectada="AsignacionPoliticaBD (Auto)",
        id_entidad=payload.id_politica,
        descripcion_evento=f"Asignación masiva automática de política '{politica.nombre_politica}' a {len(valid_db_ids)} BDs del servidor '{servidor.nombre_servidor}'.",
        id_usuario=user_id,
        id_tipo_evento=5  # Tipo de evento de ejecución/asignación
    )
    db.add(nueva_bitacora)
    
    db.commit()

    return {
        "success": True,
        "message": f"Asociación masiva exitosa. Se asignó la política a {len(valid_db_ids)} bases de datos.",
        "asociadas": db_names_requested
    }


def get_historial_respaldos_enriquecido(db: Session, id_base_datos: Optional[int] = None) -> List[dict]:
    """
    Retorna el historial de ejecuciones de respaldos enriquecido con
    detalles de servidor, IP, DBMS, bases de datos y criticidades.
    """
    from app.models.infrastructure_models import BaseDeDatos, InstanciaDBMS, Servidor, DBMS, NivelCriticidad
    from app.models.user_models import UserStatus

    query = db.query(
        Respaldo,
        BaseDeDatos,
        InstanciaDBMS,
        Servidor,
        DBMS,
        NivelCriticidad,
        PoliticaRespaldo,
        UserStatus
    ).join(BaseDeDatos, Respaldo.id_base_datos == BaseDeDatos.id_base_datos)\
     .join(InstanciaDBMS, BaseDeDatos.id_instancia == InstanciaDBMS.id_instancia)\
     .join(Servidor, InstanciaDBMS.id_servidor == Servidor.id_servidor)\
     .join(DBMS, InstanciaDBMS.id_dbms == DBMS.id_dbms)\
     .join(NivelCriticidad, Servidor.id_nivel_criticidad == NivelCriticidad.id_nivel_criticidad)\
     .join(PoliticaRespaldo, Respaldo.id_politica == PoliticaRespaldo.id_politica)\
     .join(UserStatus, Respaldo.id_estado_ejecucion == UserStatus.id_estado)

    if id_base_datos:
        query = query.filter(Respaldo.id_base_datos == id_base_datos)

    results = query.order_by(Respaldo.fecha_inicio.desc()).all()

    enriched = []
    for resp, db_obj, inst, srv, dbms, crit, pol, status in results:
        enriched.append({
            "id_respaldo": resp.id_respaldo,
            "id_base_datos": resp.id_base_datos,
            "nombre_base": db_obj.nombre_base,
            "instancia": inst.nombre_instancia,
            "motor": f"{dbms.nombre_dbms} {dbms.version}",
            "servidor": srv.nombre_servidor,
            "ip": srv.direccion_ip,
            "criticidad": crit.nombre_nivel,
            "id_politica": resp.id_politica,
            "nombre_politica": pol.nombre_politica,
            "frecuencia_horas": pol.frecuencia_horas,
            "id_estado_ejecucion": resp.id_estado_ejecucion,
            "estado_ejecucion": status.nombre_estado,
            "nombre_archivo": resp.nombre_archivo or f"backup_db_{db_obj.nombre_base}_{inst.nombre_instancia}.sql.gz",
            "path_fisico_actual": resp.path_fisico_actual,
            "tamano_mb": float(resp.tamano_mb) if resp.tamano_mb is not None else 0.0,
            "fecha_inicio": resp.fecha_inicio.isoformat() if resp.fecha_inicio else None,
            "fecha_fin": resp.fecha_fin.isoformat() if resp.fecha_fin else None,
            "fecha_descubrimiento": resp.fecha_descubrimiento.isoformat() if resp.fecha_descubrimiento else None,
        })
    return enriched



