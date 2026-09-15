import os
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

# Importaciones de ReportLab para la generación de PDF
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Simulador Avanzado de Integridad de Ductos - MENFA",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ruta del logo de MENFA
LOGO_PATH = "logo_menfa.png"

# ==========================================
# MOSTRAR LOGO EN LA BARRA LATERAL (STREAMLIT)
# ==========================================
if os.path.exists(LOGO_PATH):
    st.sidebar.image(LOGO_PATH, use_container_width=True)
else:
    st.sidebar.info("💡 Coloca 'logo_menfa.png' en la carpeta raíz para ver el logo aquí.")

# ==========================================
# 1. CRITERIOS DE EVALUACIÓN TÉCNICA
# ==========================================

def evaluar_asme_b31g_original(D, t, SMYS, P_diseno, d, L, factor_seguridad=1.25):
    if t <= 0 or D <= 0: return None
    pct_profundidad = (d / t) * 100.0
    
    if d >= 0.80 * t:
        return {"presion_fallo": 0.0, "presion_segura": 0.0, "estado": "CRÍTICO (>80% t)", "color": "rojo"}
    
    A = 0.893 * (L / np.sqrt(D * t))
    M = np.sqrt(1 + 0.8 * (L ** 2 / (D * t))) if A <= 4.0 else (0.08 * (L ** 2 / (D * t)) + 3.3)
    S_flow = 1.1 * SMYS
    d_over_t = d / t
    
    if A <= 4.0:
        num = 1 - (2 / 3) * d_over_t
        den = 1 - (2 / 3) * (d_over_t / M) if M != 0 else 1.0
        P_falla = (2 * t * S_flow / D) * (num / den)
    else:
        P_falla = (2 * t * S_flow / D) * (1 - d_over_t)
        
    P_segura = P_falla / factor_seguridad
    estado, color = ("NO SEGURO - Reducir Presión", "naranja") if P_diseno > P_segura else ("ACEPTABLE", "verde")
        
    return {"presion_fallo": P_falla, "presion_segura": P_segura, "estado": estado, "color": color, "pct_profundidad": pct_profundidad}

def evaluar_asme_b31g_modificado(D, t, SMYS, P_diseno, d, L, factor_seguridad=1.25):
    if t <= 0 or D <= 0: return None
    pct_profundidad = (d / t) * 100.0
    if d >= 0.80 * t:
        return {"presion_fallo": 0.0, "presion_segura": 0.0, "estado": "CRÍTICO (>80% t)", "color": "rojo"}
    
    z = (L ** 2) / (D * t)
    M = np.sqrt(1 + 0.6275 * z - 0.003375 * (z ** 2)) if z <= 50 else (0.032 * z + 3.293)
    S_flow = SMYS + 10000
    d_over_t = d / t
    
    num = 1 - 0.85 * d_over_t
    den = 1 - 0.85 * (d_over_t / M) if M != 0 else 1.0
    P_falla = (2 * t * S_flow / D) * (num / den)
    P_segura = P_falla / factor_seguridad
    
    estado, color = ("NO SEGURO", "naranja") if P_diseno > P_segura else ("ACEPTABLE", "verde")
    return {"presion_fallo": P_falla, "presion_segura": P_segura, "estado": estado, "color": color, "pct_profundidad": pct_profundidad}

def evaluar_dnv_rp_f101(D, t, SMYS, UTS, P_diseno, d, L, factor_seguridad=1.25):
    if t <= 0 or D <= 0: return None
    pct_profundidad = (d / t) * 100.0
    if d >= 0.85 * t:
        return {"presion_fallo": 0.0, "presion_segura": 0.0, "estado": "CRÍTICO (>85% t)", "color": "rojo"}
    
    Q = np.sqrt(1 + 0.31 * (L ** 2 / (D * t)))
    P_falla = (2 * t * UTS / (D - t)) * ((1 - (d / t)) / (1 - (d / (t * Q))))
    P_segura = P_falla / factor_seguridad
    
    estado, color = ("NO SEGURO", "naranja") if P_diseno > P_segura else ("ACEPTABLE", "verde")
    return {"presion_fallo": P_falla, "presion_segura": P_segura, "estado": estado, "color": color, "pct_profundidad": pct_profundidad}

# ==========================================
# 2. GENERACIÓN DE REPORTES PDF CON LOGO
# ==========================================

