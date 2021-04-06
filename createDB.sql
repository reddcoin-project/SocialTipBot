CREATE DATABASE tipbotdb;
USE tipbotdb;
CREATE USER 'tipbot'@'%' IDENTIFIED BY 'Tipb0tpassw0rd#';
GRANT ALL PRIVILEGES ON tipbotdb . * TO 'tipbot'@'%';
FLUSH PRIVILEGES;