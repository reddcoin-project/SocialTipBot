"""
    This file is part of ALTcointip.

    ALTcointip is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    ALTcointip is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with ALTcointip.  If not, see <http://www.gnu.org/licenses/>.
"""

import logging
import time

lg = logging.getLogger('cointipbot')


def get_value(conn, param0=None):
    """
    Fetch a value from t_values table
    """
    lg.debug("> get_value()")

    if param0 is None:
        raise Exception("get_value(): param0 is None")

    value = None
    sql = "SELECT value0 FROM t_values WHERE param0 = %s"
    try:
        sqlrow = conn.execute(sql, [param0]).fetchone()
        if sqlrow is None:
            lg.error("get_value(): query <%s> didn't return any rows", sql % param0)
            return None
        else:
            value = sqlrow['value0']
    except Exception as e:
        lg.error("get_value(): error executing query <%s>: %s", sql % param0, e)
        raise

    lg.debug("< get_value() DONE (%s)", value)
    return value


def set_value(conn, param0=None, value0=None):
    """
    Set a value in t_values table
    """
    lg.debug("> set_value(%s, %s)", param0, value0)

    if param0 is None or value0 is None:
        raise Exception("set_value(): param0 is None or value0 is None")

    sql = "REPLACE INTO t_values (param0, value0) VALUES (%s, %s)"
    try:
        sqlexec = conn.execute(sql, [param0, value0])
        if sqlexec.rowcount <= 0:
            lg.error("set_value(): query <%s> didn't affect any rows", sql % (param0, value0))
            return False
    except Exception as e:
        lg.error("set_value: error executing query <%s>: %s", sql % (param0, value0), e)
        raise

    lg.debug("< set_value() DONE")
    return True


def add_coin(coin, db, coins):
    """
    Add new coin address to each user
    """
    lg.debug("> add_coin(%s)", coin)

    sql_select = "SELECT username FROM t_users WHERE username NOT IN (SELECT username FROM t_addrs WHERE coin = %s) ORDER BY username"
    sql_insert = "REPLACE INTO t_addrs (username, coin, address) VALUES (%s, %s, %s)"

    try:
        sqlsel = db.execute(sql_select, [coin])
        for m in sqlsel:
            # Generate new coin address for user
            new_addr = coins[coin].getnewaddr(_user=m['username'])
            lg.info("add_coin(): got new address %s for %s", new_addr, m['username'])
            # Add new coin address to MySQL
            sqlins = db.execute(sql_insert, [m['username'].lower(), coin, new_addr])
            if sqlins.rowcount <= 0:
                raise Exception("add_coin(%s): rowcount <= 0 when executing <%s>", coin,
                                sql_insert % (m['username'].lower(), coin, new_addr))
            time.sleep(1)
    except Exception as e:
        lg.error("add_coin(%s): error: %s", coin, e)
        raise

    lg.debug("< add_coin(%s) DONE", coin)
    return True


class DotDict(object):
    def __init__(self, d):
        for a, b in d.items():
            if isinstance(b, (list, tuple)):
                setattr(self, a, [DotDict(x) if isinstance(x, dict) else x for x in b])
            else:
                setattr(self, a, DotDict(b) if isinstance(b, dict) else b)

    def __getitem__(self, val):
        return getattr(self, val)

    def has_key(self, key):
        return hasattr(self, key)
