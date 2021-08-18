import os
import mysql.connector as db
from mysql.connector.errors import ProgrammingError
import numpy as np
import matplotlib.pyplot as plt
import proplot as pplt
from dotenv import load_dotenv
from itertools import repeat, combinations
from enum import Enum
import getpass


# :::::::::: load ::::::::::
load_dotenv()
# ::::: configurations :::::

mysql_host = os.getenv('MYSQL_HOST')
mysql_user = os.getenv("MYSQL_USER")
mysql_password = getpass.getpass(prompt='Password: ')
mysql_database = os.getenv("MYSQL_DB")

conn = db.connect(user=mysql_user,
                  password=mysql_password,
                  host=mysql_host)
cursor = conn.cursor()


def build():
    """
    Runs all queries associated with creating, inserting and modifying
    managed clients investing portfolios,and commits transactions
    """

    cursor.execute('CREATE DATABASE ' + mysql_database + ';')
    cursor.execute('USE ' + mysql_database + ';')

    delimiter: list = [';', ';', '$$', ";", ';', '$$']

    for k, sqls in enumerate([
        open('./portfolios/create.sql'),
        open('./portfolios/insert.sql'),
        open('./portfolios/advanced/queries/procedures.sql'),
        open('./portfolios/advanced/queries/calls.sql'),
        open('./portfolios/advanced/views.sql'),
        open('./portfolios/advanced/triggers.sql')
    ]):
        for query in sqls.read().split(delimiter[k]):
            try:
                cursor.execute(query + ';')
            except ProgrammingError as blank:
                if blank.errno == 1065:
                    continue
    conn.commit()


try:
    cursor.execute('DROP DATABASE IF EXISTS ' + mysql_database + ';')
    cursor.execute('USE ' + mysql_database + ';')
except ProgrammingError as pr:
    if pr.errno == 1049:  # database doesn't exist
        build()


class Client:
    @staticmethod
    def investments_count(client_id: int):
        """
        queries the database for client's total investments
        :param client_id: id given to client by system
        :return:          total number of investments of client
        """

        cursor.callproc('all_client_investments', [client_id])
        for investments in cursor.stored_results():
            investments.fetchall()

        return investments.rowcount

    @staticmethod
    def assets_count(client_id: int):
        """
        queries the database for number of total asset classes,
        and number asset classes client invested in
        :param client_id: id given to client by system
        :return:          a tuple for total asset classes,
                          client asset classes
        """

        total__classes = [count for count in
                          cursor.callproc('all_asset_classes', [client_id])][0]
        client_classes = [c_count for c_count in
                          cursor.callproc('client_asset_classes',
                                          list(repeat(client_id, 2)))][0]

        return total__classes, client_classes


class Levels(Enum):
    POOR = '\033[91m' + 'poor in diversity'
    FAIR = '\033[1m' + 'insufficient in diversity'
    GOOD = '\033[4m' + 'just about diverse'
    VERY_GOOD = '\033[93m' + "well diverse"
    EXCELLENT = '\033[92m' + "highly diverse"


def diversity(client_id: int):
    """
    Determines diversity of portfolio by checking against
    three benchmarks
    :param client_id: id of client given by system
    :return:          diversity value for each benchmark study
    """

    assets = Client.investments_count(client_id)
    classes = Client.assets_count(client_id)
    total_volatility = cursor.callproc('find_volatility',
                                       list(repeat(client_id, 2)))[1]

    diversity_per = (total_volatility / assets) * 100

    if assets in range(22, 200) and classes[1] >= 3:
        nominal_diversity = Levels.EXCELLENT.value
    elif assets in range(18, 25) and classes[1] == 3:
        nominal_diversity = Levels.VERY_GOOD.value
    elif assets in range(15, 18) and classes[1] in range(4, 16):
        nominal_diversity = Levels.GOOD.value
    elif assets in range(9, 15):
        nominal_diversity = Levels.FAIR.value
    else:
        nominal_diversity = Levels.POOR.value

    print(
        f"\n(id:{client_id}) Client's portfolio volatility "
        f"is {round(diversity_per, 3)}%\n"
        "The volatility of the maximum "
        "diversification portfolio is 8%\n"
        f"Nominal (or face) value volatility indicates "
        f"investing portfolio is {nominal_diversity}.\n"
        f"Based on two criterias: \t 1) "
        f"Investments split on to {classes[1]} asset class(es)\n"
        f" \t \t \t \t 2) Total number of investments is {assets}, "
        "when optimum for maximum diversification is 30."
    )


def view_clients():
    cursor.execute('SELECT * FROM client_comp;')
    clients = cursor.fetchall()
    for client in clients:
        print(client)


