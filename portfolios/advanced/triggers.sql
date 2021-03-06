-- only upon inserting, deleting handled in queries/procedures.sql

CREATE TRIGGER investment_date
BEFORE INSERT ON investments
FOR EACH ROW
BEGIN
    IF NEW.date_listed IS NULL THEN
        SET NEW.date_listed := CURDATE();
    END IF;
END $$