def generar_reporte_pdf(datos_tubo, resultados_multiples):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#1E3A8A'))
    subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Heading2'], fontSize=12, leading=16, textColor=colors.HexColor('#1F2937'))
    
    historia = []
    
    # Incluir logo MENFA en el PDF si existe el archivo
    if os.path.exists(LOGO_PATH):
        img = Image(LOGO_PATH, width=150, height=50)
        img.hAlign = 'LEFT'
        historia.append(img)
        historia.append(Spacer(1, 10))

    historia.extend([
        Paragraph("Reporte Comparativo de Integridad de Ductos - MENFA", title_style),
        Spacer(1, 15),
        Paragraph("1. Parámetros del Ducto y Defecto", subtitle_style)
    ])
    
    data_input = [
        ["Parámetro", "Valor"],
        ["Diámetro Exterior (D)", f"{datos_tubo['D']} in"],
        ["Espesor Nominal (t)", f"{datos_tubo['t']} in"],
        ["SMYS Material", f"{datos_tubo['SMYS']} psi"],
        ["Presión de Operación", f"{datos_tubo['P_diseno']} psi"],
        ["Profundidad Defecto (d)", f"{datos_tubo['d']} in"],
        ["Longitud Defecto (L)", f"{datos_tubo['L']} in"]
    ]
    t_input = Table(data_input, colWidths=[220, 230])
    t_input.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F3F4F6')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB'))
    ]))
    historia.extend([t_input, Spacer(1, 15), Paragraph("2. Comparativa Criterios de Evaluación", subtitle_style)])
    
    data_res = [["Norma / Criterio", "P. Falla (psi)", "P. Segura (psi)", "Estado"]]
    for norma, res in resultados_multiples.items():
        data_res.append([norma, f"{res['presion_fallo']:.1f}", f"{res['presion_segura']:.1f}", res['estado']])
        
    t_res = Table(data_res, colWidths=[150, 100, 100, 100])
    t_res.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F3F4F6')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB'))
    ]))
    historia.append(t_res)
    doc.build(historia)
    buffer.seek(0)
    return buffer

# ==========================================
# 3. INTERFAZ Y NAVEGACIÓN
# ==========================================

st.title("🛡️ Sistema Avanzado de Integridad de Ductos - MENFA")

st.sidebar.header("⚙️ Parámetros Básicos")
D = st.sidebar.number_input("Diámetro Exterior - D (pulgadas)", 1.0, 60.0, 12.75, 0.25)
t = st.sidebar.number_input("Espesor Nominal - t (pulgadas)", 0.05, 3.0, 0.375, 0.01)
SMYS = st.sidebar.number_input("SMYS (psi)", 20000, 100000, 52000, 1000)
UTS = st.sidebar.number_input("UTS - Resistencia Tensión (psi)", 30000, 120000, 66000, 1000)
P_diseno = st.sidebar.number_input("Presión Operación (psi)", 10.0, 5000.0, 900.0, 10.0)

st.sidebar.subheader("📐 Geometría Defecto")
d = st.sidebar.number_input("Profundidad - d (pulgadas)", 0.001, float(t), min(0.125, t * 0.99), 0.005)
L = st.sidebar.number_input("Longitud - L (pulgadas)", 0.01, 50.0, 4.5, 0.1)
FS = st.sidebar.slider("Factor de Seguridad (FS)", 1.1, 2.0, 1.25, 0.05)

# Pestañas Principales
tab_eval, tab_3d, tab_ili, tab_rla = st.tabs([
    "1. Criterios Múltiples (ASME/DNV)",
    "2. Visualización 3D & Matriz",
    "3. Carga Masiva ILI",
    "4. Vida Útil Remanente (RLA)"
])

# ------------------------------------------
# MODULO 1: CRITERIOS TÉCNICOS
# ------------------------------------------
with tab_eval:
    st.subheader("Comparativa de Evaluación Multi-Norma")
    
    r_b31g = evaluar_asme_b31g_original(D, t, SMYS, P_diseno, d, L, FS)
    r_mod = evaluar_asme_b31g_modificado(D, t, SMYS, P_diseno, d, L, FS)
    r_dnv = evaluar_dnv_rp_f101(D, t, SMYS, UTS, P_diseno, d, L, FS)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("ASME B31G Original (P. Segura)", f"{r_b31g['presion_segura']:.1f} psi", delta=r_b31g['estado'])
    col2.metric("ASME B31G Modificado (P. Segura)", f"{r_mod['presion_segura']:.1f} psi", delta=r_mod['estado'])
    col3.metric("DNV-RP-F101 (P. Segura)", f"{r_dnv['presion_segura']:.1f} psi", delta=r_dnv['estado'])
    
    datos_tubo = {"D": D, "t": t, "SMYS": SMYS, "P_diseno": P_diseno, "d": d, "L": L}
    res_mult = {"B31G Original": r_b31g, "B31G Modificado": r_mod, "DNV-RP-F101": r_dnv}
    
    pdf_buf = generar_reporte_pdf(datos_tubo, res_mult)
    st.download_button("📥 Descargar Reporte Comparativo PDF", pdf_buf, "Reporte_Integridad_MENFA.pdf", "application/pdf")

