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

# ---------------------------------------------------------
# MÓDULO 5: EXAMEN DE EVALUACIÓN
# ---------------------------------------------------------
elif "5. Examen" in modulo:
    st.subheader("📝 Módulo de Evaluación Técnica")
    
    if not preguntas_db:
        st.warning("⚠️ No se encontró la base de datos `data/preguntas.json` o está vacía.")
    else:
        # Datos del Estudiante / Inspector
        with st.expander("👤 Datos del Postulante", expanded=True):
            col_u1, col_u2 = st.columns(2)
            nombre_usr = col_u1.text_input("Nombre Completo:", placeholder="Ej: Juan Pérez")
            dni_usr = col_u2.text_input("DNI / Legajo:", placeholder="Ej: 35123456")

        niveles_disponibles = sorted(list({q.get("nivel", "Todos") for q in preguntas_db if q.get("nivel")}))
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            nivel_seleccionado = st.multiselect(
                "Filtrar por Perfil / Nivel Técnico:",
                options=niveles_disponibles,
                default=niveles_disponibles,
                help="Selecciona uno o más niveles para personalizar tu examen."
            )
        
        if nivel_seleccionado:
            preguntas_filtradas = [q for q in preguntas_db if q.get("nivel") in nivel_seleccionado]
        else:
            preguntas_filtradas = preguntas_db

        with col_f2:
            st.metric("Total de Preguntas en Examen", len(preguntas_filtradas))

        st.divider()

        if not preguntas_filtradas:
            st.info("No hay preguntas disponibles para el filtro de nivel seleccionado.")
        else:
            respuestas_usuario = {}
            with st.form("form_examen_filtrado"):
                for idx, q in enumerate(preguntas_filtradas):
                    st.markdown(f"**Pregunta {idx+1}:** {q.get('pregunta', '')}")
                    st.caption(f"📌 Módulo: **{q.get('modulo', 'General')}** | Nivel: **{q.get('nivel', 'N/A')}**")
                    
                    respuestas_usuario[idx] = st.radio(
                        "Selecciona una opción:",
                        q.get("opciones", []),
                        key=f"q_filt_{q.get('id', idx)}"
                    )
                    st.divider()
                
                submit = st.form_submit_button("Enviar Respuestas")
            
            if submit:
                if not nombre_usr or not dni_usr:
                    st.warning("⚠️ Por favor ingrese su Nombre y DNI/Legajo antes de enviar la evaluación.")
                else:
                    correctas = 0
                    for idx, q in enumerate(preguntas_filtradas):
                        resp_usr = respuestas_usuario[idx]
                        resp_cor = q.get("respuesta_correcta")
                        
                        if resp_usr == resp_cor:
                            correctas += 1
                            st.success(f"**P{idx+1} Correcta:** {q.get('explicacion', '')}")
                        else:
                            st.error(f"**P{idx+1} Incorrecta:** Seleccionaste '{resp_usr}'. La respuesta correcta es '{resp_cor}'.")
                            if q.get('explicacion'):
                                st.info(f"💡 *Fundamento:* {q.get('explicacion')}")
                    
                    total_q = len(preguntas_filtradas)
                    score = (correctas / total_q) * 100 if total_q > 0 else 0
                    
                    st.divider()
                    st.metric("Puntaje Obtenido", f"{score:.0f} / 100", f"{correctas} de {total_q} correctas")
                    
                    if score >= 70:
                        st.balloons()
                        st.success(f"¡Aprobado! Postulante **{nombre_usr}** (DNI: {dni_usr}) cumple con el estándar de capacitación técnica MENFA.")
                    else:
                        st.error(f"No alcanzado. **{nombre_usr}**, se requiere un mínimo de 70% para aprobar.")
