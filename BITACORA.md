# Bitácora de desarrollo — Software Administrador de Restaurantes L&D

**Restaurante Mirador Bumangués · MVP académico local · versión v1.0.0**

| Información | Detalle |
|---|---|
| Desarrolladores | Larry Jimenez Bibanco y Diego Alonso Hernández |
| Equipo | L&D Company |
| Institución | Universidad Cooperativa de Colombia |
| Programa / asignatura | Ingeniería de Sistemas / Ingeniería de Software |
| Docente | Mg. Gustavo Adolfo Gómez Gómez |
| Período académico | 2026-2 |
| Fecha de consolidación | 25 de noviembre de 2026 |
| Repositorio | https://github.com/checod11/restaurante-ld |
| Versión | `v1.0.0` (publicación y Release confirmados por el equipo en el seguimiento) |

## 1. Propósito y alcance

Esta bitácora registra el paso del diseño académico del Software Administrador de Restaurantes a una demostración web funcional. Partimos del informe final de Ingeniería de Software, el manual de usuario y los scripts relacionales desarrollados en Gestión de la Información. El problema que se buscó atender fue la dispersión de información entre la toma de pedidos, la cocina, la caja y el inventario. La solución reúne estos procesos y permite al administrador consultar información consolidada sin reconstruir manualmente las operaciones.

El objetivo del desarrollo fue obtener un producto mínimo viable (MVP) ejecutable en un computador local, con una base de datos MariaDB, auditoría, interfaces por roles, pruebas y un repositorio que permita recuperar el código. No se trata de una instalación comercial certificada. El comprobante POS es académico, el registro de pagos es manual y las funcionalidades de facturación electrónica, sincronización offline y despliegue seguro de producción se mantienen como pendientes.

### Criterio de registro

La cronología se organiza por fases y etapas, no por horas ni jornadas inventadas. Los avances y cierres se basan en las confirmaciones efectuadas durante el acompañamiento; los archivos de cada entrega permiten verificar qué se programó. Los resultados numéricos de latencia, los identificadores reales de la última venta, las capturas privadas y los registros completos de ejecución no se reproducen porque no están disponibles en esta consolidación. Los valores usados en ejemplos de prueba no se presentan como resultados observados. Las referencias a pruebas aprobadas por el equipo corresponden a sus confirmaciones, no a una auditoría independiente de su computador.

## 2. Seguimiento general

| Fase | Entregable | Estado al cierre |
|---|---|---|
| 1. Entorno y datos | MariaDB, scripts SQL, conexión Python y modelo ampliado | Confirmada |
| 2. Backend | Diez etapas de API, seguridad, negocio e integración | Confirmada |
| 3. Frontend | Ocho etapas de interfaz, gestión y verificación integral | Confirmada dentro del alcance local |
| 4. Git y GitHub | Copia publicable, clonación y Release `v1.0.0` | Confirmada |
| 5. Bitácora | Consolidación técnica, incidencias, pruebas y limitaciones | Elaborada; pendiente de incorporar al repositorio |

## 3. Fase 1 — Configuración del entorno y base de datos

### 3.1. Preparación inicial

Se eligió MariaDB en lugar de SQLite como motor de ejecución porque el equipo ya tenía conocimientos del motor y un modelo SQL desarrollado en clase. SQLite se utilizó posteriormente como doble de prueba en memoria, no como sustituto de MariaDB en la aplicación. El entorno de trabajo fue Windows, PowerShell, Visual Studio Code, Python y un entorno virtual `.venv`. Se incorporaron PyMySQL para la conexión y python-dotenv para la configuración privada.

La estructura inicial separó `backend/`, `database/`, los archivos de configuración y las pruebas. Los scripts originales de DDL, DML, DCL, vistas, consultas y auditoría se organizaron en archivos numerados. La aplicación no debía conectarse con el usuario root: se destinó una cuenta con permisos operativos limitados. Se mantuvo una cuenta administrativa de MariaDB para creación, permisos y consultas de auditoría.

### 3.2. Cambio de nombres y ampliación del modelo (V2)

El equipo cambió el nombre de la base operativa de `restaurante` a `restaurante_pro_max` y de la base de auditoría de `audit` a `audit_pro`. Esto exigió mantener consistentes las referencias en scripts, triggers, permisos y `DB_NAME` del archivo `.env`. Se hizo una copia de seguridad antes de aplicar la migración.

El esquema original de 15 tablas se conservó. Para ajustar el sistema al manual se añadieron dos tablas y nuevos atributos, en lugar de reconstruir todo el modelo:

