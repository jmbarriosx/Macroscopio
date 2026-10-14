#######################
# Agente Economico    #
# Version Streamlit   #
#######################

# Importacion para el ambiente
from dotenv import load_dotenv

# Importacion para el LLM
from groq import Groq

# Importacion para el manejo de sistema
import os

# Importacion para el uso de formato JSON
import json
import requests
import uuid

# Importacion para el manejo de fechas y zonas horarias
from datetime import datetime
from zoneinfo import ZoneInfo

# Importacion para la interfaz y las graficas
import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

# Importacion de memoria y herramientas propias
from summary_memory import PersistentMemory
from intermediate_tools import IntermediateTools


# =========================
# CONFIGURACION ORIGINAL
# =========================

load_dotenv()

api_key = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=api_key)

now = datetime.now(ZoneInfo("America/Guatemala"))

MEMORY_RECENT_LIMIT = 10      # mensajes completos que se mandan al modelo
MAX_ITERACIONES = 6           # tope de seguridad para el ciclo de herramientas

tools = IntermediateTools()


# =========================
# CONFIGURACION STREAMLIT
# =========================

APP_NAME = "Macroscopio"
APP_TAGLINE = "Agente de análisis económico y financiero"
AUTOR = "Juan Manuel Barrios"
CURSO = "Data Analytics · Universidad Rafael Landívar"

# Paleta (inspirada en terminales de trading)
BG = "#FFFFFF"        # fondo de graficas y tarjetas
APP_BG = "#FAF9F5"    # fondo de la app
PANEL = "#F0EEE6"     # sidebar
HOVER = "#E8E6DC"     # elemento activo / hover
GRID = "#E6E4DC"      # lineas y bordes
TXT = "#3D3D3A"       # texto principal
STRONG = "#1F1E1D"    # titulos
MUTED = "#73726C"     # texto secundario
BLUE = "#4C72B0"      # acento de graficas (azul seaborn)
UP = "#55A868"        # sube (verde seaborn)
DOWN = "#C44E52"      # baja (rojo seaborn)

st.set_page_config(
    page_title=f"{APP_NAME}",
    page_icon=None,
    layout="centered"
)

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=Source+Serif+4:wght@400;500;600&display=swap');

html, body, [class*="css"], .stApp, .stMarkdown, button, input, textarea {{
    font-family: 'IBM Plex Sans', sans-serif !important;
}}
.stApp {{ background: {APP_BG}; color: {TXT}; }}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer {{ display: none !important; }}
.block-container {{ max-width: 760px; padding-top: 2.5rem; padding-bottom: 8rem; }}

/* Mensajes: sin avatares, el usuario en tarjeta, el agente en texto limpio */
[data-testid^="stChatMessageAvatar"] {{ display: none !important; }}
[data-testid="stChatMessage"] {{ background: transparent; padding: 0.5rem 0; gap: 0; }}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {{
    background: {PANEL}; border-radius: 14px; padding: 0.75rem 1.1rem; margin-top: 1rem;
}}
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {{ line-height: 1.7; color: {TXT}; font-size: 1rem; }}
[data-testid="stChatMessage"] strong {{ color: {STRONG}; }}
[data-testid="stChatMessage"] table {{ font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem; }}
code {{ font-family: 'IBM Plex Mono', monospace !important; background: {PANEL} !important; color: {STRONG} !important; }}
[data-testid="stPlotlyChart"] {{ margin: 0.8rem 0 1.2rem 0; }}

