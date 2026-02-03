import streamlit as st
import pandas as pd
import re
from html import escape

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Clasificador de Causas – CONAF",
    page_icon="🌲",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES Y DATOS
# ═══════════════════════════════════════════════════════════════════════════════

# Columnas del CSV
COL_CODIGO_ESP = "Código especifico"
COL_CODIGO_GEN = "Código general"
COL_CAUSA_GEN = "Causa general"
COL_GRUPO = "Grupo de causa"
COL_CAUSA = "Causa"

# Glosarios
GLOSARIO_GRUPOS = {
    "Grupo 1 - Accidentales": "Agrupan aquellos incendios generados por un suceso eventual, inesperado e impredecible, generado al emplear fuentes de calor.",
    "Grupo 2 - Intencionales": "Acciones antrópicas deliberadas que derivan en un incendio forestal al aplicar una fuente de calor a la vegetación con el fin de lograr un efecto determinado.",
    "Grupo 3 - Naturales": "Incendios forestales generados sin la intervención antrópica, donde actúan las condiciones propias del medio natural.",
    "Grupo 4 - Negligentes": "Incendios forestales generados por falta de cuidado, malas prácticas, omisión o desconocimiento de la normativa vigente.",
    "Grupo 5 - Indeterminadas": "Son aquellos incendios forestales que tienen causa indeterminada, es decir que se investigan, pero no es posible establecer la causa origen o bien no fue posible investigar.",
}

