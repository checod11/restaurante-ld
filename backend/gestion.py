"""Administración de catálogos con el mismo bloqueo transaccional del MVP."""
import re
from decimal import Decimal
from backend.pedidos import ErrorPedido, bloquear_restaurante, entero_positivo, MAX_INT

ROLES=('Mesero','Cocinero','Cajero','Administrador')

def texto(d,k,n):
    v=d.get(k)
    if not isinstance(v,str) or not 1<=len(v.strip())<=n: raise ErrorPedido(f'{k}: texto obligatorio de hasta {n} caracteres.')
    return v.strip()

def cantidad(d,k,positivo=False):
    v=d.get(k)
    if type(v) not in (int,str) or not re.fullmatch(r'[0-9]{1,8}(?:\.[0-9]{1,2})?',str(v)): raise ErrorPedido(f'{k}: usa hasta 8 enteros y 2 decimales con punto.')
    v=Decimal(str(v))
    if positivo and v<=0: raise ErrorPedido(f'{k} debe ser mayor que cero.')
    return v

def id_val(v):
    if not entero_positivo(v): raise ErrorPedido('Identificador inválido.')
    return v

def campos(d,obligatorios,opcionales=()):
    if not isinstance(d,dict) or not set(obligatorios)<=set(d) or set(d)-set(obligatorios)-set(opcionales): raise ErrorPedido('Campos de solicitud inválidos.')

def roles_validos(v):
    if not isinstance(v,list) or not v or any(not isinstance(x,str) or x not in ROLES for x in v) or len(set(v))!=len(v): raise ErrorPedido('Selecciona roles válidos sin repetir.')
    return v

def clave(d):
    v=d.get('contrasena')
    if not isinstance(v,str) or not 12<=len(v)<=128 or not v.strip(): raise ErrorPedido('Contraseña de 12 a 128 caracteres.')
    from werkzeug.security import generate_password_hash
    return generate_password_hash(v,method='scrypt')

def filas(c,sql,p):
    c.execute(sql,p); return c.fetchall()

def catalogos(conexion,nit):
    with conexion.cursor() as c:
        p=filas(c,'SELECT num_serial,nombre,precio,categoria_plato,disponibilidad FROM Producto WHERE NIT_restaurante=%s ORDER BY nombre',(nit,))
        i=filas(c,'SELECT id_insumo,nombre,unidad_medida,cantidad_minima,cantidad_disponible FROM Insumo WHERE NIT_restaurante=%s ORDER BY nombre',(nit,))
        r=filas(c,'SELECT num_serial_producto,id_insumo,cantidad FROM Receta WHERE NIT_restaurante=%s ORDER BY num_serial_producto,id_insumo',(nit,))
        e=filas(c,'SELECT id_empleado,nombre_empleado,usuario_software,activo FROM Empleado WHERE NIT_restaurante=%s ORDER BY nombre_empleado',(nit,))
        for x in e:x['roles']=[]
        mapa={x['id_empleado']:x for x in e}
        for rol in ROLES:
            for x in filas(c,f'SELECT id_empleado FROM {rol} WHERE NIT_restaurante=%s',(nit,)):
                if x['id_empleado'] in mapa:mapa[x['id_empleado']]['roles'].append(rol)
    return {'productos':p,'insumos':i,'recetas':r,'empleados':e}

def existe(c,tabla,campo,nit,id_):
    c.execute(f'SELECT {campo} FROM {tabla} WHERE NIT_restaurante=%s AND {campo}=%s FOR UPDATE',(nit,id_))
    if not c.fetchone():raise ErrorPedido('Registro no encontrado.',404)

def nuevo_id(c,tabla,campo,nit):
    c.execute(f'SELECT COALESCE(MAX({campo}),0) AS ultimo FROM {tabla} WHERE NIT_restaurante=%s',(nit,))
    n=int(c.fetchone()['ultimo'])+1
    if n>MAX_INT:raise ErrorPedido('Numeración agotada.',409)
    return n

