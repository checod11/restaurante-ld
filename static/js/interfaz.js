'use strict';
const body = document.body;
const mensaje = document.querySelector('#mensaje');
function aviso(texto) { if (mensaje) { mensaje.textContent = texto; mensaje.hidden = false; } }
async function api(ruta, datos) {
  const opciones = {credentials: 'same-origin', cache: 'no-store', headers: {'Accept': 'application/json'}};
  if (datos !== undefined) { opciones.method = 'POST'; opciones.headers['Content-Type'] = 'application/json'; opciones.body = JSON.stringify(datos); }
  const respuesta = await fetch(ruta, opciones);
  const json = await respuesta.json().catch(() => ({}));
  return {respuesta, json};
}
const form = document.querySelector('#login-form');
if (form) {
  const clave = document.querySelector('#contrasena');
  const ver = document.querySelector('#ver-clave');
  const ingresar = document.querySelector('#ingresar');
  ver.addEventListener('click', () => {
    const visible = clave.type === 'password'; clave.type = visible ? 'text' : 'password';
    ver.textContent = visible ? 'Ocultar' : 'Mostrar'; ver.setAttribute('aria-pressed', String(visible));
  });
  form.addEventListener('submit', async (evento) => {
    evento.preventDefault(); mensaje.hidden = true; ingresar.disabled = true; ingresar.textContent = 'Validando…';
    try {
      const {respuesta, json} = await api('/api/auth/login', {usuario: document.querySelector('#usuario').value.trim(), contrasena: clave.value});
      if (respuesta.ok && json.empleado) { clave.value = ''; location.replace(body.dataset.panel); return; }
      aviso(respuesta.status === 401 ? 'Usuario o contraseña incorrectos, o cuenta no habilitada.' : respuesta.status === 403 ? 'Tu cuenta no tiene roles asignados. Contacta al administrador.' : respuesta.status >= 500 ? 'El servicio no está disponible. Inténtalo nuevamente.' : 'Revisa los datos ingresados.');
    } catch { aviso('No se pudo conectar con el servidor. Comprueba que Flask esté ejecutándose.'); }
    finally { ingresar.disabled = false; ingresar.textContent = 'Ingresar →'; }
  });
}
const salir = document.querySelector('#cerrar-sesion');
if (salir) salir.addEventListener('click', async () => {
  salir.disabled = true;
  try { const {respuesta} = await api('/api/auth/logout', {}); if (respuesta.ok || respuesta.status === 401) { location.replace(body.dataset.login); return; } aviso('No se pudo cerrar la sesión. Inténtalo nuevamente.'); }
  catch { aviso('Sin conexión. No se ha confirmado el cierre de sesión.'); }
  finally { salir.disabled = false; }
});
// Evita mostrar una página protegida restaurada desde la memoria del navegador.
window.addEventListener('pageshow', e => { if (e.persisted && body.dataset.pagina === 'panel') location.reload(); });
