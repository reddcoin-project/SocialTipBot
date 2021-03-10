CREATE DATABASE reddittipbotdb;
USE reddittipbotdb;
CREATE USER 'tipbot'@'localhost' IDENTIFIED BY 'Tipb0tpassw0rd#';
GRANT ALL PRIVILEGES ON reddittipbotdb . * TO 'tipbot'@'localhost';
FLUSH PRIVILEGES;