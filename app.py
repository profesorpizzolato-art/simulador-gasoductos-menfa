import json
import streamlit as st
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(
    page_title="Simulador MENFA | Gasoductos NAG-100",
    page_icon="⚡",
    layout="wide"
)

# ---------------------------------------------------------
# TABLAS NORMATIVAS Y COMERCIALES (API 5L)
# ---------------------------------------------------------
ESPESORES_COMERCIALES_MM = [
    3.18, 4.78, 5.56, 6.35, 7.14, 7.92, 8.74, 9.53, 10.31, 
    11.13, 12.70, 14.27, 15.88, 17.48, 19.05, 20.62, 22.23
]

def obtener_espesor_comercial(t_req):
    for t_com in ESPESORES_COMERCIALES_MM:
        if t_com >= t_req:
            return t_com
    return ESPESORES_COMERCIALES_MM[-1]

# ---------------------------------------------------------
# CARGA Y NORMALIZACIÓN DE DATOS SECUNDARIOS
# ---------------------------------------------------------
@st.cache_data
def cargar_datos_normativos():
    preguntas_planas = []
    escenarios = []
    
    # 1. Carga de Preguntas
    try:
        with open("data/preguntas.json", "r", encoding="utf-8") as f_preg:
            data_preg = json.load(f_preg)
            if isinstance(data_preg, dict):
                for modulo_nombre, lista_q in data_preg.items():
                    for q in lista_q:
                        preguntas_planas.append({
                            "id": str(q.get("id", "")).strip(),
                            "modulo": modulo_nombre.replace("_", " ").title(),
                            "nivel": str(q.get("nivel", "")).strip(),
                            "pregunta": str(q.get("pregunta", "")).strip(),
                            "opciones": [str(opt).strip() for opt in q.get("opciones", [])],
                            "respuesta_correcta": str(q.get("respuesta_correcta", "")).strip().replace(",", "."),
                            "explicacion": str(q.get("explicacion", "")).strip()
                        })
            elif isinstance(data_preg, list):
                preguntas_planas = data_preg
    except FileNotFoundError:
        st.warning("⚠️ Archivo `data/preguntas.json` no localizado. Verifique el directorio del proyecto.")
    except json.JSONDecodeError as e:
        st.error(f"❌ Error de formato JSON en preguntas: {e}")
    except Exception as e:
        st.error(f"❌ Error inesperado al cargar preguntas: {e}")

    # 2. Carga de Escenarios
    try:
        with open("data/escenarios.json", "r", encoding="utf-8") as f_esc:
            escenarios = json.load(f_esc)
    except Exception:
        escenarios = []

    return preguntas_planas, escenarios

preguntas_db, escenarios_db = cargar_datos_normativos()

# ---------------------------------------------------------
# FUNCIONES DE CÁLCULO NORMATIVO (NAG-100 / NAG-124)
# ---------------------------------------------------------
def calcular_espesor_nag100(p_diseno_bar, d_ext_mm, smys_mpa, factor_f, factor_e=1.0, factor_t=1.0):
    p_mpa = p_diseno_bar / 10.0
    s_adm_mpa = smys_mpa * factor_f * factor_e * factor_t
    if s_adm_mpa <= 0:
        return 0.0
    t_requerido_mm = (p_mpa * d_ext_mm) / (2 * s_adm_mpa)
    return round(t_requerido_mm, 2)

def determinar_clase_trazado(viviendas_zona_influencia, es_edificio_alto=False):
    if es_edificio_alto:
        return 4, 0.40
    elif viviendas_zona_influencia <= 10:
        return 1, 0.72
    elif 11 <= viviendas_zona_influencia < 46:
        return 2, 0.60
    else:
        return 3, 0.50

def calcular_prueba_nag124(maop_bar, clase_trazado):
    factores = {1: 1.25, 2: 1.25, 3: 1.40, 4: 1.50}
    factor = factores.get(clase_trazado, 1.40)
    return {
        "factor": factor,
        "p_resistencia": round(maop_bar * factor, 2),
        "p_hermeticidad": round(maop_bar * 1.10, 2)
    }

def verificar_tension_hoop(p_prueba_bar, d_ext_mm, espesor_mm, smys_mpa):
    if espesor_mm <= 0:
        return 0.0, 0.0
    p_mpa = p_prueba_bar / 10.0
    tension_mpa = (p_mpa * d_ext_mm) / (2 * espesor_mm)
    pct_smys = (tension_mpa / smys_mpa) * 100
    return round(tension_mpa, 2), round(pct_smys, 1)