| Objeto | Cambio | Justificación |
|---|---|---|
| `Mesa` | Nueva tabla con número, restaurante y estado de activación | Distinguir mesas utilizables y relacionarlas con los pedidos |
| `Movimiento_Inventario` | Nueva tabla con insumo, empleado, tipo, cantidad, motivo, fecha y factura opcional | Trazabilidad de entradas, salidas y ajustes |
| `Empleado` | `activo` | Desactivar cuentas sin perder historial |
| `Pedido` | Cocinero asignado y fechas de inicio, listo y entrega | Gestionar comandas y tiempos |
| `Detalle_Pedido` | `nota_especial`, `precio_unitario` | Observaciones y conservación del precio histórico |
| `Factura` | Datos complementarios del cliente, campos de validación electrónica y monto recibido | Pago, comprobante y preparación de integración futura |
| `v_estado_mesas` | Nueva vista | Calcular ocupación a partir de pedidos abiertos sin factura |
| `audit_pro` | Dos tablas de auditoría, seis triggers nuevos y cuatro triggers de actualización ampliados | Mantener el registro de los nuevos objetos y cambios |

El modelo preparado pasó a 17 tablas operativas, 17 tablas de auditoría, 51 triggers y tres vistas. Se mantuvieron las claves compuestas por restaurante y los identificadores existentes. No se inventaron precios históricos, consumos antiguos ni recetas faltantes. Los cinco pedidos históricos tenían factura, incluso algunos con estados no finales; se conservaron y se usó la existencia de factura para excluirlos de los pedidos abiertos.

### 3.3. Verificación y cierre

Se comprobaron la estructura de tablas, los registros de demostración, la vista de mesas y la conexión desde Python mediante `test_conexion.py`. Durante la configuración aparecieron problemas de reconocimiento del ejecutable de respaldo, variables de entorno y autenticación de MariaDB, descritos en la sección 8. El equipo confirmó la conexión y el cierre de la fase antes de avanzar a Flask.

Entregables: scripts `01` a `10` de `database/`, `backend/db.py`, `test_conexion.py`, `.env.example`, `requirements.txt`, `CAMBIOS_V2.md` y documentación inicial.

## 4. Fase 2 — Desarrollo del backend

Se construyó una API HTTP con Flask. Cada etapa añadió funciones concretas y pruebas antes de avanzar. Las consultas SQL se parametrizaron y las operaciones de escritura se concentraron en la capa de negocio. La identidad y el restaurante se obtienen de la sesión; no se confía en los identificadores de empleado enviados desde el navegador.

### 4.1. Etapa 2.1 — Servidor Flask

Se creó `app.py`, se incorporó Flask y se habilitaron las rutas `/` y `/api/estado`. La primera permite comprobar que el servidor responde; la segunda consulta la conexión con MariaDB y devuelve su estado. Se mantuvo el servidor en `127.0.0.1:5000`, sin modo de depuración para la entrega local. El equipo confirmó el funcionamiento de ambas rutas.

### 4.2. Etapa 2.2 — Autenticación y contraseñas seguras

Se implementó `backend/auth.py` y el configurador `configurar_claves_demo.py`. Las claves de demostración reemplazaron el marcador inicial `hash123` por hashes scrypt de Werkzeug; no se distribuyó una contraseña común en el repositorio. Se añadieron inicio y cierre de sesión, consulta de la identidad y verificación de cuentas activas. La clave de firma de sesión se configuró en `.env` con al menos 32 caracteres. Se aplicaron cookies HttpOnly, SameSite Strict y duración de ocho horas; la cookie no utiliza el atributo Secure en HTTP local. El equipo confirmó autenticación y sesiones.

### 4.3. Etapa 2.3 — Identificación y permisos por roles

Se integraron `auth.py` y `permisos.py` para identificar los roles a partir de las tablas `Mesero`, `Cocinero`, `Cajero` y `Administrador`. Se respetó la posibilidad de que un empleado tenga varios roles. Se revalida la cuenta y sus roles en las peticiones protegidas. Se estableció la distinción entre falta de autenticación (401) y ausencia del rol requerido (403). Se prepararon diez pruebas de permisos y el equipo confirmó sus resultados.

### 4.4. Etapa 2.4 — Mesas y productos

Se desarrollaron `salon.py` y `catalogo.py` para consultar mesas, categorías y productos. La disponibilidad efectiva considera la configuración del producto, la existencia de una receta válida y el stock utilizable después de las reservas de pedidos abiertos. Un producto sin receta queda bloqueado; se mantuvo así el Mute Santandereano del conjunto de datos original. La disponibilidad consultada es una estimación que se revalida al registrar el pedido, no una garantía de stock futuro. Se prepararon 14 pruebas de catálogo y API; el equipo confirmó el módulo.

### 4.5. Etapa 2.5 — Registro de pedidos

Se añadió `pedidos.py` y la ruta de registro del salón. El sistema valida mesa, productos, cantidades, notas y disponibilidad conjunta de los ingredientes; guarda el encabezado y los detalles en una transacción y conserva el precio unitario del momento. Se incorporó un bloqueo de la fila del restaurante para serializar operaciones de escritura relacionadas, además de bloqueos de filas pertinentes. Ante errores se realiza rollback. Se permite registrar pedidos adicionales en una mesa ocupada activa, como órdenes independientes. Se prepararon 15 pruebas y el equipo confirmó las transacciones y el registro.

### 4.6. Etapa 2.6 — Gestión de comandas

