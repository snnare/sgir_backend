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

def list_recent_files_modern(client, path: str, days: int = 1, deep: bool = False) -> list:
    """
    Lista archivos modificados en los últimos 'n' días.
    Retorna lista de diccionarios con name, path y size_bytes.
    """
    depth_filter = "" if deep else "-maxdepth 1"
    mtime_filter = f"-mtime -{days}" if days > 0 else ""
    cmd = f"find {path} {depth_filter} -type f {mtime_filter} -printf '%p|%s\\n' 2>/dev/null"
    output = execute_command(client, cmd)
    if not output:
        return []
    
    results = []
    for line in output.split('\n'):
        if '|' in line:
            parts = line.split('|')
            full_path = parts[0]
            name = full_path.split('/')[-1]
            results.append({"name": name, "path": full_path, "size": int(parts[1])})
    return results

def list_recent_files_legacy(client, path: str, days: int = 1, deep: bool = False) -> list:
    """
    Lista archivos modificados recientemente en sistemas antiguos.
    Usa mtime de find (estándar POSIX).
    """
    depth_filter = "" if deep else "-maxdepth 1"
    mtime_filter = f"-mtime -{days}" if days > 0 else ""
    cmd = f"find {path} {depth_filter} -type f {mtime_filter} -exec ls -nl {{}} \\; 2>/dev/null"
    output = execute_command(client, cmd)
    if not output:
        return []
    
    results = []
    for line in output.split('\n'):
        parts = line.split()
        if len(parts) >= 8:
            try:
                size = int(parts[4])
                if "-" in parts[5]: # Long ISO
                    full_path = parts[7]
                else: # Standard
                    if len(parts) >= 9:
                        full_path = parts[8]
                    else:
                        continue
                name = full_path.split('/')[-1]
                results.append({"name": name, "path": full_path, "size": size})
            except:
                continue
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

def discover_cron_tasks(client) -> list:
    """
    Ejecuta crontab -l y devuelve una lista de tareas activas procesadas.
    """
    cmd = "crontab -l"
    output = execute_command(client, cmd)
    
    if not output or "no crontab for" in output.lower():
        return []
        
    results = []
    for line in output.split('\n'):
        clean_line = line.strip()
        
        # Ignorar vacíos, comentarios y variables de entorno de cron
        if not clean_line or clean_line.startswith('#'):
            continue
        if any(clean_line.startswith(env) for env in ['SHELL=', 'PATH=', 'MAILTO=', 'HOME=']):
            continue
            
        # Intentar separar cron de comando (mínimo 5 campos de tiempo + comando)
        parts = clean_line.split()
        if len(parts) >= 6:
            # Los primeros 5 campos son el cron, el resto es el comando
            schedule = " ".join(parts[:5])
            command = " ".join(parts[5:])
            results.append({
                "linea_completa": clean_line,
                "schedule": schedule,
                "command": command
            })
        elif clean_line.startswith('@'): # Soporte para alias como @daily
            parts = clean_line.split()
            if len(parts) >= 2:
                results.append({
                    "linea_completa": clean_line,
                    "schedule": parts[0],
                    "command": " ".join(parts[1:])
                })
            
    return results

def calculate_file_hash(client, file_path: str, es_legacy: bool):
    """
    Calcula el hash de integridad de un archivo remoto por SSH.
    Si el OS es legado (es_legacy=True), calcula usando md5sum/md5/csum.
    Si el OS es moderno (es_legacy=False), calcula usando sha256sum/shasum.
    Si el intento moderno falla, realiza un fallback automático a la versión legada.
    """
    import shlex
    escaped_path = shlex.quote(file_path)
    
    if es_legacy:
        # Intento 1: md5sum (Linux legacy estándar)
        cmd = f"md5sum {escaped_path} 2>/dev/null"
        output = execute_command(client, cmd)
        if output and len(output.split()) >= 1:
            return output.split()[0]
            
        # Intento 2: md5 (Solaris / BSD / macOS)
        cmd = f"md5 {escaped_path} 2>/dev/null"
        output = execute_command(client, cmd)
        if output and len(output.split()) >= 1:
            parts = output.split()
            if len(parts[-1]) == 32:
                return parts[-1]
            return parts[0]
            
        # Intento 3: csum MD5 (AIX)
        cmd = f"csum -h MD5 {escaped_path} 2>/dev/null"
        output = execute_command(client, cmd)
        if output and len(output.split()) >= 1:
            return output.split()[0]
            
        return None
    else:
        # Intento 1: sha256sum (Linux moderno estándar)
        cmd = f"sha256sum {escaped_path} 2>/dev/null"
        output = execute_command(client, cmd)
        if output and len(output.split()) >= 1:
            token = output.split()[0]
            if len(token) == 64:
                return token
                
        # Intento 2: shasum -a 256 (sistemas Unix con Perl / macOS)
        cmd = f"shasum -a 256 {escaped_path} 2>/dev/null"
        output = execute_command(client, cmd)
        if output and len(output.split()) >= 1:
            token = output.split()[0]
            if len(token) == 64:
                return token
                
        # Fallback a legado si los intentos modernos fallan
        return calculate_file_hash(client, file_path, es_legacy=True)

