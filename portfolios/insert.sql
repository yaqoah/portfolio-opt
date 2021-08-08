-- SET FOREIGN_KEY_CHECKS = 0;
-- TRUNCATE TABLE assets;
-- TRUNCATE TABLE clients;
-- SET FOREIGN_KEY_CHECKS = 1;
INSERT INTO assets
	(asset_class)
VALUES 
	('Cash and cash equivalent'), 
    ('Bonds'), 
    ('Stocks'),
    ('Real Estate'), 
    ('Currency'),
    ('Sinking Fund'),
    ('Pension Fund'),
    ('Long-term notes'), 
    ('Inventory'), 
    ('Art collection'),
    ('Precious metals'), 
    ('Rare earth metals'), 
    ('Real Property'), 
    ('Commodity'), 
    ('Futures'), 
    ('Infrastructure');
INSERT INTO clients
	(c_name, c_location, c_mobile, c_email, contract_type)
VALUES
	('Sophia Joseph', 'Chicago', '+1 312 649 5541', 'thesophiejo@gmail.com', 'flexible'),
    ('Faris Al-Zaabi', 'Dubai', '+971 50 5472957', 'FarisAl@hotmail.com', 'long-term'),
    ('Chongxi Ma', 'Hong Kong', '+852 2360 3382', 'xima@baidu.cn', 'long-term'),
    ('Williams Brown', 'New York', '+1 718 963 0375', 'williambr@brown.edu', 'short-term'),
    ('Hazlina Wong', 'Singapore', '+65 8458 2573', 'won8lina@gmail.com', 'flexible'),
    ('Mike Karlsson', 'Boston', '+1 617 918 4243', 'Mikesson-pr1v@gmail.com', 'flexible');