GLOSARIO_POR_CODIGO = {
    "1.1": ("Faenas forestales", "Actividades asociadas a la producción forestal a micro o macro escala. Considera trabajos de eliminación de desechos vegetales, manejo de plantaciones y uso de maquinaria y herramientas. Se consideran dentro de esta categoría incendios en terrenos de aptitud preferentemente forestal y los predios particulares con especies forestales nativas o exóticas."),
    "1.2": ("Faenas agrícolas y pecuarias", "Actividades asociadas a la producción agrícola y pecuaria a micro o macro escala. Considera eliminación de desechos vegetales, manejo de cultivos y uso de maquinaria y herramientas. Se incluyen los incendios en terrenos de aptitud agrícola."),
    "1.3": ("Actividades al aire libre", "Actividades asociadas al empleo de fuentes de calor en actividades de entretención al aire libre en áreas habilitadas como camping, caminatas, actividades de pesca, caza u otras."),
    "1.4": ("Vías férreas", "Actividades o eventos asociadas al desplazamiento, funcionamiento o mantención del sistema ferroviario."),
    "1.5": ("Actividades de control y extinción de incendios forestales", "Clasificación que incluye accidentes de aeronaves en combate de incendio forestal, reconocimiento de zonas y el uso de herramientas en actividades de extinción."),
    "1.6": ("Parcelaciones, edificaciones residenciales, industriales u otras", "Las parcelaciones son subdivisiones del terreno rural, destinadas para el desarrollo inmobiliario, cultivos u otros fines. Las edificaciones residenciales corresponden a viviendas, habitadas por personas o familias. Las edificaciones industriales son los que albergan actividad económica y/o productiva."),
    "1.7": ("Originados por desplazamiento de personas, vehículos o aeronaves", "Incendio forestal generado por desplazamiento de personas a través de diversos medios de transportes, terrestre o aéreo."),
    "1.8": ("Otras quemas", "Otras quemas distintas a lo dispuesto en el DS 276, así como también, la quema avisada para limpieza de canales, cercas u otros."),
    "1.9": ("Líneas eléctricas", "Situaciones asociadas a los tendidos eléctricos de baja, media o alta tensión. Incluye todo tipo de estructura asociada tales como postación, transformador, otros. Esta causa general hace referencia a que es total y exclusiva responsabilidad de las empresas eléctricas el correcto funcionamiento, instalación y mantenimiento de la vegetación circundante."),
    "1.10": ("Otras causas", "Actividades o acciones particulares que no están asociados a las causas generales anteriores o que no se encuentran dentro del sistema de clasificación de causas."),
    "2.1": ("Incendios Intencionales", "Incendios forestales provocados de manera premeditada y directa con diversas motivaciones: conflictos personales, venganza, ataques incendiarios, conflictos territoriales, obtención de beneficios económicos, observación de operaciones de combate, encubrimiento de delitos, extracción de productos del bosque, o cambio irregular de uso del suelo."),
    "3.1": ("Incendios naturales", "Incendios forestales generados por fenómenos naturales como caída de rayo, actividad volcánica u otras causas naturales sin intervención humana."),
    "4.1": ("Faenas forestales", "Incendios forestales generados por negligencia en actividades forestales: quemas no avisadas o mal ejecutadas, incendio de maquinaria por falta de mantención, contacto con conductor eléctrico, partículas incandescentes, rebrotes de quemas, empleo inadecuado de fuentes de calor en campamentos forestales."),
    "4.2": ("Faenas agrícolas y pecuarias", "Incendios forestales generados por negligencia en actividades agrícolas y pecuarias: quemas no avisadas o mal ejecutadas, incendio de maquinaria por falta de mantención, contacto con conductor eléctrico, partículas incandescentes, rebrotes de quemas, empleo inadecuado de fuentes de calor en faenas agropecuarias."),
    "4.3": ("Actividades al aire libre", "Incendios forestales generados por el empleo de fuentes de calor por personas que realizan actividades recreativas en sectores no habilitados para el uso del fuego, tales como excursiones, camping, caza, pesca u otras."),
    "4.4": ("Vías férreas", "Causas negligentes asociadas al sistema ferroviario, incluyendo partículas incandescentes por falta de mantención de fajas de seguridad, uso de fuentes de calor en mantención y contacto o corte de conductor eléctrico de línea férrea."),
    "4.5": ("Actividades de control y extinción de incendios forestales", "Causas negligentes en operaciones de control y extinción, como rebrote de incendio declarado extinto por trabajo deficiente, o generado por uso de equipos durante operaciones de control."),
    "4.6": ("Parcelaciones, edificaciones residenciales, industriales u otras", "Causas negligentes asociadas a parcelaciones y edificaciones en zonas rurales o de interfaz, incluyendo uso de equipos de construcción, conexiones eléctricas irregulares, infraestructura de energía, chimeneas y desecho de cenizas."),
    "4.7": ("Originados por desplazamiento de personas, vehículos o aeronaves", "Causas negligentes por desplazamiento, como empleo de fuentes de calor en actividades religiosas o de peregrinación, y señalización en rutas o faenas de mantención."),
    "4.8": ("Otras quemas", "Causas negligentes por quemas no avisadas para limpieza, quema de basura residencial, desechos industriales, eliminación de fauna y uso de fuentes de calor en vertederos o basurales."),
    "4.9": ("Tendido eléctrico", "Causas negligentes asociadas al tendido eléctrico, como combustión por contacto con la vegetación, corte de conductor por caída de rama o fatiga de estructura, sobrecalentamiento de transformadores y otros elementos del sistema eléctrico."),
    "4.10": ("Otras causas", "Causas negligentes que no encaben en las anteriores: maniobras militares, faenas mineras, explosiones, fumar, menores de edad con fuente de calor, fuegos artificiales, elaboración de ladrillos, combustión espontánea y personas en situación de calle."),
    "4.11": ("Producción y/o extracción de productos y/o derivados del bosque", "Causas negligentes en actividades de producción forestal no industriales, como elaboración de carbón vegetal, extracción de hongos y frutos, confección de leña y actividades de apicultura."),
    "5.1": ("Incendios de causa indeterminada", "Incendios forestales donde, tras la investigación, no es posible establecer la causa origen, bien sea por área de inicio alterada, hipótesis sin validación o imposibilidad de llegar al área de inicio por dificultades geográficas."),
}

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES CACHEADAS
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data
def load_data():
    """Carga y procesa los datos del CSV con caché para optimizar performance."""
    try:
        df = pd.read_csv("causas_csv.csv", sep=";", encoding="utf-8-sig")
        df.columns = df.columns.str.strip()
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].str.strip()
        
        # Validar columnas requeridas
        required_cols = [COL_CODIGO_ESP, COL_CODIGO_GEN, COL_CAUSA_GEN, COL_GRUPO, COL_CAUSA]
        missing_cols = [c for c in required_cols if c not in df.columns]
        
        if missing_cols:
            st.error(f"⚠️ Columnas no encontradas en causas_csv.csv: {missing_cols}")
            st.info(f"📋 Columnas disponibles: {list(df.columns)}")
            st.info("💡 Asegúrate de que el archivo causas_csv.csv esté en el mismo directorio que la aplicación.")
            st.stop()
        
        return df
    
    except FileNotFoundError:
        st.error("❌ No se encontró el archivo causas_csv.csv")
        st.info("📥 Por favor, asegúrate de que el archivo causas_csv.csv esté en el mismo directorio que esta aplicación.")
        st.info("📄 El CSV debe contener las columnas: Código especifico, Código general, Causa general, Grupo de causa, Causa")
        st.stop()
    
    except Exception as e:
        st.error(f"❌ Error al cargar causas_csv.csv: {str(e)}")
        st.stop()