/* Entrada de chat */
[data-testid="stBottom"], [data-testid="stBottom"] > div {{ background: {APP_BG}; }}
[data-testid="stChatInput"] {{
    background: {BG}; border: 1px solid {GRID}; border-radius: 18px;
    box-shadow: 0 2px 10px rgba(31,30,29,0.06);
}}
[data-testid="stChatInput"] textarea {{ color: {STRONG}; }}
[data-testid="stChatInput"]:focus-within {{ border-color: #BDBAAE; }}

/* Sidebar */
[data-testid="stSidebar"] {{ background: {PANEL}; border-right: 1px solid {GRID}; }}
[data-testid="stSidebar"] * {{ color: {TXT}; }}
.side-brand {{ font-family: 'Source Serif 4', serif; font-size: 1.35rem; font-weight: 600; color: {STRONG}; margin: 0.2rem 0 1rem 0.2rem; }}
.side-brand .dot {{ width: 8px; height: 8px; border-radius: 50%; background: {UP}; display: inline-block; margin-right: 8px; vertical-align: middle; }}
.side-title {{ font-size: 0.78rem; color: {MUTED}; margin: 1.4rem 0 0.3rem 0.4rem; }}
.side-foot {{ margin-top: 2rem; padding-top: 0.9rem; border-top: 1px solid {GRID}; font-size: 0.8rem; color: {MUTED}; line-height: 1.6; }}
.side-foot b {{ color: {STRONG}; font-weight: 500; }}

/* Botones del sidebar: lista limpia, sin bordes */
[data-testid="stSidebar"] .stButton > button {{
    background: transparent; border: none; box-shadow: none; border-radius: 8px;
    justify-content: flex-start; padding: 0.45rem 0.6rem; font-weight: 400; color: {TXT};
}}
[data-testid="stSidebar"] .stButton > button:hover {{ background: {HOVER}; color: {STRONG}; }}
[data-testid="stSidebar"] .stButton > button[kind="primary"],
[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] {{
    background: {HOVER}; color: {STRONG}; font-weight: 500;
}}
[data-testid="stSidebar"] .stButton > button, .stButton > button {{ justify-content: flex-start !important; }}
[data-testid="stSidebar"] .stButton > button > div, .stButton > button > div {{ width: 100%; justify-content: flex-start !important; }}
[data-testid="stSidebar"] .stButton > button p, .stButton > button p {{ width: 100%; text-align: left !important; }}
[data-testid="stSidebar"] .stButton > button p {{ overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
[data-testid="stPopover"] > div > button {{ background: transparent !important; border: none !important; color: {MUTED} !important; }}

/* Botones del area principal (sugerencias) */
.stButton > button {{
    background: {BG}; color: {TXT}; border: 1px solid {GRID}; border-radius: 12px;
    justify-content: flex-start; text-align: left; font-weight: 400; padding: 0.7rem 0.9rem;
    transition: border-color .15s, background .15s;
}}
.stButton > button div[data-testid="stMarkdownContainer"] {{ width: 100%; text-align: left; }}
.stButton > button:hover {{ border-color: #BDBAAE; background: {PANEL}; color: {STRONG}; }}
.stButton > button:focus-visible {{ outline: 2px solid {BLUE}; }}

/* Estado vacio */
.hero {{ text-align: center; margin: 14vh 0 2.2rem 0; }}
.hero .name {{ font-family: 'Source Serif 4', serif; font-size: 2.6rem; font-weight: 500; color: {STRONG}; letter-spacing: -0.01em; }}
.hero .sub {{ color: {MUTED}; margin-top: 0.4rem; font-size: 1.02rem; }}

[data-testid="stExpander"] {{ border: 1px solid {GRID}; border-radius: 10px; background: {BG}; }}

/* Forzar tema claro aunque el sistema/navegador este en modo oscuro */
:root {{ color-scheme: light; }}
.stButton > button {{ background: {BG} !important; color: {TXT} !important; border: 1px solid {GRID} !important; }}
.stButton > button p {{ color: {TXT} !important; }}
.stButton > button:hover {{ background: {PANEL} !important; border-color: #BDBAAE !important; }}
[data-testid="stChatInput"], [data-testid="stChatInput"] > div, [data-testid="stChatInput"] div[data-baseweb] {{ background: {BG} !important; }}
[data-testid="stChatInput"] textarea {{ color: {STRONG} !important; -webkit-text-fill-color: {STRONG} !important; background: transparent !important; }}
[data-testid="stChatInput"] textarea::placeholder {{ color: {MUTED} !important; -webkit-text-fill-color: {MUTED} !important; }}
[data-testid="stBottom"] > div {{ background: {APP_BG} !important; }}
[data-testid="stSidebar"] .stButton > button {{ background: transparent !important; color: {TXT} !important; border: none !important; }}
[data-testid="stSidebar"] .stButton > button:hover {{ background: {HOVER} !important; }}
[data-testid="stSidebar"] .stButton > button[kind="primary"], [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] {{ background: {HOVER} !important; }}
[data-testid="stSidebar"] .stButton > button p {{ color: {TXT} !important; }}
[data-testid="stPopover"] > div > button, [data-testid="stPopoverButton"] {{ background: transparent !important; color: {MUTED} !important; border: none !important; }}
[data-testid="stExpander"] summary, [data-testid="stExpander"] details {{ background: {BG} !important; color: {TXT} !important; }}
</style>
""", unsafe_allow_html=True)


# =========================
# MEMORIA PARA STREAMLIT
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _carpeta_de_chats():
    """En tu compu: carpeta 'chats'. Publicada en internet (APP_PUBLICA=1): una carpeta
    privada por visitante, identificada por el parametro ?u= de la URL."""
    base = os.path.join(BASE_DIR, "chats")
    if os.environ.get("APP_PUBLICA") != "1":
        return base
    uid = st.query_params.get("u", "")
    if not uid or not uid.isalnum() or len(uid) > 32:
        uid = uuid.uuid4().hex[:12]
        st.query_params["u"] = uid
    return os.path.join(base, uid)


CHATS_DIR = _carpeta_de_chats()
INDEX_FILE = os.path.join(CHATS_DIR, "index.json")
os.makedirs(CHATS_DIR, exist_ok=True)


def _leer_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _escribir_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, path)


def cargar_indice():
    return _leer_json(INDEX_FILE, [])


def ruta_memoria(cid):
    return os.path.join(CHATS_DIR, f"{cid}.json")


def ruta_ui(cid):
    return os.path.join(CHATS_DIR, f"{cid}_ui.json")


def crear_chat():
    return datetime.now().strftime("%Y%m%d%H%M%S%f")


def abrir_chat(cid):
    """Carga la memoria y la conversacion visible (con sus graficas) de un chat."""
    st.session_state.chat_id = cid
    st.session_state.memory = PersistentMemory(
        client=client, filepath=ruta_memoria(cid), recent_limit=MEMORY_RECENT_LIMIT
    )
    historial = []
    for m in _leer_json(ruta_ui(cid), []):
        figuras = []
        for fj in m.get("figuras", []):
            try:
                figuras.append(pio.from_json(fj))
            except Exception:
                pass
        historial.append({"role": m["role"], "content": m["content"], "figuras": figuras})
    st.session_state.chat_history = historial


def guardar_ui(cid, historial):
    datos = [
        {"role": m["role"], "content": m["content"],
         "figuras": [f.to_json() for f in m.get("figuras", [])]}
        for m in historial
    ]
    _escribir_json(ruta_ui(cid), datos)


def registrar_chat(cid, primer_texto=""):
    """Agrega el chat al indice (con titulo) o lo sube al inicio si ya existe."""
    indice = cargar_indice()
    chat = next((c for c in indice if c["id"] == cid), None)
    if chat is None:
        titulo = " ".join(primer_texto.split())
        if len(titulo) > 38:
            titulo = titulo[:37].rstrip() + "…"
        chat = {"id": cid, "title": titulo or "Nuevo chat"}
    else:
        indice.remove(chat)
    chat["updated"] = datetime.now().isoformat(timespec="seconds")
    indice.insert(0, chat)
    _escribir_json(INDEX_FILE, indice)


def eliminar_chat(cid):
    indice = [c for c in cargar_indice() if c["id"] != cid]
    _escribir_json(INDEX_FILE, indice)
    for ruta in (ruta_memoria(cid), ruta_ui(cid)):
        try:
            if os.path.exists(ruta):
                os.remove(ruta)
        except Exception as e:
            print(f"No se pudo borrar {ruta}: {e}")
    if st.session_state.get("chat_id") == cid:
        abrir_chat(indice[0]["id"] if indice else crear_chat())


def nuevo_chat():
    if st.session_state.chat_history:   # evita acumular chats vacios
        abrir_chat(crear_chat())


if "chat_id" not in st.session_state:
    _indice = cargar_indice()
    abrir_chat(_indice[0]["id"] if _indice else crear_chat())


# =========================
# PROMPT Y HERRAMIENTAS
# =========================

SYSTEM_PROMPT = f"""
Eres un Agente Económico especializado en análisis cuantitativo. Hablas en
español, de forma clara y concisa.

Fecha actual (Guatemala): {now.strftime('%Y-%m-%d')}

Tu objetivo es ayudar al usuario a consultar variables económicas y financieras
(tipo de cambio, indicadores macroeconómicos, precios de acciones) y a analizar
estadísticamente esos datos (variación, media, desviación estándar).

Herramientas disponibles:
- consultar_tipo_cambio_api: tipo de cambio actual de una moneda respecto al
  dólar (moneda obligatoria). Para "¿cuántos X son 1 USD?", llamá con
  moneda="USD" y leé rates["X"].
- consultar_serie_historica_indicador_api: serie histórica de un indicador del
  Banco Mundial para un país y rango de años (pais, indicador, anio_inicio,
  anio_fin obligatorios). Códigos: NY.GDP.MKTP.KD.ZG (crecimiento del PIB %),
  FP.CPI.TOTL.ZG (inflación %), SL.UEM.TOTL.ZS (desempleo %).
- consultar_precio_accion_api: precio actual y serie de precios de cierre de una
  acción (ticker obligatorio, por ejemplo NVDA, AAPL).
- calcular_variacion_porcentual: variación entre periodos consecutivos de una
  lista de valores. Usá es_tasa=true cuando la serie ya es un porcentaje o tasa
  (crecimiento del PIB, inflación, desempleo); es_tasa=false cuando son niveles
  (precio de una acción, PIB en dólares, población).
- calcular_estadisticas_descriptivas: media, desviación estándar, mínimo, máximo
  y coeficiente de variación de una lista de valores.

Reglas:
- Si el usuario pide un análisis estadístico (variación, volatilidad,
  tendencia), primero llamá a la herramienta que trae los datos y luego a la de
  cálculo correspondiente.
- Si el usuario solo pide los datos o la serie, NO llames a las herramientas de
  cálculo por tu cuenta; úsalas solo cuando lo pida explícitamente.
- Las gráficas se generan automáticamente en la interfaz a partir de los datos;
  no hace falta que dibujes nada ni que pidas permiso para graficar.
- Nunca inventes valores: si una herramienta no trae datos suficientes, dilo.
- No des recomendaciones de inversión (comprar/vender); limítate a presentar los
  datos y las métricas de forma objetiva.
- Nunca llames herramientas que no estén en esta lista.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "consultar_tipo_cambio_api",
            "description": "Consulta el tipo de cambio actual de una moneda respecto al dólar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "moneda": {"type": "string", "description": "Código de la moneda, por ejemplo USD, EUR, GTQ"}
                },
                "required": ["moneda"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_serie_historica_indicador_api",
            "description": "Consulta una serie histórica de un indicador económico del Banco Mundial para un país y un rango de años.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pais": {"type": "string", "description": "Código ISO de 2 letras del país, por ejemplo GT, US, MX, CR"},
                    "indicador": {
                        "type": "string",
                        "description": "NY.GDP.MKTP.KD.ZG (crecimiento del PIB %), FP.CPI.TOTL.ZG (inflación %), SL.UEM.TOTL.ZS (desempleo %)"
                    },
                    "anio_inicio": {"type": "string", "description": "Año inicial, por ejemplo 2018"},
                    "anio_fin": {"type": "string", "description": "Año final, por ejemplo 2023"}
                },
                "required": ["pais", "indicador", "anio_inicio", "anio_fin"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_precio_accion_api",
            "description": "Consulta el precio actual y una serie de precios de cierre de una acción en bolsa.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Símbolo de la acción, por ejemplo NVDA, AAPL, MSFT"},
                    "rango": {"type": "string", "description": "1mo, 3mo, 6mo, 1y. Por defecto 1mo."}
                },
                "required": ["ticker"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calcular_variacion_porcentual",
            "description": "Calcula la variación entre periodos consecutivos de una lista de valores numéricos. Usar después de obtener una serie de datos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "valores": {"type": "array", "items": {"type": "number"}, "description": "Valores en orden cronológico"},
                    "etiquetas": {"type": "array", "items": {"type": "string"}, "description": "Etiquetas (años o fechas) opcionales"},
                    "es_tasa": {"type": "boolean", "description": "true si la serie ya es un porcentaje o tasa; false si son niveles. Por defecto false."}
                },
                "required": ["valores"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calcular_estadisticas_descriptivas",
            "description": "Calcula media, desviación estándar, mínimo, máximo y coeficiente de variación de una lista de valores numéricos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "valores": {"type": "array", "items": {"type": "number"}, "description": "Lista de valores numéricos"}
                },
                "required": ["valores"]
            }
        }
    }
]


# =========================
# GRAFICAS (segun la herramienta)
# =========================

PAISES = {
    "GT": "Guatemala", "US": "Estados Unidos", "MX": "México", "CR": "Costa Rica",
    "SV": "El Salvador", "HN": "Honduras", "NI": "Nicaragua", "PA": "Panamá",
    "CO": "Colombia", "BR": "Brasil", "AR": "Argentina", "CL": "Chile", "PE": "Perú",
    "ES": "España", "DE": "Alemania", "FR": "Francia", "GB": "Reino Unido",
    "CN": "China", "JP": "Japón", "CA": "Canadá", "IN": "India", "IT": "Italia",
}

# codigo -> (nombre, unidad para mostrar, es_usd)
INDICADORES = {
    "NY.GDP.MKTP.KD.ZG": ("Crecimiento del PIB", "% anual", False),
    "FP.CPI.TOTL.ZG": ("Inflación", "% anual", False),
    "SL.UEM.TOTL.ZS": ("Desempleo", "% de la fuerza laboral", False),
    "NY.GDP.MKTP.CD": ("PIB", "miles de millones de USD", True),
    "NY.GDP.PCAP.CD": ("PIB per cápita", "USD", False),
}


def hex_a_rgba(hex_color, alpha):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


FUENTE = "IBM Plex Sans, sans-serif"
FUENTE_NUM = "IBM Plex Mono, monospace"


def estilo_base(fig, titulo, subtitulo="", altura=340, eje_y=True):
    """Estilo minimalista (tipo seaborn): fondo transparente, sin cajas,
    cuadricula horizontal muy tenue y casi sin ejes."""
    texto = f"<b>{titulo}</b>"
    if subtitulo:
        texto += f"<br><span style='font-size:12.5px;color:{MUTED}'>{subtitulo}</span>"

    fig.update_layout(
        title=dict(text=texto, x=0.0, xanchor="left", y=0.97, yanchor="top",
                   font=dict(size=16, color=STRONG, family=FUENTE)),
        height=altura,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=8, r=64, t=76, b=36),
        font=dict(family=FUENTE, color=MUTED, size=12),
        showlegend=False,
        hovermode="x",
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=GRID,
                        font=dict(family=FUENTE_NUM, color=TXT, size=12)),
    )
    fig.update_xaxes(
        showgrid=False, zeroline=False, showline=True, linecolor=GRID,
        ticks="outside", tickcolor=GRID, ticklen=4, tickfont=dict(color=MUTED),
    )
    fig.update_yaxes(
        side="right", visible=eje_y, showgrid=True, gridcolor=GRID, griddash="dot",
        gridwidth=1, zeroline=False, showline=False,
        tickfont=dict(color=MUTED, family=FUENTE_NUM, size=11),
    )
    return fig