# ------------------------------------------
# MODULO 2: VISUALIZACIÓN 3D & MATRIZ
# ------------------------------------------
with tab_3d:
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("Modelado 3D del Defecto")
        theta = np.linspace(0, 2 * np.pi, 50)
        z = np.linspace(0, L * 3, 50)
        THETA, Z = np.meshgrid(theta, z)
        R = np.full_like(THETA, D / 2.0)
        
        mask_z = (Z > L) & (Z < L * 2)
        mask_th = (THETA > np.pi / 2) & (THETA < 3 * np.pi / 2)
        R[mask_z & mask_th] -= d
        
        X = R * np.cos(THETA)
        Y = R * np.sin(THETA)
        
        fig_3d = go.Figure(data=[go.Surface(x=X, y=Y, z=Z, colorscale='Reds_r')])
        fig_3d.update_layout(title="Simulación Geométrica 3D", autosize=False, width=400, height=400)
        st.plotly_chart(fig_3d, use_container_width=True)
        
    with col_b:
        st.subheader("Matriz de Riesgo: d/t vs L")
        d_vals = np.linspace(0, t, 30)
        L_vals = np.linspace(0.1, 20, 30)
        Z_risk = np.zeros((30, 30))
        
        for i, d_v in enumerate(d_vals):
            for j, L_v in enumerate(L_vals):
                res = evaluar_asme_b31g_modificado(D, t, SMYS, P_diseno, d_v, L_v, FS)
                Z_risk[i, j] = res['presion_segura']
                
        fig_mat = go.Figure(data=go.Heatmap(z=Z_risk, x=L_vals, y=d_vals / t * 100, colorscale='RdYlGn'))
        fig_mat.add_trace(go.Scatter(x=[L], y=[d / t * 100], mode='markers', marker=dict(color='blue', size=14, symbol='star'), name='Defecto Actual'))
        fig_mat.update_layout(title="Mapa de Presión Segura (psi)", xaxis_title="Longitud L (in)", yaxis_title="Profundidad d/t (%)")
        st.plotly_chart(fig_mat, use_container_width=True)

# ------------------------------------------
# MODULO 3: CARGA MASIVA ILI
# ------------------------------------------
with tab_ili:
    st.subheader("Procesamiento en Lote de Inspecciones (Smart Pig)")
    uploaded_file = st.file_uploader("Cargar archivo Excel/CSV de Inspección", type=["csv", "xlsx"])
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        st.write("Vista previa de datos cargados:", df.head())
        
        if all(col in df.columns for col in ['d_in', 'L_in']):
            p_seguras = []
            estados = []
            for _, row in df.iterrows():
                res = evaluar_asme_b31g_modificado(D, t, SMYS, P_diseno, row['d_in'], row['L_in'], FS)
                p_seguras.append(res['presion_segura'])
                estados.append(res['estado'])
                
            df['P_Segura_psi'] = p_seguras
            df['Estado'] = estados
            
            st.success("Análisis masivo completado.")
            st.dataframe(df)
            
            criticos = len(df[df['Estado'].str.contains("CRÍTICO|NO SEGURO")])
            st.metric("Total Defectos Críticos / No Seguros", criticos)
        else:
            st.error("El archivo debe contener las columnas 'd_in' (profundidad) y 'L_in' (longitud).")

# ------------------------------------------
# MODULO 4: VIDA ÚTIL REMANENTE (RLA)
# ------------------------------------------
with tab_rla:
    st.subheader("Proyección Temporizada de Crecimiento de Corrosión")
    
    tasa_corrosion = st.number_input("Tasa de Crecimiento Anual - (mpy / mils por año)", 1.0, 50.0, 10.0, 0.5)
    tasa_in = tasa_corrosion / 1000.0
    
    años_proyeccion = st.slider("Años a proyectar", 1, 30, 10)
    
    linea_tiempo = np.arange(0, años_proyeccion + 1)
    profundidades = [d + (tasa_in * año) for año in linea_tiempo]
    p_admisibles = [evaluar_asme_b31g_modificado(D, t, SMYS, P_diseno, p, L, FS)['presion_segura'] for p in profundidades]
    
    fig_rla = go.Figure()
    fig_rla.add_trace(go.Scatter(x=linea_tiempo, y=p_admisibles, mode='lines+markers', name='P. Segura Admisible'))
    fig_rla.add_trace(go.Scatter(x=linea_tiempo, y=[P_diseno] * len(linea_tiempo), mode='lines', name='Presión de Operación', line=dict(color='red', dash='dash')))
    fig_rla.update_layout(title="Degradación de Presión Segura en el Tiempo", xaxis_title="Años Transcurridos", yaxis_title="Presión (psi)")
    
    st.plotly_chart(fig_rla, use_container_width=True)
    
    ano_falla = next((i for i, p in enumerate(p_admisibles) if p < P_diseno), None)
    if ano_falla:
        st.warning(f"⚠️ Alerta: El defecto superará la capacidad segura en aprox. **{ano_falla} años**.")
    else:
        st.success("✅ La tubería mantendrá la presión de operación dentro del periodo proyectado.")
