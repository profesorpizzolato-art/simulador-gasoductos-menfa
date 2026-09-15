import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

# Importaciones de ReportLab para la generación de PDF
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Simulador de integridad de conductos - ASME B31G",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FUNCIONES DE CÁLCULO (ASME B31G) ---
def evaluar_asme_b31g(D, t, SMYS, P_diseno, d, L, factor_seguridad=1.25):
    """
    Evaluación de la severidad de corrosión y presión admisible según ASME B31G.
    """
    if t <= 0 or D <= 0:
        return None
    
    # 1. Porcentaje de pérdida de pared
    pct_profundidad = (d / t) * 100.0
    
    # Criterio preliminar: Si d >= 0.80 * t, la falla es inminente / no admisible por ASME B31G
    if d >= 0.80 * t:
        presion_fallo = 0.0
        presion_segura = 0.0
        falla_inminente = True
        M = 0.0
        A = 0.0
    else:
        falla_inminente = False
        # Parámetro Folias (M)
        A = 0.893 * (L / np.sqrt(D * t))
        
        if A <= 4.0:
            M = np.sqrt(1 + 0.8 * (L ** 2 / (D * t)))
        else:
            M = 0.08 * (L ** 2 / (D * t)) + 3.3
            
        # Presión de flujo (S_flow) según ASME B31G original = 1.1 * SMYS
        S_flow = 1.1 * SMYS
        
        # Presión de falla (P_pf)
        d_over_t = d / t
        if A <= 4.0:
            num = 1 - (2 / 3) * d_over_t
            den = 1 - (2 / 3) * (d_over_t / M) if M != 0 else 1.0
            presion_fallo = (2 * t * S_flow / D) * (num / den)
        else:
            presion_fallo = (2 * t * S_flow / D) * (1 - d_over_t)
            
        # Presión máxima admisible de operación (MAOP_safe / P_safe)
        presion_segura = presion_fallo / factor_seguridad

    # Estado / Evaluación
    if falla_inminente or d >= 0.80 * t:
        estado = "CRÍTICO - Profundidad excesiva (>80% t)"
        color_estado = "rojo"
    elif P_diseno > presion_segura:
        estado = "NO SEGURO - Requiere Reducción de Presión o Reparación"
        color_estado = "naranja"
    else:
        estado = "ACEPTABLE - Operación Segura bajo ASME B31G"
        color_estado = "verde"
        
    return {
        "pct_profundidad": pct_profundidad,
        "presion_fallo": presion_fallo,
        "presion_segura": presion_segura,
        "estado": estado,
        "color_estado": color_estado,
        "M": M,
        "A": A
    }

def generar_reporte_pdf(datos_tubo, resultados):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#1E3A8A'))
    subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Heading2'], fontSize=12, leading=16, textColor=colors.HexColor('#1F2937'))
    normal_style = styles['Normal']
    
    color_map = {
        'verde': colors.HexColor('#10B981'),
        'naranja': colors.HexColor('#F59E0B'),
        'rojo': colors.HexColor('#EF4444')
    }
    
    historia = []
    
    historia.append(Paragraph("Reporte de Evaluación de Integridad - ASME B31G", title_style))
    historia.append(Spacer(1, 15))
    
    historia.append(Paragraph("1. Parámetros de Entrada", subtitle_style))
    data_input = [
        ["Parámetro", "Valor"],
        ["Diámetro Exterior (D)", f"{datos_tubo['D']} in"],
        ["Espesor Nominal (t)", f"{datos_tubo['t']} in"],
        ["SMYS Material", f"{datos_tubo['SMYS']} psi"],
        ["Presión de Diseño", f"{datos_tubo['P_diseno']} psi"],
        ["Profundidad Defecto (d)", f"{datos_tubo['d']} in"],
        ["Longitud Defecto (L)", f"{datos_tubo['L']} in"],
        ["Factor de Seguridad", f"{datos_tubo['FS']}"]
    ]
    t_input = Table(data_input, colWidths=[220, 230])
    t_input.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    historia.append(t_input)
    historia.append(Spacer(1, 15))
    
    historia.append(Paragraph("2. Resultados del Análisis", subtitle_style))
    data_res = [
        ["Métrica", "Resultado"],
        ["Pérdida de Espesor", f"{resultados['pct_profundidad']:.1f} %"],
        ["Presión de Falla Estimada", f"{resultados['presion_fallo']:.1f} psi"],
        ["Presión Segura Admisible", f"{resultados['presion_segura']:.1f} psi"],
        ["Estado", resultados['estado']]
    ]
    t_res = Table(data_res, colWidths=[220, 230])
    t_res.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('TEXTCOLOR', (1, 3), (1, 3), color_map.get(resultados['color_estado'], colors.black)),
        ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold')
    ]))
    historia.append(t_res)
    historia.append(Spacer(1, 20))
    
    historia.append(Paragraph("3. Recomendaciones Operativas", subtitle_style))
    if resultados['color_estado'] == "verde":
        rec_text = "El defecto inspeccionado satisface las condiciones de integridad de ASME B31G. La tubería puede operar a la presión de diseño sin requerir reparación inmediata."
    elif resultados['color_estado'] == "naranja":
        p_reducida = resultados['presion_segura']
        rec_text = f"<b>ALERTA DE SEGURIDAD:</b> La presión de diseño ({datos_tubo['P_diseno']} psi) supera la presión admisible calculada ({p_reducida:.1f} psi). Se recomienda reducir la presión de operación a un valor no mayor a <b>{p_reducida:.1f} psi</b> o programar una reparación."
    else:
        rec_text = "<b>CRÍTICO:</b> La profundidad del defecto excede el 80% del espesor nominal. Requiere reparación física inmediata o reemplazo de carrete."
        
    historia.append(Paragraph(rec_text, normal_style))
    
    doc.build(historia)
    buffer.seek(0)
    return buffer