def etiqueta_punto(fig, x, y, texto, color, posicion="right", dy=0):
    """Punto resaltado con su valor escrito al lado (etiqueta directa)."""
    fig.add_trace(go.Scatter(
        x=[x], y=[y], mode="markers", hoverinfo="skip",
        marker=dict(size=9, color=color, line=dict(width=2, color="#FFFFFF")),
    ))
    fig.add_annotation(
        x=x, y=y, text=texto, showarrow=False,
        xanchor="left" if posicion == "right" else "center",
        yanchor="middle" if posicion == "right" else "bottom",
        xshift=12 if posicion == "right" else 0, yshift=dy,
        font=dict(family=FUENTE_NUM, size=12, color=color),
    )


def grafica_indicador(resultado, args):
    if not isinstance(resultado, list) or not resultado:
        return None
    codigo = args.get("indicador", "")
    pais_cod = str(args.get("pais", "")).upper()
    pais = PAISES.get(pais_cod, pais_cod)
    nombre, unidad, es_usd = INDICADORES.get(codigo, (codigo, "", False))

    pares = [(str(d["anio"]), d["valor"]) for d in resultado][::-1]  # viene descendente
    pares = [(a, v) for a, v in pares if v is not None]
    if not pares:
        return None
    anios = [a for a, _ in pares]
    valores = [v / 1e9 if es_usd else v for _, v in pares]

    sufijo = "%" if (not es_usd and "%" in unidad) else ""
    prefijo = "$" if es_usd else ""
    fmt = lambda v: f"{prefijo}{v:,.1f}{sufijo}"
    con_etiquetas = len(valores) <= 12

    minimo, maximo = min(valores), max(valores)
    margen = (maximo - minimo) * 0.22 or 1

    # Etiqueta arriba del punto, salvo en los minimos locales (abajo) para no pisar la linea
    posiciones = []
    for i, v in enumerate(valores):
        vecinos = [valores[j] for j in (i - 1, i + 1) if 0 <= j < len(valores)]
        posiciones.append("bottom center" if vecinos and all(v < w for w in vecinos) else "top center")

    fig = go.Figure()
    if minimo < 0 < maximo:
        fig.add_hline(y=0, line_width=1, line_color=GRID)
    fig.add_trace(go.Scatter(
        x=anios, y=valores,
        mode="lines+markers+text" if con_etiquetas else "lines",
        line=dict(width=2.2, color=BLUE),
        marker=dict(size=8, color=BLUE, line=dict(width=2, color="#FFFFFF")),
        text=[fmt(v) for v in valores] if con_etiquetas else None,
        textposition=posiciones, cliponaxis=False,
        textfont=dict(family=FUENTE_NUM, size=11.5, color=STRONG),
        hovertemplate="<b>" + prefijo + "%{y:,.2f}" + sufijo + "</b>  ·  %{x}<extra></extra>",
    ))
    fig.update_yaxes(range=[minimo - margen, maximo + margen])
    fig.update_xaxes(type="category")

    subt = f"{unidad} · {anios[0]} a {anios[-1]}" if unidad else f"{anios[0]} a {anios[-1]}"
    return estilo_base(fig, f"{pais} · {nombre}", subt, altura=330, eje_y=not con_etiquetas)


