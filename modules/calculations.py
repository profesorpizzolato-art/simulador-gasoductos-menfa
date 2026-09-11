import numpy as np

def calcular_espesor_nag100(p_diseno_bar, d_ext_mm, smys_mpa, factor_f, factor_e=1.0, factor_t=1.0):
    """
    Calcula el espesor mínimo requerido de pared (mm) según la NAG-100 (Barlow).
    """
    p_mpa = p_diseno_bar / 10.0
    s_adm_mpa = smys_mpa * factor_f * factor_e * factor_t
    
    if s_adm_mpa <= 0:
        return 0.0
        
    t_requerido_mm = (p_mpa * d_ext_mm) / (2 * s_adm_mpa)
    return round(t_requerido_mm, 2)

def determinar_clase_trazado(viviendas_zona_influencia):
    """
    Determina la Clase de Trazado según densidad de edificaciones (1600m x 200m).
    """
    if viviendas_zona_influencia <= 10:
        return 1, 0.72
    elif 11 <= viviendas_zona_influencia < 46:
        return 2, 0.60
    elif viviendas_zona_influencia >= 46:
        return 3, 0.50
    return 4, 0.40