# ---------------------------------------------------------
# INTERFAZ PRINCIPAL Y NAVEGACIÓN
# ---------------------------------------------------------
st.title("⚡ Simulador de Aplicación Normativa: NAG-100 & NAG-124")
st.caption("MENFA - Capacitación Técnica e Inspección de Gasoductos")

st.sidebar.title("Menú Principal")
modulo = st.sidebar.selectbox(
    "Seleccionar Módulo",
    [
        "1. Cálculo de Diseño (NAG-100)",
        "2. Pruebas Hidrostáticas (NAG-124)",
        "3. Inspección de Campo",
        "4. Verificación de Tapadas (NAG-100)",
        "5. Examen de Evaluación"
    ]
)

# ---------------------------------------------------------
# MÓDULO 1: CÁLCULO DE DISEÑO
# ---------------------------------------------------------
if "1. Cálculo" in modulo:
    st.subheader("📐 Cálculo de Espesor Mínimo (Ecuación de Barlow / NAG-100)")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Parámetros de Operación y Trazado**")
        presion_bar = st.slider("Presión de Diseño (bar)", 10, 120, 75, 5)
        dn_inch = st.selectbox("Diámetro Nominal (pulgadas)", [4, 6, 8, 10, 12, 16, 20, 24, 30, 36], index=4)
        d_ext_mm = dn_inch * 25.4
        
        viviendas = st.number_input("Viviendas en Zona de Influencia (1600m x 200m)", value=5, min_value=0)
        es_edificio = st.checkbox("¿Predominan edificios de 4 o más pisos? (Clase 4)")
        
        clase, factor_f = determinar_clase_trazado(viviendas, es_edificio)
        st.info(f"**Clase de Trazado Detectada:** Clase {clase} (Factor F = {factor_f})")

    with col2:
        st.markdown("**Especificación de Materiales**")
        grado_acero = st.selectbox("Grado API 5L", ["Grado B (241 MPa)", "X42 (290 MPa)", "X52 (360 MPa)", "X60 (415 MPa)", "X70 (485 MPa)"], index=2)
        smys_dict = {"Grado B (241 MPa)": 241, "X42 (290 MPa)": 290, "X52 (360 MPa)": 360, "X60 (415 MPa)": 415, "X70 (485 MPa)": 485}
        smys_val = smys_dict[grado_acero]
        
        factor_e = st.selectbox("Factor de Junta E", [1.00, 0.85, 0.60], index=0, help="1.00 para caño longitudinal o sin costura inspeccionado")
        factor_t = st.selectbox("Factor de Temperatura T", [1.00, 0.937, 0.867], index=0, help="1.00 para T < 120 °C")

    espesor_req = calcular_espesor_nag100(presion_bar, d_ext_mm, smys_val, factor_f, factor_e, factor_t)
    espesor_com = obtener_espesor_comercial(espesor_req)
    tension_calculada = (presion_bar / 10.0 * d_ext_mm) / (2 * espesor_req) if espesor_req > 0 else 0.0
    
    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Diámetro Exterior", f"{d_ext_mm:.1f} mm")
    m2.metric("Espesor Mínimo Calculado", f"{espesor_req} mm")
    m3.metric("Espesor Comercial Recom.", f"{espesor_com} mm", f"+{round(espesor_com - espesor_req, 2)} mm")
    m4.metric("Tensión Admisible (S x F)", f"{smys_val * factor_f:.1f} MPa")

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=tension_calculada,
        title={'text': "Tensión Circunferencial Calculada (MPa)"},
        gauge={
            'axis': {'range': [0, smys_val]},
            'bar': {'color': "#1E3A8A"},
            'steps': [
                {'range': [0, smys_val * factor_f], 'color': "#D1FAE5"},
                {'range': [smys_val * factor_f, smys_val], 'color': "#FEE2E2"}
            ],
            'threshold': {'line': {'color': "red", 'width': 4}, 'value': smys_val * factor_f}
        }
    ))
    fig.update_layout(margin=dict(l=30, r=30, t=50, b=20), height=320)
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# MÓDULO 2: PRUEBAS NAG-124
# ---------------------------------------------------------
elif "2. Pruebas" in modulo:
    st.subheader("🧪 Presiones de Prueba de Resistencia y Hermeticidad (NAG-124)")
    
    c1, c2 = st.columns(2)
    with c1:
        maop = st.number_input("MAOP / Presión Máxima de Operación (bar)", value=60.0, step=5.0)
        clase_tr = st.selectbox("Clase de Trazado del Tramo", [1, 2, 3, 4], index=2)
        dn = st.selectbox("Diámetro Nominal (pulgadas)", [6, 8, 10, 12, 16, 20, 24], index=3)
        d_ext = dn * 25.4

    with c2:
        espesor = st.number_input("Espesor Adquirido/Medido (mm)", value=7.11, step=0.1)
        smys = st.selectbox("SMYS del Acero (MPa)", [241, 290, 360, 415, 485], index=2)

    prueba = calcular_prueba_nag124(maop, clase_tr)
    p_res = prueba["p_resistencia"]
    sigma_m, pct_smys = verificar_tension_hoop(p_res, d_ext, espesor, smys)

    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Prueba Resistencia (Mínima)", f"{p_res} bar", f"Factor {prueba['factor']}x MAOP")
    m2.metric("Prueba Hermeticidad", f"{prueba['p_hermeticidad']} bar", "1.10x MAOP")
    m3.metric("Tensión Solicitada", f"{sigma_m} MPa", f"{pct_smys}% del SMYS")

    if pct_smys > 100:
        st.error("⚠️ ALERTA: La presión de prueba supera el límite elástico del material (SMYS). Riesgo de deformación plástica.")
    else:
        st.success("✅ Tensión durante la prueba dentro del rango seguro admisible.")