def covariances(variance):
    """
    calculates relation of returns between
    pairs of assets by formula
    :param variance: list of relations of return of assets with themselves
    :return:         list of all relations (value) between asset pairs
    """

    assets_covariance = []
    co_assets = list(combinations(variance, 2))
    for pair in co_assets:
        covariance = np.sqrt(pair[0]) * np.sqrt(pair[1])
        assets_covariance.append(covariance)

    return assets_covariance


def get_values(client_id: int):
    """
    Queries amounts invested and its respective weight,
    variance of each asset with itself
    and covariance of all assets together
    :param client_id: id associated with client
    :yield:           lists of - amounts invested, their weights,
                      variance and covariance values of assets
    """

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

    conn.close()
    cursor.close()

    yield amounts
    yield weights
    yield variance
    yield assets_covariance


def portfolio_variance(weights, variance, covariance):
    """
    calculates portfolio risk
    :param weights:    list of weights of every asset in portfolio
    :param variance:   list of variance of returns for asset with itself
    :param covariance: list of covariance between all assets in portfolio
    :return:           value for portfolio variance (risk)
    """

    dimension = len(weights)
    correlation = np.zeros((dimension, dimension))

    # populate diagonal for correlation matrix
    row, col = np.diag_indices(dimension)
    correlation[row, col] = np.array(variance)

    # To populate correlation matrix with covariances around diagonal
    below_diag = above_diag = 1
    height_inwards = width_inwards = dimension - 1
    upper, ubound = height_inwards, width_inwards
    lower, lbound = 0, 0
    while height_inwards and width_inwards:
        # fill by column
        correlation[below_diag:, below_diag - 1] = covariance[lower:upper]
        below_diag += 1
        lower = upper
        height_inwards -= 1
        upper += height_inwards

        # fill by row
        correlation[above_diag - 1, above_diag:] = covariance[lbound:ubound]
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

    result = 0

    try:
        result_pre = (horizontal_weights_matrix
                      @ correlation
                      @ vertical_weights_matrix)
    except TypeError as te:
        print("Matrix multiplication: {0}".format(te))
    else:
        result = result_pre[0][0]

    return result


def point(amounts, weights, variance, covariance):
    """
    Calculates expected return and portfolio risk (variance)
    :param amounts:    list of all amounts invested by client
    :param weights:    list of weight of investment of entire portfolio
    :param variance:   list of variance of each asset with itself
    :param covariance: list of relationships of returns between
                       assets
    :return:           coordinates of single point
                       in graph in the form
                       ((risk)standard deviation, expected return)
    """

    means = []
    for j, asset_price in enumerate(amounts):
        asset_price = float(asset_price)

        # approx 4 years of closed prices
        closed_prices = 8

        stock_prices = []
        while closed_prices:
            price_change = asset_price * float(variance[j])
            closing = np.random.uniform(asset_price,
                                        asset_price +
                                        price_change, 1)[0]
            stock_prices.append(closing)
            closed_prices -= 1
        means.append(stock_prices)

    for n, asset_closings in enumerate(means):
        stock_mean = np.mean(asset_closings)
        means[n] = stock_mean

    prices_means_matrix = np.array(means)
    prices_means_matrix.shape = (1, len(variance))
    prices_means_matrix = prices_means_matrix.astype('float64')

    weights.shape = (len(variance), 1)
    weight_matrix = weights.astype('float64')

    pvariance = portfolio_variance(weights, variance, covariance)
    sdeviation = np.sqrt(pvariance)
    preturn = weight_matrix @ prices_means_matrix
    returns = preturn.sum()

    expected_return = ((returns - float(sum(amounts))) / float(sum(amounts)))

    return sdeviation, expected_return


def risk_return_tradeoff(risks, returns, safest):
    """
    chooses portfolio that has low risk and high returns
    and its respective optimum value of return or risk
    :param risks:   list of all x_values
    :param returns: list of all y_values
    :param safest:  boolean for which calculation to make
                    (0: highest return, 1: lowest risk)
    :yield:         points for lowest risk, highest return
                    and remaining portfolios
    """

    winners_xs, winners_ys = [], []
    ratios = []
    if safest:
        for x in range(50):
            least_risky = min(risks)
            position = risks.index(least_risky)
            matching_return = returns[position]

            winners_xs.append(least_risky)
            winners_ys.append(matching_return)

            risks.remove(least_risky)
            returns.remove(matching_return)

            ratio = least_risky / matching_return
            ratios.append(ratio)
    else:
        for y in range(50):
            highest_return = max(returns)
            position = returns.index(highest_return)
            port_risk = risks[position]

            winners_xs.append(port_risk)
            winners_ys.append(highest_return)

            risks.remove(port_risk)
            returns.remove(highest_return)

            ratio = port_risk / highest_return
            ratios.append(ratio)

    index = ratios.index(min(ratios))
    winner_risk = winners_xs[index]
    winner_return = winners_ys[index]
    yield [winner_risk, winner_return]

    winners_xs.remove(winner_risk)
    winners_ys.remove(winner_return)

    risks.extend(winners_xs)
    yield risks

    returns.extend(winners_ys)
    yield returns


