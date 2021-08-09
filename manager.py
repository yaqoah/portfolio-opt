import os
import getpass
from dotenv import load_dotenv
import mysql.connector as db
from mysql.connector.errors import ProgrammingError

# :::::::::::::::::::::::
load_dotenv() # prepare environment variables
# :::::::::::::::::::::::

mysql_host = os.getenv('MYSQL_HOST')
mysql_user = os.getenv("MYSQL_USER")
mysql_password = getpass.getpass(prompt='Password: ')
mysql_database = os.getenv("MYSQL_DB")
conn = db.connect(user=mysql_user,
                  password=mysql_password,
                  host=mysql_host)
cursor = conn.cursor()


def build():
    cursor.execute('CREATE DATABASE portfolios_db;')
    cursor.execute('USE portfolios_db;')

    delimiter: list = [';', ';']

    for k, cmds in enumerate([
        open('./portfolios/create.sql'),
        open('./portfolios/insert.sql')
    ]):
        for query in cmds.read().split(delimiter[k]):
            if query:
                cursor.execute(query + ';')

    conn.commit()


try:
    cursor.execute('DROP DATABASE IF EXISTS portfolios_db')
    cursor.execute('USE ' + mysql_database + ';')
except ProgrammingError as pr:
    if pr.errno == 1049:  # database doesn't exist
        build()
