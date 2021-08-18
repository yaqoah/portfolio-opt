CREATE PROCEDURE add_investment (
    IN new_platform VARCHAR(50),
	IN new_client_id INT,
    IN new_asset_id INT,
	IN new_date_listed DATE,
    IN new_amount DECIMAL(10,2),
    IN new_volatility DECIMAL(5,4),
    IN new_variance DECIMAL(6,4) )
BEGIN
    INSERT INTO investments
        (platform, client_id,
         asset_id, date_listed,
         amount, volatility,variance)
    VALUES
        (new_platform, new_client_id,
         new_asset_id, new_date_listed,
         new_amount, new_volatility, new_variance);
END $$


CREATE PROCEDURE add_client (
    IN name TEXT(30),
    IN mobile VARCHAR(20),
    IN email VARCHAR(320),
    IN client_contract TEXT(12),
    IN client_investment_horizon INT(2))
BEGIN
    INSERT INTO clients
        (c_name, c_mobile, c_email,
        contract_type, investment_horizon)
    VALUES
        (name, mobile, email, client_contract,
        client_investment_horizon);
END $$


CREATE PROCEDURE delete_client(
        IN id INT,
        IN name TEXT(30))
BEGIN
    DELETE
        FROM clients
    WHERE clients.c_id = id OR clients.c_name = name;

    ALTER TABLE clients AUTO_INCREMENT = id;
END $$


CREATE PROCEDURE all_client_investments (
    IN id INT)
BEGIN
    SELECT *
        FROM investments
    WHERE client_id = id;
END $$


CREATE PROCEDURE all_asset_classes (
    OUT classes INT)
BEGIN
    SELECT COUNT(asset_id)
        INTO classes
    FROM assets;
END $$


CREATE PROCEDURE client_asset_classes (
    IN id INT,
    OUT clients_assets INT)
BEGIN
    SELECT COUNT(DISTINCT(asset_id))
            INTO clients_assets
        FROM investments
    WHERE client_id = id;
END $$


CREATE PROCEDURE find_volatility (
    IN id INT,
    OUT total_volatility FLOAT )
BEGIN
    DECLARE vol_sum FLOAT;

    SELECT SUM(volatility)
        INTO vol_sum
            FROM investments
    WHERE client_id = id;

    SET total_volatility = vol_sum;

END $$


CREATE PROCEDURE assets_amount_variance (
    IN id INT)
BEGIN
    SELECT amount, variance
        FROM investments
    WHERE id = client_id;

END $$