def abierto(c,nit,cond,param):
    c.execute('''SELECT p.num_pedido FROM Pedido p WHERE p.NIT_restaurante=%s AND p.estado_pedido NOT IN ('Cerrado','Cancelado') AND NOT EXISTS (SELECT 1 FROM Factura f WHERE f.NIT_restaurante=p.NIT_restaurante AND f.num_pedido=p.num_pedido) AND '''+cond+' LIMIT 1',(nit,param))
    return bool(c.fetchone())

def guardar(conexion,nit,actor,accion,d):
    # Validar identidad y todas las escrituras dentro del mutex compartido.
    try:
        conexion.begin()
        with conexion.cursor() as c:
            bloquear_restaurante(c,nit)
            c.execute('SELECT e.id_empleado FROM Empleado e JOIN Administrador a ON a.id_empleado=e.id_empleado AND a.NIT_restaurante=e.NIT_restaurante WHERE e.NIT_restaurante=%s AND e.id_empleado=%s AND e.activo=1 FOR UPDATE',(nit,actor))
            if not c.fetchone():raise ErrorPedido('Administrador no habilitado.',403)
            if accion=='producto':
                campos(d,('nombre','precio','categoria_plato','disponibilidad'),('num_serial',))
                n=texto(d,'nombre',100); p=cantidad(d,'precio',True); cat=texto(d,'categoria_plato',50); disp=d['disponibilidad']
                if disp not in ('Disponible','No Disponible'):raise ErrorPedido('Disponibilidad inválida.')
                if 'num_serial' in d:
                    id_=id_val(d['num_serial']); existe(c,'Producto','num_serial',nit,id_)
                    c.execute('UPDATE Producto SET nombre=%s,precio=%s,categoria_plato=%s,disponibilidad=%s WHERE NIT_restaurante=%s AND num_serial=%s',(n,p,cat,disp,nit,id_))
                else:
                    id_=nuevo_id(c,'Producto','num_serial',nit)
                    c.execute('INSERT INTO Producto (num_serial,NIT_restaurante,nombre,precio,categoria_plato,disponibilidad) VALUES (%s,%s,%s,%s,%s,%s)',(id_,nit,n,p,cat,disp))
            elif accion=='insumo':
                campos(d,('nombre','unidad_medida','cantidad_minima'))
                n=texto(d,'nombre',100); u=texto(d,'unidad_medida',20); m=cantidad(d,'cantidad_minima'); id_=nuevo_id(c,'Insumo','id_insumo',nit)
                c.execute('INSERT INTO Insumo (id_insumo,NIT_restaurante,nombre,unidad_medida,cantidad_disponible,cantidad_minima) VALUES (%s,%s,%s,%s,0,%s)',(id_,nit,n,u,m))
            elif accion=='minimo':
                campos(d,('id_insumo','cantidad_minima')); id_=id_val(d['id_insumo']); m=cantidad(d,'cantidad_minima'); existe(c,'Insumo','id_insumo',nit,id_)
                c.execute('UPDATE Insumo SET cantidad_minima=%s WHERE NIT_restaurante=%s AND id_insumo=%s',(m,nit,id_))
            elif accion=='receta':
                campos(d,('num_serial','ingredientes')); id_=id_val(d['num_serial']); existe(c,'Producto','num_serial',nit,id_)
                items=d['ingredientes']
                if not isinstance(items,list) or len(items)>100:raise ErrorPedido('Máximo 100 ingredientes.')
                vistos=set(); valores=[]
                for x in items:
                    campos(x,('id_insumo','cantidad')); i=id_val(x['id_insumo']); q=cantidad(x,'cantidad',True)
                    if i in vistos:raise ErrorPedido('Ingrediente repetido.')
                    vistos.add(i); existe(c,'Insumo','id_insumo',nit,i); valores.append((id_,i,nit,q))
                if abierto(c,nit,'EXISTS (SELECT 1 FROM Detalle_Pedido d WHERE d.NIT_restaurante=p.NIT_restaurante AND d.num_pedido=p.num_pedido AND d.num_serial_producto=%s)',id_):raise ErrorPedido('El plato tiene pedidos abiertos. Cierra sus pedidos antes de modificar la receta.',409)
                c.execute('DELETE FROM Receta WHERE NIT_restaurante=%s AND num_serial_producto=%s',(nit,id_))
                if valores:c.executemany('INSERT INTO Receta (num_serial_producto,id_insumo,NIT_restaurante,cantidad) VALUES (%s,%s,%s,%s)',valores)
            elif accion=='empleado':
                campos(d,('nombre_empleado','cedula','usuario_software','contrasena','roles'))
                n=texto(d,'nombre_empleado',100); ced=texto(d,'cedula',20); user=texto(d,'usuario_software',50); rs=roles_validos(d['roles']); h=clave(d)
                c.execute('SELECT id_empleado FROM Empleado WHERE NIT_restaurante=%s AND usuario_software=%s LIMIT 1',(nit,user))
                if c.fetchone():raise ErrorPedido('Usuario ya registrado.',409)
                id_=nuevo_id(c,'Empleado','id_empleado',nit)
                c.execute('INSERT INTO Empleado (id_empleado,NIT_restaurante,nombre_empleado,cedula,usuario_software,`contraseña_software`,fecha_antiguedad,activo) VALUES (%s,%s,%s,%s,%s,%s,CURDATE(),1)',(id_,nit,n,ced,user,h))
                for rol in rs:c.execute(f'INSERT INTO {rol} (id_empleado,NIT_restaurante) VALUES (%s,%s)',(id_,nit))
            elif accion in ('estado-empleado','clave-empleado','roles-empleado'):
                campo={'estado-empleado':'activo','clave-empleado':'contrasena','roles-empleado':'roles'}[accion]
                campos(d,('id_empleado',campo)); id_=id_val(d['id_empleado']); existe(c,'Empleado','id_empleado',nit,id_)
                if accion=='estado-empleado':
                    if type(d[campo]) is not bool:raise ErrorPedido('Estado inválido.')
                    if not d[campo]:
                        if id_==actor:raise ErrorPedido('No puedes desactivar tu propia cuenta.',409)
                        if abierto(c,nit,'p.id_mesero=%s',id_) or abierto(c,nit,'p.id_cocinero=%s',id_):raise ErrorPedido('El empleado tiene pedidos abiertos.',409)
                    c.execute('UPDATE Empleado SET activo=%s WHERE NIT_restaurante=%s AND id_empleado=%s',(d[campo],nit,id_))
                elif accion=='clave-empleado':
                    h=clave(d); c.execute('UPDATE Empleado SET `contraseña_software`=%s WHERE NIT_restaurante=%s AND id_empleado=%s',(h,nit,id_))
                else:
                    deseados=set(roles_validos(d[campo]))
                    if id_==actor and 'Administrador' not in deseados:raise ErrorPedido('No puedes retirar tu propio rol de Administrador.',409)
                    referencias={'Mesero':('Pedido','id_mesero'),'Cocinero':('Pedido','id_cocinero'),'Cajero':('Factura','id_cajero')}
                    for rol in ROLES:
                        c.execute(f'SELECT id_empleado FROM {rol} WHERE NIT_restaurante=%s AND id_empleado=%s',(nit,id_))
                        tiene=bool(c.fetchone())
                        if rol in deseados and not tiene:c.execute(f'INSERT INTO {rol} (id_empleado,NIT_restaurante) VALUES (%s,%s)',(id_,nit))
                        elif tiene and rol not in deseados:
                            if rol in referencias:
                                tabla,campo_ref=referencias[rol]
                                c.execute(f'SELECT {campo_ref} FROM {tabla} WHERE NIT_restaurante=%s AND {campo_ref}=%s LIMIT 1',(nit,id_))
                                if c.fetchone():raise ErrorPedido(f'El rol {rol} tiene historial asociado. Conserva el rol o desactiva la cuenta.',409)
                            c.execute(f'DELETE FROM {rol} WHERE NIT_restaurante=%s AND id_empleado=%s',(nit,id_))
            else:raise ErrorPedido('Operación no válida.',404)
        conexion.commit(); return {'id':id_,'mensaje':'Registro guardado.'}
    except Exception as e:
        conexion.rollback()
        if getattr(e,'args',()) and e.args[0]==1062:raise ErrorPedido('Registro duplicado (cédula u otro identificador).',409) from None
        raise
