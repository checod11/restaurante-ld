/* Tablero de cocina. La API sigue siendo la autoridad de estados y permisos. */
(() => {
  'use strict';
  const root = document.querySelector('#cocina-app');
  if (!root) return;
  const $ = id => document.getElementById(id);
  const estados = ['Tomado', 'Preparacion', 'Lista'];
  const empleado = root.dataset.empleado;
  const board = $('cocina-tablero');
  const botonActualizar = $('cocina-actualizar');
  const error = $('cocina-error');
  const aviso = $('cocina-aviso');
  const conexion = $('cocina-conexion');
  let ocupado = false, vigente = false, bloqueado = false, datos = null, firma = '';
  let detener = false;
  function el(tag, clase, texto) {
    const node = document.createElement(tag);
    if (clase) node.className = clase;
    if (texto !== undefined && texto !== null) node.textContent = String(texto);
    return node;
  }
  function mostrar(node, texto) { node.textContent = texto || ''; node.hidden = !texto; }
  function estadoConexion(texto, estado) { conexion.textContent = texto; conexion.dataset.state = estado; }
  function controles() {
    botonActualizar.disabled = ocupado || detener;
    board.setAttribute('aria-busy', String(ocupado));
    board.querySelectorAll('button[data-accion]').forEach(b => {b.disabled = ocupado || !vigente || bloqueado || detener;});
  }
  async function solicitud(ruta, post = false) {
    const opciones = {credentials:'same-origin', cache:'no-store', headers:{Accept:'application/json'}, signal:AbortSignal.timeout(12000)};
    if (post) { opciones.method = 'POST'; opciones.headers['Content-Type']='application/json'; opciones.body='{}'; }
    let r;
    try { r = await fetch(ruta, opciones); } catch { throw Object.assign(new Error('No hay conexión con el servidor.'), {incierto:post}); }
    if (r.status === 401) { detener=true; vigente=false; location.replace(document.body.dataset.login || '/login'); throw new Error('La sesión expiró.'); }
    let json;
    try { json = await r.json(); } catch { throw Object.assign(new Error('Respuesta del servidor no válida.'), {incierto:post}); }
    if (!r.ok) throw Object.assign(new Error(json.error || 'No se pudo completar la solicitud.'), {status:r.status, incierto:post && r.status>=500});
    return json;
  }
  function fecha(valor) {
    if (!valor) return 'No registrada';
    // MariaDB entrega hora local sin zona: mostrarla tal como fue registrada.
    return String(valor).replace('T',' ').replace(/\.\d+$/,'');
  }
  function duracion(segundos) {
    if (segundos === null || segundos === undefined || !Number.isFinite(Number(segundos)) || Number(segundos)<0) return null;
    const s = Math.floor(Number(segundos));
    return `${Math.floor(s/60)} min ${String(s%60).padStart(2,'0')} s`;
  }
  function tarjeta(p, estado) {
    const card = el('article','ck-card'); card.dataset.pedido=String(p.num_pedido);
    const top=el('div','ck-card-top'); top.append(el('h4','',`Pedido #${p.num_pedido}`),el('span','ck-mesa',`Mesa ${p.num_mesa}`)); card.append(top);
    card.append(el('p','ck-meta',`Ingreso: ${fecha(p.fecha_hora_pedido)}`),el('p','ck-meta',`Mesero: ${p.mesero || 'No registrado'}`));
    if (estado !== 'Tomado') card.append(el('p','ck-meta',`Cocinero: ${p.cocinero || 'Sin asignar'}`),el('p','ck-meta',`Inicio: ${fecha(p.fecha_inicio_preparacion)}`));
    if (estado === 'Lista') {
      card.append(el('p','ck-meta',`Lista: ${fecha(p.fecha_lista)}`));
      const d=duracion(p.duracion_preparacion_segundos); if (d) card.append(el('p','ck-meta',`Preparación: ${d}`));
    }
    const items=el('ul','ck-items');
    for (const prod of (Array.isArray(p.productos)?p.productos:[])) {
      const li=el('li','ck-item'); li.append(el('span','ck-qty',`${prod.cantidad} × `),document.createTextNode(prod.nombre || `Producto ${prod.num_serial}`));
      if (prod.nota_especial) li.append(el('div','ck-note',`⚠ Observación: ${prod.nota_especial}`));
      items.append(li);
    }
    if (!items.children.length) items.append(el('li','ck-meta','Sin productos registrados.'));
    card.append(items);
    const propio=empleado!=='' && String(p.id_cocinero)===empleado;
    if (estado === 'Lista') card.append(el('div','ck-ready','✓ Lista para retirar · esperando al mesero'));
    else if (estado === 'Preparacion' && !propio) card.append(el('div','ck-meta','Solo el cocinero asignado puede finalizar esta comanda.'));
    else if (estado === 'Tomado' && (p.id_cocinero!=null || p.fecha_inicio_preparacion || !Array.isArray(p.productos) || !p.productos.length)) card.append(el('div','ck-meta','Comanda con datos incompletos o inconsistentes.'));
    else {
      const b=el('button','ck-action',estado==='Tomado'?'Iniciar preparación':'✓ Marcar como listo'); b.type='button'; b.dataset.accion=estado==='Tomado'?'iniciar':'lista'; b.dataset.pedido=String(p.num_pedido); b.setAttribute('aria-label',`${b.textContent} pedido ${p.num_pedido}`); card.append(b);
    }
    return card;
  }
  function pintar(json) {
    if (!json.comandas || !estados.every(s=>Array.isArray(json.comandas[s]))) throw new Error('El tablero recibió datos incompletos.');
    datos=json.comandas;
    const nuevaFirma=JSON.stringify(datos);
    if (nuevaFirma!==firma) {
      for (const s of estados) {
        const lista=$( `cocina-${s}` ); lista.replaceChildren();
        $( `cocina-contador-${s}` ).textContent=String(datos[s].length);
        if (!datos[s].length) lista.append(el('p','ck-empty','No hay comandas en esta columna.'));
        else for (const p of datos[s]) lista.append(tarjeta(p,s));
      }
      firma=nuevaFirma;
    }
    vigente=true;
    estadoConexion('Conectado','ok');
    $('cocina-ultima').textContent=`Última actualización: ${new Date().toLocaleTimeString('es-CO')}`;
  }
  async function refrescar(manual=false) {
    if (ocupado || detener) return;
    ocupado=true; controles();
    try {
      pintar(await solicitud('/api/cocina/comandas'));
      if (manual) { bloqueado=false; mostrar(error,''); }
      else if (!bloqueado) mostrar(error,'');
    } catch(e) {
      vigente=false; estadoConexion('Sin datos actualizados','error');
      mostrar(error,`${e.message} Las tarjetas visibles pueden estar desactualizadas. Pulsa Actualizar.`);
    } finally { ocupado=false; controles(); }
  }
  async function cambiar(numero, accion) {
    if (ocupado || !vigente || bloqueado || detener) return;
    const estado=accion==='iniciar'?'Tomado':'Preparacion';
    const p=datos?.[estado]?.find(p=>String(p.num_pedido)===numero);
    if (!p || !/^\d+$/.test(numero) || (accion==='lista' && String(p.id_cocinero)!==empleado)) return;
    ocupado=true; controles(); mostrar(aviso,''); mostrar(error,'');
    try {
      await solicitud(`/api/cocina/comandas/${numero}/${accion}`,true);
      mostrar(aviso,accion==='iniciar'?`Preparación iniciada para el pedido #${numero}.`:`Pedido #${numero} listo. El mesero podrá consultarlo desde salón.`);
    } catch(e) {
      bloqueado=true; mostrar(error,e.incierto?`No se confirmó el cambio del pedido #${numero}. Revisa su estado y pulsa Actualizar antes de volver a actuar.`:`${e.message} Revisa el tablero y pulsa Actualizar.`);
    }
    if (!detener) {
      try { pintar(await solicitud('/api/cocina/comandas')); }
      catch(e) { vigente=false; bloqueado=true; estadoConexion('Sin datos actualizados','error'); mostrar(error,`${error.hidden?'':error.textContent+' '}${e.message} Pulsa Actualizar.`); }
    }
    ocupado=false; controles();
  }
  board.addEventListener('click',e=>{
    const b=e.target.closest('button[data-accion]');
    if (b && !b.disabled) cambiar(b.dataset.pedido,b.dataset.accion);
  });
  botonActualizar.addEventListener('click',()=>refrescar(true));
  document.addEventListener('visibilitychange',()=>{if(!document.hidden) refrescar();});
  window.addEventListener('online',()=>refrescar());
  window.addEventListener('offline',()=>{vigente=false;estadoConexion('Sin conexión','error');controles();});
  setInterval(()=>{if(!document.hidden) refrescar();},4000);
  refrescar();
})();
