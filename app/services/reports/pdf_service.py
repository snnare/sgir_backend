import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

# Directorios de la aplicación
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates", "reports")
STATIC_ASSETS_DIR = os.path.join(BASE_DIR, "static", "assets")

# Configurar el entorno de Jinja2
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

def generate_db_inventory_pdf(databases: list, peso_total: float, usuario_nombre: str) -> bytes:
    """
    Renderiza la plantilla HTML de inventario con Jinja2 e inyecta
    los datos y recursos (logo y favicon locales) para generar el PDF con WeasyPrint.
    """
    # 1. Obtener los paths absolutos para WeasyPrint (usando el protocolo file://)
    logo_path = os.path.join(STATIC_ASSETS_DIR, "logo_uaemex.png")
    favicon_path = os.path.join(STATIC_ASSETS_DIR, "favicon.png")
    
    logo_url = f"file://{logo_path}" if os.path.exists(logo_path) else None
    favicon_url = f"file://{favicon_path}" if os.path.exists(favicon_path) else None

    # 2. Cargar la plantilla HTML
    template = env.get_template("db_inventory_template.html")
    
    # 3. Formatear la fecha y los valores numéricos de forma elegante
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    peso_total_formatted = f"{peso_total:,.2f}"
    
    databases_formatted = []
    for db in databases:
        tamano = float(db.get("tamano_mb") or 0)
        databases_formatted.append({
            "ip": db.get("ip", "N/D"),
            "motor": db.get("motor", "N/D"),
            "nombre": db.get("nombre", "N/D"),
            "tamano_mb": f"{tamano:,.2f}"
        })
    
    # 4. Renderizar el HTML con los datos reales
    html_content = template.render(
        fecha=fecha_actual,
        usuario_generador=usuario_nombre,
        databases=databases_formatted,
        peso_total=peso_total_formatted,
        logo_url=logo_url,
        favicon_url=favicon_url
    )
    
    # 5. Generar y retornar el PDF en bytes usando WeasyPrint
    pdf_bytes = HTML(string=html_content).write_pdf()
    return pdf_bytes

def generate_general_sre_pdf(servidores: list, databases: list, total_alerts: int, usuario_nombre: str) -> bytes:
    """
    Renderiza la plantilla HTML de SRE consolidado con Jinja2 e inyecta
    los datos y recursos (logo y favicon locales) para generar el PDF con WeasyPrint.
    """
    logo_path = os.path.join(STATIC_ASSETS_DIR, "logo_uaemex.png")
    favicon_path = os.path.join(STATIC_ASSETS_DIR, "favicon.png")
    
    logo_url = f"file://{logo_path}" if os.path.exists(logo_path) else None
    favicon_url = f"file://{favicon_path}" if os.path.exists(favicon_path) else None

    template = env.get_template("general_infrastructure_template.html")
    
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Calcular KPIs
    total_servidores = len(servidores)
    total_instancias = len(set(db.get("ip") for db in databases))
    
    html_content = template.render(
        titulo_reporte="Reporte Consolidado de SRE e Infraestructura",
        tipo_reporte="Consolidado General de Infraestructura (Offline)",
        fecha=fecha_actual,
        usuario_generador=usuario_nombre,
        total_servidores=total_servidores,
        total_instancias=total_instancias,
        total_databases=len(databases),
        total_alertas_activas=total_alerts,
        servidores=servidores,
        databases=databases,
        logo_url=logo_url,
        favicon_url=favicon_url
    )
    
    pdf_bytes = HTML(string=html_content).write_pdf()
    return pdf_bytes

def generate_sre_sla_pdf(servidores_sla: list, incidentes: list, average_sla: float, total_incidents: int, total_days: int, lowest_sla_srv: str, usuario_nombre: str) -> bytes:
    """
    Renderiza la plantilla HTML de SLA e incidentes SRE con Jinja2 e inyecta
    los datos y recursos (logo y favicon locales) para generar el PDF con WeasyPrint.
    """
    logo_path = os.path.join(STATIC_ASSETS_DIR, "logo_uaemex.png")
    favicon_path = os.path.join(STATIC_ASSETS_DIR, "favicon.png")
    
    logo_url = f"file://{logo_path}" if os.path.exists(logo_path) else None
    favicon_url = f"file://{favicon_path}" if os.path.exists(favicon_path) else None

    template = env.get_template("sre_sla_uptime_template.html")
    
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html_content = template.render(
        titulo_reporte="Reporte Mensual de SLA e Incidentes SRE",
        fecha=fecha_actual,
        usuario_generador=usuario_nombre,
        average_sla=f"{average_sla:,.2f}",
        total_incidents=total_incidents,
        total_monitored_days=total_days,
        lowest_sla_srv=lowest_sla_srv,
        servidores_sla=servidores_sla,
        incidentes=incidentes,
        logo_url=logo_url,
        favicon_url=favicon_url
    )
    
    pdf_bytes = HTML(string=html_content).write_pdf()
    return pdf_bytes
