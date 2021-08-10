CREATE PROCEDURE add_investment (
    IN new_platform VARCHAR(50),
	IN new_client_id INT,
    IN new_asset_id INT,
	IN new_date_listed DATE,
    IN new_amount DECIMAL(10,2),
    IN new_volatility DECIMAL(5,4),
    IN new_variance DECIMAL(5,4),
    IN new_standard_deviation DECIMAL(4,3),
    IN new_details VARCHAR(80) )
BEGIN
    INSERT INTO investments
        (id, platform, client_id,
         asset_id, date_listed,
         amount, volatility,variance,
         standard_deviation,details)
    VALUES
        (new_platform, new_client_id,
         new_asset_id, new_date_listed,
         new_amount, new_volatility, new_variance,
         new_standard_deviation, new_details);
END $$
