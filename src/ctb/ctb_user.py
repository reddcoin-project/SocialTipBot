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

import ctb.ctb_misc as ctb_misc

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

    # TODO currently balance is username-specific and totally ignorant of networks.
    def get_balance(self, coin=None, kind=None):
        """
        If coin is specified, return float with coin balance for user. Else, return a dict with balance of each coin for user.
        """
        lg.debug("> CtbUser::balance(%s on %s)", self.name, self.network)

        if not bool(coin) or not bool(kind):
            raise Exception("CtbUser::balance(%s on %s): coin or kind not set" % (self.name, self.network))

        # Ask coin daemon for account balance
        lg.info("CtbUser::balance(%s): getting %s %s balance", self.name, coin, kind)
        balance = self.ctb.coins[coin].getbalance(_user=self.name, _minconf=self.ctb.conf.coins[coin].minconf[kind])

        lg.debug("< CtbUser::balance(%s on %s) DONE", self.name, self.network)
        return float(balance)

    def get_addr(self, coin=None):
        """
        Return coin address of user
        """
        lg.debug("> CtbUser::get_addr(%s on %s, %s)", self.name, self.network, coin)

        if coin in self.addr:
            return self.addr[coin]

        sql = "SELECT address FROM t_addrs WHERE username = ? AND network = ? AND coin = ?"
        sqlrow = self.ctb.db.execute(sql, [self.name.lower(), self.network.lower(), coin.lower()]).fetchone()
        if not sqlrow:
            lg.debug("< CtbUser::get_addr(%s on %s, %s) DONE (no)", self.name, self.network, coin)
            return None
        else:
            self.addr[coin] = sqlrow['address']
            lg.debug("< CtbUser::get_addr(%s on %s, %s) DONE (%s)", self.name, self.network, coin, self.addr[coin])
            return self.addr[coin]

        lg.debug("< CtbUser::get_addr(%s, %s, %s) DONE (should never happen)", self.name, self.network, coin)
        return None

    def is_on_network(self, name):
        """
        Return true if username exists on the specified network.
        """
        lg.debug("> CtbUser::is_on_network(%s, %s)", self.name, name)
        return self.network.lower() == name

    def is_registered(self):
        """
        Return true if user is registered with CointipBot
        """
        lg.debug("> CtbUser::is_registered(%s on %s)", self.name, self.network)

        sql = "SELECT * FROM t_users WHERE username = ? AND network = ?"
        try:
            # First, check t_users table
            sqlrow = self.ctb.db.execute(sql, [self.name.lower(), self.network.lower()]).fetchone()

            if not sqlrow:
                lg.debug("< CtbUser::is_registered(%s on %s) DONE (no)", self.name, self.network)
                return False

            else:
                # Next, check t_addrs table for whether  user has correct number of coin addresses
                sql_coins = "SELECT COUNT(*) AS count FROM t_addrs WHERE username = ? AND network = ?"
                sqlrow_coins = self.ctb.db.execute(sql_coins, [self.name.lower(), self.network.lower()]).fetchone()

                if int(sqlrow_coins['count']) != len(self.ctb.coins):
                    if int(sqlrow_coins['count']) == 0:
                        # Bot probably crashed during user registration process
                        # Delete user
                        lg.warning("CtbUser::is_registered(%s on %s): deleting user, incomplete registration",
                                   self.name, self.network)
                        sql_delete = "DELETE FROM t_users WHERE username = ? AND network = ?"
                        sql_res = self.ctb.db.execute(sql_delete, [self.name.lower(), self.network.lower()])
                        # User is not registered
                        return False
                    else:
                        raise Exception("CtbUser::is_registered(%s on %s): user has %s coins but %s active" % (
                            self.name, self.network, sqlrow_coins['count'], len(self.ctb.coins)))

                # Set some properties
                self.giftamount = sqlrow['giftamount']

                # Done
                lg.debug("< CtbUser::is_registered(%s on %s) DONE (yes)", self.name, self.network)
                return True

        except Exception as e:
            lg.error("CtbUser::is_registered(%s on %s): error while executing <%s>: %s",
                     self.name, self.network, sql, e)
            raise

        lg.warning("< CtbUser::is_registered(%s on %s): returning None (shouldn't happen)", self.name, self.network)
        return False

    def tell(self, subj=None, msg=None, msgobj=None):
        """
        Send a message to user
        """
        lg.debug("> CtbUser::tell(%s)", self.name)

        if not subj or not msg:
            lg.warning("CtbUser::tell(%s): subj or msg not set", self.name)
            return False

        if self.ctb.network.name != "reddit" and msgobj:
            msgobj.author.name = self.name
            self.ctb.network.reply_msg(msg, msgobj)
        else:
            lg.debug("CtbUser::tell(%s): sending message", self.name)
            self.ctb.network.send_msg(self.name, subj, msg)

        lg.debug("< CtbUser::tell(%s) DONE", self.name)
        return True

    def register(self):
        """
        Add user to database and generate coin addresses
        """
        lg.debug("> CtbUser::register(%s on %s)", self.name, self.network)

        # Add user to database
        sql_adduser = "INSERT INTO t_users (username, network) VALUES (:u, :n)"
        try:
            sqlexec = self.ctb.db.execute(sql_adduser, {'u': self.name.lower(), 'n': self.network.lower()})
            if sqlexec.rowcount <= 0:
                raise Exception("CtbUser::register(%s): rowcount <= 0 while executing <%s>" % (self.name, sql_adduser))
        except Exception as e:
            lg.error("CtbUser::register(%s): exception while executing <%s>: %s", self.name, sql_adduser, e)
            raise

        # Get new coin addresses
        new_addrs = {}
        for c in self.ctb.coins:
            new_addrs[c] = self.ctb.coins[c].getnewaddr(_user=self.name.lower())
            lg.info("CtbUser::register(%s): got %s address %s", self.name, c, new_addrs[c])

        # Add coin addresses to database
        # sql_addr = "UPDATE t_addrs SET username=:u, network=:n, coin=:c, address=:a"
        sql_addr = "INSERT OR REPLACE INTO t_addrs (username, network, coin, address) VALUES (?, ?, ?, ?)"
        for c, a in iter(new_addrs.items()):
            try:
                sqlexec = self.ctb.db.execute(sql_addr, [self.name.lower(), self.network.lower(), c, a])
                if sqlexec.rowcount <= 0:
                    # Undo change to database
                    lg.warning("CtbUser::register(%s on %s): rowcount <= 0 while executing <%s>",
                               self.name, self.network, sql_addr)
                    self.delete()
            except Exception:
                # Undo change to database
                self.delete()
                raise

        lg.debug("< CtbUser::register(%s on %s) DONE", self.name, self.network)
        return True

    def delete(self):
        """
        Delete user from t_users and t_addrs tables
        """
        lg.debug("> CtbUser::delete(%s on %s)", self.name, self.network)

        try:
            sql_arr = ["DELETE FROM t_users WHERE username = ? AND network = ?",
                       "DELETE FROM t_addrs WHERE username = ? AND network = ?"]
            for sql in sql_arr:
                sqlexec = _db.execute(sql, [self.name.lower(), self.network.lower()])
                if sqlexec.rowcount <= 0:
                    lg.warning("delete_user(%s on %s): rowcount <= 0 while executing <%s>",
                               self.name, self.network, sql)

        except Exception as e:
            lg.error("delete_user(%s on %s): error while executing <%s>: %s", self.name, self.network, sql, e)
            return False

        lg.debug("< delete_user(%s on %s) DONE", self.name, self.network)
        return True
