-- SOLO en copia académica con DML original. Ejecutar una vez; IDs 306/307 deben estar libres.
-- En caso de error, ROLLBACK; no continuar ni confirmar parcialmente.
SET NAMES utf8mb4;
USE restaurante_pro_max;
START TRANSACTION;
INSERT INTO Mesa (num_mesa,NIT_restaurante)
SELECT n.num_mesa, '900123456-1' FROM (
 SELECT 1 AS num_mesa UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8
 UNION ALL SELECT 9 UNION ALL SELECT 10 UNION ALL SELECT 11 UNION ALL SELECT 12
) n WHERE NOT EXISTS (SELECT 1 FROM Mesa m WHERE m.num_mesa=n.num_mesa AND m.NIT_restaurante='900123456-1');
INSERT INTO Pedido (num_pedido,NIT_restaurante,id_mesero,num_mesa,fecha_hora_pedido,estado_pedido,id_cocinero,fecha_inicio_preparacion) VALUES
(306,'900123456-1',1,3,NOW(),'Tomado',NULL,NULL),
(307,'900123456-1',2,4,NOW(),'Preparacion',6,NOW());
INSERT INTO Detalle_Pedido (num_pedido,num_serial_producto,NIT_restaurante,cantidad,nota_especial,precio_unitario)
SELECT 306,num_serial,NIT_restaurante,2,'Sin hielo',precio FROM Producto WHERE num_serial=105 AND NIT_restaurante='900123456-1'
UNION ALL
SELECT 307,num_serial,NIT_restaurante,1,NULL,precio FROM Producto WHERE num_serial=102 AND NIT_restaurante='900123456-1';
COMMIT;
-- El stock no se altera: son pedidos abiertos, no facturados.