Se incorporaron `cocina.py` y `comandas.py`. El pedido actúa como comanda digital; no se duplicó en otra tabla. El flujo normal acordado fue `Tomado → Preparacion → Lista → Entregado → Cerrado`, con controles de transición y registro de fechas. El cocinero que inicia la preparación queda asignado y el mesero confirma la entrega. El estado inicial `Tomado` diferencia las órdenes nuevas de las ya aceptadas por cocina. Se prepararon 18 pruebas; el equipo confirmó los cambios de estado y las comandas.

### 4.7. Etapa 2.7 — Facturación y pagos

Se desarrollaron `caja.py` y `facturacion.py`. Solo se facturan pedidos entregados sin factura previa. La precuenta usa los precios históricos registrados y el backend calcula el total con `Decimal`. Se registran pagos manuales en efectivo, tarjeta o Nequi; para efectivo se calcula el cambio, mientras los demás requieren el monto exacto. El impuesto adicional de la demo es cero. La factura, el descuento de ingredientes según receta, los movimientos de inventario y el cierre del pedido se confirman en una sola transacción. La unicidad de la factura por pedido protege frente a una doble facturación. La mesa queda libre si no hay otras órdenes abiertas. Se prepararon 21 pruebas y se confirmó el flujo. No se implementó integración fiscal ni bancaria.

### 4.8. Etapa 2.8 — Inventario, movimientos y alertas

Se añadieron `inventario.py` y `administracion.py`. Se distinguió el stock físico del comprometido y del utilizable. Se habilitaron entradas, ajustes positivos y negativos con motivo obligatorio, historial paginado y alertas por stock mínimo. Se impide retirar cantidades que afecten las reservas. Las salidas por facturación se generan automáticamente desde caja. Se realizaron pruebas controladas de ingreso, alerta, rechazo y restitución mediante un movimiento compensatorio, sin borrar el historial. Se prepararon 22 pruebas; el equipo confirmó el módulo. Durante la comprobación de auditoría surgió el error 1267 de collations, resuelto mediante una comparación explícita.

### 4.9. Etapa 2.9 — Dashboard y reportes administrativos

Se incorporó `reportes.py` y se ampliaron las rutas administrativas de lectura. Se desarrollaron los informes de ventas por período, platos más vendidos, consumo de insumos y cierre de caja, además de un dashboard consolidado. Los períodos son inclusivos, de hasta 366 días; los estados de mesas, pedidos pendientes e inventario corresponden al momento de consulta. No se usan precios actuales para reconstruir ventas históricas ni recetas actuales para inventar consumos pasados. El cierre de caja es un consolidado de ventas, no un arqueo físico. Se prepararon 17 pruebas; el equipo confirmó sus resultados.

### 4.10. Etapa 2.10 — Integración del backend

Se entregaron `prueba_integracion.py`, `test_integracion_utilidades.py` y `database/11_verificacion_integracion.sql`. La prueba real autentica perfiles independientes, registra una orden académica previa confirmación, recorre cocina y entrega, valida el pago, comprueba la factura única, la liberación de mesa, el descuento y los reportes. Las consultas SQL permiten revisar auditoría. Se añadieron cinco pruebas de utilidades, para una suite acumulada prevista de 122 pruebas. El equipo confirmó la integración y la auditoría antes de iniciar el frontend. La prueba real escribe en MariaDB y no debe repetirse indiscriminadamente si ya existe un pedido o una factura.

### 4.11. Rutas principales por módulo

| Módulo | Rutas de referencia |
|---|---|
| Estado | `GET /`, `GET /api/estado` |
| Autenticación | `POST /api/auth/login` y rutas de sesión |
| Salón | `GET /api/salon/mesas`, `/categorias`, `/productos`; `GET` y `POST /api/salon/pedidos` |
| Cocina | `GET /api/cocina/comandas`; `POST /api/cocina/comandas/{numero}/iniciar` y `/lista` |
| Caja | `GET /api/caja/pendientes`; precuenta, pago y comprobante bajo `/api/caja/pedidos/{numero}` |
| Inventario | `/api/administracion/inventario`, `/alertas`, `/movimientos` |
| Reportes | `/api/administracion/dashboard`, `/api/administracion/reportes/{tipo}` |

## 5. Fase 3 — Desarrollo del frontend

Se decidió conservar Flask y sus rutas API, agregando plantillas Jinja, HTML, CSS, Bootstrap local y JavaScript con `fetch`. El frontend no ejecuta SQL ni reemplaza las validaciones del servidor. La identidad visual utiliza verde bosque, dorado y marfil; verde y naranja identifican mesas libres y ocupadas, y amarillo destaca notas de cocina. El diseño se inspiró en los prototipos de las ilustraciones 16 y 17 (página 38 del informe), sin reproducir un logotipo oficial.

### 5.1. Etapa 3.1 — Acceso y navegación

Se crearon `backend/interfaz.py`, las plantillas `base.html`, `login.html`, `panel.html`, `marca.html` y `error_ui.html`, además de `ld.css` e `interfaz.js`. La interfaz quedó disponible en `/login` y los módulos en `/panel/salon`, `/panel/cocina`, `/panel/caja` y `/panel/administracion`. Los accesos directos se protegen desde Flask; la navegación admite empleados con varios roles. Bootstrap se incluyó localmente. Se agregaron seis pruebas de interfaz; el equipo confirmó acceso, diseño y permisos.

