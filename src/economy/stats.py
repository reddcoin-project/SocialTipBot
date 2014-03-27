__author__ = 'bren'


from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, Numeric, UnicodeText
from sqlalchemy.pool import SingletonThreadPool

from datetime import datetime
import pytz
import pandas as pd


class Economy:
    metadata = MetaData()

    def __init__(self, dsn_url):
        """
        Pass a DSN URL conforming to the SQLAlchemy API
        """
        self.dsn_url = dsn_url
        self.db = self.connect()

    def connect(self):
        """
        Return a connection object
        """
        engine = create_engine(self.dsn_url, echo_pool=True, poolclass=SingletonThreadPool,
                               execution_options={'autocommit': True})
        self.metadata.create_all(engine)
        return engine.connect()

    def top_tippers(self, limit=100):
        sql = "SELECT from_user as user, sum(coin_val) AS amount FROM t_action WHERE type = 'givetip' "
        sql += "AND state != 'failed' GROUP BY from_user ORDER BY amount DESC LIMIT ?"
        sqlexec = self.db.execute(sql, limit)
        results = pd.DataFrame(sqlexec.fetchall(), columns=sqlexec.keys())
        return results

    def top_receivers(self, limit=100):
        sql = "SELECT to_user as user, sum(coin_val) AS amount FROM t_action WHERE type = 'givetip' "
        sql += "AND state = 'completed' GROUP BY to_user ORDER BY amount DESC LIMIT ?"
        sqlexec = self.db.execute(sql, limit)
        results = pd.DataFrame(sqlexec.fetchall(), columns=sqlexec.keys())
        return results

    def recent_transactions(self, state, limit=100):
        sql = "SELECT created_utc AS timestamp, from_user, to_user, coin_val AS amount, state FROM t_action "
        sql += "WHERE type = 'givetip' AND state = ? ORDER BY timestamp DESC LIMIT ?"
        sqlexec = self.db.execute(sql, [state, limit])
        results = pd.DataFrame(sqlexec.fetchall(), columns=sqlexec.keys())
        dts = map(datetime.fromtimestamp, results['timestamp'])
        results['timestamp'] = map(pytz.utc.localize, dts)
        return results


if __name__ == '__main__':
    dsn_url = 'sqlite:///../db/twitter-live1.db'
    economy = Economy(dsn_url)
    tippers = economy.top_tippers()
    receivers = economy.top_receivers()
    transactions = economy.recent_transactions('completed')