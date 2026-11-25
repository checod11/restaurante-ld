'use strict';
(() => {
  const root=document.getElementById('caja-app'); if(!root)return;
  const $=id=>document.getElementById('caja-'+id), base='/api/caja';
  const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
  const money=new Intl.NumberFormat('es-CO',{style:'currency',currency:'COP',minimumFractionDigits:2,maximumFractionDigits:2});
  // El importe se representa en centavos enteros: DECIMAL(12,2) cabe en Number seguro.
  function cents(v){const s=String(v??'').trim().replace(',','.');if(!/^\d{1,10}(\.\d{1,2})?$/.test(s))return null;const [a,b='']=s.split('.');return Number(a)*100+Number(b.padEnd(2,'0'));}
  const fmt=v=>cents(v)===null?'—':money.format(cents(v)/100), fmtc=v=>money.format(v/100), amount=v=>`${Math.floor(v/100)}.${String(v%100).padStart(2,'0')}`;
  const key='ld-caja-pago-pendiente-'+root.dataset.empleado;
  let orders=[],selected=null,pre=null,busy=false,loading=false,online=false,uncertain=null,last=null,receipt=null,revision=0;
  try{const v=sessionStorage.getItem(key);if(v&&/^\d+$/.test(v))uncertain=Number(v);}catch{}
  function lock(n){uncertain=n;try{if(n)sessionStorage.setItem(key,String(n));else sessionStorage.removeItem(key);}catch{}renderLock();}
  function renderLock(){ $('incertidumbre').hidden=!uncertain; $('incertidumbre-texto').textContent=uncertain?`Pedido #${uncertain}: comprueba si se creó la factura. No repitas el cobro hasta confirmar el resultado.`:''; $('verificar').disabled=busy;$('revisado').disabled=busy; updateControls();}
  function message(kind,text){$(kind).textContent=text;$(kind).hidden=!text;}
  function clearMessages(){message('error','');message('aviso','');}
  async function request(path,data){
    const opt={credentials:'same-origin',cache:'no-store',headers:{Accept:'application/json'}};
    if(data!==undefined){opt.method='POST';opt.headers['Content-Type']='application/json';opt.body=JSON.stringify(data);}
    const r=await fetch(base+path,opt);let j;try{j=await r.json();}catch{throw new Error('Respuesta no verificable del servidor.');}
    if(r.status===401){location.replace(document.body.dataset.login||'/login');}
    if(!r.ok){const e=new Error(j.error||`Error HTTP ${r.status}`);e.status=r.status;throw e;}return j;
  }
  function updateControls(){
    const total=pre?cents(pre.total):null, received=cents($('monto').value), cash=$('metodo').value==='Efectivo';
    const valid=total!==null&&received!==null&&(cash?received>=total:received===total);
    $('campos').disabled=busy||!pre||!online||!!uncertain;
    $('monto').readOnly=!cash;
    $('pagar').disabled=$('campos').disabled||!valid||!$('cliente').value.trim();
    $('cambio-label').textContent=total!==null&&received!==null&&received<total?'Faltante':'Cambio';
    $('cambio').textContent=total===null||received===null?'—':fmtc(Math.abs(received-total));
    $('cambio').parentElement.classList.toggle('cj-falta',total!==null&&received!==null&&!valid);
    $('actualizar').disabled=busy||loading;
    $('ultimo').disabled=busy||!last; $('imprimir').disabled=busy||!receipt||!!uncertain;
    $('numero').disabled=busy; $('buscar-comprobante').querySelector('button').disabled=busy;
  }
  function drawOrders(){
    const q=$('buscar').value.trim().toLowerCase();const list=$('pendientes');list.replaceChildren();$('contador').textContent=orders.length+' pendientes';
    const filtered=orders.filter(p=>!q||String(p.num_pedido).includes(q)||String(p.num_mesa).includes(q));
    if(!filtered.length)list.append(el('p',q?'Sin coincidencias.':'No hay pedidos pendientes de pago.','cj-empty'));
    for(const p of filtered){const b=el('button',undefined,'cj-order');b.type='button';b.disabled=busy||!!uncertain;b.setAttribute('aria-pressed',String(selected===Number(p.num_pedido)));b.append(el('strong',`Pedido #${p.num_pedido} · Mesa ${p.num_mesa}`),el('small',`Entregado · ${p.fecha_hora_pedido||''}`));b.onclick=()=>select(Number(p.num_pedido));list.append(b);}
  }
  function drawPre(){
    $('seleccion').textContent=pre?`#${pre.num_pedido} · Mesa ${pre.num_mesa}`:'Sin pedido';$('vacio').hidden=!!pre;$('detalle').hidden=!pre;$('productos').replaceChildren();
    if(pre){for(const p of pre.productos){const row=el('tr'),name=el('td',p.nombre);name.append(el('small',fmt(p.precio_unitario)+' / unidad'));if(p.nota_especial)name.append(el('small',p.nota_especial));row.append(name,el('td',p.cantidad),el('td',fmt(p.subtotal)));$('productos').append(row);}
    $('subtotal').textContent=fmt(pre.subtotal);$('impuesto').textContent=fmt(pre.impuesto_adicional);$('total').textContent=fmt(pre.total);}
    updateControls();
  }
  async function refresh(){if(busy||loading)return;loading=true;const rev=revision;updateControls();try{const j=await request('/pendientes');if(!Array.isArray(j.pedidos))throw Error('Listado no válido.');if(rev!==revision)return;orders=j.pedidos;online=true;$('conexion').textContent='Conectado';if(selected!==null&&!orders.some(p=>Number(p.num_pedido)===selected)){selected=null;pre=null;drawPre();}drawOrders();}catch(e){if(rev!==revision)return;online=false;$('conexion').textContent='Sin actualización';message('error',e.message+' Actualiza antes de cobrar.');}finally{loading=false;updateControls();}}
  async function select(n){if(busy||uncertain)return;clearMessages();revision++;selected=n;pre=null;busy=true;drawOrders();drawPre();try{const j=await request(`/pedidos/${n}/precuenta`);if(Number(j.num_pedido)!==n||!Array.isArray(j.productos)||cents(j.total)===null)throw Error('Precuenta no válida.');pre=j;online=true;$('cliente').value='Consumidor Final';$('metodo').value='Efectivo';$('monto').value='';}catch(e){message('error',e.message);selected=null;pre=null;}finally{busy=false;drawPre();drawOrders();}}
  function pair(dl,k,v,cls){const d=el('div',undefined,cls);d.append(el('dt',k),el('dd',v));dl.append(d);}
  function showReceipt(f){if(!f||f.es_demo!==true||!Array.isArray(f.productos)||!Number.isInteger(Number(f.num_pedido))||cents(f.total)===null)throw Error('No se pudo verificar el comprobante.');receipt=f;last=Number(f.num_pedido);$('numero').value=last;const r=$('recibo');r.replaceChildren();r.append(el('h4','Mirador Bumangués'),el('p','L&D · COMPROBANTE POS DEMO','cj-center'),el('p',`Factura interna #${f.id_factura} · Pedido #${f.num_pedido}`,'cj-center'));const info=el('dl');for(const [k,v] of [['Mesa',f.num_mesa],['Fecha',f.fecha_emision],['Cajero (ID)',f.id_cajero],['Cliente',f.nombre_cliente]])pair(info,k,v??'—');r.append(info);const items=el('ul');for(const p of f.productos){const li=el('li');li.append(el('span',`${p.cantidad} × ${p.nombre}`),el('span',fmt(p.subtotal)));items.append(li);}r.append(items);const totals=el('dl');for(const [k,v] of [['Subtotal',fmt(f.subtotal)],['Impuesto adicional demo',fmt(f.impuesto_adicional)],['TOTAL',fmt(f.total)],['Método',f.metodo_pago],['Recibido',fmt(f.monto_recibido)],['Cambio',fmt(f.cambio)]])pair(totals,k,v,k==='TOTAL'?'cj-total':'');r.append(totals,el('p','Gracias por su visita.','cj-center'),el('p','Documento académico sin validez fiscal.','cj-center'));$('recibo-panel').hidden=false;updateControls();}
  async function findReceipt(n){if(busy||!Number.isSafeInteger(n)||n<=0)return;clearMessages();busy=true;renderLock();try{const j=await request(`/pedidos/${n}/comprobante`);if(Number(j.factura?.num_pedido)!==n)throw Error('Comprobante no válido.');showReceipt(j.factura);if(uncertain===n){lock(null);selected=null;pre=null;drawPre();}message('aviso',`Comprobante del pedido #${n} recuperado. No se ha registrado otro pago.`);}catch(e){message('error',e.status===404?'No se encontró un comprobante de demostración. Si el pago fue incierto, verifica en MariaDB antes de reintentar.':e.message);}finally{busy=false;renderLock();drawOrders();await refresh();}}
  $('form').addEventListener('submit',async e=>{e.preventDefault();if(busy||uncertain||$('pagar').disabled||!pre)return;const n=selected,total=cents(pre.total),received=cents($('monto').value);if(!confirm(`¿Registrar el pago de ${fmtc(total)} del pedido #${n}? Esta operación crea una factura académica.`))return;clearMessages();busy=true;revision++;lock(n);drawOrders();try{const j=await request(`/pedidos/${n}/pagar`,{metodo_pago:$('metodo').value,monto_recibido:amount(received),nombre_cliente:$('cliente').value.trim()});if(Number(j.factura?.num_pedido)!==n)throw Error('Pago no verificable.');showReceipt(j.factura);lock(null);selected=null;pre=null;orders=orders.filter(p=>Number(p.num_pedido)!==n);message('aviso',`Pago registrado · Factura #${j.factura.id_factura}. Mesa ${j.factura.num_mesa}: ${j.factura.estado_mesa||'consulta su estado en salón'}.`);drawPre();$('recibo-panel').scrollIntoView({block:'start',behavior:'smooth'});}catch(err){if([400,403,404,409,413,415].includes(err.status)){lock(null);message('error',err.message+' Consulta el comprobante si el pedido ya fue facturado.');}else{message('error','No se pudo confirmar el resultado. Consulta el comprobante antes de repetir cualquier operación.');}}finally{busy=false;renderLock();drawOrders();await refresh();}});
  $('metodo').onchange=()=>{if(pre)$('monto').value=$('metodo').value==='Efectivo'?'':pre.total;updateControls();};$('monto').oninput=updateControls;$('cliente').oninput=updateControls;$('buscar').oninput=drawOrders;$('actualizar').onclick=()=>refresh();
  $('buscar-comprobante').onsubmit=e=>{e.preventDefault();findReceipt(Number($('numero').value));};$('ultimo').onclick=()=>findReceipt(last);$('verificar').onclick=()=>findReceipt(uncertain);
  $('revisado').onclick=()=>{if(busy||!uncertain)return;if(confirm('Confirma solo si comprobaste en MariaDB que no existe factura para este pedido y que la solicitud anterior terminó. ¿Desbloquear caja?')){lock(null);selected=null;pre=null;drawPre();drawOrders();refresh();}};
  $('imprimir').onclick=()=>{if(receipt&&!busy&&!uncertain)window.print();};
  renderLock();refresh();setInterval(()=>{if(!document.hidden)refresh();},8000);
})();
