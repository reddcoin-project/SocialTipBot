CREATE DATABASE tipbotdb;
USE tipbotdb;
CREATE USER 'tipbot'@'localhost' IDENTIFIED BY 'Tipb0tpassw0rd#';
GRANT ALL PRIVILEGES ON tipbotdb . * TO 'tipbot'@'localhost';
FLUSH PRIVILEGES;