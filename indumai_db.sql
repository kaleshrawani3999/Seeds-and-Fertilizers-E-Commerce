create database indumai;
use indumai; 
create table users (
id int auto_increment primary key,
name varchar(100),
email varchar(100) unique,
password varchar(255)
);


-- product database--

USE indumai;
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200),
    price INT,
    category VARCHAR(100),
    image VARCHAR(255)
);

INSERT INTO products (name, price, category, image) VALUES
('Tomato Seeds', 299, 'seeds', '/static/images/TOMATO PKM-1.jpg'),
('Wheat Seeds', 450, 'seeds', '/static/images/Wheat LOK-01.jpg'),
('NPK Fertilizer', 850, 'fertilizers', '/static/images/NPK.jpg'),
('Lady Finger', 450, 'seeds', '/static/images/Lady-finger.jpg'),
('Yellow Marigold', 300, 'seeds', '/static/images/YELLOW MARIGOLD.jpg'),
('Wheat HI-1544', 450, 'seeds', '/static/images/Wheat Hi-1544.jpg'),
('Watermelon', 350, 'seeds', '/static/images/watermelon.jpg'),
('Bottle Guard Samrat', 450, 'seeds', '/static/images/Bottle Guard Samrat.jpg'),
('Brinjal', 450, 'seeds', '/static/images/BRINJAL.jpg'),
('Cluster Bean', 380, 'seeds', '/static/images/CLUSTER BEAN.jpg'),
('Coriander', 450, 'seeds', '/static/images/Coriander.jpg'),
('Cowpea', 450, 'seeds', '/static/images/COWPEA.jpg'),
('Cucumber Green', 480, 'seeds', '/static/images/CUCUMBER Green.jpg'),
('Dollichos Bean', 450, 'seeds', '/static/images/DOLLICHOS BEAN.jpg'),
('Musk Melon F-1 Chandra', 450, 'seeds', '/static/images/F-1 CHANDRA.jpg'),
('Chilli F-1 Pranjal', 450, 'seeds', '/static/images/F-1 Pranjal Manbhari-Chilli.jpg'),
('Watermelon F-1 Virat 656', 650, 'seeds', '/static/images/F-1 virat 656 WATERMELON.jpg'),
('Long Brinjal', 450, 'seeds', '/static/images/LONG BRINJAL.jpg'),
('Maize African Tall', 450, 'seeds', '/static/images/MAIZE African Tall.jpg'),
('Methi', 550, 'seeds', '/static/images/METHI.JPG'),
('Mustard Varuna', 550, 'seeds', '/static/images/MUSTARD Varuna.jpg'),
('Okra Bhendi', 450, 'seeds', '/static/images/OKRA(BHENDI).jpg'),
('Onion Phule Samarth', 550, 'seeds', '/static/images/Onion Phule Samarth.jpg'),
('NA-25 Organic Manure', 850, 'fertilizers', '/static/images/ORGANIC MANURE.jpg'),
('ADP-25', 850, 'fertilizers', '/static/images/ADP-25.jpg'),
('ARSH-54', 850, 'fertilizers', '/static/images/ARSH-54.jpg'),
('BMS-54', 850, 'fertilizers', '/static/images/BMS-54.jpg'),
('Phosphate Rich Organic Manure', 850, 'fertilizers', '/static/images/PHOSPHATE RICH ORGANIC MANURE.jpg'),
('Potash Derived', 850, 'fertilizers', '/static/images/POTASH DERIVED.jpg'),
('PRATHA-11', 850, 'fertilizers', '/static/images/PRATHA-11.jpg'),
('Vermicompost', 850, 'fertilizers', '/static/images/VERMICOMPOST.jpg'),
('Palak All Green', 550, 'seeds', '/static/images/PALAK ALL Green.jpg'),
('Pusa Jwala Chilli', 550, 'seeds', '/static/images/PUSA JWALA CHILLI.jpg'),
('Pusa Rudra Carrot', 550, 'seeds', '/static/images/PUSA RUDRA CARROT.jpg'),
('Pusa Sadabahar Chilli', 550, 'seeds', '/static/images/PUSA SADABAHAR CHILLI.jpg'),
('Radish Pusa Chetaki', 550, 'seeds', '/static/images/RADISH PUSA CHETAKI.jpg'),
('Ridge Gourd', 550, 'seeds', '/static/images/RIDGE GOURD.jpg'),
('Rounded Brinjal', 550, 'seeds', '/static/images/ROUNDED BRINJAL.jpg'),
('Shubra King', 550, 'flowers', '/static/images/SHUBRA KING.jpg'),
('Yellow Marigold Premium', 550, 'flowers', '/static/images/YELLOW MARIGOLD.jpg'),
('Soybean KDS-726', 550, 'seeds', '/static/images/Soybean KDS-726.jpg'),
('Suryabindu', 550, 'seeds', '/static/images/SURYABINDU.jpg'),
('Suryodayi', 550, 'flowers', '/static/images/SURYODAYI.jpg'),
('Tinda', 550, 'seeds', '/static/images/TINDA.jpg');
SELECT * FROM products;

-- cart session--
use indumai;
CREATE TABLE cart (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL
);
SHOW TABLES;
SELECT * FROM cart;
SELECT * FROM users;
DESCRIBE users;
INSERT INTO users (name, email, password)
VALUES ('Admin User', 'admin@gmail.com', 'its.pdv.0410');
INSERT INTO users (name, email, password)
VALUES ('Pallavi', 'pallavi@gmail.com', 'its.pdv.0410');
USE indumai;

CREATE TABLE contact (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    total_amount INT,
    status VARCHAR(50) DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    product_id INT,
    quantity INT,
    price INT
);
CREATE TABLE blog (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200),
    content TEXT,
    image VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
delete from cart;
delete from users;

INSERT INTO users (name, email, password)
VALUES 
('Admin User', 'admin@gmail.com', 'scrypt:32768:8:1$daNTGlIXXbpnnz8p$d48c3fa31aa1b16bc9ee10660ba55e7f26fcce081f0b30bc7cd4f8b8dae5093efbb5d2b48c4781ecea27c3aad67fb8adbdf18a7f336a83c5fb335d765ccc6ede'),
('Pallavi', 'pallavi@gmail.com', 'scrypt:32768:8:1$LSaTGUTHfYdgFibQ$23ec7746314c97690461bdac336b4cc39cb01f74c01b89af7315870568e0c30175cc650bf9897e361283a8cc73e52635e514b1ab6148bc059cf6c2fcae541a21');
ALTER TABLE users ADD COLUMN is_admin TINYINT(1) DEFAULT 0;
UPDATE users SET is_admin = 1 WHERE email = 'admin@gmail.com';
UPDATE users 
SET password = 'scrypt:32768:8:1$4OGKj5VP9ntbeEeb$309103a6cc92a0d434e78eddb34183dfbaca0ac34b4a9113ec3b41f6f19ebc3543b5362389a5e84d4a9300d915818b1afce0535fde73e10c00989c569b858768'
WHERE email = 'admin@gmail.com';
ALTER TABLE orders
ADD COLUMN current_location VARCHAR(255) DEFAULT 'Warehouse';

ALTER TABLE contact ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

INSERT INTO contact (name, email, message) VALUES (name, email, message);
USE indumai;
show tables;
DESCRIBE contact;
INSERT INTO contact (name, email, message)
VALUES ('Test User', 'test@example.com', 'This is a test message.');
SELECT * FROM contact;
show tables;