def optimisation_analysis(amounts, weights, variance, covariance):
    """
    Generates all graph portfolios and obtains optimum portfolios
    :param amounts:   list of asset prices
    :param weights:   list of associated weight in portfolio
    :param variance:  value for relationship of return of asset
    :param covariance:value for variance between assets
    :yield:           client portfolio point,
                      all portfolios coordinates,
                      optimum portfolio coordinates
    """
    x_coords, y_coords = [], []
    arr_weights = np.array(weights)
    clients_x, clients_y = point(amounts, arr_weights,
                                 variance, covariance)
    x_coords.append(clients_x)
    y_coords.append(clients_y)

    for portfolio in range(300):
        arbitrary_weights = np.random.dirichlet(np.ones(len(variance)), 1)
        temp_amounts = np.array(arbitrary_weights * (float(sum(amounts))))
        p_amounts = temp_amounts.tolist()

        portfolio_x, portfolio_y = point(p_amounts[0], arbitrary_weights,
                                         variance, covariance)

        x_coords.append(portfolio_x)
        y_coords.append(portfolio_y)

    # for least risky portfolio
    l_risk = risk_return_tradeoff(x_coords, y_coords, 1)
    opt_risk = next(l_risk)
    new_xs = next(l_risk)
    new_ys = next(l_risk)

    # for highest return portfolio
    h_return = risk_return_tradeoff(new_xs, new_ys, 0)
    opt_reward = next(h_return)
    all_xs = next(h_return)
    all_ys = next(h_return)

    yield [clients_x, clients_y]
    yield [opt_risk, opt_reward]
    yield [all_xs, all_ys]


def get_id():
    """CLI for the client id of client to study and analyse"""

    directed = False
    valid = False
    affirm = ["yes", "y", "ye", "yeah", "yup", "ya"]
    deny = ["no", "n", "nope", "nah"]

    while not directed:
        check_view = input("To calculate client's portfolio risk "
                           "you need Client ID.\n"
                           "Do you want to refer to a table view "
                           "for client ID? (y/n)  ")
        if check_view in affirm:
            view_clients()
            directed = True
        elif check_view in deny:
            directed = True
        else:
            print("type yes, no or equivalent")

    while not valid:
        try:
            client_id = int(input("What's the valid ID of the client that you "
                                  "want to study? "))
        except ValueError as ve:
            print("give id as number")
        else:
            valid = True

    return client_id


def albarzakh():
    """A bridge to connect code"""

    client_id = get_id()
    diversity(client_id)

    portfolio_computatives = get_values(client_id)
    amounts = next(portfolio_computatives)
    weights = next(portfolio_computatives)
    variance = next(portfolio_computatives)
    assets_covariance = next(portfolio_computatives)

    return optimisation_analysis(amounts,
                                 weights,
                                 variance,
                                 assets_covariance)


data = albarzakh()
client_coords = next(data)
optimum_coords = next(data)
remaining_coords = next(data)

plt.style.use('Solarize_Light2')

plt.grid(color='#BEA100',
         linestyle='dotted',
         linewidth=0.4)
plt.xlabel("Portfolio Standard Deviation (risk)",
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

plt.plot(np.array(remaining_coords[0]),
         np.array(remaining_coords[1]),
         "o",
         markersize=4,
         mfc="none",
         color="olive",
         label='Achievable Client Portfolio')
plt.plot(np.array(client_coords[0]),
         np.array(client_coords[1]),
         marker="X",
         markersize=9,
         color="black",
         label="Client's Portfolio")
plt.plot(np.array(optimum_coords[0][0]),
         np.array(optimum_coords[0][1]),
         marker="$L$",
         markersize=7,
         color="crimson",
         label='Lowest Risk, Optimum Return (Portfolio)')
plt.plot(np.array(optimum_coords[1][0]),
         np.array(optimum_coords[1][1]),
         marker="$H$",
         markersize=8,
         color="darkblue",
         label='Highest Return, Optimum Risk (Portfolio)')

plt.legend()
plt.show()
