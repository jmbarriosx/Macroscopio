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
import re
import math
import html
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

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
APP_BG = "#FFFFFF"    # fondo de la app (blanco)
PANEL = "#F4F6F8"     # sidebar y paneles
HOVER = "#E9EDF2"     # elemento activo / hover
GRID = "#E2E6EB"      # lineas y bordes
TXT = "#2A2F37"       # texto principal
STRONG = "#0B1220"    # titulos
MUTED = "#6B7480"     # texto secundario
BLUE = "#1F4E9C"      # acento (azul terminal)
NAVY = "#0B2545"      # cabeceras de paneles
AMBER = "#F59E0B"     # acento ambar (guino a la terminal)
UP = "#0F9D58"        # sube
DOWN = "#D93025"      # baja

st.set_page_config(
    page_title=f"{APP_NAME}",
    page_icon=None,
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=Source+Serif+4:wght@400;500;600&display=swap');

html, body, [class*="css"], .stApp, .stMarkdown, button, input, textarea {{
    font-family: 'IBM Plex Sans', sans-serif !important;
}}
.stApp {{ background: {APP_BG}; color: {TXT}; }}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stDecoration"], #MainMenu, footer, [data-testid="stMainMenu"], [data-testid="stAppDeployButton"], [data-testid="stToolbarActions"] {{ display: none !important; }}
/* El boton para abrir/cerrar la barra lateral SIEMPRE visible */
[data-testid="stToolbar"] {{ background: transparent !important; }}
[data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] {{ display: flex !important; visibility: visible !important; opacity: 1 !important; }}
[data-testid="stExpandSidebarButton"], [data-testid="stExpandSidebarButton"] *, [data-testid="stSidebarCollapsedControl"] *, [data-testid="stSidebarCollapseButton"] * {{ color: {STRONG} !important; fill: {STRONG} !important; background: transparent !important; }}
/* Boton de enviar visible aunque el navegador este en modo oscuro */
[data-testid="stChatInputSubmitButton"] {{ background: {PANEL} !important; color: {MUTED} !important; }}
[data-testid="stChatInputSubmitButton"] svg, [data-testid="stChatInputSubmitButton"] svg path:last-child {{ color: {MUTED} !important; fill: {MUTED} !important; }}
[data-testid="stChatInputSubmitButton"]:not(:disabled) {{ background: {STRONG} !important; }}
[data-testid="stChatInputSubmitButton"]:not(:disabled) svg, [data-testid="stChatInputSubmitButton"]:not(:disabled) svg path:last-child {{ color: #FFFFFF !important; fill: #FFFFFF !important; }}
.block-container {{ max-width: 920px; padding-top: 1.2rem; padding-bottom: 4.5rem; }}

/* Mensajes: sin avatares, el usuario en tarjeta, el agente en texto limpio */
[data-testid^="stChatMessageAvatar"] {{ display: none !important; }}
[data-testid="stChatMessage"] {{ background: transparent; padding: 0.5rem 0; gap: 0; }}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {{
    background: {PANEL}; border-radius: 8px; padding: 0.75rem 1.1rem; margin-top: 1rem;
}}
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {{ line-height: 1.7; color: {TXT}; font-size: 1rem; }}
[data-testid="stChatMessage"] strong {{ color: {STRONG}; }}
[data-testid="stChatMessage"] table {{ font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem; }}
code {{ font-family: 'IBM Plex Mono', monospace !important; background: {PANEL} !important; color: {STRONG} !important; }}
[data-testid="stPlotlyChart"] {{ margin: 0.8rem 0 1.2rem 0; }}

/* Entrada de chat */
[data-testid="stBottom"], [data-testid="stBottom"] > div {{ background: {APP_BG}; }}
[data-testid="stChatInput"] {{
    background: {BG}; border: 1px solid {GRID}; border-radius: 8px;
    box-shadow: 0 2px 10px rgba(11,18,32,0.06);
}}
[data-testid="stChatInput"] textarea {{ color: {STRONG}; }}
[data-testid="stChatInput"]:focus-within {{ border-color: #AEB6C2; }}

/* Sidebar */
[data-testid="stSidebar"] {{ background: {PANEL}; border-right: 1px solid {GRID}; }}
[data-testid="stSidebar"] * {{ color: {TXT}; }}
.side-brand {{ font-family: 'IBM Plex Mono', monospace; text-transform: uppercase; letter-spacing: 0.14em; font-size: 0.98rem; font-weight: 600; color: {STRONG}; margin: 0.2rem 0 1rem 0.2rem; }}
.side-brand .dot {{ width: 9px; height: 9px; border-radius: 1px; background: {AMBER}; display: inline-block; margin-right: 8px; vertical-align: middle; }}
.side-title {{ font-size: 0.78rem; color: {MUTED}; margin: 1.4rem 0 0.3rem 0.4rem; }}
.side-foot {{ margin-top: 2rem; padding-top: 0.9rem; border-top: 1px solid {GRID}; font-size: 0.8rem; color: {MUTED}; line-height: 1.6; }}
.side-foot b {{ color: {STRONG}; font-weight: 500; }}

/* Botones del sidebar: lista limpia, sin bordes */
[data-testid="stSidebar"] .stButton > button {{
    background: transparent; border: none; box-shadow: none; border-radius: 6px;
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
    background: {BG}; color: {TXT}; border: 1px solid {GRID}; border-radius: 6px;
    justify-content: flex-start; text-align: left; font-weight: 400; padding: 0.7rem 0.9rem;
    transition: border-color .15s, background .15s;
}}
.stButton > button div[data-testid="stMarkdownContainer"] {{ width: 100%; text-align: left; }}
.stButton > button:hover {{ border-color: #AEB6C2; background: {PANEL}; color: {STRONG}; }}
.stButton > button:focus-visible {{ outline: 2px solid {BLUE}; }}

/* Estado vacio */
.hero {{ text-align: center; margin: 14vh 0 2.2rem 0; }}
.hero .name {{ font-family: 'IBM Plex Mono', monospace; text-transform: uppercase; font-size: 2rem; font-weight: 500; color: {STRONG}; letter-spacing: 0.16em; }}
.hero .name::after {{ content: ''; display: block; width: 54px; height: 3px; background: {AMBER}; margin: 0.5rem auto 0.1rem auto; }}
.hero .sub {{ color: {MUTED}; margin-top: 0.2rem; font-size: 0.95rem; }}

[data-testid="stExpander"] {{ border: 1px solid {GRID}; border-radius: 6px; background: {BG}; }}

/* Forzar tema claro aunque el sistema/navegador este en modo oscuro */
:root {{ color-scheme: light; }}
.stButton > button {{ background: {BG} !important; color: {TXT} !important; border: 1px solid {GRID} !important; }}
.stButton > button p {{ color: {TXT} !important; }}
.stButton > button:hover {{ background: {PANEL} !important; border-color: #AEB6C2 !important; }}
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

/* Mejoras de interfaz */
.block-container .stButton > button [data-testid="stMarkdownContainer"] p {{ display: block !important; text-align: left; margin: 0 0 .15rem 0; }}
[data-testid="stPopover"] button svg, [data-testid="stPopover"] button [aria-hidden="true"], [data-testid="stPopover"] button [data-testid="stIconMaterial"] {{ display: none !important; }}
[data-testid="stPopover"] button {{ padding: 0.3rem 0.5rem; font-size: 1.2rem; line-height: 1; }}
.side-title {{ letter-spacing: 0.01em; }}
.block-container .stButton > button {{ min-height: 3.9rem; align-items: flex-start; }}
.block-container .stButton > button p {{ white-space: normal !important; text-align: left !important; line-height: 1.45; }}
.block-container .stButton > button p strong {{ color: {MUTED}; font-weight: 500; font-size: 0.82rem; }}
.hero .sub2 {{ color: {MUTED}; font-size: 0.88rem; margin-top: 0.35rem; opacity: 0.85; }}
[data-testid="stCaptionContainer"] {{ color: {MUTED}; }}
[data-testid="stStatusWidget"], [data-testid="stExpander"] details {{ border-radius: 6px; }}
.modebar {{ opacity: 0.55; }}
.modebar-btn {{ font-size: 18px !important; }}

/* ===== Interfaz moderna ===== */
.mk-title {{ font-size: 0.78rem; color: {MUTED}; margin: 0 0 0.45rem 0.15rem; letter-spacing: 0.04em; text-transform: uppercase; display: flex; align-items: center; gap: 6px; }}
.mk-title .live {{ width: 7px; height: 7px; border-radius: 50%; background: {UP}; animation: pulso 2s infinite; }}
@keyframes pulso {{ 0% {{ box-shadow: 0 0 0 0 rgba(85,168,104,.55); }} 70% {{ box-shadow: 0 0 0 7px rgba(85,168,104,0); }} 100% {{ box-shadow: 0 0 0 0 rgba(85,168,104,0); }} }}
.block-container .stButton > button {{ box-shadow: 0 1px 3px rgba(11,18,32,0.04); transition: transform .15s, box-shadow .15s, border-color .15s, background .15s; }}
.block-container .stButton > button:hover {{ transform: translateY(-2px); box-shadow: 0 6px 16px rgba(11,18,32,0.08); }}
[data-testid="stChatInput"] {{ box-shadow: 0 2px 10px rgba(11,18,32,0.07); border-radius: 8px; }}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {{ border: 1px solid {GRID}; }}
[data-testid="stStatus"], [data-testid="stStatusWidget"] {{ border: 1px solid {GRID} !important; border-radius: 6px !important; background: {BG} !important; }}
[data-testid="stStatus"] summary, [data-testid="stStatus"] summary * {{ color: {TXT} !important; }}

/* Sugerencias de seguimiento (chips) */
.block-container .st-key-chips {{ display: flex !important; flex-direction: row !important; flex-wrap: wrap !important; gap: 0.5rem !important; margin: 0.4rem 0 0 0; }}
.block-container .st-key-chips > div {{ width: auto !important; flex: 0 0 auto !important; }}
.block-container .st-key-chips .stButton > button {{ min-height: 0 !important; padding: 0.35rem 0.95rem !important; border-radius: 4px !important; font-size: 0.82rem; font-family: "IBM Plex Mono", monospace; align-items: center; }}
.block-container .st-key-chips .stButton > button p {{ white-space: nowrap !important; font-size: 0.85rem; }}

/* ===== Estilo terminal (blanco) ===== */
.hero {{ margin: 0 0 0.6rem 0; }}
.mk-title {{ font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; letter-spacing: 0.1em; color: {MUTED}; margin: 0.7rem 0 0.35rem 0; }}
.tape {{ overflow: hidden; border-top: 1px solid {GRID}; border-bottom: 1px solid {GRID}; background: {PANEL}; margin: 0 0 0.6rem 0; white-space: nowrap; }}
.tape-in {{ display: inline-flex; animation: cinta 140s linear infinite; }}
.tape:hover .tape-in {{ animation-play-state: paused; }}
.ti {{ font-family: 'IBM Plex Mono', monospace; font-size: 0.74rem; padding: 0.42rem 1.3rem; color: {TXT}; border-right: 1px solid {GRID}; }}
.ti b {{ color: {STRONG}; font-weight: 600; margin-right: 0.5rem; }}
.ti i {{ font-style: normal; margin-left: 0.45rem; }}
.mt-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 0.4rem; }}
@media (max-width: 760px) {{ .mt-grid {{ grid-template-columns: 1fr; }} }}
.mt {{ border: 1px solid {GRID}; border-radius: 4px; background: {BG}; overflow: hidden; }}
.mt-head {{ background: {NAVY}; color: #FFFFFF; font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; letter-spacing: 0.1em; padding: 0.38rem 0.7rem; display: flex; justify-content: space-between; align-items: center; }}
.mt-head .live {{ color: {AMBER}; display: flex; align-items: center; gap: 6px; }}
.mt-head .live::before {{ content: ''; width: 6px; height: 6px; border-radius: 50%; background: {AMBER}; animation: pulso 2s infinite; }}
@keyframes pulso {{ 0% {{ box-shadow: 0 0 0 0 rgba(245,158,11,.6); }} 70% {{ box-shadow: 0 0 0 6px rgba(245,158,11,0); }} 100% {{ box-shadow: 0 0 0 0 rgba(245,158,11,0); }} }}
.mt-cols, .mt-row {{ display: grid; grid-template-columns: minmax(0,1.5fr) 1fr 0.8fr 0.8fr 56px; align-items: center; column-gap: 8px; padding: 0 0.7rem; }}
.mt-cols {{ font-family: 'IBM Plex Mono', monospace; font-size: 0.64rem; letter-spacing: 0.06em; color: {MUTED}; border-bottom: 1px solid {GRID}; padding-top: 0.3rem; padding-bottom: 0.3rem; text-transform: uppercase; }}
.mt-cols span:not(:first-child), .mt-row span:not(:first-child) {{ text-align: right; }}
.mt-row {{ height: 28px; border-bottom: 1px solid {PANEL}; font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem; transition: background .12s; }}
.mt-row:last-child {{ border-bottom: none; }}
.mt-row:hover {{ background: {PANEL}; }}
.mt-row .n {{ font-family: 'IBM Plex Sans', sans-serif; font-size: 0.82rem; color: {STRONG}; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.mt-row .p {{ color: {STRONG}; }}
.mt-row .spark {{ width: 56px; height: 20px; display: block; }}
.block-container .stButton > button:hover {{ border-left: 3px solid {NAVY} !important; }}
[data-testid="stBottomBlockContainer"] {{ max-width: 920px !important; }}
[data-testid="stChatInput"] textarea {{ font-family: 'IBM Plex Mono', monospace !important; font-size: 0.9rem !important; }}

/* ===== Cinta fija a todo el ancho ===== */
.tape {{ position: fixed; top: 0; left: 0; right: 0; height: 32px; z-index: 1000002; margin: 0; border-top: none; border-bottom: 1px solid {GRID}; display: flex; align-items: center; }}
.tape-in {{ animation: cinta 140s linear infinite; }}
@keyframes cinta {{ from {{ transform: translateX(0); }} to {{ transform: translateX(-25%); }} }}
[data-testid="stAppViewContainer"] {{ top: 32px !important; height: auto !important; bottom: 0 !important; }}
[data-testid="stHeader"] {{ top: 32px !important; }}
[data-testid="stElementContainer"]:has(.tape) {{ height: 0 !important; min-height: 0 !important; margin: 0 !important; padding: 0 !important; }}
.block-container {{ padding-top: 2.4rem; }}

/* ===== Autor abajo del todo en la barra lateral ===== */
[data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"] {{ min-height: calc(100vh - 9rem); }}
[data-testid="stSidebarUserContent"] [data-testid="stElementContainer"]:has(.side-foot) {{ margin-top: auto; }}
.side-foot {{ margin-top: 0 !important; }}

/* ===== Texto legible en las respuestas (tablas, titulos) aunque el navegador este en modo oscuro ===== */
[data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h4 {{ color: {STRONG} !important; font-weight: 600; }}
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li, [data-testid="stMarkdownContainer"] em {{ color: {TXT}; }}
[data-testid="stMarkdownContainer"] table {{ width: 100%; border-collapse: collapse; background: {BG}; border: 1px solid {GRID}; margin: 0.6rem 0 1rem 0; font-size: 0.86rem; }}
[data-testid="stMarkdownContainer"] thead th {{ background: {NAVY} !important; color: #FFFFFF !important; font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; font-weight: 500; letter-spacing: 0.04em; text-transform: uppercase; padding: 0.5rem 0.75rem; border: 1px solid {NAVY}; text-align: left; }}
[data-testid="stMarkdownContainer"] tbody td {{ background: {BG} !important; color: {TXT} !important; padding: 0.5rem 0.75rem; border: 1px solid {GRID}; vertical-align: top; }}
[data-testid="stMarkdownContainer"] tbody tr:nth-child(even) td {{ background: #F7F9FB !important; }}
[data-testid="stMarkdownContainer"] tbody td:first-child {{ color: {STRONG} !important; font-weight: 500; font-family: 'IBM Plex Sans', sans-serif; }}
[data-testid="stMarkdownContainer"] tbody td code {{ background: transparent !important; color: {STRONG} !important; padding: 0; font-size: 0.86rem; }}
[data-testid="stChatMessage"] h1 {{ font-size: 1.45rem; }}
[data-testid="stChatMessage"] h2 {{ font-size: 1.2rem; margin-top: 1.2rem; }}
[data-testid="stChatMessage"] h3 {{ font-size: 1.05rem; }}

/* ===== Paneles de mercado clicables ===== */
[class*="st-key-panel_"] {{ border: 1px solid {GRID}; border-radius: 4px; background: {BG}; overflow: hidden; gap: 0 !important; margin-bottom: 0.2rem; }}
[class*="st-key-row_"] {{ position: relative; gap: 0 !important; height: 28px !important; min-height: 28px; }}
[class*="st-key-row_"] > [data-testid="stElementContainer"]:first-child {{ height: 28px !important; }}
[class*="st-key-hd_"] {{ gap: 0 !important; height: 52px !important; min-height: 52px; }}
[class*="st-key-hd_"] > [data-testid="stElementContainer"]:first-child {{ height: 52px !important; }}
.mt-head {{ height: 28px; box-sizing: border-box; }}
.mt-cols {{ height: 24px; box-sizing: border-box; padding-top: 0 !important; padding-bottom: 0 !important; }}
.block-container [class*="st-key-row_"] [data-testid="stElementContainer"]:has(.stButton) {{ position: absolute; inset: 0; width: 100% !important; margin: 0; }}
.block-container [class*="st-key-row_"] .stButton, .block-container [class*="st-key-row_"] .stButton button {{ width: 100% !important; height: 100% !important; }}
.block-container [class*="st-key-row_"] .stButton button {{ opacity: 0 !important; min-height: 0 !important; padding: 0 !important; border-radius: 0 !important; cursor: pointer; transform: none !important; box-shadow: none !important; border: none !important; }}
[class*="st-key-row_"]:hover .mt-row {{ background: {PANEL}; }}
.mt-grid, .mt {{ display: block; }}
[class*="st-key-panel_"] .mt-row {{ border-bottom: 1px solid {PANEL}; }}

/* ===== Buscador y selector de rango ===== */
[data-testid="stTextInput"] input {{ background: {BG} !important; color: {STRONG} !important; -webkit-text-fill-color: {STRONG} !important; font-family: 'IBM Plex Mono', monospace !important; font-size: 0.82rem !important; }}
[data-testid="stTextInput"] input::placeholder {{ color: {MUTED} !important; -webkit-text-fill-color: {MUTED} !important; }}
[data-testid="stTextInput"] div[data-baseweb="input"], [data-testid="stTextInput"] div[data-baseweb="base-input"] {{ background: {BG} !important; border: 1px solid {GRID}; border-radius: 6px; }}
[data-testid="stButtonGroup"] button {{ background: {BG} !important; color: {TXT} !important; border: 1px solid {GRID} !important; border-radius: 4px !important; font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; min-height: 0 !important; padding: 0.25rem 0.7rem !important; }}
[data-testid="stButtonGroup"] button p {{ color: inherit !important; font-size: 0.78rem; }}
[data-testid="stButtonGroup"] button[aria-checked="true"], [data-testid="stButtonGroup"] button[aria-pressed="true"], [data-testid="stButtonGroup"] button[data-testid="stBaseButton-segmented_controlActive"], [data-testid="stButtonGroup"] button[kind="segmented_controlActive"] {{ background: {NAVY} !important; color: #FFFFFF !important; border-color: {NAVY} !important; }}

/* ===== Ficha del activo (ventana) ===== */
[data-testid="stDialog"] > div, [data-testid="stDialog"] section[role="dialog"] {{ background: {BG} !important; }}
[data-testid="stDialog"] > div {{ border-radius: 8px; border: 1px solid {GRID}; }}
[data-testid="stDialog"] h1, [data-testid="stDialog"] h2, [data-testid="stDialog"] [data-testid="stDialogTitle"] {{ color: {STRONG} !important; font-family: 'IBM Plex Mono', monospace; font-size: 0.9rem !important; letter-spacing: 0.08em; text-transform: uppercase; }}
[data-testid="stDialog"] button[aria-label="Close"], [data-testid="stDialog"] button[aria-label="Close"] * {{ color: {STRONG} !important; background: transparent !important; }}
[data-testid="stDialog"] [data-testid="stCaptionContainer"], [data-testid="stDialog"] [data-testid="stCaptionContainer"] * {{ color: {MUTED} !important; font-size: 0.74rem; }}
.fh {{ margin-bottom: 0.4rem; }}
.fh-n {{ font-size: 1.15rem; font-weight: 600; color: {STRONG}; }}
.fh .tag {{ display: inline-block; font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; color: {MUTED}; border: 1px solid {GRID}; border-radius: 3px; padding: 1px 6px; margin: 4px 6px 0 0; }}
.fh-p {{ font-family: 'IBM Plex Mono', monospace; display: flex; align-items: baseline; gap: 14px; margin-top: 0.5rem; }}
.fh-p span:first-child {{ font-size: 2.1rem; font-weight: 500; color: {STRONG}; }}
.fh-p span:last-child {{ font-size: 1rem; }}
.sec-t {{ font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; letter-spacing: 0.1em; color: {MUTED}; margin: 1rem 0 0.35rem 0; padding-bottom: 0.25rem; border-bottom: 1px solid {GRID}; }}
.tl-grid {{ display: grid; grid-template-columns: repeat(var(--c, 4), 1fr); gap: 8px; }}
@media (max-width: 640px) {{ .tl-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
.tl {{ border: 1px solid {GRID}; border-radius: 4px; padding: 0.45rem 0.6rem; background: {BG}; }}
.tl span {{ display: block; font-size: 0.68rem; color: {MUTED}; }}
.tl b {{ display: block; font-family: 'IBM Plex Mono', monospace; font-size: 0.86rem; font-weight: 500; color: {STRONG}; margin-top: 2px; }}
.rb {{ position: relative; height: 4px; background: {GRID}; border-radius: 2px; margin-top: 6px; }}
.rb i {{ position: absolute; top: -3px; width: 3px; height: 10px; background: {NAVY}; border-radius: 1px; transform: translateX(-50%); }}
.st-key-analizar_ficha button {{ background: {NAVY} !important; border: 1px solid {NAVY} !important; }}
.st-key-analizar_ficha button, .st-key-analizar_ficha button p {{ color: #FFFFFF !important; }}
.st-key-analizar_ficha button:hover {{ background: {BLUE} !important; border-left: 1px solid {BLUE} !important; }}
.perfil {{ margin-top: 0.6rem; font-size: 0.8rem; color: {MUTED}; }}
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


# --- Supabase (opcional): base de datos en la nube para que los chats no se pierdan ---
# Si SUPABASE_URL y SUPABASE_KEY existen, todo lo que se guarda en disco se copia tambien a
# la tabla "kv" de Supabase, y si el archivo local no existe (p. ej. la app en la nube se
# reinicio) se recupera desde ahi. Sin esas variables, todo funciona solo con archivos.
SUPABASE_URL = (os.environ.get("SUPABASE_URL") or "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or ""
SUPABASE_ON = bool(SUPABASE_URL and SUPABASE_KEY)
SUPABASE_TABLA = "kv"


def _sb_headers(extra=None):
    h = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
         "Content-Type": "application/json"}
    h.update(extra or {})
    return h


def _clave(path):
    """Clave en Supabase = ruta del archivo relativa a la carpeta 'chats' (incluye el id del visitante)."""
    return os.path.relpath(path, os.path.join(BASE_DIR, "chats")).replace(os.sep, "/")


def _sb_leer(path):
    if not SUPABASE_ON:
        return None
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLA}", headers=_sb_headers(),
                         params={"key": f"eq.{_clave(path)}", "select": "data"}, timeout=8)
        r.raise_for_status()
        filas = r.json()
        return filas[0]["data"] if filas else None
    except Exception as e:
        print(f"[Supabase] No se pudo leer {_clave(path)}: {e}")
        return None


def _sb_escribir(path, data):
    if not SUPABASE_ON:
        return
    try:
        r = requests.post(f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLA}", headers=_sb_headers(
            {"Prefer": "resolution=merge-duplicates,return=minimal"}),
            params={"on_conflict": "key"},
            json={"key": _clave(path), "data": data,
                  "updated_at": datetime.now(ZoneInfo("UTC")).isoformat()}, timeout=8)
        r.raise_for_status()
    except Exception as e:
        print(f"[Supabase] No se pudo guardar {_clave(path)}: {e}")


def _sb_borrar(path):
    if not SUPABASE_ON:
        return
    try:
        requests.delete(f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLA}", headers=_sb_headers(),
                        params={"key": f"eq.{_clave(path)}"}, timeout=8).raise_for_status()
    except Exception as e:
        print(f"[Supabase] No se pudo borrar {_clave(path)}: {e}")


def _escribir_local(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, path)


def _leer_json(path, default):
    """Lee el archivo local; si no existe, lo recupera de Supabase (y lo deja en disco)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        pass
    data = _sb_leer(path)
    if data is None:
        return default
    try:
        _escribir_local(path, data)
    except Exception:
        pass
    return data


def _escribir_json(path, data):
    _escribir_local(path, data)
    _sb_escribir(path, data)


def sincronizar_memoria(cid):
    """Copia a Supabase el archivo de memoria del chat (lo escribe PersistentMemory en disco)."""
    if SUPABASE_ON:
        data = _leer_json(ruta_memoria(cid), None)
        if data is not None:
            _sb_escribir(ruta_memoria(cid), data)


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
    _leer_json(ruta_memoria(cid), None)   # si el archivo local no existe, lo trae de Supabase
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
        historial.append({"role": m["role"], "content": m["content"], "figuras": figuras,
                          "fuentes": m.get("fuentes", [])})
    st.session_state.chat_history = historial


def guardar_ui(cid, historial):
    datos = [
        {"role": m["role"], "content": m["content"],
         "figuras": [f.to_json() for f in m.get("figuras", [])],
         "fuentes": m.get("fuentes", [])}
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
        _sb_borrar(ruta)
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
        margin=dict(l=8, r=64, t=76, b=52),
        font=dict(family=FUENTE, color=MUTED, size=12),
        showlegend=False,
        hovermode="x",
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=GRID,
                        font=dict(family=FUENTE_NUM, color=TXT, size=12)),
    )
    fig.update_xaxes(
        showgrid=False, zeroline=False, showline=True, linecolor=GRID,
        ticks="outside", tickcolor=GRID, ticklen=4, tickfont=dict(color=MUTED),
        automargin=True,
    )
    fig.update_xaxes(showspikes=True, spikemode="across", spikesnap="cursor",
                     spikethickness=1, spikecolor="#AEB6C2", spikedash="dot")
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


FUENTES = {
    "consultar_tipo_cambio_api": "open.er-api.com",
    "consultar_serie_historica_indicador_api": "Banco Mundial",
    "consultar_precio_accion_api": "Yahoo Finance",
    "calcular_variacion_porcentual": "Cálculo propio",
    "calcular_estadisticas_descriptivas": "Cálculo propio",
}

ETAPAS = {
    "consultar_tipo_cambio_api": "Consultando el tipo de cambio",
    "consultar_serie_historica_indicador_api": "Descargando la serie del Banco Mundial",
    "consultar_precio_accion_api": "Consultando precios en Yahoo Finance",
    "calcular_variacion_porcentual": "Calculando variaciones",
    "calcular_estadisticas_descriptivas": "Calculando estadísticas descriptivas",
}


def process_response(client: Groq, memory_messages: list, summary: str, user_text: str,
                     on_tool=None, fuentes=None):
    """Devuelve (texto_final, lista_de_figuras). Opcionales: on_tool(nombre) avisa cada
    herramienta que se usa y fuentes (lista) recibe las fuentes de datos consultadas."""
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

            if on_tool:
                on_tool(name)
            result = ejecutar_herramienta(name, args)
            fuente = FUENTES.get(name)
            if fuentes is not None and fuente and fuente not in fuentes \
                    and not (isinstance(result, str) and result.startswith("ERROR")):
                fuentes.append(fuente)

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
# PANEL DE MERCADOS (pantalla de inicio)
# =========================

GRUPOS_MERCADO = [
    ("Índices y cripto", [
        ("S&P 500", "^GSPC", "idx"), ("Nasdaq 100", "^NDX", "idx"),
        ("Dow Jones", "^DJI", "idx"), ("VIX", "^VIX", "idx"),
        ("Bitcoin", "BTC-USD", "usd0")]),
    ("Divisas, materias primas y tasas", [
        ("EUR / USD", "EURUSD=X", "fx"), ("USD / GTQ", "GTQ=X", "fx"),
        ("Oro", "GC=F", "usd"), ("Petróleo WTI", "CL=F", "usd"),
        ("Bono EE. UU. 10a", "^TNX", "yld")]),
    ("Acciones destacadas", [
        ("NVIDIA", "NVDA", "usd"), ("Apple", "AAPL", "usd"),
        ("Microsoft", "MSFT", "usd"), ("Tesla", "TSLA", "usd"),
        ("AMD", "AMD", "usd")]),
    ("ETFs", [
        ("SPY · S&P 500", "SPY", "usd"), ("QQQ · Nasdaq 100", "QQQ", "usd"),
        ("GLD · Oro", "GLD", "usd"), ("TLT · Bonos 20a+", "TLT", "usd"),
        ("IWM · Russell 2000", "IWM", "usd")]),
]
UA = {"User-Agent": "Mozilla/5.0"}


def _esc(t):
    return html.escape(str(t))


def _tarjeta_mercado(simbolo):
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(simbolo)}"
           "?range=1mo&interval=1d")
    r = requests.get(url, headers=UA, timeout=6)
    r.raise_for_status()
    res = r.json()["chart"]["result"][0]
    cierres = [c for c in res["indicators"]["quote"][0]["close"] if c is not None]
    precio = res["meta"].get("regularMarketPrice") or cierres[-1]
    previo = cierres[-2] if len(cierres) > 1 else cierres[0]
    return {"precio": precio, "abs": precio - previo,
            "pct": (precio / previo - 1) * 100 if previo else 0.0, "serie": cierres}


@st.cache_data(ttl=600, show_spinner=False)
def datos_mercado():
    """Devuelve {simbolo: datos} para todos los instrumentos que se pudieron consultar."""
    todos = [m for _, lista in GRUPOS_MERCADO for m in lista]

    def uno(m):
        try:
            return m[1], _tarjeta_mercado(m[1])
        except Exception as e:
            print(f"[Mercado] {m[1]}: {e}")
            return m[1], None
    with ThreadPoolExecutor(max_workers=8) as ex:
        return {k: v for k, v in ex.map(uno, todos) if v}


def _spark(serie, color):
    if len(serie) < 2:
        return ""
    lo, hi = min(serie), max(serie)
    rango = (hi - lo) or 1
    n = len(serie)
    linea = " ".join(f"{i * 100 / (n - 1):.1f},{26 - (v - lo) / rango * 24:.1f}"
                     for i, v in enumerate(serie))
    return (f'<svg class="spark" viewBox="0 0 100 28" preserveAspectRatio="none">'
            f'<polygon points="0,28 {linea} 100,28" fill="{hex_a_rgba(color, 0.10)}"/>'
            f'<polyline points="{linea}" fill="none" stroke="{color}" stroke-width="1.6" '
            f'vector-effect="non-scaling-stroke"/></svg>')


def _formato(tipo, d):
    p, a = d["precio"], d["abs"]
    if tipo == "fx":
        return f"{p:.4f}", f"{a:+.4f}"
    if tipo == "usd":
        return f"${p:,.2f}", f"{a:+,.2f}"
    if tipo == "usd0":
        return f"${p:,.0f}", f"{a:+,.0f}"
    if tipo == "yld":
        return f"{p:.3f}%", f"{a:+.3f}"
    return f"{p:,.2f}", f"{a:+,.2f}"


def cinta_mercados_html():
    datos = datos_mercado()
    items = []
    for _, lista in GRUPOS_MERCADO:
        for nombre, simbolo, tipo in lista:
            d = datos.get(simbolo)
            if not d:
                continue
            color = UP if d["pct"] >= 0 else DOWN
            flecha = "▲" if d["pct"] >= 0 else "▼"
            precio, _ = _formato(tipo, d)
            items.append(f'<span class="ti"><b>{_esc(nombre)}</b>{precio}'
                         f'<i style="color:{color}">{flecha} {abs(d["pct"]):.2f}%</i></span>')
    if not items:
        return ""
    # 4 copias y desplazamiento de 25%: la cinta nunca queda con huecos, ni en pantallas muy anchas
    return f'<div class="tape"><div class="tape-in">{"".join(items) * 4}</div></div>'


# =========================
# PANELES CLICABLES + FICHA DEL ACTIVO
# =========================

def seleccionar(simbolo, nombre):
    st.session_state.abrir = (simbolo, nombre)


def buscar_simbolo():
    v = (st.session_state.get("buscar") or "").strip().upper()
    if v:
        st.session_state.abrir = (v, v)
    st.session_state.buscar = ""


def mostrar_paneles():
    """Tablas de mercado: cada fila es clicable (un boton invisible cubre la fila)."""
    datos = datos_mercado()
    if not datos:
        return
    for inicio in range(0, len(GRUPOS_MERCADO), 2):
        cols = st.columns(2, gap="small")
        for col, (g, (titulo, lista)) in zip(cols, list(enumerate(GRUPOS_MERCADO))[inicio:inicio + 2]):
            with col, st.container(key=f"panel_{g}"):
                with st.container(key=f"hd_{g}"):
                    st.markdown(
                        f'<div class="mt-head"><span>{_esc(titulo).upper()}</span>'
                        '<span class="live">EN VIVO</span></div>'
                        '<div class="mt-cols"><span>Instrumento</span><span>Último</span>'
                        '<span>Var.</span><span>Var. %</span><span>1M</span></div>',
                        unsafe_allow_html=True)
                for j, (nombre, simbolo, tipo) in enumerate(lista):
                    d = datos.get(simbolo)
                    if not d:
                        continue
                    color = UP if d["pct"] >= 0 else DOWN
                    precio, var = _formato(tipo, d)
                    with st.container(key=f"row_{g}_{j}"):
                        st.markdown(
                            f'<div class="mt-row"><span class="n">{_esc(nombre)}</span>'
                            f'<span class="p">{precio}</span>'
                            f'<span style="color:{color}">{var}</span>'
                            f'<span style="color:{color}">{d["pct"]:+.2f}%</span>'
                            f'{_spark(d["serie"], color)}</div>', unsafe_allow_html=True)
                        st.button("Ver ficha", key=f"sel_{g}_{j}",
                                  on_click=seleccionar, args=(simbolo, nombre))


# ---- datos de la ficha ----

RANGOS = {"1M": ("1mo", "1d"), "3M": ("3mo", "1d"), "6M": ("6mo", "1d"),
          "1A": ("1y", "1d"), "5A": ("5y", "1wk")}


@st.cache_data(ttl=600, show_spinner=False)
def historial_activo(simbolo, rango, intervalo):
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(simbolo)}"
           f"?range={rango}&interval={intervalo}")
    r = requests.get(url, headers=UA, timeout=10)
    r.raise_for_status()
    res = r.json()["chart"]["result"][0]
    meta = res["meta"]
    q = res["indicators"]["quote"][0]
    try:
        tz = ZoneInfo(meta.get("exchangeTimezoneName", "America/New_York"))
    except Exception:
        tz = ZoneInfo("America/New_York")
    filas = []
    for t, o, h, l, c, v in zip(res["timestamp"], q["open"], q["high"], q["low"],
                                q["close"], q["volume"]):
        if c is None:
            continue
        filas.append({"fecha": datetime.fromtimestamp(t, tz).date().isoformat(),
                      "open": o if o is not None else c, "high": h if h is not None else c,
                      "low": l if l is not None else c, "close": c, "volume": v or 0})
    if not filas:
        raise ValueError("Sin datos")
    return {"meta": meta, "filas": filas}


@st.cache_resource(ttl=3000, show_spinner=False)
def _sesion_yahoo():
    s = requests.Session()
    s.headers.update(UA)
    try:
        s.get("https://fc.yahoo.com", timeout=6)      # entrega la cookie (responde 404, es normal)
    except Exception:
        pass
    crumb = s.get("https://query1.finance.yahoo.com/v1/test/getcrumb", timeout=6).text
    if not crumb or "<" in crumb or "Too Many" in crumb:
        raise ValueError("Sin crumb")
    return s, crumb


@st.cache_data(ttl=3600, show_spinner=False)
def _fundamentales_yahoo(simbolo):
    s, crumb = _sesion_yahoo()
    r = s.get(f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{quote(simbolo)}",
              params={"modules": "summaryDetail,defaultKeyStatistics,financialData,assetProfile,price",
                      "crumb": crumb}, timeout=8)
    r.raise_for_status()
    res = r.json()["quoteSummary"]["result"][0]

    def g(mod, campo):
        v = (res.get(mod) or {}).get(campo)
        if isinstance(v, dict):
            v = v.get("raw")
        return v
    return {
        "cap": g("price", "marketCap") or g("summaryDetail", "marketCap"),
        "pe": g("summaryDetail", "trailingPE"), "pe_fwd": g("summaryDetail", "forwardPE"),
        "eps": g("defaultKeyStatistics", "trailingEps"),
        "div": g("summaryDetail", "dividendYield"), "beta": g("summaryDetail", "beta"),
        "pb": g("defaultKeyStatistics", "priceToBook"),
        "margen": g("financialData", "profitMargins"),
        "objetivo": g("financialData", "targetMeanPrice"),
        "recom": g("financialData", "recommendationKey"),
        "sector": (res.get("assetProfile") or {}).get("sector"),
        "industria": (res.get("assetProfile") or {}).get("industry"),
        "pais": (res.get("assetProfile") or {}).get("country"),
        "empleados": (res.get("assetProfile") or {}).get("fullTimeEmployees"),
    }


def fundamentales(simbolo):
    try:
        return _fundamentales_yahoo(simbolo)
    except Exception as e:
        print(f"[Fundamentales] {simbolo}: {e}")
        return {}


def estadisticas_tecnicas(filas):
    """Rendimientos, volatilidad y drawdown calculados a partir de 1 anio de cierres diarios."""
    c = [f["close"] for f in filas]
    n = len(c)

    def rend(k):
        return (c[-1] / c[-1 - k] - 1) * 100 if n > k and c[-1 - k] else None
    anio = filas[-1]["fecha"][:4]
    previos = [f["close"] for f in filas if f["fecha"][:4] < anio]
    base_ytd = previos[-1] if previos else c[0]
    vol = None
    if n > 31:
        r = [math.log(c[i] / c[i - 1]) for i in range(n - 30, n) if c[i - 1] > 0 and c[i] > 0]
        if len(r) > 5:
            m = sum(r) / len(r)
            vol = math.sqrt(sum((x - m) ** 2 for x in r) / (len(r) - 1)) * math.sqrt(252) * 100
    pico, mdd = c[0], 0.0
    for x in c:
        pico = max(pico, x)
        mdd = min(mdd, (x / pico - 1) * 100)
    return {"r1m": rend(21), "r3m": rend(63), "r6m": rend(126),
            "ytd": (c[-1] / base_ytd - 1) * 100 if base_ytd else None,
            "r1a": (c[-1] / c[0] - 1) * 100 if n > 200 and c[0] else None,
            "vol30": vol, "mdd": mdd}


def _num(x, dec=2, pref="", suf=""):
    return "—" if x is None else f"{pref}{x:,.{dec}f}{suf}"


def _grande(x, pref="$"):
    if x is None:
        return "—"
    for lim, suf in ((1e12, " T"), (1e9, " B"), (1e6, " M")):
        if abs(x) >= lim:
            return f"{pref}{x / lim:,.2f}{suf}"
    return f"{pref}{x:,.0f}"


def _pct_html(x, dec=2):
    if x is None:
        return "—", None
    return f"{x:+.{dec}f}%", (UP if x >= 0 else DOWN)


def _tile(label, valor, color=None, extra=""):
    estilo = f' style="color:{color}"' if color else ""
    return f'<div class="tl"><span>{label}</span><b{estilo}>{valor}</b>{extra}</div>'


def _barra_rango(bajo, alto, actual):
    if bajo is None or alto is None or alto <= bajo or actual is None:
        return ""
    pos = min(max((actual - bajo) / (alto - bajo) * 100, 0), 100)
    return f'<div class="rb"><i style="left:{pos:.0f}%"></i></div>'


def _seccion(titulo, tiles, cols=4):
    tiles = [t for t in tiles if t]
    if not tiles:
        return ""
    return (f'<div class="sec-t">{titulo}</div>'
            f'<div class="tl-grid" style="--c:{cols}">{"".join(tiles)}</div>')


def grafica_detalle(filas, simbolo, rango_lbl):
    fechas = [f["fecha"] for f in filas]
    cierres = [f["close"] for f in filas]
    n = len(cierres)
    sube = cierres[-1] >= cierres[0]
    color = UP if sube else DOWN
    hay_vol = sum(f["volume"] for f in filas) > 0
    if hay_vol:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03,
                            row_heights=[0.78, 0.22])
    else:
        fig = make_subplots(rows=1, cols=1)
    lo, hi = min(cierres), max(cierres)
    margen = (hi - lo) * 0.12 or 1
    base = lo - margen
    fig.add_trace(go.Scatter(x=fechas, y=[base] * n, mode="lines", line=dict(width=0),
                             hoverinfo="skip"), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=fechas, y=cierres, mode="lines", line=dict(width=2.2, color=color),
        fill="tonexty", fillcolor=hex_a_rgba(color, 0.08),
        hovertemplate="<b>%{y:,.2f}</b>  ·  %{x}<extra></extra>"), row=1, col=1)
    fig.add_annotation(x=fechas[-1], y=cierres[-1], text=f"{cierres[-1]:,.2f}", showarrow=False,
                       xanchor="right", yshift=16, row=1, col=1,
                       font=dict(family=FUENTE_NUM, size=12, color="#FFFFFF"),
                       bgcolor=color, borderpad=3)
    if hay_vol:
        colores = [hex_a_rgba(UP if f["close"] >= f["open"] else DOWN, 0.55) for f in filas]
        fig.add_trace(go.Bar(x=fechas, y=[f["volume"] for f in filas], marker_color=colores,
                             hovertemplate="Vol. %{y:,.0f}<extra></extra>"), row=2, col=1)
    estilo_base(fig, "", "", altura=380 if hay_vol else 320)
    fig.update_layout(title=None, margin=dict(l=8, r=72, t=14, b=54))
    fig.update_yaxes(range=[base, hi + margen], row=1, col=1)
    fig.update_yaxes(showgrid=False, showticklabels=False, row=2, col=1)
    formato = "%b %Y" if rango_lbl in ("1A", "5A") else "%b %d"
    if not simbolo.upper().endswith("-USD"):
        fig.update_xaxes(type="date", tickformat=formato, rangebreaks=[dict(bounds=["sat", "mon"])])
    else:
        fig.update_xaxes(type="date", tickformat=formato)
    return fig


def contenido_detalle(simbolo, nombre):
    try:
        base = historial_activo(simbolo, "1y", "1d")
    except Exception as e:
        print(f"[Ficha] {simbolo}: {e}")
        st.error(f"No encontré datos para «{simbolo}». Probá con otro símbolo de Yahoo Finance "
                 "(por ejemplo AAPL, MSFT, ^GSPC o EURUSD=X).")
        return
    meta, f1a = base["meta"], base["filas"]
    cierres = [f["close"] for f in f1a]
    precio = meta.get("regularMarketPrice") or cierres[-1]
    previo = cierres[-2] if len(cierres) > 1 else cierres[0]
    cam = precio - previo
    pct = cam / previo * 100 if previo else 0.0
    color = UP if cam >= 0 else DOWN
    titulo = meta.get("longName") or meta.get("shortName") or nombre
    bolsa = meta.get("fullExchangeName") or meta.get("exchangeName") or ""
    moneda = meta.get("currency") or ""
    tipo = (meta.get("instrumentType") or "").replace("_", " ")
    etiquetas = " ".join(f'<span class="tag">{_esc(t)}</span>' for t in
                         (simbolo.upper(), bolsa, moneda, tipo) if t)
    dec = 4 if abs(precio) < 20 else 2
    st.markdown(
        f'<div class="fh"><div class="fh-n">{_esc(titulo)}</div><div>{etiquetas}</div>'
        f'<div class="fh-p"><span>{precio:,.{dec}f}</span>'
        f'<span style="color:{color}">{"▲" if cam >= 0 else "▼"} {cam:+,.{dec}f}  ({pct:+.2f}%)</span></div></div>',
        unsafe_allow_html=True)

    rango_lbl = st.segmented_control("Rango", list(RANGOS), default="3M", key="rango_ficha",
                                     label_visibility="collapsed") or "3M"
    try:
        hist = base if rango_lbl == "1A" else historial_activo(simbolo, *RANGOS[rango_lbl])
        st.plotly_chart(grafica_detalle(hist["filas"], simbolo, rango_lbl),
                        use_container_width=True, config=PLOT_CONFIG, key=f"det_{simbolo}_{rango_lbl}")
    except Exception as e:
        print(f"[Ficha grafica] {simbolo}: {e}")
        st.caption("No se pudo cargar la gráfica de ese rango.")

    t = estadisticas_tecnicas(f1a)
    h = f1a[-1]
    vol_prom = sum(f["volume"] for f in f1a[-63:]) / max(len(f1a[-63:]), 1)
    d_bajo, d_alto = meta.get("regularMarketDayLow"), meta.get("regularMarketDayHigh")
    a_bajo, a_alto = meta.get("fiftyTwoWeekLow"), meta.get("fiftyTwoWeekHigh")
    rend = []
    for etq, k in (("1 mes", "r1m"), ("3 meses", "r3m"), ("6 meses", "r6m"), ("En el año", "ytd"), ("1 año", "r1a")):
        txt, col = _pct_html(t[k])
        rend.append(_tile(etq, txt, col))
    html_ficha = _seccion("RENDIMIENTO", rend, 5)
    html_ficha += _seccion("PRECIO Y VOLUMEN", [
        _tile("Cierre anterior", _num(previo, dec)),
        _tile("Apertura", _num(h["open"], dec)),
        _tile("Rango del día", f'{_num(d_bajo, dec)} – {_num(d_alto, dec)}', None, _barra_rango(d_bajo, d_alto, precio)),
        _tile("Rango 52 sem.", f'{_num(a_bajo, dec)} – {_num(a_alto, dec)}', None, _barra_rango(a_bajo, a_alto, precio)),
        _tile("Volumen", _grande(meta.get("regularMarketVolume"), "") if meta.get("regularMarketVolume") else "—"),
        _tile("Vol. promedio (3M)", _grande(vol_prom, "") if vol_prom else "—"),
    ])
    html_ficha += _seccion("RIESGO", [
        _tile("Volatilidad 30d (anual.)", _num(t["vol30"], 1, "", "%")),
        _tile("Máx. drawdown (1A)", _num(t["mdd"], 1, "", "%"), DOWN if t["mdd"] < 0 else None),
    ], 4)
    st.markdown(html_ficha, unsafe_allow_html=True)

    fu = fundamentales(simbolo)
    if fu:
        div = fu.get("div")
        recom = (fu.get("recom") or "").replace("_", " ").capitalize() or "—"
        fund = [
            _tile("Capitalización", _grande(fu.get("cap")) if fu.get("cap") else "—"),
            _tile("P/E (TTM)", _num(fu.get("pe"))),
            _tile("P/E (adelantado)", _num(fu.get("pe_fwd"))),
            _tile("BPA (TTM)", _num(fu.get("eps"), 2, "$")),
            _tile("Rend. por dividendo", _num(div * 100 if div is not None else None, 2, "", "%")),
            _tile("Beta", _num(fu.get("beta"))),
            _tile("Precio / valor libros", _num(fu.get("pb"))),
            _tile("Margen neto", _num(fu["margen"] * 100 if fu.get("margen") is not None else None, 1, "", "%")),
            _tile("Precio objetivo", _num(fu.get("objetivo"), 2, "$")),
            _tile("Recomendación", _esc(recom)),
        ]
        html_f = _seccion("FUNDAMENTALES", [x for x in fund if "—</b>" not in x], 5)
        perfil = [p for p in (fu.get("sector"), fu.get("industria"), fu.get("pais")) if p]
        if perfil:
            html_f += f'<div class="perfil">{_esc(" · ".join(perfil))}</div>'
        st.markdown(html_f, unsafe_allow_html=True)
    st.caption("Datos de Yahoo Finance, pueden tener unos minutos de retraso. "
               "Rendimiento, volatilidad y drawdown calculados por Macroscopio con 1 año de cierres diarios.")

    if st.button("Analizar con Macroscopio", icon=":material/insights:", key="analizar_ficha",
                 type="primary"):
        pedir(f"Analizá {titulo} ({simbolo.upper()}): variación y volatilidad del último mes")
        st.rerun()


def abrir_ficha(simbolo, nombre):
    @st.dialog(nombre, width="large")
    def _ventana():
        contenido_detalle(simbolo, nombre)
    _ventana()


# =========================
# SUGERENCIAS DE SEGUIMIENTO
# =========================

SEGUIMIENTO = {
    "Yahoo Finance": ["¿Y en los últimos 6 meses?", "Compará con el S&P 500 (SPY)", "¿Qué tan volátil ha sido?"],
    "Banco Mundial": ["Compará con Costa Rica", "Ahora la inflación", "¿Cuál fue la variación promedio?"],
    "open.er-api": ["¿Y el yen japonés?", "¿Y el quetzal?", "¿Cuánto es 1,000 dólares en euros?"],
}


def sugerencias(fuentes):
    out = []
    for f in fuentes or []:
        for clave, lista in SEGUIMIENTO.items():
            if clave in f:
                out += [x for x in lista if x not in out]
    return out[:3]


def pedir(texto):
    st.session_state.pending_query = texto


def tipear(texto):
    """Efecto de escritura progresiva para las respuestas nuevas."""
    for trozo in re.findall(r"\S+\s*", texto):
        yield trozo
        time.sleep(0.012)


# =========================
# MOSTRAR CONVERSACION
# =========================

PLOT_CONFIG = {
    "displaylogo": False,
    "displayModeBar": "hover",
    "modeBarButtons": [["toImage"]],     # solo el boton de descargar como imagen
    "toImageButtonOptions": {"format": "png", "filename": "macroscopio", "scale": 2},
}

EJEMPLOS = [
    ("Tipo de cambio", "¿Cuál es el tipo de cambio del euro?"),
    ("Indicadores macro", "Dame el crecimiento del PIB de Guatemala de 2018 a 2023"),
    ("Acciones", "¿Qué tan volátil ha sido NVIDIA en el último mes?"),
    ("Comparar países", "Compará el PIB de Guatemala y Costa Rica de 2018 a 2023"),
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

    def _grupo(chat):
        try:
            dias = (datetime.now().date() - datetime.fromisoformat(chat.get("updated", "")).date()).days
        except Exception:
            return "Anteriores"
        if dias <= 0:
            return "Hoy"
        if dias == 1:
            return "Ayer"
        return "Últimos 7 días" if dias <= 7 else "Anteriores"

    grupo_actual = None
    for chat in indice:
        grupo = _grupo(chat)
        if grupo != grupo_actual:
            st.markdown(f'<div class="side-title">{grupo}</div>', unsafe_allow_html=True)
            grupo_actual = grupo
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
        'Fuentes: Banco Mundial, Yahoo Finance, open.er-api'
        + ('<br>Chats guardados en Supabase' if SUPABASE_ON else '') + '</div>',
        unsafe_allow_html=True,
    )


# =========================
# CONVERSACION
# =========================

st.markdown(cinta_mercados_html(), unsafe_allow_html=True)

memory = st.session_state.memory
chat_id = st.session_state.chat_id
consulta_pendiente = st.session_state.pop("pending_query", None)

if not st.session_state.chat_history and not consulta_pendiente:
    st.markdown(
        f'<div class="hero"><div class="name">{APP_NAME}</div>'
        f'<div class="sub">{APP_TAGLINE}</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    mostrar_paneles()
    st.text_input("Buscar símbolo", key="buscar", on_change=buscar_simbolo,
                  placeholder="Buscar cualquier símbolo de Yahoo Finance (AAPL, MSFT, ^GSPC, EURUSD=X) y presionar Enter",
                  label_visibility="collapsed")
    st.markdown('<div class="mk-title">CONSULTAS SUGERIDAS</div>', unsafe_allow_html=True)
    columnas = st.columns(len(EJEMPLOS))
    for i, (categoria, ejemplo) in enumerate(EJEMPLOS):
        with columnas[i]:
            if st.button(f"**{categoria}**  \n{ejemplo}", key=f"ej_{i}", use_container_width=True):
                st.session_state.pending_query = ejemplo
                st.rerun()

_abrir = st.session_state.pop("abrir", None)
if _abrir:
    abrir_ficha(*_abrir)

for idx, message in enumerate(st.session_state.chat_history):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        mostrar_figuras(message.get("figuras", []), f"fig_{chat_id}_{idx}")
        if message.get("fuentes"):
            st.caption("Fuentes: " + " · ".join(message["fuentes"]))


chips_slot = st.empty()
if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "assistant":
    _sug = sugerencias(st.session_state.chat_history[-1].get("fuentes"))
    if _sug:
        with chips_slot.container(key="chips"):
            for k, texto in enumerate(_sug):
                st.button(texto, key=f"chip_{chat_id}_{k}", on_click=pedir, args=(texto,))

# =========================
# ENTRADA DEL USUARIO
# =========================

user_text = st.chat_input("Escribí tu consulta: tipo de cambio, PIB, inflación, una acción...")
if not user_text and consulta_pendiente:
    user_text = consulta_pendiente

if user_text:

    chips_slot.empty()
    user_text = user_text.strip()

    if user_text:

        es_primer_mensaje = not st.session_state.chat_history

        st.session_state.chat_history.append(
            {"role": "user", "content": user_text, "figuras": []}
        )

        with st.chat_message("user"):
            st.markdown(user_text)

        with st.chat_message("assistant"):

            fuentes = []
            with st.status("Analizando tu consulta…", expanded=True) as estado:
                def al_usar_herramienta(nombre):
                    estado.write(ETAPAS.get(nombre, nombre) + "…")

                assistant_text, figuras = process_response(
                    client, memory.messages(), memory.summary, user_text,
                    on_tool=al_usar_herramienta, fuentes=fuentes,
                )
                estado.update(label="Listo", state="complete", expanded=False)

            st.write_stream(tipear(assistant_text))
            mostrar_figuras(figuras, "fig_nueva")
            if fuentes:
                st.caption("Fuentes: " + " · ".join(fuentes))

        # =========================
        # ACTUALIZAR MEMORIA Y GUARDAR EL CHAT
        # =========================

        with st.spinner("Guardando..."):
            memory.add("user", user_text)
            memory.add("assistant", assistant_text)
            sincronizar_memoria(st.session_state.chat_id)

        st.session_state.chat_history.append(
            {"role": "assistant", "content": assistant_text, "figuras": figuras,
             "fuentes": fuentes}
        )
        guardar_ui(chat_id, st.session_state.chat_history)
        registrar_chat(chat_id, user_text if es_primer_mensaje else "")

        st.rerun()
