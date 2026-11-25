"""L&D 3.8: preflight y regresión. No ejecuta ventas ni migraciones."""
import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODULOS = ['test_permisos','test_salon','test_pedidos','test_comandas',
           'test_facturacion','test_inventario','test_reportes','test_integracion_utilidades',
           'test_interfaz','test_salon_ui','test_cocina_ui','test_caja_ui',
           'test_inventario_ui','test_dashboard_ui','test_gestion','test_exportaciones','test_gestion_ui']
ARCHIVOS = ['app.py','.env','backend/db.py','static/vendor/bootstrap.min.css']
ARCHIVOS += ['backend/'+p+'.py' for p in ('auth','permisos','salon','catalogo','pedidos','cocina','comandas','caja','facturacion','administracion','inventario','reportes','interfaz','gestion','exportaciones')]
ARCHIVOS += ['templates/'+p+'.html' for p in ('base','marca','login','error_ui','panel','salon','cocina','caja','inventario','dashboard','gestion')]
ARCHIVOS += ['static/css/'+p+'.css' for p in ('ld','salon','cocina','caja','inventario','dashboard','gestion')]
ARCHIVOS += ['static/js/'+p+'.js' for p in ('interfaz','salon','cocina','caja','inventario','dashboard','gestion')]
ARCHIVOS += [p+'.py' for p in MODULOS]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--solo-archivos',action='store_true')
    args=parser.parse_args()
    carpeta=ROOT/'evidencias'; carpeta.mkdir(exist_ok=True)
    ruta=carpeta/('regresion_3_8_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f')+'.txt')
    with ruta.open('w',encoding='utf-8') as log:
        def escribir(s):
            print(s); log.write(s+'\n'); log.flush()
        faltantes=[p for p in ARCHIVOS if not (ROOT/p).is_file()]
        escribir('L&D | Etapa 3.8 | '+datetime.now().isoformat(timespec='seconds'))
        escribir(f'Archivos comprobados: {len(ARCHIVOS)-len(faltantes)}/{len(ARCHIVOS)}')
        if faltantes:
            for p in faltantes: escribir('FALTA: '+p)
            escribir('DETENIDO: recupera archivos de su etapa, sin reemplazar panel.html por una versión anterior.')
            return 1
        if args.solo_archivos:
            escribir('Archivos presentes. No se ejecutaron pruebas.'); return 0
        escribir('Ejecutando módulos de pruebas acumuladas; no ejecuta prueba_integracion.py ni test_conexion.py.')
        proceso=subprocess.Popen([sys.executable,'-X','utf8','-m','unittest','-v',*MODULOS],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
        for linea in proceso.stdout:
            escribir(linea.rstrip('\n'))
        codigo=proceso.wait()
        escribir('RESULTADO REGRESION: '+('APROBADO' if codigo==0 else 'REVISAR FALLOS'))
        escribir('Evidencia: '+ruta.name)
        return codigo
if __name__=='__main__': sys.exit(main())
