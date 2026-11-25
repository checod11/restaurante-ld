# L&D | Matriz de trazabilidad y aceptación — etapa 3.8

Cliente: Restaurante Mirador Bumangués. Versión: MVP académico local.
Fuentes: Informe 2_ingenieria.pdf (pp. 18–20, 21, 33–38 y 42–46); Manual de Usuario — Software Administrador de Restaurantes L&D, secciones 2–5.

Estados iniciales: **C** = confirmado por el usuario en etapas anteriores, pendiente de regresión final; **P** = parcial; **NV** = no verificado; **NI** = no implementado. No son resultados de las pruebas 3.8. Registrar resultado observado y evidencia; no marcar automáticamente como aprobado.

| ID | Fuente | Requerimiento | Estado inicial | Prueba / evidencia | Resultado final |
|---|---|---|---|---|---|
| RF01 | HU01; manual 3.1 | Inicio/cierre de sesión y acceso por rol | C | EV02, EV03 | |
| RF02 | HU02; manual 4.1 | Mesas verdes/naranjas, categorías y cantidades | C | EV04 | |
| RF03 | HU02; manual 4.1 | Bloquear productos no disponibles | C | EV04 | |
| RF04 | HU03; manual 4.1 | Notas especiales por producto | C | EV04, EV05 | |
| RF05 | Informe p.18; HU04; manual 4.2 | Generar y recibir comanda digital con detalle y hora | C | EV05 | |
| RF06 | HU05; manual 4.2 | Iniciar preparación y marcar lista | C | EV05 | |
| RF07 | Manual 4.2 | Aviso instantáneo al mesero | P | EV06: consulta periódica, no push | |
| RF08 | HU06; manual 4.3 | Precuenta, subtotal, impuestos, total | P | EV07: total correcto, impuesto adicional demo cero | |
| RF09 | HU07; manual 4.3 | Documento equivalente POS e impresión térmica | P | EV08: comprobante académico e impresión navegador, no fiscal | |
| RF10 | Manual 4.3 | Efectivo y datáfono | P | EV07: registro manual, no integración con datáfono | |
| RF11 | Manual 4.3 | Liberar mesa tras pagar | C | EV09: mesa sin otros pedidos abiertos | |
| RF12 | HU08; informe p.18 | Descontar insumos exactos por receta | C | EV10: comparación antes/después y movimientos | |
| RF13 | HU10; manual 4.4 | Alertas al alcanzar stock mínimo | C | EV11: alerta por stock utilizable | |
| RF14 | Manual 4.4 | Gestionar insumos, mínimos, productos, recetas, usuarios | C | EV12 | |
| RF15 | Manual 4.4; informe p.31 | Reportes de ventas, platos, consumo, cierre | C | EV13 | |
| RF16 | Manual 4.4; informe p.31 | Exportar PDF y Excel | C | EV14: ocho archivos | |
| RF17 | Informe p.18; manual 4.3 | Sandbox proveedor autorizado, XML/CUFE | NI | No se implementó integración; no presentar como aprobado | |
| RNF01 | Informe p.18 | Comanda sala-cocina <5 s | NV | EV15: cronometrar desde confirmación hasta aparición automática | |
| RNF02 | Informe p.18 | >=8 dispositivos concurrentes, latencia <=2 s | NV | EV16: sondeo 8 sesiones locales; falta prueba física LAN | |
| RNF03 | Informe p.18 | Cifrado de datos personales y SSL/TLS | P | Hash scrypt de claves y RBAC; HTTP local, no cifrado integral ni TLS certificado | |
| RNF04 | Informe p.18; manual 2 y 5 | Offline-First, caché y sincronización | NI | Sin cola offline; no confundir LAN con sincronización | |
| RNF05 | Manual 2 | Navegadores Chrome, Edge, Firefox, Brave y dispositivos compatibles | NV | EV17: pruebas por navegador y resolución; emulación no prueba física | |
| RNF06 | Informe p.18 | Presupuesto <=54.450.000 COP, cronograma <=12 semanas, sin interrumpir piloto | NV | Requiere registros reales de gestión y piloto | |
| EXT01 | MVP desarrollado | Auditoría de pedido, factura y movimientos | C | EV10, EV18 | |
| EXT02 | MVP desarrollado | Protección de reservas, pagos duplicados y acceso indebido | C | EV01, EV03, EV07, EV10 | |

Observaciones de trazabilidad: HU02 (p.20) describe estado inicial “En preparación”; el MVP registra Tomado antes de que cocina acepte, coherente con las tres columnas del manual. Documentar esta diferencia. HU09 productiva queda en Release 2 (p.19), pero p.18 conserva Sandbox como alcance revisado; tampoco está implementado. La rentabilidad mencionada en el proyecto no equivale a ventas: no hay costos completos ni medición de impacto en el piloto. La auditoría se añade como evidencia del modelo de datos, no como un RF numerado de la fuente.

## Registro de resultados
Fecha: ____  Equipo/navegador: ____  Responsable: ____  Pedido: ____  Factura: ____
Para cada caso: resultado esperado, observado, estado (Aprobado / Fallido / No ejecutado), evidencia, observaciones. Los C iniciales representan confirmaciones anteriores del usuario y no reemplazan resultados de 3.8.