def grafica_accion(resultado):
    if not isinstance(resultado, dict):
        return None
    ohlcv = resultado.get("_ohlcv")
    if ohlcv:
        fechas = [f["fecha"] for f in ohlcv]
        precios = [f["close"] for f in ohlcv]
        con_fechas = True
    else:
        precios = resultado.get("precios_cierre_serie")
        if not precios:
            return None
        fechas = list(range(1, len(precios) + 1))
        con_fechas = False

    n = len(precios)
    sube = precios[-1] >= precios[0]
    color = UP if sube else DOWN
    variacion = (precios[-1] / precios[0] - 1) * 100 if precios[0] else 0
    i_max = max(range(n), key=lambda i: precios[i])
    i_min = min(range(n), key=lambda i: precios[i])
    rango = precios[i_max] - precios[i_min]
    margen = rango * 0.18 or 1
    base = precios[i_min] - margen

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=fechas, y=[base] * n, mode="lines",
                             line=dict(width=0), hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=fechas, y=precios, mode="lines", line=dict(width=2.2, color=color),
        fill="tonexty", fillcolor=hex_a_rgba(color, 0.08),
        hovertemplate="<b>$%{y:,.2f}</b>  ·  %{x}<extra></extra>",
    ))

    # Etiquetas directas: maximo, minimo y ultimo precio
    etiqueta_punto(fig, fechas[-1], precios[-1], f"${precios[-1]:,.2f}", color)
    if i_max != n - 1:
        etiqueta_punto(fig, fechas[i_max], precios[i_max], f"máx ${precios[i_max]:,.2f}",
                       MUTED, posicion="top", dy=8)
    if i_min != n - 1 and i_min != i_max:
        fig.add_trace(go.Scatter(
            x=[fechas[i_min]], y=[precios[i_min]], mode="markers", hoverinfo="skip",
            marker=dict(size=8, color=MUTED, line=dict(width=2, color="#FFFFFF"))))
        fig.add_annotation(x=fechas[i_min], y=precios[i_min], text=f"mín ${precios[i_min]:,.2f}",
                           showarrow=False, yanchor="top", yshift=-10,
                           font=dict(family=FUENTE_NUM, size=12, color=MUTED))

    fig.update_yaxes(range=[base, precios[i_max] + margen], tickprefix="$")
    if con_fechas:
        fig.update_xaxes(type="date", rangebreaks=[dict(bounds=["sat", "mon"])])

    empresa = resultado.get("empresa", "") or resultado.get("ticker", "")
    flecha = "▲" if sube else "▼"
    subt = (f"<span style='color:{color}'>{flecha} {variacion:+.2f}%</span>"
            f" en {n} sesiones" + (f" · {fechas[0]} a {fechas[-1]}" if con_fechas else ""))
    return estilo_base(fig, empresa, subt, altura=350)


