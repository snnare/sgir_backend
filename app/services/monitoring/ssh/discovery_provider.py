def execute_command(client, command: str) -> str:
    stdin, stdout, stderr = client.exec_command(command)
    return stdout.read().decode('utf-8').strip()

def search_files_modern(client, path: str, extension: str) -> list:
    """
    Búsqueda de archivos en sistemas modernos usando find con filtro de tipo.
    """
    cmd = f"find {path} -name '*{extension}' -type f 2>/dev/null"
    output = execute_command(client, cmd)
    if not output:
        return []
    return output.split('\n')

def search_files_legacy(client, path: str, extension: str) -> list:
    """
    Búsqueda de archivos en sistemas antiguos (sintaxis simplificada).
    """
    # En sistemas muy viejos, a veces -type f puede dar problemas o no existir según la versión de find
    cmd = f"find {path} -name '*{extension}' 2>/dev/null"
    output = execute_command(client, cmd)
    if not output:
        return []
    return output.split('\n')
