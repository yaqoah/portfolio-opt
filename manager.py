from dotenv import load_dotenv
import mysql.connector as db
from mysql.connector.errors import ProgrammingError
import numpy as np
import matplotlib.pyplot as plt
import proplot as pplt

import os
import decimal
import getpass
from itertools import repeat, combinations
from enum import Enum

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

    delimiter: list = [';', ';', '$$', ";", ';', '$$']

    for k, cmds in enumerate([
        open('./portfolios/create.sql'),
        open('./portfolios/insert.sql'),
        open('./portfolios/advanced/queries/procedures.sql'),
        open('./portfolios/advanced/queries/calls.sql'),
        open('./portfolios/advanced/views.sql'),
        open('./portfolios/advanced/triggers.sql')
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
    POOR = '\033[91m' + 'poor in diversity' + '\033[0m'
    FAIR = '\033[1m' + 'insufficient in diversity' + '\033[0m'
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
    elif stakes in range(18, 25) and classes[1] == 3:
        nominal_diversity = Levels.VERY_GOOD.value
    elif stakes in range(15, 18) and classes[1] in range(4, 16):
        nominal_diversity = Levels.GOOD.value
    elif stakes in range(9, 15):
        nominal_diversity = Levels.FAIR.value
    else:
        nominal_diversity = Levels.POOR.value

    yield(
        f"\n(id:{client_id}) Client's portfolio volatility is {round(diversity, 3)}%\n"
        "The volatility of the maximum diversification portfolio is 8%"
          )
    yield(
        f"Nominal (or face) value volatility indicates "
        f"investing portfolio is {nominal_diversity}."
          )
    yield(
        f"Based on two criterias: \t 1) "
        f"Investments split on to {classes[1]} asset class(es)\n"
        f" \t \t \t \t 2) Total number of investments is {stakes}, "
        "when optimum for maximum diversification is 30."
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


def get_values(client_id: int):
    view = 'SELECT amount, variance FROM investments WHERE client_id ='
    cursor.execute(f'{view} {client_id};')
    client_data = cursor.fetchall()

    amounts, variance, weights = [], [], []

    for index, record in enumerate(client_data):
        amounts.append(client_data[index][0])
        variance.append(client_data[index][1])

    for value in amounts:
        weights.append(value / sum(amounts))

    assets_covariance = covariances(variance)

    return amounts, weights, variance, assets_covariance


def portfolio_variance(weights, variance, covariance):
    dimension = len(weights)
    correlation_matrix = np.zeros((dimension, dimension))
    row, col = np.diag_indices(dimension)
    correlation_matrix[row, col] = np.array(variance)

    below_diag = above_diag = 1
    height_inwards = width_inwards = dimension - 1
    upper, ubound = height_inwards, width_inwards
    lower, lbound = 0, 0

    # To populate correlation matrix with covariances around diagonal
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
    horizontal_weights_matrix = horizontal_weights_matrix.astype('float64')

    vertical_weights_matrix = np.array(weights)
    vertical_weights_matrix.shape = (dimension, 1)
    vertical_weights_matrix = vertical_weights_matrix.astype('float64')
    result_final = 0

    try:
        result_pre = (horizontal_weights_matrix
                      @ correlation_matrix
                      @ vertical_weights_matrix)
    except TypeError as te:
        print('error number: ', te.errno)
    else:
        result_final = result_pre[0][0]

    return result_final


def point(amounts, weights, variance, covariance):
    means = []
    for ratio, stock_price in enumerate(amounts):
        stock_price = float(stock_price)
        closed_prices = 8
        stock_prices = []
        while closed_prices:
            price_change = stock_price * float(variance[ratio])
            closing = np.random.uniform(stock_price,
                                        stock_price + price_change, 1)[0]
            stock_prices.append(closing)
            closed_prices -= 1
        means.append(stock_prices)
    for i, stock_closing_prices in enumerate(means):
        stock_mean = np.mean(stock_closing_prices)
        means[i] = stock_mean
    prices_means_matrix = np.array(means)
    prices_means_matrix.shape = (1, len(variance))
    amounts_matrix = np.array(amounts)
    amounts_matrix.shape = (1, len(amounts))
    weights.shape = (len(variance), 1)
    weight_matrix = weights.astype('float64')
    prices_means_matrix = prices_means_matrix.astype('float64')
    point_variance = portfolio_variance(weights, variance, covariance)
    point_standard_dev = np.sqrt(point_variance)
    point_return = weight_matrix @ prices_means_matrix
    overall = point_return.sum()
    expected_return = ((overall - float(sum(amounts))) / float(sum(amounts)))

    return point_standard_dev, expected_return


def risk_return_tradeoff(x_risk, y_return, risk_or_return):  # low risk
    potential_winner_ports = [[],
                              []]
    ratios = []
    if risk_or_return:
        for x in range(30):  # change 10 by number of portfolios provided and other for
            least_risky = min(x_risk)
            position = x_risk.index(least_risky)
            port_return = y_return[position]
            potential_winner_ports[0].append(least_risky)
            potential_winner_ports[1].append(port_return)
            x_risk.remove(least_risky)
            y_return.remove(port_return)
            ratio = least_risky / port_return
            ratios.append(ratio)
    else:
        for y in range(30):
            highest_return = max(y_return)
            position = y_return.index(highest_return)
            port_risk = x_risk[position]
            potential_winner_ports[0].append(port_risk)
            potential_winner_ports[1].append(highest_return)
            x_risk.remove(port_risk)
            y_return.remove(highest_return)
            ratio = port_risk / highest_return
            ratios.append(ratio)

    winner_ratio = ratios.index(min(ratios))
    x_risk_winner = potential_winner_ports[0][winner_ratio]
    y_return_winner = potential_winner_ports[1][winner_ratio]
    potential_winner_ports[0].remove(x_risk_winner)
    potential_winner_ports[1].remove(y_return_winner)
    x_risk.extend(potential_winner_ports[0])
    y_return.extend(potential_winner_ports[1])

    return [x_risk_winner, y_return_winner], x_risk, y_return


def optimisation_analysis(amounts, weight, variance, covariance):
    x_coord = []
    y_coord = []
    arr_weight = np.array(weight)
    current_portfolio = point(amounts, arr_weight, variance, covariance)
    x_coord.append(current_portfolio[0])
    y_coord.append(current_portfolio[1])
    for possible_portfolio in range(300):
        arb_portfolio_weighting = np.random.dirichlet(np.ones(len(variance)), 1)
        arb_amounts = np.array(arb_portfolio_weighting * (float(sum(amounts))))
        new_amounts = arb_amounts.tolist()
        x_y_portfolio_point = point(new_amounts[0],
                                    arb_portfolio_weighting,
                                    variance,
                                    covariance)
        x_coord.append(x_y_portfolio_point[0])
        y_coord.append(x_y_portfolio_point[1])
    # for least risky portfolio
    opt_risk, new_xs, new_ys = risk_return_tradeoff(x_coord, y_coord, 1)
    # for highest return portfolio
    opt_reward, final_xs, final_ys = risk_return_tradeoff(new_xs, new_ys, 0)

    return [opt_risk, opt_reward], final_xs, final_ys, [current_portfolio[0], current_portfolio[1]]


def get_id():
    directed = False
    while not directed:
        check_view = input("To calculate client's portfolio risk "
                           "you need Client ID.\n"
                           "Do you want to refer to a table view "
                           "for client ID? (y/n)  ")
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

    client_id = int(input("What's the valid ID of "
                          "the client that you want "
                          "to study? "))

    return client_id


def albarzakh():
    client_id = get_id()
    diversity_facts = diversity(client_id)
    for fact in diversity_facts:
        print(fact)
    amounts, weights, variance, assets_covariance = get_values(client_id)

    return optimisation_analysis(amounts,
                                 weights,
                                 variance,
                                 assets_covariance)


special_cords, risk_coord, return_coord, client_port = albarzakh()

ax = plt.figure()
plt.style.use('Solarize_Light2')

plt.grid(color='#BEA100',
         linestyle='dotted',
         linewidth=0.4)

plt.xlabel("Portfolio Variance",
           fontname=pplt.rc['font.fantasy'],
           fontsize=17,
           labelpad=15)
plt.ylabel("Expected Return",
           fontname=pplt.rc['font.fantasy'],
           fontsize=17,
           labelpad=15)
plt.title("P O R T F O L I O    O P T I M I S A T I O N",
          fontsize=10,
          fontname=pplt.rc['font.monospace'],
          pad=12)


plt.plot(np.array(risk_coord),
         np.array(return_coord),
         "o",
         markersize=4,
         mfc="none",
         color="olive",
         label='Possible Client Portfolios')

plt.plot(np.array(client_port[0]),
         np.array(client_port[1]),
         marker="X",
         markersize=8,
         color="black",
         label="Client's Portfolio")

plt.plot(np.array(special_cords[0][0]),
         np.array(special_cords[0][1]),
         marker="$L$",
         markersize=6,
         color="crimson",
         label='Lowest Risk, Optimum Return (Portfolio)')

plt.plot(np.array(special_cords[1][0]),
         np.array(special_cords[1][1]),
         marker="$H$",
         markersize=7,
         color="darkblue",
         label='Highest Return, Optimum Risk (Portfolio)')


plt.legend()

plt.show()

conn.close()

cursor.close()