def grafica_variacion(resultado, fechas=None):
    """Variaciones entre periodos como 'lollipop' (tallo + punto). Si hay fechas
    de una accion consultada antes, se usan en el eje; si no, etiquetas cortas."""
    if not isinstance(resultado, list) or not resultado:
        return None
    en_pp = "variacion_puntos_porcentuales" in resultado[0]
    clave = "variacion_puntos_porcentuales" if en_pp else "variacion_pct"
    valores = [d.get(clave) for d in resultado]
    n = len(valores)
    unidad = " pp" if en_pp else "%"

    genericas = all(str(d["hasta"]).startswith("periodo_") for d in resultado)
    eje_fechas = False
    if genericas and fechas and len(fechas) == n + 1:
        x = list(fechas[1:])
        eje_fechas = True
        tipo_x = dict(type="date", rangebreaks=[dict(bounds=["sat", "mon"])])
        etiqueta_x = lambda xi: xi
    elif genericas:
        x = [f"{i}" for i in range(1, n + 1)]
        paso = max(1, -(-n // 10))
        tipo_x = dict(type="category", tickmode="array", tickvals=x[::paso])
        etiqueta_x = lambda xi: f"periodo {xi}"
    else:
        x = [str(d["hasta"]) for d in resultado]
        tipo_x = dict(type="category")
        etiqueta_x = lambda xi: xi

    puntos = [(xi, v) for xi, v in zip(x, valores) if v is not None]
    if not puntos:
        return None
    xs = [p[0] for p in puntos]
    vs = [p[1] for p in puntos]
    colores = [UP if v >= 0 else DOWN for v in vs]
    promedio = sum(vs) / len(vs)
    i_mejor = max(range(len(vs)), key=lambda i: vs[i])
    i_peor = min(range(len(vs)), key=lambda i: vs[i])

    fig = go.Figure()
    # Tallo fino desde cero hasta cada valor
    # En ejes de categorias se usa la posicion numerica (evita que "2019" se lea como numero)
    pos = (lambda i: xs[i]) if eje_fechas else (lambda i: i)
    for i, v in enumerate(vs):
        fig.add_shape(type="line", x0=pos(i), x1=pos(i), y0=0, y1=v, layer="below",
                      line=dict(color=GRID, width=2))
    fig.add_trace(go.Scatter(
        x=xs, y=vs, mode="markers",
        marker=dict(size=9, color=colores, line=dict(width=2, color="#FFFFFF")),
        hovertemplate="<b>%{y:+.2f}" + unidad + "</b>  ·  %{customdata}<extra></extra>",
        customdata=[etiqueta_x(xi) for xi in xs],
    ))
    fig.add_hline(y=0, line_width=1, line_color=MUTED)
    fig.add_hline(y=promedio, line_dash="dot", line_width=1, line_color=BLUE, opacity=0.7)

    if len(vs) > 1:
        for i, rotulo in ((i_mejor, "mejor"), (i_peor, "peor")):
            fig.add_annotation(
                x=pos(i), y=vs[i], text=f"{rotulo} {vs[i]:+.2f}{unidad}", showarrow=False,
                yanchor="bottom" if vs[i] >= 0 else "top", yshift=10 if vs[i] >= 0 else -10,
                font=dict(family=FUENTE_NUM, size=11.5, color=colores[i]),
            )

    margen = (max(vs) - min(vs)) * 0.25 if len(vs) > 1 else 1
    fig.update_yaxes(range=[min(min(vs), 0) - margen, max(max(vs), 0) + margen],
                     ticksuffix="" if en_pp else "%")
    fig.update_xaxes(showline=False, ticks="", **tipo_x)

    subt = (("Cambio en puntos porcentuales" if en_pp else "Cambio porcentual")
            + f" respecto al periodo anterior · línea azul = promedio ({promedio:+.2f}{unidad})")
    return estilo_base(fig, "Variación entre periodos", subt, altura=330, eje_y=True)


def generar_grafica(nombre, args, resultado, fechas=None):
    try:
        if nombre == "consultar_serie_historica_indicador_api":
            return grafica_indicador(resultado, args)
        if nombre == "consultar_precio_accion_api":
            return grafica_accion(resultado)
        if nombre == "calcular_variacion_porcentual":
            return grafica_variacion(resultado, fechas)
    except Exception as e:
        print(f"No se pudo graficar {nombre}: {e}")
    return None


# =========================
# LOGICA DEL AGENTE
# =========================

def obtener_ohlcv(ticker, rango):
    """Velas diarias (apertura, maximo, minimo, cierre, volumen) solo para dibujar la grafica."""
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker.upper()}"
           f"?range={rango}&interval=1d")
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    r.raise_for_status()
    res = r.json()["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    tz = ZoneInfo(res["meta"].get("exchangeTimezoneName", "America/New_York"))
    filas = []
    for t, o, h, l, c, v in zip(res["timestamp"], q["open"], q["high"], q["low"], q["close"], q["volume"]):
        if None in (o, h, l, c):
            continue
        filas.append({
            "fecha": datetime.fromtimestamp(t, tz).date().isoformat(),
            "open": o, "high": h, "low": l, "close": c, "volume": v or 0,
        })
    return filas


def ejecutar_herramienta(name, args):
    if name == "consultar_tipo_cambio_api":
        return tools.consultar_tipo_cambio_api(moneda=args.get("moneda", ""))
    elif name == "consultar_serie_historica_indicador_api":
        return tools.consultar_serie_historica_indicador_api(
            pais=args.get("pais", ""),
            indicador=args.get("indicador", ""),
            anio_inicio=args.get("anio_inicio", ""),
            anio_fin=args.get("anio_fin", "")
        )
    elif name == "consultar_precio_accion_api":
        resultado = tools.consultar_precio_accion_api(
            ticker=args.get("ticker", ""),
            rango=args.get("rango", "1mo")
        )
        if isinstance(resultado, dict):
            try:
                resultado["_ohlcv"] = obtener_ohlcv(args.get("ticker", ""), args.get("rango", "1mo"))
            except Exception as e:
                print(f"No se pudieron obtener las velas: {e}")
        return resultado
    elif name == "calcular_variacion_porcentual":
        return tools.calcular_variacion_porcentual(
            valores=args.get("valores", []),
            etiquetas=args.get("etiquetas"),
            es_tasa=args.get("es_tasa", False)
        )
    elif name == "calcular_estadisticas_descriptivas":
        return tools.calcular_estadisticas_descriptivas(valores=args.get("valores", []))
    print(f"Se intentó llamar a una herramienta desconocida {name}")
    return {"error": f"Herramienta desconocida: {name}"}


MAX_PUNTOS_PARA_MODELO = 25


def compactar_para_modelo(name, result):
    """
    La gráfica usa la serie completa, pero al modelo le mandamos una versión
    compacta para no pasar el límite de tokens por minuto de Groq.
    Las estadísticas se calculan aquí sobre TODA la serie.
    """
    if name != "consultar_precio_accion_api" or not isinstance(result, dict):
        return result

    result = {k: v for k, v in result.items() if k != "_ohlcv"}

    precios = result.get("precios_cierre_serie")
    if not precios or len(precios) <= MAX_PUNTOS_PARA_MODELO:
        return result

    n = len(precios)
    retornos = [
        (precios[i] / precios[i - 1] - 1) * 100
        for i in range(1, n) if precios[i - 1]
    ]
    media_ret = sum(retornos) / len(retornos) if retornos else 0
    desv_ret = (sum((r - media_ret) ** 2 for r in retornos) / len(retornos)) ** 0.5 if retornos else 0
    media_precio = sum(precios) / n

    paso = max(1, n // MAX_PUNTOS_PARA_MODELO)
    muestra = precios[::paso]
    if muestra[-1] != precios[-1]:
        muestra.append(precios[-1])

    compacto = {k: v for k, v in result.items() if k != "precios_cierre_serie"}
    compacto["resumen_serie_completa"] = {
        "n_sesiones": n,
        "primer_cierre": round(precios[0], 2),
        "ultimo_cierre": round(precios[-1], 2),
        "variacion_total_pct": round((precios[-1] / precios[0] - 1) * 100, 2) if precios[0] else None,
        "minimo": round(min(precios), 2),
        "maximo": round(max(precios), 2),
        "media_precio": round(media_precio, 2),
        "desv_est_precio": round((sum((p - media_precio) ** 2 for p in precios) / n) ** 0.5, 2),
        "media_retorno_diario_pct": round(media_ret, 3),
        "volatilidad_diaria_pct": round(desv_ret, 3),
    }
    compacto["precios_cierre_muestra"] = [round(p, 2) for p in muestra]
    compacto["nota"] = (
        f"La serie original tiene {n} sesiones; se resumió para optimizar la consulta. "
        "Las estadísticas de 'resumen_serie_completa' ya están calculadas sobre todos los datos "
        "(la volatilidad diaria es la desviación estándar de los retornos diarios en %). "
        "No hace falta llamar a otra herramienta para calcularlas."
    )
    return compacto


def process_response(client: Groq, memory_messages: list, summary: str, user_text: str):
    """Devuelve (texto_final, lista_de_figuras)."""
    system_content = SYSTEM_PROMPT
    if summary:
        system_content += (
            "\n\nResumen de la conversación anterior (memoria a largo plazo):\n"
            f"{summary}"
        )

    messages = [{"role": "system", "content": system_content}]
    messages.extend(memory_messages)
    messages.append({"role": "user", "content": user_text})

    figuras = []
    ultimas_fechas = None

    for _ in range(MAX_ITERACIONES):
        try:
            resp = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages,
                tools=TOOLS
            )
        except Exception as e:
            print(f"Error al llamar al modelo: {e}")
            texto_error = str(e).lower()
            if "rate_limit" in texto_error or "429" in texto_error:
                return ("⚠️ Se alcanzó el límite de tokens por minuto de Groq. "
                        "Esperá unos segundos y volvé a intentar."), figuras
            if "tool_use_failed" in texto_error or "not in request.tools" in texto_error:
                return ("⚠️ El modelo intentó usar una herramienta que no existe. "
                        "Probá reformular la pregunta."), figuras
            return f"⚠️ Error inesperado: {e}", figuras

        msg = resp.choices[0].message

        # Si no hay llamados a herramientas, ya tenemos la respuesta final
        if not getattr(msg, "tool_calls", None):
            return msg.content or "", figuras

        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [tc.model_dump() for tc in msg.tool_calls]
        })

        for tool_call in msg.tool_calls:
            name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}

            result = ejecutar_herramienta(name, args)

            # Fechas de la ultima accion consultada: sirven para el eje de las variaciones
            if name == "consultar_precio_accion_api" and isinstance(result, dict) and result.get("_ohlcv"):
                ultimas_fechas = [f["fecha"] for f in result["_ohlcv"]]

            fig = generar_grafica(name, args, result, ultimas_fechas)
            if fig is not None:
                figuras.append(fig)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(compactar_para_modelo(name, result), ensure_ascii=False)
            })

    return ("⚠️ El agente encadenó demasiadas herramientas sin concluir. "
            "Probá con una pregunta más específica."), figuras


