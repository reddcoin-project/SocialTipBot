__author__ = 'bren'


from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, Numeric, UnicodeText
from sqlalchemy.pool import SingletonThreadPool

import pandas as pd


def connect_db(dsn_url):
    metadata = MetaData()
    engine = create_engine(dsn_url, echo_pool=True, poolclass=SingletonThreadPool,
                           execution_options={'autocommit': True})
    metadata.create_all(engine)
    return engine


if __name__ == '__main__':
    dsn_url = 'sqlite:///../db/twitter-live1.db'
    db = connect_db(dsn_url)
    conn = db.connect()

    # top tippers
    sql1 = "SELECT from_user as user, sum(coin_val) AS amount FROM t_action WHERE type = 'givetip' AND state != 'failed' GROUP BY from_user ORDER BY amount DESC"

    # top receivers
    sql2 = "SELECT to_user as user, sum(coin_val) AS amount FROM t_action WHERE type = 'givetip' AND state = 'completed' GROUP BY to_user ORDER BY amount DESC"

    sqlexec = conn.execute(sql2)
    results = pd.DataFrame(sqlexec.fetchall(), columns=sqlexec.keys())
