CREATE OR REPLACE VIEW client_comp AS
SELECT CONCAT ( 'ClIENT ID: ',
       clients.c_id)                        AS `Client id`,
       CONCAT ( ' CLIENT NAME: ',
       clients.c_name )                     AS `Client name`,
       clients.c_mobile                     AS `Mobile`,
       clients.c_email                      AS `Email`,
       CONCAT ( clients.contract_type,
       ' contract, max profits in ',
       clients.investment_horizon,
       ' years' )                           AS `Description`,
       CONCAT ( 'Platforms in use: ',
       cid_platforms.platforms)             AS `Platforms`,
       CONCAT ( 'Portfolio Asset Classes: ',
       aid_classes.asset_classes )          AS `Invested Asset-Classes`
FROM   clients,
       (
                SELECT   client_id                 AS cid_p,
                         GROUP_CONCAT( DISTINCT(platform) ) AS platforms
                FROM     investments
                GROUP BY cid_p )
     AS
       cid_platforms,
       (
                  SELECT     client_id        AS cid_c,
                             GROUP_CONCAT( DISTINCT(asset_class) ) AS asset_classes
                  FROM       (assets
                  INNER JOIN investments
                  USING      (asset_id))
                  GROUP BY   cid_c )

     AS
       aid_classes
WHERE clients.c_id = cid_platforms.cid_p AND clients.c_id = aid_classes.cid_c
ORDER BY clients.c_id;