# ---------------------------------------------------------
# MÓDULO 3: INSPECCIÓN DE CAMPO
# ---------------------------------------------------------
elif "3. Inspección" in modulo:
    st.subheader("🔍 Auditoría de Campo y Detección de Hallazgos")
    
    st.warning("📋 Caso #101: Tapada de Zanja en Cruce de Ruta (Clase 3)")
    st.write("**Datos reportados por el inspector:**")
    st.write("- Ubicación: PK 14+200 - Cruce Ruta Provincial (Sin Camisa Protectora)")
    st.write("- Profundidad de Tapada Medida: **0.80 metros**")
    st.write("- Revestimiento: Tricapa de Polietileno")
    
    dictamen = st.radio(
        "¿El parámetro de profundidad cumple con la NAG-100?",
        ["Conforme", "No Conforme - Tapada Insuficiente (Exige min. 1.20 m)", "Requiere más datos"]
    )
    
    if st.button("Validar Dictamen"):
        if "No Conforme" in dictamen:
            st.success("¡Correcto! La NAG-100 exige un mínimo de 1.20 metros de tapada en cruces de carreteras para Clase 3 sin encamisado.")
        else:
            st.error("Incorrecto. 0.80 m no cumple el requisito reglamentario para cruces especiales.")

# ---------------------------------------------------------
# MÓDULO 4: TAPADAS MÍNIMAS DE ZANJA
# ---------------------------------------------------------
elif "4. Verificación" in modulo:
    st.subheader("🚜 Tabla de Tapadas Mínimas de Zanja (NAG-100 Sección 327)")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        tipo_ubicacion = st.selectbox(
            "Ubicación de la Instalación",
            ["Ubicación Normal (Tierra)", "Roca Consolidada", "Cruces de Carreteras / FFCC", "Cursos de Agua / Zonas Anegables"]
        )
        clase_sel = st.selectbox("Clase de Trazado", [1, 2, 3, 4], index=2)
    
    with col_t2:
        if tipo_ubicacion == "Ubicación Normal (Tierra)":
            tapada_min = 0.60 if clase_sel == 1 else 0.80
        elif tipo_ubicacion == "Roca Consolidada":
            tapada_min = 0.50 if clase_sel == 1 else 0.60
        elif tipo_ubicacion == "Cruces de Carreteras / FFCC":
            tapada_min = 1.20
        else:
            tapada_min = 1.20

        st.metric("Tapada Mínima Exigida", f"{tapada_min:.2f} m")
        tapada_real = st.number_input("Profundidad Medida en Campo (m)", value=0.90, step=0.05)
        
        if tapada_real >= tapada_min:
            st.success("✅ Profundidad conforme a la norma NAG-100.")
        else:
            st.error(f"❌ No Conforme: Se requieren al menos {tapada_min:.2f} m de tapada.")