### 5.2. Etapa 3.2 — Salón

Se añadieron `salon.html`, `salon.css` y `salon.js`. Se siguió la distribución del prototipo: categorías a la izquierda, menú en el centro y orden actual a la derecha; las mesas se muestran arriba. Se incorporaron búsqueda, cantidades, notas, subtotal, confirmación y seguimiento de los pedidos. Los productos no disponibles se bloquean, el carrito es temporal y los cambios de estado se consultan cada ocho segundos con la pestaña visible. Ante un envío incierto se pide verificar el pedido antes de repetirlo. Se añadieron cinco pruebas; el equipo confirmó el funcionamiento del módulo.

### 5.3. Etapa 3.3 — Cocina y bar

Se añadieron `cocina.html`, `cocina.css` y `cocina.js` con tres columnas: Nuevas comandas, En preparación y Listas para entregar. Se mostraron mesa, número, hora, platos, observaciones amarillas y acciones según el cocinero asignado. La consulta automática se realiza cada cuatro segundos con la pestaña visible. Se verificó la comunicación con salón utilizando sesiones independientes. Se agregaron cinco pruebas y el equipo confirmó la etapa. La actualización periódica no equivale a notificaciones push instantáneas.

### 5.4. Etapa 3.4 — Caja y facturación

Se incorporaron `caja.html`, `caja.css` y `caja.js`. La pantalla presenta pedidos pendientes, precuenta y formulario de pago. Se añadió el cálculo visual de cambio, la validación del monto y la consulta/reimpresión del comprobante por número de pedido. El documento puede imprimirse o guardarse como PDF desde el navegador; no tiene validez fiscal. Se introdujo un bloqueo local de cobro ante respuestas inciertas. Durante las pruebas acumuladas se detectaron archivos de cocina faltantes y se preparó un parche que no reemplazaba `panel.html`. Después se confirmó la etapa y la integración con salón. Cinco pruebas nuevas.

### 5.5. Etapa 3.5 — Inventario administrativo

Se incorporaron `inventario.html`, `inventario.css` e `inventario.js`. Se visualizaron indicadores de stock, cantidades físicas, reservadas y utilizables, filtros, formularios de entradas y ajustes e historial. Se comprobó el ciclo de alerta y restitución y se mantuvieron las unidades originales de los insumos. La actualización automática se estableció en 15 segundos con la pestaña visible. Cinco pruebas nuevas; el equipo confirmó movimientos, alertas y validaciones.

### 5.6. Etapa 3.6 — Dashboard gerencial

Se añadieron `dashboard.html`, `dashboard.css` y `dashboard.js`, conservando inventario en la navegación administrativa. Se visualizaron ventas, facturas, ticket promedio, mesas libres, tiempo de preparación y alertas. Los cuatro reportes se presentan mediante tablas y gráficos generados localmente, sin depender de servicios de gráficos externos. El reporte de consumo separa unidades incompatibles y los datos históricos faltantes no se inventan. Cinco pruebas nuevas; el equipo confirmó indicadores y reportes.

### 5.7. Etapa 3.7 — Exportaciones y gestión administrativa

Se amplió el backend con `gestion.py`, `exportaciones.py` y nuevas rutas en `administracion.py`. Se incorporaron ReportLab y XlsxWriter para generar PDF y XLSX reales. Los documentos incluyen resúmenes y tablas; los gráficos permanecen en el dashboard. El archivo Excel mantiene valores numéricos y evita interpretar textos de usuario como fórmulas.

Se añadieron `gestion.html`, `gestion.css` y `gestion.js` para crear y editar productos, crear insumos en cero, modificar mínimos, configurar recetas, crear empleados, asignar roles, restablecer contraseñas y activar/desactivar cuentas. Se protege la receta de productos con pedidos abiertos y el historial de empleados. Los cambios de precio no modifican las líneas históricas. El administrador no puede desactivar su propia cuenta ni retirar su propio rol administrativo. Se utilizaron un insumo, un producto y una cuenta ficticios de prueba; se indicó desactivar el producto y la cuenta al terminar. Se agregaron 19 pruebas (nueve de gestión, cuatro de exportación y seis de integración UI/seguridad). El equipo confirmó el módulo y las descargas de ambos formatos.

### 5.8. Etapa 3.8 — Pruebas visuales e integración final

Se prepararon `verificar_frontend.py`, `medir_concurrencia.py`, `database/12_verificacion_final.sql` y una matriz de trazabilidad. Se definió un recorrido completo desde cuatro sesiones del navegador: pedido, cocina, entrega, pago, inventario, reportes y auditoría. Se propusieron pruebas por resolución y navegador, así como un sondeo local de ocho sesiones concurrentes con tres rondas de lectura. El equipo confirmó la ejecución de las pruebas finales y que documentó resultados y limitaciones. No se dispone aquí del valor máximo de latencia ni del tiempo de transmisión observado; por tanto no se certifican sus umbrales. La fase quedó cerrada dentro del alcance académico local.