@st.cache_data
def get_unique_grupos(df):
    """Obtiene lista única de grupos."""
    return sorted(df[COL_GRUPO].unique().tolist())

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES HELPER
# ═══════════════════════════════════════════════════════════════════════════════

def get_grupo_class(grupo: str) -> str:
    """Retorna clase CSS según el grupo."""
    grupo_map = {
        "1": "g1",
        "2": "g2",
        "3": "g3",
        "4": "g4",
    }
    return grupo_map.get(grupo[0] if grupo else "", "g5")

def sanitize_text(text: str) -> str:
    """Sanitiza HTML para prevenir XSS."""
    return escape(str(text))

def extract_codigo_general(codigo_esp: str) -> str:
    """Extrae código general del específico: '4.9.3' → '4.9'"""
    parts = str(codigo_esp).split(".")
    return ".".join(parts[:2]) if len(parts) >= 2 else codigo_esp

def filter_dataframe(df: pd.DataFrame, grupo_filter: str, search_query: str) -> pd.DataFrame:
    """Filtra el DataFrame de forma optimizada."""
    df_filtered = df.copy()
    
    # Filtro por grupo
    if grupo_filter != "Todos":
        df_filtered = df_filtered[df_filtered[COL_GRUPO] == grupo_filter]
    
    # Filtro por búsqueda (optimizado con vectorización)
    if search_query.strip():
        tokens = search_query.strip().lower().split()
        
        # Crear índice de búsqueda combinando todas las columnas
        search_index = df_filtered.astype(str).apply(
            lambda row: ' '.join(row.values).lower(),
            axis=1
        )
        
        # Aplicar filtro para cada token
        mask = search_index.str.contains(tokens[0], na=False, regex=False)
        for token in tokens[1:]:
            mask &= search_index.str.contains(token, na=False, regex=False)
        
        df_filtered = df_filtered[mask]
    
    return df_filtered

# ═══════════════════════════════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════════════════════════════