# --- INTERFAZ STREAMLIT ---
st.title("🛡️ Simulador de Integridad de Ductos: ASME B31G")
st.markdown("Evaluación de la resistencia remanente de tuberías de acero con defectos de corrosión axial.")

st.sidebar.header("⚙️ Parámetros del Ducto y Defecto")

D = st.sidebar.number_input("Diámetro Exterior - D (pulgadas)", min_value=1.0, max_value=60.0, value=12.75, step=0.25)
t = st.sidebar.number_input("Espesor Nominal - t (pulgadas)", min_value=0.05, max_value=3.0, value=0.375, step=0.01)

grado_smys = st.sidebar.selectbox(
    "Grado del Material (SMYS)",
    options=[
        ("API 5L X42 (42.000 psi)", 42000),
        ("API 5L X52 (52.000 psi)", 52000),
        ("API 5L X60 (60.000 psi)", 60000),
        ("API 5L X65 (65.000 psi)", 65000),
        ("API 5L X70 (70.000 psi)", 70000),
        ("Personalizado", 0)
    ],
    format_func=lambda x: x[0]
)

SMYS = st.sidebar.number_input("SMYS Personalizado (psi)", min_value=20000, max_value=100000, value=52000, step=1000) if grado_smys[1] == 0 else grado_smys[1]

P_diseno = st.sidebar.number_input("Presión de Operación / Diseño - P (psi)", min_value=10.0, max_value=5000.0, value=900.0, step=10.0)

st.sidebar.subheader("📐 Geometría del Defecto de Corrosión")
d = st.sidebar.number_input("Profundidad del Defecto - d (pulgadas)", min_value=0.001, max_value=float(t), value=min(0.125, t * 0.99), step=0.005)
L = st.sidebar.number_input("Longitud Axial del Defecto - L (pulgadas)", min_value=0.01, max_value=50.0, value=4.5, step=0.1)

factor_s = st.sidebar.slider("Factor de Seguridad (FS)", min_value=1.1, max_value=2.0, value=1.25, step=0.05)

res = evaluar_asme_b31g(D, t, SMYS, P_diseno, d, L, factor_s)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Pérdida de Espesor", f"{res['pct_profundidad']:.1f}%")
col2.metric("Presión Estimada Falla", f"{res['presion_fallo']:.1f} psi")
col3.metric("Presión Segura Admisible", f"{res['presion_segura']:.1f} psi")
col4.metric("Presión de Operación", f"{P_diseno:.1f} psi")

if res['color_estado'] == "verde":
    st.success(f"✅ **ESTADO: {res['estado']}**")
elif res['color_estado'] == "naranja":
    st.warning(f"⚠️ **ESTADO: {res['estado']}**")
else:
    st.error(f"🚨 **ESTADO: {res['estado']}**")

tab1, tab2, tab3 = st.tabs(["📊 Análisis Gráfico & Curvas", "⚙️ Detalles Matemáticos", "📄 Exportar Reporte PDF"])

with tab1:
    st.subheader("Curva de Presión vs. Profundidad del Defecto")
    d_array = np.linspace(0.001, t * 0.799, 100)
    p_safe_array, p_fail_array = [], []
    
    for d_val in d_array:
        r_temp = evaluar_asme_b31g(D, t, SMYS, P_diseno, d_val, L, factor_s)
        p_safe_array.append(r_temp['presion_segura'])
        p_fail_array.append(r_temp['presion_fallo'])
        
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d_array / t * 100, y=[P_diseno] * len(d_array), mode='lines', name='Presión Operación', line=dict(color='red', dash='dash')))
    fig.add_trace(go.Scatter(x=d_array / t * 100, y=p_fail_array, mode='lines', name='Presión Falla (P_falla)', line=dict(color='gray')))
    fig.add_trace(go.Scatter(x=d_array / t * 100, y=p_safe_array, mode='lines', name='Presión Segura (P_segura)', line=dict(color='green', width=3)))
    fig.add_trace(go.Scatter(x=[res['pct_profundidad']], y=[res['presion_segura']], mode='markers', name='Defecto Actual', marker=dict(color='blue', size=12, symbol='star')))
    
    fig.update_layout(title=f"Evaluación ASME B31G (L = {L:.2f} in)", xaxis_title="Profundidad / Espesor t (%)", yaxis_title="Presión (psi)", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Formulación Estándar ASME B31G")
    st.latex(r"A = 0.893 \cdot \frac{L}{\sqrt{D \cdot t}}")
    st.latex(r"M = \sqrt{1 + 0.8 \cdot \left(\frac{L^2}{D \cdot t}\right)} \quad \text{si } A \le 4.0")
    st.latex(r"P_{falla} = \frac{2 \cdot t \cdot (1.1 \cdot SMYS)}{D} \cdot \left[\frac{1 - \frac{2}{3}\left(\frac{d}{t}\right)}{1 - \frac{2}{3}\left(\frac{d}{t \cdot M}\right)}\right]")

with tab3:
    st.subheader("Generación del Reporte Oficial PDF")
    datos_tubo = {"D": D, "t": t, "SMYS": SMYS, "P_diseno": P_diseno, "d": d, "L": L, "FS": factor_s}
    pdf_buffer = generar_reporte_pdf(datos_tubo, res)
    
    st.download_button(
        label="📥 Descargar Informe PDF",
        data=pdf_buffer,
        file_name=f"Reporte_ASME_B31G_{D}in.pdf",
        mime="application/pdf"
    )