# =========================
# MOSTRAR CONVERSACION
# =========================

PLOT_CONFIG = {"displayModeBar": False}

EJEMPLOS = [
    "¿Cuál es el tipo de cambio del euro?",
    "Dame el crecimiento del PIB de Guatemala de 2018 a 2023",
    "¿Qué tan volátil ha sido NVIDIA en el último mes?",
    "Compará el PIB de Guatemala y Costa Rica de 2018 a 2023",
]


def mostrar_figuras(figuras, prefijo):
    for j, fig in enumerate(figuras):
        st.plotly_chart(fig, use_container_width=True, config=PLOT_CONFIG,
                        key=f"{prefijo}_{j}")


# =========================
# SIDEBAR: LISTA DE CHATS
# =========================

with st.sidebar:
    st.markdown(f'<div class="side-brand"><span class="dot"></span>{APP_NAME}</div>',
                unsafe_allow_html=True)
    st.button("Nuevo chat", icon=":material/add:", use_container_width=True,
              on_click=nuevo_chat, key="btn_nuevo")

    indice = cargar_indice()
    if indice:
        st.markdown('<div class="side-title">Recientes</div>', unsafe_allow_html=True)

    for chat in indice:
        col_chat, col_menu = st.columns([6, 1], gap="small", vertical_alignment="center")
        with col_chat:
            st.button(
                chat["title"], key=f"abrir_{chat['id']}", use_container_width=True,
                type="primary" if chat["id"] == st.session_state.chat_id else "secondary",
                on_click=abrir_chat, args=(chat["id"],),
            )
        with col_menu:
            with st.popover("⋯", use_container_width=True):
                st.button("Eliminar chat", key=f"borrar_{chat['id']}",
                          icon=":material/delete:", use_container_width=True,
                          on_click=eliminar_chat, args=(chat["id"],))

    if st.session_state.memory.summary:
        st.markdown('<div class="side-title">Memoria de este chat</div>', unsafe_allow_html=True)
        with st.expander("Resumen acumulado"):
            st.write(st.session_state.memory.summary)

    st.markdown(
        f'<div class="side-foot"><b>{AUTOR}</b><br>{CURSO}<br>'
        'Fuentes: Banco Mundial, Yahoo Finance, open.er-api</div>',
        unsafe_allow_html=True,
    )


