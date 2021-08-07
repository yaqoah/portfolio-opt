import os
import getpass
from dotenv import load_dotenv
import mysql.connector as db

load_dotenv()  # prepare environment variables

mysql_host = os.getenv('MYSQL_HOST')
mysql_user = os.getenv("MYSQL_USER")
mysql_password = getpass.getpass(prompt='Password: ')
mysql_database = os.getenv("MYSQL_DB")
conn = db.connect(user=mysql_user,
                  password=mysql_password,
                  host=mysql_host,
                  database=mysql_database)
cursor = conn.cursor()

# ..
