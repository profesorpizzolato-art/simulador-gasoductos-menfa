import io
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime

def generar_certificado_pdf(nombre_alumno, dni_legajo, nivel_evaluado, puntaje):
    buffer = io.BytesIO()
    
    # Documento horizontal
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=40, leftMargin=40,
        topMargin=40, bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    title_style = ParagraphStyle(
        'CertTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=26,
        leading=32,
        textColor=colors.HexColor('#1E3A8A'),
        alignment=1
    )
    
    subtitle_style = ParagraphStyle(
        'CertSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#4B5563'),
        alignment=1
    )
    
    name_style = ParagraphStyle(
        'CertName',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=28,
        textColor=colors.HexColor('#0F172A'),
        alignment=1
    )
    
    body_style = ParagraphStyle(
        'CertBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#334155'),
        alignment=1
    )

    story = []
    
    # Encabezado institucional
    story.append(Paragraph("<b>INSTITUTO IPCL MENFA</b>", title_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Capacitación Técnica en Gasoductos & Normativa ENARGAS", subtitle_style))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Otorgan el presente", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>CERTIFICADO DE APROBACIÓN</b>", title_style))
    story.append(Spacer(1, 20))
    
    # Nombre del Alumno
    story.append(Paragraph(f"<b>{nombre_alumno.upper()}</b>", name_style))
    if dni_legajo:
        story.append(Paragraph(f"DNI / Legajo: {dni_legajo}", body_style))
    story.append(Spacer(1, 15))
    
    # Detalles del Curso
    texto_certificado = (
        f"Ha completado y aprobado satisfactoriamente la Evaluación Técnica Normativa "
        f"<b>NAG-100 & NAG-124</b> para el nivel <b>{nivel_evaluado}</b>, "
        f"obteniendo una calificación de <b>{puntaje:.0f}%</b>."
    )
    story.append(Paragraph(texto_certificado, body_style))
    story.append(Spacer(1, 30))
    
    # Metadata y Firma
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    data_tabla = [
        [
            Paragraph(f"<b>Fecha de Emisión:</b> {fecha_actual}", body_style),
            Paragraph("______________________________<br><b>Fabricio Pizzolato</b><br>Instructor Técnico - MENFA", body_style)
        ]
    ]
    
    t = Table(data_tabla, colWidths=[350, 350])
    t.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t)
    
    doc.build(story)
    buffer.seek(0)
    return buffer
  
