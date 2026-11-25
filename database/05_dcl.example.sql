-- PLANTILLA: copiar a 05_dcl.local.sql y sustituir las tres claves antes de ejecutar.
-- Cuentas TCP locales; mismos permisos que en el DCL original.
-- Creación de usuarios

-- 1.Usuario para la aplicación principal del restaurante
CREATE USER 'app_mirador'@'127.0.0.1' IDENTIFIED BY 'CAMBIAR_CLAVE_APP';

--2. Usuario para el equipo de desarrolladores (L&D Company)
CREATE USER 'dev_ldcompany'@'127.0.0.1' IDENTIFIED BY 'CAMBIAR_CLAVE_DEV';

--3. Usuario administrador de base de datos (DBA)
CREATE USER 'admin_dba'@'127.0.0.1' IDENTIFIED BY 'CAMBIAR_CLAVE_DBA';


-- Configuración de permisos

GRANT SELECT, INSERT, UPDATE, DELETE 
ON restaurante_pro_max.* 
TO 'app_mirador'@'127.0.0.1';

GRANT ALL 
ON restaurante_pro_max.* 
TO 'dev_ldcompany'@'127.0.0.1';

GRANT ALL 
ON audit_pro.* 
TO 'dev_ldcompany'@'127.0.0.1';

GRANT ALL 
ON restaurante_pro_max.* 
TO 'admin_dba'@'127.0.0.1' 
WITH GRANT OPTION;

GRANT SELECT 
ON audit_pro.* 
TO 'admin_dba'@'127.0.0.1';

-- Recargar la tabla de privilegios
FLUSH PRIVILEGES;
