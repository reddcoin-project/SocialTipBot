import datetime as datetime

import bittrex.bittrex as bittrex
import bitcoincom.bitcoin_com as bitcoin_com
from datetime import datetime
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, Numeric, UnicodeText
from sqlalchemy.pool import SingletonThreadPool
import yaml

# connect to database
metadata = MetaData()
#dsn_url = 'sqlite:///../db/twitter-live1.db'
with open(r'../conf/db.yml') as file:
    conf = yaml.full_load(file)

dsn_url = "mysql+mysqldb://%s:%s@%s:%s/%s?charset=utf8" % (conf["auth"]["user"], conf["auth"]["password"], conf["auth"]["host"], conf["auth"]["port"], conf["auth"]["dbname"])
engine = create_engine(dsn_url, echo_pool=True, poolclass=SingletonThreadPool,
                       execution_options={'autocommit': True})
metadata.create_all(engine)
db = engine.connect()


def midpoint(p1, p2):
    return (p1+p2)/2

def find(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    return -1

print("Retrieving Bittrex history rates")
pAPI = bittrex.PublicAPI(bittrex.API_V3_0)
prices = {}
pricesRDDBTC = []


for year in range(2014,2021):
    status, result = pAPI.get_market_history('RDD-BTC', candleType='TRADE', candleInterval='DAY_1', year=year)
    pricesRDDBTC = pricesRDDBTC + result

print("Done(): Retrieving Bittrex history rates")


print("Retrieving Bittrex recent rates")
status, recent = pAPI.get_recent('RDD-BTC', candleType='TRADE', candleInterval='DAY_1')
print("Done(): Retrieving Bittrex recent rates")

# add elements from recent list to history list
print("Combining history and recent Bittrex rates")
comparedate = datetime.strptime(pricesRDDBTC[-1]['startsAt'], '%Y-%m-%dT%H:%M:%SZ')
for day in recent:
    recentdate = datetime.strptime(day['startsAt'], '%Y-%m-%dT%H:%M:%SZ')
    if recentdate > comparedate:
        pricesRDDBTC.append(day)
print("Done(): Combining history and recent Bittrex rates")

print("Retrieving Bitcoin.com rates")
pAPIBTC = bitcoin_com.PublicAPI(bitcoin_com.API_V2_0)
pricesUSDBTC = []

for year in range(2014,2022):

    if year == 2014:
        startdate = datetime.strptime(pricesRDDBTC[0]['startsAt'], '%Y-%m-%dT%H:%M:%SZ')
    else:
        startdate = datetime(year, 1, 1)
    enddate = datetime(year, 12, 31, 23, 59, 59)
    status, result = pAPIBTC.get_candles('BTCUSD', 'D1', start=startdate.isoformat(), till = enddate.isoformat(), limit=400)
    pricesUSDBTC = pricesUSDBTC + result

print("Done(): Retrieving Bitcoin.com rates")

# Normalise the dates to the same format to aid searching
print("Normalising Bitcoin.com dates")
for day in pricesUSDBTC:
    datestamp = datetime.strptime(day['timestamp'], '%Y-%m-%dT%H:%M:%S.000Z')
    datestamp_str = datestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
    day['timestamp'] = datestamp_str

print("Done(): Normalising Bitcoin.com dates")

print("Generating combined rates data")
coin_rates = []
indexnext = 0
for day in pricesRDDBTC:
    index = find(pricesUSDBTC, 'timestamp', day['startsAt'])
    if index != indexnext:
        # element was missing, copy and insert a dummy/calculated element
        elem = pricesUSDBTC[indexnext-1].copy()
        elem['timestamp'] = day['startsAt']
        pricesUSDBTC.insert(indexnext, elem)
        index = find(pricesUSDBTC, 'timestamp', day['startsAt'])

    val_element = {}
    val_element['timestamp'] = day['startsAt']
    val_element['rdd_high'] = day['high']
    val_element['rdd_low'] = day['low']
    val_element['rdd_mid'] = "{:.8f}".format(midpoint(float(day['high']), float(day['low'])))
    val_element['fiat_high'] = pricesUSDBTC[index]['max']
    val_element['fiat_low'] = pricesUSDBTC[index]['min']
    val_element['fiat_mid'] = "{:.3f}".format(midpoint(float(pricesUSDBTC[index]['max']), float(pricesUSDBTC[index]['min'])))
    val_element['coin_val'] = "{:.8f}".format(float(val_element['rdd_mid']) * float(val_element['fiat_mid']))

    coin_rates.append(val_element)
    indexnext = index + 1

print("Done(): Generating combined rates data")

print("Query Database")
sql = "SELECT created_utc, type, state, from_user, to_user, coin_val, coin, fiat_val, fiat, msg_id FROM t_action WHERE type='givetip'"

for sqlrow in db.execute(sql):
    dt1 = datetime.fromtimestamp(sqlrow['created_utc']).replace(hour=0, minute=0, second=0, microsecond=0)
    datestamp_str = dt1.strftime('%Y-%m-%dT%H:%M:%SZ')
    index = find(coin_rates,'timestamp', datestamp_str)
    element = coin_rates[index]
    fiat_val = float(element['coin_val']) * float(sqlrow['coin_val'])

    sql_update = "UPDATE t_action SET fiat_val=%s, fiat=%s WHERE type=%s AND msg_id=%s"
    fiat = 'usd'
    actiontype = 'givetip'

    try:
        sqlexec = db.execute(sql_update, [fiat_val, fiat, actiontype, sqlrow['msg_id']])
        if sqlexec.rowcount <= 0:
            raise Exception("query didn't affect any rows")
    except Exception as e:
        print("CtbAction::update(%s): error executing query <%s>: %s", sqlrow['msg_id'],
                 sql_update % (fiat_val, fiat, actiontype, sqlrow['msg_id']))
        raise

    print("< CtbAction::update(%s) DONE", sqlrow['msg_id'])

print("Done(): Query Database")