## 6. Fase 4 — Organización, Git y publicación

| Etapa | Trabajo registrado |
|---|---|
| 4.1 | Se preparó una copia independiente `restaurante-ld`, sin eliminar `restaurante-ld-fase1-v2`. El organizador copia el código y recursos autorizados, no la base de datos existente. |
| 4.2 | Se consolidaron dependencias y 12 scripts SQL; se preparó una semilla sintética y se creó un entorno virtual independiente. |
| 4.3 | Se configuró `.gitignore` para excluir `.env`, entornos virtuales, respaldos, evidencias, exportaciones y volcados privados. Se conservó `.env.example` como plantilla sin claves reales. |
| 4.4 | Se elaboró un README con arquitectura, requisitos, instalación, cuentas demo, pruebas, capturas simuladas y limitaciones. |
| 4.5 | Se inicializó Git en la carpeta definitiva, se configuró la identidad y se creó el primer commit después de revisar los archivos a publicar. |
| 4.6 | Se vinculó el remoto `origin` y se publicó el código en la rama `main`. Se corrigieron la URL de ejemplo y la ubicación de trabajo de la terminal. |
| 4.7 | El equipo confirmó la clonación del repositorio y su comprobación de funcionamiento. La guía utiliza la instancia de MariaDB ya configurada; no acredita una instalación nueva en una instancia aislada. |
| 4.8 | El equipo confirmó la etiqueta y el Release `v1.0.0` del MVP académico. |

Repositorio confirmado por el equipo: https://github.com/checod11/restaurante-ld. No se comprueba aquí su visibilidad, contenido remoto exacto ni hash del commit. La recomendación inicial fue mantenerlo privado hasta contar con autorización de publicación. La publicación del código en GitHub no aloja la aplicación Flask ni la base de datos. El README no asigna una licencia de distribución al código propio sin decisión de los desarrolladores; Bootstrap conserva su licencia.

## 7. Arquitectura y decisiones técnicas consolidadas

```text
Navegador: HTML / Jinja / CSS / Bootstrap / JavaScript
                       ↕ HTTP + JSON
             Flask: rutas HTML y API por rol
                       ↕
        Servicios de negocio + conexión PyMySQL
                       ↕
           MariaDB: restaurante_pro_max
                       │ triggers
                       ↓
                   audit_pro
```

| Decisión | Motivo y efecto |
|---|---|
| MariaDB como motor real | Reutilización del modelo relacional y conocimiento del equipo. SQLite solo sirve como simulador de pruebas. |
| Flask con Blueprints | Modularización progresiva de la API y de las pantallas. |
| NIT en consultas y claves compuestas | Aislar registros del restaurante autenticado; la demo se configura para un restaurante fijo, no es un servicio multicliente completo. |
| Sesiones firmadas, scrypt y roles | Evitar claves en texto plano y comprobar autorización en el servidor. No equivale a cifrado integral de datos personales. |
| Precio histórico en detalle | Mantener el importe acordado en el pedido aunque el menú cambie. |
| Reserva lógica y descuento al facturar | No alterar stock físico al tomar pedidos y evitar comprometer más ingredientes de los disponibles. |
| Transacciones y bloqueos | Evitar escrituras parciales e inconsistencias en pedidos, pagos y gestión. |
| Mesa con estado derivado | La liberación depende de todas las órdenes abiertas, no solo de la última factura. |
| Auditoría por triggers | Registrar cambios en tablas sin duplicar lógica; el usuario SQL del trigger no equivale siempre al usuario web. |
| Polling de cocina, salón e inventario | Simplificar la demo local; no sustituye notificaciones instantáneas ni certifica latencias máximas. |
| Reportes de lectura | Separar el análisis de las operaciones comerciales y evitar reconstruir datos históricos desconocidos. |
| Desactivación y no borrado | Conservar el historial de productos y empleados. |
| Exportación real en servidor | PDF con ReportLab y XLSX con XlsxWriter; sin depender de renombrar HTML o CSV. |
| Copia independiente para publicar | Reducir riesgo de perder la versión local o publicar datos privados. |

Dependencias directas consolidadas: Flask, Werkzeug, PyMySQL, python-dotenv, ReportLab y XlsxWriter. El archivo `requirements.txt` combina versiones fijas y rangos; no es un bloqueo exacto de todas las dependencias transitivas. El entorno de ejecución es local, por HTTP; no se debe utilizar el servidor de desarrollo como servidor de producción.

## 8. Registro de incidencias y soluciones

