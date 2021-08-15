import decimal
import os
import getpass
import numpy as np
from enum import Enum
from itertools import repeat, combinations
from dotenv import load_dotenv
import mysql.connector as db
from mysql.connector.errors import ProgrammingError

# ::::::::::::::::::::::::::::::::::::::::::::::
load_dotenv()  # prepares environment variables
# ::::::::::::::::::::::::::::::::::::::::::::::

mysql_host = os.getenv('MYSQL_HOST')
mysql_user = os.getenv("MYSQL_USER")
mysql_password = "juniorito11"
# getpass.getpass(prompt='Password: ')
mysql_database = os.getenv("MYSQL_DB")
conn = db.connect(user=mysql_user,
                  password=mysql_password,
                  host=mysql_host)
cursor = conn.cursor()


def build():
    cursor.execute('CREATE DATABASE portfolios_db;')
    cursor.execute('USE portfolios_db;')

    delimiter: list = [';', ';', '$$', ";", ';']

    for k, cmds in enumerate([
        open('./portfolios/create.sql'),
        open('./portfolios/insert.sql'),
        open('./portfolios/advanced/queries/procedures.sql'),
        open('./portfolios/advanced/queries/calls.sql'),
        open('./portfolios/advanced/views.sql')
    ]):
        for query in cmds.read().split(delimiter[k]):
            try:
                cursor.execute(query + ';')
            except ProgrammingError as blank:
                if blank.errno == 1065:
                    continue
    conn.commit()


try:
    cursor.execute('DROP DATABASE IF EXISTS portfolios_db')
    cursor.execute('USE ' + mysql_database + ';')
except ProgrammingError as pr:
    if pr.errno == 1049:  # database doesn't exist
        build()


class Client:
    @staticmethod
    def investments_count(client_id: int):
        query_all = cursor.callproc('all_client_investments', [client_id])
        for investments in cursor.stored_results():
            investments.fetchall()

        return investments.rowcount

    @staticmethod
    def assets_count(client_id: int):
        total_aclasses = [count for count in
                          cursor.callproc('all_asset_classes',
                                          [client_id])][0]
        client_classes = [c_count for c_count in
                          cursor.callproc('client_asset_classes',
                                          list(repeat(client_id, 2)))][0]

        return total_aclasses, client_classes


class Levels(Enum):
    POOR = '\033[91m' + 'poorly diverse' + '\033[0m'
    FAIR = '\033[1m' + 'insufficiently diverse' + '\033[0m'
    GOOD = '\033[4m' + 'just about diverse' + '\033[0m'
    VERY_GOOD = '\033[93m' + "well diverse" + '\033[0m'
    EXCELLENT = '\033[92m' + "highly diverse" + '\033[0m'


def diversity(client_id: int):
    stakes = Client.investments_count(client_id)
    classes = Client.assets_count(client_id)
    total_volatility = cursor.callproc('find_volatility',
                                       list(repeat(client_id, 2)))[1]

    diversity = (total_volatility / stakes) * 100

    if stakes in range(22, 200) and classes[1] >= 3:
        nominal_diversity = Levels.EXCELLENT.value
    elif stakes in range(18, 25) and classes[1] in range(2, 4):
        nominal_diversity = Levels.VERY_GOOD.value
    elif stakes in range(15, 18) and classes[1] in range(4, 16):
        nominal_diversity = Levels.GOOD.value
    elif stakes in range(9, 15):
        nominal_diversity = Levels.FAIR.value
    else:
        nominal_diversity = Levels.POOR.value

    return (
        f"(id:{client_id}) Client's portfolio volatility is {round(diversity, 3)}%\n"
        f"The volatility of the maximum diversification portfolio is 8%\n"
        f"\nNominal (or face) value volatility indicates "
        f"investing portfolio is {nominal_diversity}.\n"
        f"Based on two criterias: \t 1) "
        f"Investments split on to {classes[1]} asset class(es)\n"
        f" \t \t \t \t 2) Total number of investments is {stakes}, "
        f"when optimum for maximum diversification is 30."
    )


def view_clients():
    cursor.execute('SELECT * FROM client_comp;')
    clients = cursor.fetchall()
    for client in clients:
        print(client)


def covariances(arr):
    assets_covariance = []
    co_assets = list(combinations(arr, 2))
    for pair in co_assets:
        covariance = np.sqrt(pair[0]) * np.sqrt(pair[1])
        assets_covariance.append(covariance)
    return assets_covariance


def risk():
    directed = False
    while not directed:
        check_view = input("To calculate client's portfolio risk you need Client ID.\n"
                           "Do you want to refer to view for client ID? (y/n)  ")
        affirm = ["yes", "y", "ye", "yeah", "yup", "ya"]
        deny = ["no", "n", "nope", "nah"]
        if check_view in affirm:
            view_clients()
            directed = True
        elif check_view in deny:
            directed = True
        else:
            print("type yes, no or equivalent")
            continue

        client_id = int(input("What's the valid ID of the client that you want "
                              "to check their portfolio-risk? "))
        cursor.execute(f'SELECT amount, variance FROM investments WHERE client_id = {client_id};')
        client_data = cursor.fetchall()
        amounts = []
        variance = []
        weights = []

        for index, record in enumerate(client_data):
            amounts.append(client_data[index][0])
            variance.append(client_data[index][1])

        for value in amounts:
            weights.append(value/sum(amounts))

        assets_covariance = covariances(variance)
        portfolio_variance(weights, variance, assets_covariance)
        # here sent to portfolio variance method (weights, variances, covariances)
        '''
        another_example = covariances([1, 2, 3, 4])
        print(list(combinations([1, 2, 3, 4], 2)))
        print(another_example)
        '''

        '''
        example = list(np.diag_indices(16)[0])
        test = np.array([[1, 2], [3, 4], [5, 6]])
        print(test[1:,1])
        '''


def portfolio_variance(weights, variance, covariance):
    dimension = len(weights)
    correlation_matrix = np.zeros((dimension, dimension))
    row, col = np.diag_indices(dimension)
    correlation_matrix[row, col] = np.array(variance)

    below_diag = above_diag = 1
    height_inwards = width_inwards = dimension - 1
    upper, ubound = height_inwards, width_inwards
    lower, lbound = 0, 0

    # To populate matrix with covariances around diagonal
    while height_inwards and width_inwards:
        # fill by column
        correlation_matrix[below_diag:, below_diag - 1] = covariance[lower:upper]
        below_diag += 1
        lower = upper
        height_inwards -= 1
        upper += height_inwards

        # fill by row
        correlation_matrix[above_diag - 1, above_diag:] = covariance[lbound:ubound]
        above_diag += 1
        lbound = ubound
        width_inwards -= 1
        ubound += width_inwards

    horizontal_weights_matrix = np.array(weights)
    horizontal_weights_matrix.shape = (1, dimension)
    horizontal_weights_matrix= horizontal_weights_matrix.astype('float64')

    vertical_weights_matrix = np.array(weights)
    vertical_weights_matrix.shape = (dimension, 1)
    vertical_weights_matrix = vertical_weights_matrix.astype('float64')
    result_fin = 0

    try:
        result_pre = (horizontal_weights_matrix
                      @ correlation_matrix
                      @ vertical_weights_matrix)
    except TypeError as te:
        print('error number: ', te.errno)
    else:
        result_fin = result_pre[0][0]

    print(result_fin)


risk()
