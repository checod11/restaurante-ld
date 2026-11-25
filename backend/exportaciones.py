"""Exportaciones reales en memoria; conserva cifras y datos desconocidos."""
from io import BytesIO
from decimal import Decimal
from xml.sax.saxutils import escape
from backend import reportes

TIPOS={'ventas':('Ventas por período',reportes.ventas),'productos':('Platos más vendidos',reportes.productos),'consumo':('Consumo de insumos',reportes.consumo),'cierre-caja':('Cierre de caja',reportes.cierre_caja)}

def modelo(tipo,j):
    if tipo=='ventas':
        resumen=j['resumen']; k=[('Ventas (COP)',Decimal(resumen['ventas_totales'])),('Facturas',resumen['facturas']),('Ticket promedio (COP)',Decimal(resumen['ticket_promedio'])),('Subtotal (COP)',Decimal(resumen['subtotal']))]; h=['Fecha','Facturas','Subtotal (COP)','Total (COP)']; r=[[x['fecha'],x['facturas'],Decimal(x['subtotal']),Decimal(x['total'])] for x in j['serie_diaria']]
    elif tipo=='productos':
        k=[('Unidades vendidas',j['total_unidades'])]; h=['Código','Producto','Categoría','Unidades','Importe conocido (COP)','Unidades sin precio']; r=[[x['num_serial'],x['nombre'],x['categoria_plato'],x['unidades'],None if x['importe_conocido'] is None else Decimal(x['importe_conocido']),x['unidades_sin_precio']] for x in j['productos']]
    elif tipo=='consumo':
        k=[('Facturas sin movimientos',j['facturas_sin_movimientos'])]; h=['Código','Insumo','Unidad','Consumo','Movimientos']; r=[[x['id_insumo'],x['nombre'],x['unidad_medida'],Decimal(x['cantidad_consumida']),x['movimientos']] for x in j['insumos']]
    else:
        k=[('Ventas (COP)',Decimal(j['total'])),('Facturas',j['facturas'])]+[(x['metodo_pago']+' (COP)',Decimal(x['total'])) for x in j['por_metodo']]; h=['Cajero','Método','Facturas','Total (COP)','Recibido (COP)','Cambio (COP)','Sin dato efectivo']; r=[[x['cajero'],x['metodo_pago'],x['facturas'],Decimal(x['total']),None if x['efectivo_recibido'] is None else Decimal(x['efectivo_recibido']),None if x['cambio'] is None else Decimal(x['cambio']),x['efectivo_sin_dato']] for x in j['por_cajero_metodo']]
    return TIPOS[tipo][0],j['periodo'],k,h,r,j.get('nota','')

def xlsx(tipo,j):
    import xlsxwriter
    title,p,k,h,r,note=modelo(tipo,j); out=BytesIO()
    with xlsxwriter.Workbook(out,{'in_memory':True,'strings_to_formulas':False,'strings_to_urls':False}) as w:
        s=w.add_worksheet('Detalle'); a=w.add_worksheet('Resumen')
        head=w.add_format({'bold':True,'bg_color':'#234439','font_color':'white','text_wrap':True,'valign':'vcenter'}); num=w.add_format({'num_format':'#,##0.00'}); wrap=w.add_format({'text_wrap':True,'valign':'top'}); big=w.add_format({'bold':True,'font_size':16,'font_color':'#234439'})
        for sh in (s,a):
            sh.write_string(0,0,title,big); sh.write_string(1,0,f"Período: {p['desde']} a {p['hasta']}"); sh.write_string(2,0,'Mirador Bumangués · Uso académico')
        s.set_column(0,len(h)-1,22); a.set_column(0,0,42); a.set_column(1,1,24); s.set_row(4,32)
        s.write_row(4,0,h,head); s.freeze_panes(5,0); s.autofilter(4,0,4+len(r),len(h)-1)
        def escribir(sh,i,c,v):
            if v is None:sh.write_string(i,c,'Sin datos',wrap)
            elif isinstance(v,(int,Decimal)):sh.write_number(i,c,float(v),num if isinstance(v,Decimal) else None)
            else:sh.write_string(i,c,str(v),wrap)
        for i,row in enumerate(r,5):
            for c,v in enumerate(row):escribir(s,i,c,v)
        if not r:s.write_string(5,0,'Sin registros para este período.')
        a.write_row(4,0,['Indicador','Valor'],head)
        for i,(key,v) in enumerate(k,5):escribir(a,i,0,key);escribir(a,i,1,v)
        if note:a.merge_range(6+len(k),0,8+len(k),1,note,wrap)
    out.seek(0); return out

def pdf(tipo,j):
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,LongTable,TableStyle
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.lib.pagesizes import A4,landscape
    title,p,k,h,r,note=modelo(tipo,j); out=BytesIO(); styles=getSampleStyleSheet(); body=ParagraphStyle('cell',fontName='Helvetica',fontSize=9,leading=12); header=ParagraphStyle('header',parent=body,fontName='Helvetica-Bold',textColor=colors.white)
    def fmt(v):
        if v is None:return 'Sin datos'
        if isinstance(v,Decimal):return f'{v:,.2f}'.replace(',','@').replace('.',',').replace('@','.')
        return str(v)
    def para(v,style=body):return Paragraph(escape(fmt(v)),style)
    story=[Paragraph('MIRADOR BUMANGUÉS · L&amp;D',styles['Heading3']),Paragraph(escape(title),styles['Title']),Paragraph(f"Período: {p['desde']} a {p['hasta']} · Uso académico",styles['Normal']),Spacer(1,12)]
    story += [para(f'{key}: {fmt(v)}') for key,v in k]+[Spacer(1,12)]
    rows=[[para(x,header) for x in h]]+[[para(v) for v in row] for row in r]
    if r:
        t=LongTable(rows,repeatRows=1,colWidths=[(landscape(A4)[0]-72)/len(h)]*len(h)); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#234439')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F1F5EF')]),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7)])); story.append(t)
    else:story.append(para('Sin registros para este período.'))
    if note:story.extend([Spacer(1,12),para(note)])
    def footer(c,doc):c.setFont('Helvetica',8);c.drawString(36,23,'Reporte administrativo · L&D');c.drawRightString(landscape(A4)[0]-36,23,f'Página {doc.page}')
    SimpleDocTemplate(out,pagesize=landscape(A4),leftMargin=36,rightMargin=36,topMargin=30,bottomMargin=36).build(story,onFirstPage=footer,onLaterPages=footer)
    out.seek(0);return out