| ID / fase | Incidencia observada | Diagnóstico y solución aplicada o indicada | Resultado de seguimiento |
|---|---|---|---|
| INC-01 / 1 | PowerShell no reconocía `mariadb-dump` | Se utilizó la ruta completa del ejecutable instalado y se preparó el directorio de respaldos. | El equipo confirmó que pudo continuar con la copia de seguridad. |
| INC-02 / 1 | `Configura DB_PASSWORD en el archivo .env.` | Se revisó que el archivo `.env` existiera con el nombre correcto y que el marcador de contraseña se sustituyera por la credencial local. | El equipo continuó con las pruebas de conexión; no se registra el valor de la clave. |
| INC-03 / 1 | MariaDB 1045: `Access denied for user 'app_mirador'@'localhost' (using password: YES)` | Se revisó la coincidencia entre cuenta, host, contraseña y permisos sobre la base renombrada. No era un fallo de la sintaxis de Python. | Conexión confirmada posteriormente; no consta aquí el comando exacto que resolvió la cuenta local. |
| INC-04 / 2.2 | `RuntimeError: Configura SECRET_KEY en .env con una clave aleatoria de al menos 32 caracteres.` | Se debía generar una clave aleatoria y guardarla en `.env`, sin publicarla. | El equipo confirmó autenticación y sesiones al cerrar 2.2. |
| INC-05 / 2.8 | MariaDB 1267: `Illegal mix of collations` entre `utf8mb4_uca1400_ai_ci` y `utf8mb4_unicode_ci` | El JOIN entre auditoría y movimientos comparaba NIT con reglas de caracteres distintas. Se unificó explícitamente la comparación con `COLLATE utf8mb4_unicode_ci`, sin alterar columnas ni claves foráneas. | El equipo confirmó la etapa 2.8; se reutilizó la corrección en verificaciones posteriores. |
| INC-06 / 3.4 | `TemplateNotFound: cocina.html`, `ModuleNotFoundError: No module named 'test_cocina_ui'` y `500 != 200` | Faltaban archivos de cocina en la ubicación esperada. Se entregó un parche con `cocina.html`, `cocina.css`, `cocina.js` y `test_cocina_ui.py`, sin sobrescribir el `panel.html` actualizado de caja. Se indicó verificar rutas con `Test-Path` y repetir la suite. | Captura de la ejecución fallida: 17 pruebas contabilizadas, tres fallos y un error. El equipo confirmó después el cierre de 3.4. |
| INC-07 / 4 | `fatal: not a git repository (or any of the parent directories): .git` y URL con `TU_USUARIO` | Se identificó que PowerShell estaba en la carpeta superior. Se indicó entrar a `restaurante-ld`, comprobar `git status`, revisar `git remote -v` y corregir `origin` con `git remote set-url`. | El equipo confirmó que el repositorio apareció en GitHub y posteriormente el cierre de la fase 4. |

### 8.1. Ejemplo de corrección SQL de auditoría

```sql
SELECT a.*
FROM audit_pro.auditoria_Movimiento_Inventario a
INNER JOIN restaurante_pro_max.Movimiento_Inventario m
  ON a.id_movimiento = m.id_movimiento
 AND a.NIT_restaurante COLLATE utf8mb4_unicode_ci
   = m.NIT_restaurante COLLATE utf8mb4_unicode_ci
WHERE m.NIT_restaurante = '900123456-1'
  AND m.id_insumo = 201
ORDER BY a.id_auditoria DESC;
```

El NIT de la consulta pertenece a la semilla de demostración. Esta solución evita modificar de manera global las collations de tablas relacionadas.

### 8.2. Prevención de recurrencias

Se incorporaron respaldos previos a migraciones, verificación de archivos antes de las pruebas, instalación acumulativa sin eliminar carpetas, revisión del remoto antes de publicar y manejo de respuestas inciertas en las operaciones de escritura. Ante una desconexión al enviar una orden o un pago, primero se debe verificar si el servidor lo registró. No se debe repetir de manera automática una operación cuyo resultado se desconoce. Se mantiene pendiente un mecanismo de idempotencia general entre dispositivos.

## 9. Pruebas y evidencias

### 9.1. Suite automatizada acumulada

Los números siguientes corresponden a la suite planificada y entregada. Las confirmaciones de cierre del equipo respaldan su ejecución satisfactoria según el seguimiento, pero no se adjunta una salida íntegra de las 172 pruebas de su computador. En la preparación de la etapa 3.8 se reportaron 93 pruebas ejecutadas con simuladores y 79 pendientes en ese entorno por dependencias de Flask; estos números no son resultados adicionales a las 172 pruebas.

| Módulo | Pruebas | Tipo |
|---|---:|---|
| `test_permisos` | 10 | Autenticación, roles, API |
| `test_salon` | 14 | Mesas, catálogo, disponibilidad |
| `test_pedidos` | 15 | Registro, validación y transacciones |
| `test_comandas` | 18 | Estados y asignación |
| `test_facturacion` | 21 | Pago, factura y consumo |
| `test_inventario` | 22 | Entradas, ajustes, reservas y alertas |
| `test_reportes` | 17 | Fechas, cálculos y permisos |
| `test_integracion_utilidades` | 5 | Utilidades de prueba integral |
| **Subtotal backend** | **122** | |
| `test_interfaz` | 6 | Login, navegación y acceso |
| `test_salon_ui` | 5 | Plantilla y permisos |
| `test_cocina_ui` | 5 | Plantilla y permisos |
| `test_caja_ui` | 5 | Plantilla y permisos |
| `test_inventario_ui` | 5 | Plantilla y permisos |
| `test_dashboard_ui` | 5 | Plantilla y permisos |
| `test_gestion` | 9 | Catálogos y transacciones |
| `test_exportaciones` | 4 | PDF y XLSX |
| `test_gestion_ui` | 6 | Integración y seguridad |
| **Subtotal frontend y ampliación** | **50** | |
| **Total** | **172** | 17 módulos |

