def execute_command(client, command: str) -> str:
    stdin, stdout, stderr = client.exec_command(command)
    return stdout.read().decode('utf-8').strip()

def search_files_modern(client, path: str, extension: str) -> list:
    """
    Búsqueda de archivos en sistemas modernos usando find con filtro de tipo, tamaño y fecha.
    Retorna lista de diccionarios con {path, size_bytes, mtime}.
    """
    # %p|%s|%TY-%Tm-%Td %TH:%TM:%TS
    cmd = f"find {path} -name '*{extension}' -type f -printf '%p|%s|%TY-%Tm-%Td %TH:%TM:%TS\\n' 2>/dev/null"
    output = execute_command(client, cmd)
    if not output:
        return []
    
    results = []
    for line in output.split('\n'):
        if '|' in line:
            parts = line.split('|')
            results.append({
                "path": parts[0], 
                "size": int(parts[1]),
                "mtime": parts[2]
            })
    return results

def search_files_legacy(client, path: str, extension: str) -> list:
    """
    Búsqueda de archivos en sistemas antiguos usando ls para obtener el tamaño y fecha.
    Retorna lista de diccionarios con {path, size_bytes, mtime}.
    """
    # Usamos ls -nl --time-style=long-iso si está disponible, o simplemente ls -nl
    # Para máxima compatibilidad en legacy puro, ls -nl suele dar:
    # -rw-r--r-- 1 1000 1000 1024 May 12 10:00 /path/file.sql
    cmd = f"find {path} -name '*{extension}' -type f -exec ls -nl --time-style=long-iso {{}} \\; 2>/dev/null"
    output = execute_command(client, cmd)
    
    # Si falla por --time-style, intentamos ls -nl estándar
    if not output:
        cmd = f"find {path} -name '*{extension}' -type f -exec ls -nl {{}} \\; 2>/dev/null"
        output = execute_command(client, cmd)

    if not output:
        return []
    
    results = []
    for line in output.split('\n'):
        parts = line.split()
        if len(parts) >= 8:
            # ISO Style: [0:perm, 1:links, 2:user, 3:group, 4:size, 5:date, 6:time, 7:path]
            # Standard: [0:perm, 1:links, 2:user, 3:group, 4:size, 5:month, 6:day, 7:time/year, 8:path]
            try:
                size = int(parts[4])
                if "-" in parts[5]: # Long ISO
                    mtime = f"{parts[5]} {parts[6]}"
                    path_file = parts[7]
                else: # Standard
                    mtime = f"{parts[5]} {parts[6]} {parts[7]}"
                    path_file = parts[8]
                results.append({"path": path_file, "size": size, "mtime": mtime})
            except: continue
    return results

def list_recent_files_modern(client, path: str, days: int = 1) -> list:
    """
    Lista archivos modificados en los últimos 'n' días.
    Retorna lista de diccionarios con name y size_bytes.
    """
    cmd = f"find {path} -maxdepth 1 -type f -mtime -{days} -printf '%f|%s\\n' 2>/dev/null"
    output = execute_command(client, cmd)
    if not output:
        return []
    
    results = []
    for line in output.split('\n'):
        if '|' in line:
            parts = line.split('|')
            results.append({"name": parts[0], "size": int(parts[1])})
    return results

def list_recent_files_legacy(client, path: str, days: int = 1) -> list:
    """
    Lista archivos modificados recientemente en sistemas antiguos.
    Usa mtime de find (estándar POSIX).
    """
    cmd = f"find {path} -maxdepth 1 -type f -mtime -{days} -exec ls -nl {{}} \\; 2>/dev/null"
    output = execute_command(client, cmd)
    if not output:
        return []
    
    results = []
    for line in output.split('\n'):
        parts = line.split()
        if len(parts) >= 9:
            size = int(parts[4])
            # En ls -nl, el nombre puede estar en la última posición, pero find puede devolver path completo
            # Intentamos extraer solo el nombre del path
            full_path = parts[8]
            name = full_path.split('/')[-1]
            results.append({"name": name, "size": size})
    return results

def discover_filesystems(client) -> list:
    """
    Ejecuta df -h y parsea la salida para identificar puntos de montaje reales.
    Filtra filesystems virtuales como tmpfs, devtmpfs, etc.
    """
    cmd = "df -h"
    output = execute_command(client, cmd)
    if not output:
        return []
    
    lines = output.split('\n')
    if not lines:
        return []
    
    # El encabezado suele ser: Filesystem Size Used Avail Use% Mounted on
    results = []
    for line in lines[1:]: # Saltar encabezado
        parts = line.split()
        if len(parts) >= 6:
            fs_source = parts[0]
            size = parts[1]
            used = parts[2]
            avail = parts[3]
            usage_pct = parts[4]
            mount_point = parts[5]
            
            # Filtro de FS irrelevantes para monitoreo de SRE
            ignored_prefixes = ['tmpfs', 'devtmpfs', 'udev', 'loop']
            if any(fs_source.startswith(p) for p in ignored_prefixes):
                continue
            if mount_point.startswith('/boot') or mount_point.startswith('/run'):
                continue
                
            results.append({
                "source": fs_source,
                "size": size,
                "used": used,
                "avail": avail,
                "usage_pct": usage_pct,
                "mount_point": mount_point
            })
    return results
