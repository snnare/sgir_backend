import time
import paramiko
from app.models.infrastructure_models import Servidor, CredencialAcceso
from app.core.security.encryption import decrypt_password
from fastapi import HTTPException

# POOL GLOBAL DE CONEXIONES SSH: { servidor_id: paramiko.SSHClient }
SSH_POOL = {}

def ssh_no_legacy(host: str, port: int, user: str, password: str) -> paramiko.SSHClient:
    """
    Perfil de conexión estándar para sistemas modernos con Keep-Alive.
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
    # Configurar Keep-Alive cada 30 segundos
    transport = client.get_transport()
    if transport:
        transport.set_keepalive(30)
    return client

def ssh_legacy(host: str, port: int, user: str, password: str) -> paramiko.SSHClient:
    """
    Perfil de conexión para sistemas antiguos (RHEL 4/5).
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
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
    # Keep-Alive para legacy
    transport = client.get_transport()
    if transport:
        transport.set_keepalive(30)
    return client

def is_connection_alive(client: paramiko.SSHClient) -> bool:
    """Verifica si la conexión sigue activa intentando un comando nulo."""
    if client is None or client.get_transport() is None or not client.get_transport().is_active():
        return False
    try:
        # Intentar una operación mínima para confirmar el canal
        client.exec_command('ls -d .', timeout=5)
        return True
    except Exception:
        return False

def get_ssh_connection(servidor: Servidor, credencial: CredencialAcceso, use_pool: bool = True) -> paramiko.SSHClient:
    """
    ORQUESTADOR DE CONEXIÓN SSH CON POOLING:
    1. Reutiliza conexiones existentes si están activas.
    2. Gestiona reintentos y perfiles legacy.
    """
    
    # 1. Verificar Pool (Si se solicita)
    if use_pool and servidor.id_servidor in SSH_POOL:
        existing_client = SSH_POOL[servidor.id_servidor]
        if is_connection_alive(existing_client):
            print(f"[SSH POOL] Reutilizando conexión activa para {servidor.direccion_ip}")
            return existing_client
        else:
            print(f"[SSH POOL] Conexión muerta para {servidor.direccion_ip}, re-conectando...")
            try:
                existing_client.close()
            except:
                pass
            del SSH_POOL[servidor.id_servidor]

    # 2. Validación de Tipo
    if credencial.id_tipo_acceso != 1:
        raise HTTPException(
            status_code=400, 
            detail=f"Error: La credencial '{credencial.usuario}' no es de tipo SSH."
        )

    password = decrypt_password(credencial.password_hash)
    host_raw = servidor.direccion_ip
    user = credencial.usuario
    
    if ":" in host_raw:
        host, port_str = host_raw.split(":")
        port = int(port_str)
    else:
        host = host_raw
        port = 22

    max_intentos = 3
    ultimo_error = ""

    for intento in range(1, max_intentos + 1):
        try:
            print(f"[SSH] Nuevo Handshake {intento}/{max_intentos} para {host}:{port} (Legacy: {servidor.es_legacy})")
            
            client = None
            if servidor.es_legacy:
                client = ssh_legacy(host, port, user, password)
            else:
                client = ssh_no_legacy(host, port, user, password)
            
            # Guardar en Pool si la conexión fue exitosa
            if use_pool:
                SSH_POOL[servidor.id_servidor] = client
            return client
                
        except Exception as e:
            print(f"[SSH] Fallo en handshake {intento}: {str(e)}")
            ultimo_error = str(e)
            if intento < max_intentos:
                time.sleep(2) # Reducido de 5 a 2 para mayor agilidad
            continue

    raise HTTPException(
        status_code=500, 
        detail=f"Fallo de conexión SSH con {servidor.direccion_ip} tras {max_intentos} intentos."
    )

def close_all_ssh_connections():
    """Libera todas las conexiones del pool (Uso en apagado del sistema)."""
    for srv_id, client in SSH_POOL.items():
        try:
            client.close()
            print(f"[SSH POOL] Conexión {srv_id} cerrada.")
        except:
            pass
    SSH_POOL.clear()