Para reproducir la regresión desde la raíz con `.env` y dependencias configurados:

```powershell
.\.venv\Scripts\python.exe verificar_frontend.py
```

El programa verifica 61 archivos y ejecuta los módulos `unittest`, sin realizar una venta ni una migración. `test_conexion.py` consulta la instancia MariaDB; `prueba_integracion.py` realiza operaciones reales previa confirmación; `medir_concurrencia.py` realiza lecturas concurrentes con el servidor en ejecución. Son verificaciones separadas de la suite automatizada.

### 9.2. Prueba integral de aceptación

| Caso | Criterio de aceptación | Seguimiento |
|---|---|---|
| E2E-01 | Login de los cuatro perfiles, rechazo de roles incorrectos | Confirmado en las etapas 2.3, 3.1 y cierre final |
| E2E-02 | Pedido con mesa, productos, cantidad y nota | Confirmado en salón |
| E2E-03 | Comanda visible y cambios de estado controlados | Confirmado en cocina y salón |
| E2E-04 | Precuenta, rechazo de pago insuficiente y comprobante único | Confirmado en caja |
| E2E-05 | Descuento por receta, movimientos y liberación de mesa si procede | Confirmado en integración e inventario |
| E2E-06 | Indicadores y reportes coherentes con MariaDB | Confirmado en etapas 2.9 y 3.6 |
| E2E-07 | Exportación de cuatro informes a dos formatos | Confirmado en etapa 3.7 |
| E2E-08 | Gestión de catálogos y acceso de empleados | Confirmado en etapa 3.7 |
| E2E-09 | Registros de auditoría y trazabilidad | Confirmado en integración 2.10 |
| E2E-10 | Recuperar el código clonado y ejecutar la aplicación | Confirmado en fase 4 |

La etapa 3.8 propuso una venta de una limonada con una nota identificable, comparación antes/después de ventas, facturas, existencias y movimientos. El precio de $8.000 y el consumo de una unidad de panela y 0,10 kg de limón eran valores esperados de la semilla original, sujetos al catálogo y receta vigentes; no se afirma que sean los valores reales de la última prueba.

### 9.3. Registro de evidencias para el equipo

Esta tabla sirve como índice de evidencias, no como afirmación de que cada captura se encuentra adjunta al repositorio. Conservar los originales privados en `evidencias/`; para publicar, generar copias anonimizadas y revisar su contenido.

| Código | Evidencia prevista |
|---|---|
| EV01 | Salida de regresión `evidencias/regresion_3_8_*.txt` |
| EV02–EV03 | Login y rechazos de permisos |
| EV04–EV06 | Pedido desde salón, comanda de cocina y entrega |
| EV07–EV09 | Precuenta, comprobante y liberación de mesa |
| EV10–EV12 | Consumo por receta, alertas y gestión administrativa |
| EV13–EV14 | Dashboard, reportes y archivos PDF/XLSX |
| EV15–EV16 | Medición de transmisión y sondeo `concurrencia_3_8_*.txt` |
| EV17 | Diseño por resolución y navegador |
| EV18 | Consultas SQL de auditoría |
| EV19 | Repositorio, clonación y Release `v1.0.0` |

Los archivos de referencia de la fase 4 contienen capturas simuladas de las pantallas; no deben presentarse como evidencia de una transacción real. Los triggers registran operaciones directas y usuario SQL; no garantizan trazabilidad completa de toda acción web ni de cascadas de claves foráneas.

## 10. Cumplimiento de requerimientos y alcance pendiente

La siguiente clasificación reproduce los 17 requerimientos funcionales agrupados en la matriz de la etapa 3.8. No son identificadores RF originales del informe, sino códigos de trazabilidad elaborados para el MVP. Los estados se basan en las confirmaciones anteriores y el alcance documentado, no reemplazan la matriz final completada por el equipo.

| ID | Requerimiento | Estado |
|---|---|---|
| RF01 | Autenticación y acceso por roles | Confirmado |
| RF02 | Mesas, categorías y menú | Confirmado |
| RF03 | Bloqueo de productos no disponibles | Confirmado |
| RF04 | Notas especiales | Confirmado |
| RF05 | Comandas digitales | Confirmado |
| RF06 | Estados de preparación | Confirmado |
| RF07 | Notificación instantánea al mesero | Parcial: polling |
| RF08 | Precuenta, subtotal e impuestos | Parcial: impuesto adicional demo cero |
| RF09 | Documento equivalente POS e impresión térmica | Parcial: comprobante académico imprimible |
| RF10 | Métodos de pago | Parcial: registro manual sin integración bancaria |
| RF11 | Liberación de mesa | Confirmado, si no existen otros pedidos abiertos |
| RF12 | Descuento de insumos por receta | Confirmado |
| RF13 | Alertas de stock mínimo | Confirmado |
| RF14 | Gestión de insumos, mínimos, productos, recetas y usuarios | Confirmado |
| RF15 | Cuatro reportes analíticos | Confirmado |
| RF16 | Exportación a PDF y Excel | Confirmado |
| RF17 | Facturación electrónica Sandbox XML/CUFE | No implementado |