def load_css():
    """Carga estilos CSS."""
    st.markdown("""
    <style>
    html, body, .stApp { font-family: 'Segoe UI', system-ui, sans-serif; }
    
    /* Header */
    .app-header {
        background: linear-gradient(135deg, #1B4332 0%, #2D6A4F 60%, #40916C 100%);
        color: #fff; padding: 1.6rem 2rem 1.2rem;
        border-radius: 0 0 16px 16px; margin: -1rem -2rem 1.8rem;
        text-align: center; box-shadow: 0 4px 20px rgba(27,67,50,.35);
    }
    .app-header h1 { margin:0; font-size:1.75rem; font-weight:700; letter-spacing:-.3px; }
    .app-header p { margin:.3rem 0 0; font-size:.88rem; opacity:.82; }
    
    /* Contador */
    .results-count { font-size:.82rem; color:#6c757d; margin-bottom:8px; }
    .results-count span { font-weight:700; color:#2D6A4F; }
    
    /* Badges */
    .badge-codigo {
        display:inline-block; background:#d8f3dc; color:#1B4332;
        border:1.5px solid #95d5b2; border-radius:6px;
        padding:3px 9px; font-weight:700; font-size:.82rem;
        font-variant-numeric:tabular-nums; min-width:38px; text-align:center;
    }
    
    .badge-grupo {
        display:inline-block; border-radius:6px;
        padding:3px 10px; font-weight:600; font-size:.78rem; white-space:nowrap;
    }
    .badge-grupo.g1 { background:#fff3cd; color:#856404; border:1.5px solid #ffc107; }
    .badge-grupo.g2 { background:#f8d7da; color:#721c24; border:1.5px solid #f5c6cb; }
    .badge-grupo.g3 { background:#d1ecf1; color:#0c5460; border:1.5px solid #bee5eb; }
    .badge-grupo.g4 { background:#e2d9f3; color:#4a235a; border:1.5px solid #c9b1ff; }
    .badge-grupo.g5 { background:#e9ecef; color:#495057; border:1.5px solid #ced4da; }
    
    /* Tabla */
    .tabla-header {
        display:grid; grid-template-columns: 90px 150px 200px 1fr;
        background:#1B4332; color:#fff; font-size:.76rem;
        text-transform:uppercase; letter-spacing:.6px; font-weight:600;
        border-radius:10px 10px 0 0; border:1.5px solid #1B4332;
        border-bottom:none;
    }
    .tabla-header > div { padding:10px 12px; }
    
    .fila-row {
        display:grid; grid-template-columns: 90px 150px 200px 1fr;
        align-items:center; width:100%; padding:8px 12px;
        font-size:.88rem; color:#343a40; gap:0;
        background: #fff;
    }
    
    /* Panel glosario */
    .panel-glosario {
        background:#f0fdf4; border-top:1px solid #b7e4c7;
        padding:16px; display:flex; gap:14px; flex-wrap:wrap;
    }
    .glos-card {
        background:#fff; border:1.5px solid #d8f3dc;
        border-radius:8px; padding:12px 14px;
    }
    .glos-card .glos-label {
        font-size:.72rem; text-transform:uppercase;
        letter-spacing:.5px; color:#2D6A4F; font-weight:700; margin-bottom:5px;
    }
    .glos-card .glos-title { font-size:.85rem; font-weight:600; color:#1B4332; margin-bottom:4px; }
    .glos-card .glos-text { font-size:.82rem; color:#495057; line-height:1.45; margin:0; }
    
    /* Empty state */
    .empty-state { text-align:center; padding:3rem 1rem; color:#6c757d; }
    .empty-state .empty-icon { font-size:2.4rem; margin-bottom:.6rem; }
    .empty-state p { margin:0; font-size:.92rem; }
    
    /* Footer */
    .app-footer {
        text-align:center; padding:1rem 0 .4rem;
        font-size:.76rem; color:#adb5bd;
        border-top:1px solid #eee; margin-top:1.8rem;
    }
    
    /* Streamlit overrides */
    .stMainMenu, footer { display:none !important; }
    
    /* Expander styling */
    div[data-testid="expander"] {
        border: none !important; box-shadow: none !important;
        border-radius: 0 !important; margin: 0 !important;
        background: transparent !important;
    }
    div[data-testid="expander"] > div:first-child {
        border: none !important; border-bottom: 1px solid #e9ecef !important;
        border-radius: 0 !important; background: #fff !important;
        box-shadow: none !important; padding: 0 !important; margin: 0 !important;
    }
    div[data-testid="expander"] summary {
        padding: 8px 12px !important; background: #fff !important;
        border-radius: 0 !important; transition: background 0.2s ease;
        cursor: pointer !important;
    }
    div[data-testid="expander"] summary:hover { 
        background: #f0faf4 !important; 
    }
    div[data-testid="expander"][open] summary {
        background: #fff !important;
    }
    div[data-testid="expander"] summary svg { display: none !important; }
    div[data-testid="expander"] > div:last-child {
        padding: 0 !important; margin: 0 !important; border-radius: 0 !important;
        background: #fff !important;
    }
    
    .tabla-wrap-outer {
        border: 1.5px solid #dee2e6; border-top: none;
        border-radius: 0 0 10px 10px; overflow: hidden;
        box-shadow: 0 2px 10px rgba(0,0,0,.06);
    }
    </style>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    # Cargar CSS
    load_css()
    
    # Cargar datos
    df = load_data()
    
    # Inicializar session state
    if "grupo_pill" not in st.session_state:
        st.session_state.grupo_pill = "Todos"
    
    # Header
    st.markdown("""
    <div class="app-header">
        <h1>🌲 Sistema de Clasificación de Causas de Incendios Forestales</h1>
        <p>Chile · Glosario v1.5 · CONAF</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Buscador
    query_input = st.text_input(
        label="Buscar",
        placeholder="🔍  Buscar causa… ej: quema no avisada, tendido eléctrico, carbón…",
        label_visibility="hidden",
        key="buscar_input",
    )
    
    # Pills de grupo
    grupos_opciones = ["Todos"] + get_unique_grupos(df)
    
    try:
        sel = st.pills(
            "Grupo",
            options=grupos_opciones,
            selection_mode="single",
            default=st.session_state.grupo_pill,
            label_visibility="hidden",
            key="grupo_pills"
        )
        if sel is not None and sel != st.session_state.grupo_pill:
            st.session_state.grupo_pill = sel
            st.rerun()
    
    except AttributeError:
        # Fallback para versiones antiguas sin pills
        cols = st.columns(len(grupos_opciones))
        for i, g in enumerate(grupos_opciones):
            with cols[i]:
                if st.button(
                    g,
                    key=f"pill_{g}",
                    use_container_width=True,
                    type="primary" if st.session_state.grupo_pill == g else "secondary"
                ):
                    st.session_state.grupo_pill = g
                    st.rerun()
    
    # Filtrar datos
    df_filtered = filter_dataframe(df, st.session_state.grupo_pill, query_input)
    n_results = len(df_filtered)
    
    # Contador
    st.markdown(
        f'<p class="results-count">'
        f'<span>{n_results}</span> causa{"s" if n_results != 1 else ""} '
        f'encontrada{"s" if n_results != 1 else ""}'
        f'</p>',
        unsafe_allow_html=True
    )
    
    # Resultados
    if n_results == 0:
        st.markdown(
            '<div class="empty-state">'
            '<div class="empty-icon">🔍</div>'
            '<p>No se encontraron causas que coincidan.<br>'
            'Intentar con otros términos o quitar el filtro de grupo.</p>'
            '</div>',
            unsafe_allow_html=True
        )
    
    else:
        # Header de tabla
        st.markdown("""
        <div class="tabla-header">
            <div>Código</div>
            <div>Grupo</div>
            <div>Causa general</div>
            <div>Causa específica</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Wrapper de tabla
        st.markdown('<div class="tabla-wrap-outer">', unsafe_allow_html=True)
        
        # Renderizar filas
        for _, row in df_filtered.iterrows():
            codigo_esp = str(row[COL_CODIGO_ESP])
            codigo_gen = extract_codigo_general(codigo_esp)
            grupo = str(row[COL_GRUPO])
            causa_gen = str(row[COL_CAUSA_GEN])
            causa_esp = str(row[COL_CAUSA])
            g_class = get_grupo_class(grupo)
            
            # Label descriptivo del expander - mostrar código y causa específica completa
            expander_label = f"{codigo_esp} - {causa_esp}"
            
            with st.expander(label=expander_label, expanded=False):
                # Fila estilizada
                st.markdown(
                    f'<div class="fila-row">'
                    f'<div><span class="badge-codigo">{escape(codigo_esp)}</span></div>'
                    f'<div><span class="badge-grupo {g_class}">{escape(grupo)}</span></div>'
                    f'<div>{sanitize_text(causa_gen)}</div>'
                    f'<div>{sanitize_text(causa_esp)}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                
                # Panel de glosario
                grupo_def = GLOSARIO_GRUPOS.get(grupo, "")
                cg_titulo, cg_def = GLOSARIO_POR_CODIGO.get(codigo_gen, ("", ""))
                
                st.markdown(
                    f'<div class="panel-glosario">'
                    f'<div class="glos-card" style="flex:0 0 260px;">'
                    f'<div class="glos-label">📌 Grupo de causa</div>'
                    f'<div class="glos-title"><span class="badge-grupo {g_class}">{escape(grupo)}</span></div>'
                    f'<p class="glos-text">{escape(grupo_def)}</p>'
                    f'</div>'
                    f'<div class="glos-card" style="flex:1 1 300px; border-color:#95d5b2;">'
                    f'<div class="glos-label">📂 Causa general · <span class="badge-codigo" style="font-size:.72rem;">{escape(codigo_gen)}</span></div>'
                    f'<div class="glos-title">{escape(cg_titulo)}</div>'
                    f'<p class="glos-text">{escape(cg_def)}</p>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown(
        '<div class="app-footer">'
        'Sistema de Clasificación de Causas de Incendios Forestales · '
        'Chile 2026 · Glosario v1.5 · CONAF · Autor: Alumno en Practica Francisco Vidal'
        '</div>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
