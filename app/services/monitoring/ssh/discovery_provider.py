def execute_command(client, command: str) -> str:
    stdin, stdout, stderr = client.exec_command(command)
    return stdout.read().decode('utf-8').strip()

def search_files_modern(client, path: str, extension: str) -> list:
    """
    Búsqueda de archivos en sistemas modernos usando find con filtro de tipo y tamaño en bytes.
    Retorna lista de tuplas (path, size_bytes).
    """
    # Usamos printf para obtener path y tamaño en bytes separados por |
    cmd = f"find {path} -name '*{extension}' -type f -printf '%p|%s\\n' 2>/dev/null"
    output = execute_command(client, cmd)
    if not output:
        return []
    
    results = []
    for line in output.split('\n'):
        if '|' in line:
            parts = line.split('|')
            results.append((parts[0], int(parts[1])))
    return results

def search_files_legacy(client, path: str, extension: str) -> list:
    """
    Búsqueda de archivos en sistemas antiguos usando ls para obtener el tamaño.
    Retorna lista de tuplas (path, size_bytes).
    """
    # En legacy, find puede no tener -printf. Usamos una combinación con ls.
    # Buscamos archivos y para cada uno ejecutamos ls -nl (n para IDs numéricos, l para formato largo)
    cmd = f"find {path} -name '*{extension}' -type f -exec ls -nl {{}} \\; 2>/dev/null"
    output = execute_command(client, cmd)
    if not output:
        return []
    
    results = []
    for line in output.split('\n'):
        parts = line.split()
        if len(parts) >= 9:
            # En ls -l: 1:perm 2:links 3:user 4:group 5:size 6-8:date 9:path
            size = int(parts[4])
            path_file = parts[8]
            results.append((path_file, size))
    return results