Balance preliminar: 12 confirmados, cuatro parciales y uno no implementado. No constituye una certificación de calidad ni un porcentaje ponderado de cumplimiento del contrato original.

| Requisito no funcional o restricción original | Situación al cierre |
|---|---|
| Comanda sala-cocina estrictamente inferior a 5 segundos | Se diseñó medición visual; el tiempo real no está disponible en esta bitácora. El polling de cuatro segundos no garantiza el umbral. |
| Al menos ocho dispositivos concurrentes, latencia máxima de dos segundos | Se preparó un sondeo de ocho sesiones locales y 24 lecturas. No equivale a una prueba de ocho dispositivos físicos; latencias reales no disponibles aquí. |
| Cifrado de datos personales y SSL/TLS | Hash de claves y autorización implementados; HTTP local, sin certificación de TLS ni cifrado integral. |
| Offline-First (LAN) | No se implementó cola offline, caché transaccional ni reconciliación. El uso de recursos locales no implica sincronización offline. |
| Compatibilidad de navegadores y dispositivos | Diseño adaptable comprobado según seguimiento; no hay detalle de todos los dispositivos físicos o navegadores certificados. |
| Presupuesto inicial máximo de $54.450.000 COP, plazo de 12 semanas y continuidad del piloto | Son restricciones del informe, no costos ni plazos efectivamente medidos en esta bitácora. No se certifica operación comercial del piloto. |

El informe (p. 18) redujo la integración DIAN productiva a Sandbox de un proveedor autorizado; dicho alcance revisado también sigue pendiente. La HU02 (p. 20) preveía que el pedido pasara inicialmente a En preparación, mientras que la implementación incorpora `Tomado` para diferenciar comandas nuevas, en consonancia con el tablero del manual. Las alertas de stock de HU10, previstas para una iteración posterior en el mapa de historias, sí fueron incorporadas a este MVP por su utilidad administrativa.

## 11. Fase 5 — Consolidación de documentación

Se reunieron las decisiones técnicas, el registro de cada etapa, los problemas encontrados, las pruebas y las limitaciones en este archivo `BITACORA.md`. El propósito es preservar la trazabilidad del desarrollo para la sustentación y para futuras modificaciones del código.

La actividad restante consiste en copiar este documento a la raíz de `restaurante-ld`, revisarlo con los responsables, añadirlo a Git y publicar un commit documental. Se debe conservar la etiqueta original `v1.0.0` como referencia del código liberado; no hace falta modificarla ni crear otra versión para incorporar la bitácora. La publicación de esta documentación no se declara realizada hasta que el equipo la confirme.

## 12. Conclusiones y próximos desarrollos

El proyecto logró trasladar el modelo relacional y los prototipos académicos a una aplicación web integrada. La construcción por etapas permitió detectar errores de configuración, integridad de datos, integración de plantillas y control de versiones sin reiniciar el proyecto. La incorporación de transacciones, precios históricos, reservas de inventario y auditoría aporta coherencia a la operación; la separación entre backend y frontend permite mantener y ampliar los módulos.

La publicación y clonación confirmadas de la versión `v1.0.0` permiten conservar una referencia del entregable académico. Sin embargo, la aprobación funcional local no equivale a certificación fiscal, comercial o de seguridad. Para una futura versión se recomienda priorizar el Sandbox electrónico, HTTPS y protección integral de datos, sincronización Offline-First, notificaciones push, pruebas concurrentes con dispositivos físicos, control de idempotencia y recuperación ante fallos, validación de impresoras y pagos externos y un sistema de costos que permita calcular rentabilidad. También se recomienda una instalación desde cero en una instancia MariaDB aislada, pruebas de restauración y una revisión de seguridad previa a producción.

## 13. Fuentes de trazabilidad

- Jimenez Bibanco, L., y Hernández, D. A. (2026, 22 de octubre). *Informe final: Software Administrador de Restaurantes*. Universidad Cooperativa de Colombia. Documento académico interno, especialmente pp. 18–21 y 33–38.
- L&D Company. (s. f.). *Manual de usuario – Software Administrador de Restaurantes L&D*. Documento interno, secciones 2–6.
- Scripts originales de Gestión de la Información: DDL, DML, modelo de auditoría, usuarios/roles/permisos, consultas y vistas.
- Entregas de desarrollo de Fase 1/V2, etapas 2.2–2.10 y 3.1–3.8, parche de cocina y paquete de Fase 4; guías `LEEME`, scripts, pruebas y archivos de implementación revisados durante la consolidación.
- Matriz de trazabilidad y aceptación de la etapa 3.8 y README preparado en Fase 4.
- Registro de seguimiento del desarrollo y confirmaciones del equipo; capturas de incidencias en la terminal. No se publican secretos, datos personales de clientes ni respaldos de las bases reales.
