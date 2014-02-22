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

import ctb_misc

import logging
import time
import praw
import re


lg = logging.getLogger('cointipbot')


class CtbUser(object):
    """
    User class for cointip bot
    """

    name = None
    ctb = None
    network = None
    giftamount = None
    joindate = None
    addr = {}
    banned = False

    def __init__(self, name, ctb):
        """
        Initialize CtbUser object with given parameters
        """
        lg.debug("> CtbUser::__init__(%s)", name)
        self.name = name
        self.ctb = ctb
        self.network = ctb.network.name.lower()
        self.banned = ctb.network.is_user_banned(self.name)
        lg.debug("< CtbUser::__init__(%s) DONE", name)

    def __str__(self):
        """
        Return string representation of self
        """
        me = "<CtbUser: name=%s, network=%s, giftamnt=%s, joindate=%s, addr=%s, banned=%s>"
        me = me % (self.name, self.network, self.giftamount, self.joindate, self.addr, self.banned)
        return me

    def get_balance(self, coin=None, kind=None):
        """
        If coin is specified, return float with coin balance for user. Else, return a dict with balance of each coin for user.
        """
        lg.debug("> CtbUser::balance(%s)", self.name)

        if not bool(coin) or not bool(kind):
            raise Exception("CtbUser::balance(%s): coin or kind not set" % self.name)

        # Ask coin daemon for account balance
        lg.info("CtbUser::balance(%s): getting %s %s balance", self.name, coin, kind)
        balance = self.ctb.coins[coin].getbalance(_user=self.name, _minconf=self.ctb.conf.coins[coin].minconf[kind])

        lg.debug("< CtbUser::balance(%s) DONE", self.name)
        return float(balance)

    def get_addr(self, coin=None):
        """
        Return coin address of user
        """
        lg.debug("> CtbUser::get_addr(%s, %s, %s)", self.name, self.network, coin)

        if coin in self.addr:
            return self.addr[coin]

        sql = "SELECT address from t_addrs WHERE username = :u AND network = :n AND coin = :c"
        sqlrow = self.ctb.db.execute(sql, {'u': self.name.lower(),
                                           'n': self.network.lower(),
                                           'c': coin.lower()}).fetchone()
        if not sqlrow:
            lg.debug("< CtbUser::get_addr(%s, %s, %s) DONE (no)", self.name, self.network, coin)
            return None
        else:
            self.addr[coin] = sqlrow['address']
            lg.debug("< CtbUser::get_addr(%s, %s, %s) DONE (%s)", self.name, self.network, coin, self.addr[coin])
            return self.addr[coin]

        lg.debug("< CtbUser::get_addr(%s, %s, %s) DONE (should never happen)", self.name, self.network, coin)
        return None

    def is_on_reddit(self):
        """
        Return true if username exists on Reddit.
        """
        lg.debug("> CtbUser::is_on_reddit(%s)", self.name)
        return self.network.lower() == 'reddit'

    def is_on_twitter(self):
        """
        Return true if username exists on Twitter.
        """
        lg.debug("> CtbUser::is_on_twitter(%s)", self.name)
        return self.network.lower() == 'twitter'

    def is_registered(self):
        """
        Return true if user is registered with CointipBot
        """
        lg.debug("> CtbUser::is_registered(%s)", self.name)

        sql = "SELECT * FROM t_users WHERE username = :u"
        try:
            # First, check t_users table
            sqlrow = self.ctb.db.execute(sql, {'u': self.name.lower()}).fetchone()

            if not sqlrow:
                lg.debug("< CtbUser::is_registered(%s) DONE (no)", self.name)
                return False

            else:
                # Next, check t_addrs table for whether  user has correct number of coin addresses
                sql_coins = "SELECT COUNT(*) AS count FROM t_addrs WHERE username = :u"
                sqlrow_coins = self.ctb.db.execute(sql_coins, {'u': self.name.lower()}).fetchone()

                if int(sqlrow_coins['count']) != len(self.ctb.coins):
                    if int(sqlrow_coins['count']) == 0:
                        # Bot probably crashed during user registration process
                        # Delete user
                        lg.warning("CtbUser::is_registered(%s): deleting user, incomplete registration", self.name)
                        sql_delete = "DELETE FROM t_users WHERE username = :u"
                        sql_res = self.ctb.db.execute(sql_delete, {'u': self.name.lower()})
                        # User is not registered
                        return False
                    else:
                        raise Exception("CtbUser::is_registered(%s): user has %s coins but %s active" % (
                            self.name, sqlrow_coins['count'], len(self.ctb.coins)))

                # Set some properties
                self.giftamount = sqlrow['giftamount']

                # Done
                lg.debug("< CtbUser::is_registered(%s) DONE (yes)", self.name)
                return True

        except Exception, e:
            lg.error("CtbUser::is_registered(%s): error while executing <%s>: %s", self.name, sql % self.name.lower(),
                     e)
            raise

        lg.warning("< CtbUser::is_registered(%s): returning None (shouldn't happen)", self.name)
        return None

    def tell(self, subj=None, msg=None, msgobj=None):
        """
        Send a message to user
        """
        lg.debug("> CtbUser::tell(%s)", self.name)

        if not bool(subj) or not bool(msg):
            lg.warning("CtbUser::tell(%s): subj or msg not set", self.name)
            return False

        if bool(msgobj):
            lg.debug("CtbUser::tell(%s): replying to message", msgobj.id)
            self.ctb.network.reply_msg(msg, msgobj)
        else:
            lg.debug("CtbUser::tell(%s): sending message", self.name)
            self.ctb.network.send_msg(self.name, subj, msg, msgobj=msgobj)

        lg.debug("< CtbUser::tell(%s) DONE", self.name)
        return True

    def register(self):
        """
        Add user to database and generate coin addresses
        """
        lg.debug("> CtbUser::register(%s)", self.name)

        # Add user to database
        sql_adduser = "INSERT INTO t_users (username, network) VALUES (:u, :n)"
        try:
            sqlexec = self.ctb.db.execute(sql_adduser, {'u': self.name.lower(), 'n': self.network.lower()})
            if sqlexec.rowcount <= 0:
                raise Exception("CtbUser::register(%s): rowcount <= 0 while executing <%s>" % (self.name, sql_adduser))
        except Exception, e:
            lg.error("CtbUser::register(%s): exception while executing <%s>: %s", self.name, sql_adduser, e)
            raise

        # Get new coin addresses
        new_addrs = {}
        for c in self.ctb.coins:
            new_addrs[c] = self.ctb.coins[c].getnewaddr(_user=self.name.lower())
            lg.info("CtbUser::register(%s): got %s address %s", self.name, c, new_addrs[c])

        # Add coin addresses to database
        # sql_addr = "UPDATE t_addrs SET username=:u, network=:n, coin=:c, address=:a"
        sql_addr = "INSERT OR REPLACE INTO t_addrs (username, network, coin, address) VALUES (:u, :n, :c, :a)"
        for c, a in new_addrs.iteritems():
            try:
                sqlexec = self.ctb.db.execute(sql_addr, {'u': self.name.lower(), 'n': self.network.lower(),
                                                         'c': c, 'a': a})
                if sqlexec.rowcount <= 0:
                    # Undo change to database
                    delete_user(_username=self.name.lower(), _db=self.ctb.db)
                    raise Exception("CtbUser::register(%s): rowcount <= 0 while executing <%s>" % (
                        self.name, sql_addr % (self.name.lower(), c, new_addrs[c])))
            except Exception:
                # Undo change to database
                delete_user(_username=self.name.lower(), _db=self.ctb.db)
                raise

        lg.debug("< CtbUser::register(%s) DONE", self.name)
        return True


def delete_user(_username=None, _db=None):
    """
    Delete _username from t_users and t_addrs tables
    """
    lg.debug("> delete_user(%s)", _username)

    try:
        sql_arr = ["DELETE FROM t_users WHERE username = :u",
                   "DELETE FROM t_addrs WHERE username = :u"]
        for sql in sql_arr:
            sqlexec = _db.execute(sql, {'u': _username.lower()})
            if sqlexec.rowcount <= 0:
                lg.warning("delete_user(%s): rowcount <= 0 while executing <%s>", _username, sql)

    except Exception, e:
        lg.error("delete_user(%s): error while executing <%s>: %s", _username, sql, e)
        return False

    lg.debug("< delete_user(%s) DONE", _username)
    return True
