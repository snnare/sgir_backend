import time
import paramiko
from app.models.infrastructure_models import Servidor, CredencialAcceso
from app.core.security.encryption import decrypt_password
from fastapi import HTTPException

def ssh_no_legacy(host: str, port: int, user: str, password: str) -> paramiko.SSHClient:
    """
    Perfil de conexión estándar para sistemas modernos.
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=host,
        port=port,
        username=user,
        password=password,
        timeout=10
    )
    return client

def ssh_legacy(host: str, port: int, user: str, password: str) -> paramiko.SSHClient:
    """
    Perfil de conexión para sistemas antiguos (RHEL 4/5).
    Permite algoritmos de cifrado y key-exchange deprecados.
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Configuraciones específicas para legacy (ejemplo de algoritmos antiguos)
    # Nota: Paramiko 3.x+ requiere habilitar explícitamente ciertos algoritmos
    # si el servidor es extremadamente viejo (como RHEL 4).
    client.connect(
        hostname=host,
        port=port,
        username=user,
        password=password,
        timeout=15,
        banner_timeout=30,
        allow_agent=False,
        look_for_keys=False,
        disabled_algorithms={'pubkeys': ['rsa-sha2-256', 'rsa-sha2-512']} 
    )
    return client

def get_ssh_connection(servidor: Servidor, credencial: CredencialAcceso) -> paramiko.SSHClient:
    """
    ORQUESTADOR DE CONEXIÓN SSH:
    1. Valida que la credencial sea de tipo SSH.
    2. Gestiona reintentos (Máximo 3, con espera de 5s).
    3. Selecciona perfil según el atributo 'es_legacy' del servidor.
    """
    
    # 1. Validación de Tipo (ID 1 = SSH según init-db.sql)
    if credencial.id_tipo_acceso != 1:
        raise HTTPException(
            status_code=400, 
            detail=f"Error: La credencial '{credencial.usuario}' no es de tipo SSH (ID Tipo: {credencial.id_tipo_acceso})."
        )

    password = decrypt_password(credencial.password_hash)
    host = servidor.direccion_ip
    user = credencial.usuario
    
    # Mapeo de puerto (Default: 22, Local Dev: 2222)
    port = 22
    if ":" in host:
        host, port_str = host.split(":")
        port = int(port_str)
    elif host in ["localhost", "127.0.0.1"]:
        port = 2222 

    max_intentos = 3
    ultimo_error = ""

    # 2. Manejo de Reintentos
    for intento in range(1, max_intentos + 1):
        try:
            print(f"[SSH] Intento {intento}/{max_intentos} para {host}:{port} (Legacy: {servidor.es_legacy})")
            # 3. Selección de Perfil e Intento de Conexión
            if servidor.es_legacy:
                return ssh_legacy(host, port, user, password)
            else:
                return ssh_no_legacy(host, port, user, password)
                
        except Exception as e:
            print(f"[SSH] Fallo en intento {intento}: {str(e)}")
            ultimo_error = str(e)
            if intento < max_intentos:
                # 3. Reintento (Esperar 5 segundos)
                time.sleep(5)
            continue

    # 4. Resultado final si falla después de los intentos
    raise HTTPException(
        status_code=500, 
        detail=f"Fallo de conexión SSH con {servidor.direccion_ip} tras {max_intentos} intentos. Error: {ultimo_error}"
    )
