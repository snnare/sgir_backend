import paramiko
from app.models.infrastructure_models import Servidor, CredencialAcceso
from app.core.security.encryption import decrypt_password
from fastapi import HTTPException

def get_ssh_client(servidor: Servidor, credencial: CredencialAcceso) -> paramiko.SSHClient:
    """
    FABRICA DE CONEXION: Solo se encarga de establecer el canal SSH.
    """
    try:
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
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error de conexión SSH con {servidor.direccion_ip}: {str(e)}"
        )