import io
import math
import streamlit as st
import plotly.graph_objects as go

# Dependencias para la generación del reporte PDF
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ---------------------------------------------------------
# FUNCIÓN GENERADORA DEL REPORTE PDF (ASME B31G)
# ---------------------------------------------------------
def generar_pdf_asme_b31g(datos_ducto, resultados, postulante=""):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    style_title = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'],
        fontSize=18, leading=22, textColor=colors.HexColor("#1E3A8A"), alignment=1
    )
    style_subtitle = ParagraphStyle(
        'DocSubTitle', parent=styles['Normal'],
        fontSize=10, leading=12, textColor=colors.HexColor("#4B5563"), alignment=1
    )
    style_h2 = ParagraphStyle(
        'Heading2', parent=styles['Heading2'],
        fontSize=12, leading=15, textColor=colors.HexColor("#1E3A8A"), spaceBefore=10, spaceAfter=5
    )
    style_body = ParagraphStyle(
        'Body', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor("#1F2937")
    )
    style_bold = ParagraphStyle(
        'BoldBody', parent=style_body, fontName="Helvetica-Bold"
    )

    elements = []

    # 1. Encabezado institucional
    elements.append(Paragraph("<b>INSTITUTO MENFA - CAPACITACIÓN & INTEGRIDAD</b>", style_title))
    elements.append(Paragraph("Informe Técnico de Evaluación de Aptitud para el Servicio (Fitness-for-Service)", style_subtitle))
    elements.append(Paragraph("Evaluación de Pérdida de Metal por Corrosión según ASME B31G", style_subtitle))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1E3A8A"), spaceAfter=15))

    # 2. Información General / Inspector
    if postulante:
        data_inspector = [
            [Paragraph("<b>Inspector / Evaluador:</b>", style_body), Paragraph(postulante, style_body),
             Paragraph("<b>Norma Evaluativa:</b>", style_body), Paragraph("ASME B31G (Original)", style_body)]
        ]
        t_insp = Table(data_inspector, colWidths=[120, 150, 110, 140])
        t_insp.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F3F4F6")),
            ('PADDING', (0,0), (-1,-1), 6),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(t_insp)
        elements.append(Spacer(1, 12))

    # 3. Datos de la Cañería y Defecto
    elements.append(Paragraph("1. Parámetros de Entrada (Ducto y Anomalía)", style_h2))
    
    table_data = [
        [Paragraph("<b>Parámetro</b>", style_bold), Paragraph("<b>Valor</b>", style_bold), Paragraph("<b>Unidad</b>", style_bold)],
        [Paragraph("Presión Máx. Operativa (MAOP)", style_body), Paragraph(f"{datos_ducto['maop']:.2f}", style_body), Paragraph("bar", style_body)],
        [Paragraph("Diámetro Exterior ($D$)", style_body), Paragraph(f"{datos_ducto['d_ext']:.1f}", style_body), Paragraph("mm", style_body)],
        [Paragraph("Espesor Nominal ($t$)", style_body), Paragraph(f"{datos_ducto['espesor']:.2f}", style_body), Paragraph("mm", style_body)],
        [Paragraph("Profundidad de Defecto ($d$)", style_body), Paragraph(f"{datos_ducto['profundidad']:.2f}", style_body), Paragraph("mm", style_body)],
        [Paragraph("Longitud Axial Defecto ($L$)", style_body), Paragraph(f"{datos_ducto['longitud']:.1f}", style_body), Paragraph("mm", style_body)],
    ]

    t_params = Table(table_data, colWidths=[240, 140, 140])
    t_params.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E5E7EB")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(t_params)
    elements.append(Spacer(1, 12))

    # 4. Resultados de Cálculo
    elements.append(Paragraph("2. Resultados del Análisis Dimensional y Presión Remanente", style_h2))
    
    color_dictamen = colors.HexColor("#DCFCE7") if resultados["estado"] == "ACEPTABLE" else (colors.HexColor("#FEF3C7") if resultados["estado"] == "RELIQUIDEZ / DERATING" else colors.HexColor("#FEE2E2"))

    res_data = [
        [Paragraph("<b>Severidad / Profundidad (%t):</b>", style_body), Paragraph(f"{resultados['pct_prof']}%", style_bold)],
        [Paragraph("<b>Factor Geométrico (A):</b>", style_body), Paragraph(f"{resultados['A_factor']:.3f}", style_body)],
        [Paragraph("<b>Presión Remanente Segura ($P_{safe}$):</b>", style_body), Paragraph(f"<b>{resultados['p_safe_bar']:.2f} bar</b>", style_bold)],
        [Paragraph("<b>Dictamen Técnico Final:</b>", style_body), Paragraph(f"<b>{resultados['estado']}</b>", style_bold)]
    ]

    t_res = Table(res_data, colWidths=[200, 320])
    t_res.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
        ('BACKGROUND', (0,3), (-1,3), color_dictamen),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t_res)
    elements.append(Spacer(1, 12))

    # 5. Dictamen y Recomendaciones
    elements.append(Paragraph("3. Conclusión Técnica", style_h2))
    elements.append(Paragraph(f"<b>Fundamento:</b> {resultados['motivo']}", style_body))
    elements.append(Spacer(1, 20))

    # Pie institucional
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#9CA3AF"), spaceAfter=8))
    elements.append(Paragraph("Documento generado automáticamente por la Plataforma de Integridad MENFA - Norma ASME B31G.", style_subtitle))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# ---------------------------------------------------------
