import streamlit as st
import plotly.graph_objects as go
from modules.calculations import calcular_espesor_nag100, determinar_clase_trazado

st.set_page_config(
    page_title="Simulador MENFA | Gasoductos NAG-100",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Simulador de Aplicación Normativa: NAG-100")
st.caption("MENFA - Capacitación Técnica e Inspección de Gasoductos")

st.sidebar.title("Navegación")
modulo = st.sidebar.selectbox("Módulo", ["1. Cálculo de Diseño", "2. Inspección de Campo"])

if "1. Cálculo" in modulo:
    st.subheader("📐 Cálculo de Espesor Requerido (Fórmula Barlow / NAG-100)")
    
    col1, col2 = st.columns(2)
    with col1:
        presion_bar = st.slider("Presión de Diseño (bar)", 10, 120, 75, 5)
        dn_inch = st.selectbox("Diámetro Nominal (pulgadas)", [4, 6, 8, 10, 12, 16, 20, 24, 30, 36])
        d_ext_mm = dn_inch * 25.4
        viviendas = st.number_input("Viviendas en Unidad de Trazado (1600m x 200m)", value=5, min_value=0)
        clase, factor_f = determinar_clase_trazado(viviendas)
        st.info(f"**Clase de Trazado:** {clase} (Factor F = {factor_f})")

    with col2:
        grado_acero = st.selectbox("Grado API 5L", ["Grado B (241 MPa)", "X42 (290 MPa)", "X52 (360 MPa)", "X60 (415 MPa)", "X70 (485 MPa)"])
        smys_dict = {"Grado B (241 MPa)": 241, "X42 (290 MPa)": 290, "X52 (360 MPa)": 360, "X60 (415 MPa)": 415, "X70 (485 MPa)": 485}
        smys_val = smys_dict[grado_acero]
        factor_e = st.selectbox("Factor de Junta (E)", [1.00, 0.85, 0.60])
        factor_t = st.selectbox("Factor Temp. (T)", [1.00, 0.937, 0.867])

    espesor_req = calcular_espesor_nag100(presion_bar, d_ext_mm, smys_val, factor_f, factor_e, factor_t)
    
    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Diámetro Exterior", f"{d_ext_mm:.1f} mm")
    m2.metric("Espesor Requerido NAG-100", f"{espesor_req} mm")
    m3.metric("Tensión Admisible", f"{smys_val * factor_f:.1f} MPa")

elif "2. Inspección" in modulo:
    st.subheader("🔍 Inspección de Campo - Detección de Hallazgos")
    st.warning("📋 Caso #101: Tapada en Zanja - Cruce de Ruta Provincial (Clase 3)")
    st.write("Profundidad medida: **0.80 m** | Revestimiento: Tricapa Polietileno.")
    
    dictamen = st.radio("¿Cumple con la NAG-100?", ["Conforme", "No Conforme - Tapada Insuficiente"])
    if st.button("Validar Dictamen"):
        if dictamen == "No Conforme - Tapada Insuficiente":
            st.success("¡Correcto! La NAG-100 exige un mínimo de 1.20 m de profundidad en cruces de carreteras para Clase 3 sin encamisado.")
        else:
            st.error("Incorrecto. 0.80 m no cumple el requerimiento reglamentario.")
