"""Sondeo local de 8 sesiones independientes, 3 rondas de GET por rol. No crea ventas."""
import getpass
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from http.cookiejar import CookieJar
from pathlib import Path
from threading import Barrier
from time import perf_counter
from urllib.request import Request, build_opener, HTTPCookieProcessor, ProxyHandler
from urllib.error import HTTPError

BASE='http://127.0.0.1:5000'
PERFILES=[('cperez','Mesero','/api/salon/productos'),('pchef','Cocinero','/api/cocina/comandas'),('ccaja','Cajero','/api/caja/pendientes'),('rjefe','Administrador','/api/administracion/dashboard')]

def pedir(cliente,ruta,datos=None):
    req=Request(BASE+ruta,data=None if datos is None else json.dumps(datos).encode(),headers={'Content-Type':'application/json','Accept':'application/json'})
    try:
        with cliente.open(req,timeout=15) as resp:
            return resp.status,resp.read()
    except HTTPError as e:
        with e: return e.code,e.read()

def main():
    clientes=[]; resultados=[]
    carpeta=Path(__file__).resolve().parent/'evidencias'; carpeta.mkdir(exist_ok=True)
    ruta=carpeta/('concurrencia_3_8_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f')+'.txt')
    with ruta.open('w',encoding='utf-8') as f:
        def log(s): print(s); f.write(s+'\n'); f.flush()
        log('Sondeo HTTP local: 8 sesiones, 3 rondas, máximo esperado 2.000 s por GET.')
        log('No certifica ocho dispositivos físicos, red LAN, escrituras simultáneas ni rendimiento de producción.')
        try:
            for usuario,rol,endpoint in PERFILES:
                clave=getpass.getpass('Contraseña de '+usuario+': ')
                try:
                    for n in (1,2):
                        cliente=build_opener(ProxyHandler({}),HTTPCookieProcessor(CookieJar()))
                        codigo,raw=pedir(cliente,'/api/auth/login',{'usuario':usuario,'contrasena':clave})
                        if codigo!=200: raise RuntimeError(f'Login de {rol}: HTTP {codigo}')
                        clientes.append((rol,n,endpoint,cliente))
                        if rol not in json.loads(raw)['empleado']['roles']: raise RuntimeError('Rol inesperado')
                finally: del clave
            with ThreadPoolExecutor(max_workers=8) as pool:
                for ronda in range(1,4):
                    barrera=Barrier(8,timeout=10)
                    def consulta(item):
                        rol,n,endpoint,cliente=item
                        barrera.wait(); inicio=perf_counter()
                        try: codigo,_=pedir(cliente,endpoint)
                        except Exception: codigo=0
                        return rol,n,codigo,perf_counter()-inicio
                    for rol,n,codigo,t in pool.map(consulta,clientes):
                        resultados.append((codigo,t))
                        log(f'Ronda {ronda} | {rol} {n} | HTTP {codigo} | {t:.3f} s')
            ok=all(c==200 and t<=2 for c,t in resultados) and len(resultados)==24
            log(f'Máximo: {max(t for _,t in resultados):.3f} s | Solicitudes: {len(resultados)}')
            log('RESULTADO SONDEO LOCAL: '+('APROBADO' if ok else 'NO CUMPLE'))
            return 0 if ok else 1
        except Exception as e:
            log('DETENIDO: '+type(e).__name__+'; revisa conexión, credenciales y servidor.')
            return 1
        finally:
            for _,_,_,cliente in clientes:
                try: pedir(cliente,'/api/auth/logout',{})
                except Exception: pass
            log('Evidencia: '+ruta.name)
if __name__=='__main__': raise SystemExit(main())