# =========================
# CONVERSACION
# =========================

memory = st.session_state.memory
chat_id = st.session_state.chat_id
consulta_pendiente = st.session_state.pop("pending_query", None)

if not st.session_state.chat_history and not consulta_pendiente:
    st.markdown(
        f'<div class="hero"><div class="name">{APP_NAME}</div>'
        f'<div class="sub">{APP_TAGLINE}</div></div>',
        unsafe_allow_html=True,
    )
    columnas = st.columns(2)
    for i, ejemplo in enumerate(EJEMPLOS):
        with columnas[i % 2]:
            if st.button(ejemplo, key=f"ej_{i}", use_container_width=True):
                st.session_state.pending_query = ejemplo
                st.rerun()

for idx, message in enumerate(st.session_state.chat_history):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        mostrar_figuras(message.get("figuras", []), f"fig_{chat_id}_{idx}")


# =========================
# ENTRADA DEL USUARIO
# =========================

user_text = st.chat_input("Escribí tu consulta: tipo de cambio, PIB, inflación, una acción...")
if not user_text and consulta_pendiente:
    user_text = consulta_pendiente

if user_text:

    user_text = user_text.strip()

    if user_text:

        es_primer_mensaje = not st.session_state.chat_history

        st.session_state.chat_history.append(
            {"role": "user", "content": user_text, "figuras": []}
        )

        with st.chat_message("user"):
            st.markdown(user_text)

        with st.chat_message("assistant"):

            with st.spinner("Consultando fuentes y calculando..."):
                assistant_text, figuras = process_response(
                    client, memory.messages(), memory.summary, user_text
                )

            st.markdown(assistant_text)
            mostrar_figuras(figuras, "fig_nueva")

        # =========================
        # ACTUALIZAR MEMORIA Y GUARDAR EL CHAT
        # =========================

        with st.spinner("Guardando..."):
            memory.add("user", user_text)
            memory.add("assistant", assistant_text)

        st.session_state.chat_history.append(
            {"role": "assistant", "content": assistant_text, "figuras": figuras}
        )
        guardar_ui(chat_id, st.session_state.chat_history)
        registrar_chat(chat_id, user_text if es_primer_mensaje else "")

        st.rerun()
