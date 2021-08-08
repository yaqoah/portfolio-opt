-- SET foreign_key_checks = 0;
-- DROP TABLE IF EXISTS assets, clients, investments;
-- SET foreign_key_checks = 1;
CREATE TABLE assets (
	asset_id INT AUTO_INCREMENT,
    asset_class TEXT(30),
    PRIMARY KEY (asset_id)
);
CREATE TABLE clients (
	c_id INT AUTO_INCREMENT, 
    c_name TEXT(30),
    c_Location VARCHAR(30),
    c_mobile VARCHAR(20) NOT NULL,
    c_email VARCHAR(320) NOT NULL,
    contract_type TEXT(12),
    UNIQUE (c_mobile),
    UNIQUE (c_email),	
    PRIMARY KEY (c_id)
);
CREATE TABLE investments (
	id INT AUTO_INCREMENT, 
	plaform VARCHAR(50),
	date_listed DATE, 
    amount DECIMAL(10,2) NOT NULL,
    CHECK (amount > 0), 
    investment_horizon TEXT(12),
    client_id INT,
    asset_id INT,
    i_description VARCHAR(80) NOT NULL, 
    UNIQUE (i_description),
    CONSTRAINT FK_assetid
    FOREIGN KEY (asset_id)
    REFERENCES assets(asset_id), 
    CONSTRAINT FK_clientid
    FOREIGN KEY (client_id)
    REFERENCES clients(c_id)
    ON DELETE CASCADE,
    PRIMARY KEY (id)
);