# INTERFAZ DE STREAMLIT (INTEGRACIÓN EN EL MÓDULO 5)
# ---------------------------------------------------------
if "5. Evaluación Corrosión" in modulo:
    st.subheader("🔬 Evaluación de Pérdida de Metal por Corrosión (ASME B31G)")
    
    with st.expander("👤 Registro del Inspector / Evaluador", expanded=False):
        nombre_inspector = st.text_input("Nombre y Apellido del Inspector:", placeholder="Ej: Ing. Fabricio Pizzolato")

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.markdown("**Parámetros de la Cañería**")
        maop_b31g = st.number_input("MAOP Operativa (bar)", value=60.0, step=1.0)
        dn_b31g = st.selectbox("Diámetro Nominal (pulgadas)", [4, 6, 8, 10, 12, 16, 20, 24, 30], index=4)
        d_ext_b31g = dn_b31g * 25.4
        t_nom_b31g = st.number_input("Espesor Nominal del Tubo (mm)", value=7.11, min_value=1.0, step=0.1)

    with col_b2:
        st.markdown("**Dimensiones de la Pérdida de Metal (Picadura)**")
        d_defecto = st.number_input("Profundidad Máxima de Corrosión d (mm)", value=2.50, min_value=0.1, max_value=t_nom_b31g, step=0.1)
        l_defecto = st.number_input("Longitud Axial del Defecto L (mm)", value=120.0, min_value=1.0, step=5.0)

    # Función de cálculo ASME B31G previamente definida
    res_b31g = evaluar_asme_b31g(maop_b31g, d_ext_b31g, t_nom_b31g, d_defecto, l_defecto)

    st.divider()
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Profundidad del Defecto", f"{res_b31g['pct_prof']}% t")
    m2.metric("Factor Geométrico A", f"{res_b31g['A_factor']}")
    m3.metric("MAOP Actual", f"{maop_b31g:.2f} bar")
    m4.metric("Presión Remanente (P_safe)", f"{res_b31g['p_safe_bar']:.2f} bar")

    # Muestreo de Estado
    if res_b31g["estado"] == "ACEPTABLE":
        st.success(f"✅ **Dictamen:** {res_b31g['motivo']}")
    elif res_b31g["estado"] == "RELIQUIDEZ / DERATING":
        st.warning(f"⚠️ **Dictamen:** {res_b31g['motivo']}")
    else:
        st.error(f"❌ **Dictamen:** {res_b31g['motivo']}")

    # Botón de Descarga del PDF Report
    dict_datos = {
        "maop": maop_b31g,
        "d_ext": d_ext_b31g,
        "espesor": t_nom_b31g,
        "profundidad": d_defecto,
        "longitud": l_defecto
    }
    
    pdf_bytes = generar_pdf_asme_b31g(dict_datos, res_b31g, nombre_inspector)

    st.download_button(
        label="📄 Descargar Informe Técnico en PDF",
        data=pdf_bytes,
        file_name=f"Informe_ASME_B31G_DN{dn_b31g}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
