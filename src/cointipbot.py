#!/usr/bin/env python
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

from ctb import ctb_action, ctb_coin, ctb_db, ctb_exchange, ctb_log, ctb_misc, ctb_user
from ctb.ctb_network import RedditNetwork
from ctb.ctb_twitter import TwitterNetwork
from ctb.ctb_twitch import TwitchNetwork
from ctb.ctb_irc import IRCNetwork

import logging
import smtplib
import sys
import time
import traceback
import yaml
import glob
import ntpath
from email.mime.text import MIMEText
from jinja2 import Environment, PackageLoader

# Configure CointipBot logger
logging.basicConfig()
lg = logging.getLogger('cointipbot')


# noinspection PyUnresolvedReferences
class CointipBot(object):
    """
    Main class for cointip bot
    """

    conf = None
    db = None
    network = None
    coins = {}
    exchanges = {}
    jenv = None
    runtime = {'ev': {}, 'regex': []}

    def init_logging(self):
        """
        Initialize logging handlers
        """

        levels = ['warning', 'info', 'debug']
        bt = logging.getLogger('bitcoin')

        # Get handlers
        handlers = {}
        for l in levels:
            if self.conf.logs.levels[l].enabled:
                handlers[l] = logging.FileHandler(self.conf.logs.levels[l].filename,
                                                  mode='a' if self.conf.logs.levels[l].append else 'w')
                handlers[l].setFormatter(logging.Formatter(self.conf.logs.levels[l].format))

        # Set handlers
        for l in levels:
            if l in handlers:
                level = logging.WARNING if l == 'warning' else (logging.INFO if l == 'info' else logging.DEBUG)
                handlers[l].addFilter(ctb_log.LevelFilter(level))
                lg.addHandler(handlers[l])
                bt.addHandler(handlers[l])

        # Set default levels
        lg.setLevel(logging.DEBUG)
        bt.setLevel(logging.DEBUG)

        lg.info('CointipBot::init_logging(): -------------------- logging initialized --------------------')
        return True

    @classmethod
    def parse_config(cls):
        """
        Returns a Python object with CointipBot configuration
        """
        lg.debug('CointipBot::parse_config(): parsing config files...')

        conf = {}
        prefix = './conf/'
        try:
            for path in glob.glob(prefix + '*.yml'):
                f = ntpath.basename(path)
                lg.debug("CointipBot::parse_config(): reading %s", f)
                conf[f.split('.')[0]] = yaml.load(open(path))

            for folder in ['reddit', 'twitter', 'twitch', 'irc']:
                conf[folder] = {}
                for path in glob.glob(prefix + folder + '/*.yml'):
                    f = ntpath.basename(path)
                    lg.debug("CointipBot::parse_config(): reading %s/%s", folder, f)
                    conf[folder][f.split('.')[0]] = yaml.load(open(path))

        except yaml.YAMLError as e:
            lg.error("CointipBot::parse_config(): error reading config file: %s", e)
            if hasattr(e, 'problem_mark'):
                lg.error("CointipBot::parse_config(): error position: (line %s, column %s)", e.problem_mark.line + 1,
                         e.problem_mark.column + 1)
            sys.exit(1)

        lg.info('CointipBot::parse_config(): config files has been parsed')
        return ctb_misc.DotDict(conf)

    def connect_db(self):
        """
        Returns a database connection object
        """
        lg.debug('CointipBot::connect_db(): connecting to database...')

        dsn = "sqlite:///%s" % self.conf.db.auth.dbfile
        dbobj = ctb_db.CointipBotDatabase(dsn)

        try:
            conn = dbobj.connect()
        except Exception as e:
            lg.error("CointipBot::connect_db(): error connecting to database: %s", e)
            sys.exit(1)

        lg.info("CointipBot::connect_db(): connected to database %s as %s", self.conf.db.auth.dbname,
                self.conf.db.auth.user)
        return conn

    def self_checks(self):
        """
        Run self-checks before starting the bot
        """

        # Ensure bot is a registered user
        u = ctb_user.CtbUser(name=self.network.user.lower(), ctb=self)
        if not u.is_registered():
            u.register()

        # Ensure (total pending tips) < (CointipBot's balance)
        for c in self.coins:
            ctb_balance = u.get_balance(coin=c, kind='givetip')
            pending_tips = float(0)
            actions = ctb_action.get_actions(atype='givetip', state='pending', coin=c, ctb=self)
            for a in actions:
                pending_tips += a.coinval

            lg.info("CointipBot::self_checks(): CointipBot's pending tips: %s" % pending_tips)

            if (ctb_balance - pending_tips) < -0.000001:
                raise Exception("CointipBot::self_checks(): CointipBot's %s balance (%s) < total pending tips (%s)" % (
                    c.upper(), ctb_balance, pending_tips))

        # Ensure coin balances are positive
        for c in self.coins:
            b = float(self.coins[c].conn.getbalance())
            lg.info("CointipBot::self_checks(): balance of %s: %s" % (c, b))
            if b < 0:
                raise Exception("CointipBot::self_checks(): negative balance of %s: %s" % (c, b))

        # Ensure user accounts are intact and balances are not negative
        sql = "SELECT username FROM t_users ORDER BY username"
        for sqlrow in self.db.execute(sql):
            u = ctb_user.CtbUser(name=sqlrow['username'], ctb=self)
            if not u.is_registered():
                raise Exception("CointipBot::self_checks(): user %s is_registered() failed" % sqlrow['username'])
                #    for c in vars(self.coins):
                #        if u.get_balance(coin=c, kind='givetip') < 0:
                #            raise Exception("CointipBot::self_checks(): user %s %s balance is negative" % (sqlrow['username'], c))

        return True

    def expire_pending_tips(self):
        """
        Decline any pending tips that have reached expiration time limit
        """

        # Calculate timestamp
        seconds = int(self.conf.misc.times.expire_pending_hours * 3600)
        created_before = time.mktime(time.gmtime()) - seconds
        counter = 0

        # Get expired actions and decline them
        for a in ctb_action.get_actions(atype='givetip', state='pending', created_utc='< ' + str(created_before),
                                        ctb=self):
            a.expire()
            counter += 1

        # Done
        return counter > 0

    def refresh_ev(self):
        """
        Refresh coin/fiat exchange values using self.exchanges
        """

        # Return if rate has been checked in the past hour
        seconds = int(1 * 3600)
        if hasattr(self.conf.exchanges, 'last_refresh') and self.conf.exchanges.last_refresh + seconds > int(
                time.mktime(time.gmtime())):
            lg.debug("< CointipBot::refresh_ev(): DONE (skipping)")
            return

        # For each enabled coin...
        for c in vars(self.conf.coins):
            if self.conf.coins[c].enabled:

                # Get BTC/coin exchange rate
                values = []
                result = 0.0

                if not self.conf.coins[c].unit == 'btc':
                    # For each exchange that supports this coin...
                    for e in self.exchanges:
                        if self.exchanges[e].supports_pair(_name1=self.conf.coins[c].unit, _name2='btc'):
                            # Get ticker value from exchange
                            value = self.exchanges[e].get_ticker_value(_name1=self.conf.coins[c].unit, _name2='btc')
                            if value and float(value) > 0.0:
                                values.append(float(value))

                    # Result is average of all responses
                    if len(values) > 0:
                        result = sum(values) / float(len(values))

                else:
                    # BTC/BTC rate is always 1
                    result = 1.0

                # Assign result to self.runtime['ev']
                if not c in self.runtime['ev']:
                    self.runtime['ev'][c] = {}
                self.runtime['ev'][c]['btc'] = result

        # For each enabled fiat...
        for f in vars(self.conf.fiat):
            if self.conf.fiat[f].enabled:

                # Get fiat/BTC exchange rate
                values = []
                result = 0.0

                # For each exchange that supports this fiat...
                for e in self.exchanges:
                    if self.exchanges[e].supports_pair(_name1='btc', _name2=self.conf.fiat[f].unit):
                        # Get ticker value from exchange
                        value = self.exchanges[e].get_ticker_value(_name1='btc', _name2=self.conf.fiat[f].unit)
                        if value and float(value) > 0.0:
                            values.append(float(value))

                # Result is average of all responses
                if len(values) > 0:
                    result = sum(values) / float(len(values))

                # Assign result to self.runtime['ev']
                if not 'btc' in self.runtime['ev']:
                    self.runtime['ev']['btc'] = {}
                self.runtime['ev']['btc'][f] = result

        lg.debug("CointipBot::refresh_ev(): %s", self.runtime['ev'])

        # Update last_refresh
        self.conf.exchanges.last_refresh = int(time.mktime(time.gmtime()))

    def coin_value(self, _coin, _fiat):
        """
        Quick method to return _fiat value of _coin
        """
        try:
            value = self.runtime['ev'][_coin]['btc']
            if _fiat.lower() != 'btc':
                value *= self.runtime['ev']['btc'][_fiat]
        except KeyError:
            lg.warning("CointipBot::coin_value(%s, %s): KeyError", _coin, _fiat)
            value = 0.00
        return value

    def notify(self, _msg=None):
        """
        Send _msg to configured destination
        """

        # Construct MIME message
        msg = MIMEText(_msg)
        msg['Subject'] = self.conf.misc.notify.subject
        msg['From'] = self.conf.misc.notify.addr_from
        msg['To'] = self.conf.misc.notify.addr_to

        # Send MIME message
        server = smtplib.SMTP(self.conf.misc.notify.smtp_host)
        if self.conf.misc.notify.smtp_tls:
            server.starttls()
        server.login(self.conf.misc.notify.smtp_username, self.conf.misc.notify.smtp_password)
        server.sendmail(self.conf.misc.notify.addr_from, self.conf.misc.notify.addr_to, msg.as_string())
        server.quit()

    def __init__(self, self_checks=True, init_coins=True, init_db=True, init_logging=True, init_exchanges=True,
                 init_reddit=False, init_twitter=True, init_twitch=False, init_irc=False):
        """
        Constructor. Parses configuration file and initializes bot.
        """
        lg.info("CointipBot::__init__()...")

        # Configuration
        self.conf = self.parse_config()

        # Logging
        if init_logging:
            self.init_logging()

        # Database
        if init_db:
            self.db = self.connect_db()

        # Coins
        if init_coins:
            for c in vars(self.conf.coins):
                if self.conf.coins[c].enabled:
                    self.coins[c] = ctb_coin.CtbCoin(_conf=self.conf.coins[c])
            if not len(self.coins) > 0:
                lg.error("CointipBot::__init__(): Error: please enable at least one type of coin")
                sys.exit(1)

        # Networks
        if init_reddit:
            self.conf.network = self.conf.reddit.reddit
            self.conf.regex = self.conf.reddit.regex
            self.network = RedditNetwork(self.conf.network, self)
        elif init_twitter:
            self.conf.network = self.conf.twitter.twitter
            self.conf.regex = self.conf.twitter.regex
            self.network = TwitterNetwork(self.conf.network, self)
        elif init_twitch:
            self.conf.network = self.conf.twitch.twitch
            self.conf.regex = self.conf.twitch.regex
            self.network = TwitchNetwork(self.conf.network, self)
        elif init_irc:
            self.conf.network = self.conf.irc.irc
            self.conf.regex = self.conf.irc.regex
            self.network = IRCNetwork(self.conf.network, self)

        ctb_action.init_regex(self)
        self.network.connect()
        self.network.init()

        # Exchanges
        if init_exchanges:
            for e in vars(self.conf.exchanges):
                if self.conf.exchanges[e].enabled:
                    self.exchanges[e] = ctb_exchange.CtbExchange(_conf=self.conf.exchanges[e])
            if not len(self.exchanges) > 0:
                lg.warning("Cointipbot::__init__(): Warning: no exchanges are enabled")

        # Template
        self.jenv = Environment(trim_blocks=True, loader=PackageLoader('cointipbot', 'tpl/' + self.network.name))

        # Self-checks
        if self_checks:
            self.self_checks()

        lg.info("< CointipBot::__init__(): DONE, sleep-seconds = %s", self.conf.misc.times.sleep_seconds)

    def __str__(self):
        """
        Return string representation of self
        """
        me = "<CointipBot: sleepsec=%s ev=%s"
        me = me % (self.conf.misc.times.sleep_seconds, self.runtime['ev'])
        return me

    def main(self):
        """
        Main loop
        """

        while True:
            try:
                lg.debug("CointipBot::main(): beginning main() iteration")

                # Refresh exchange rate values
                self.refresh_ev()

                # Check personal messages
                self.network.check_inbox(self)

                # Expire pending tips
                self.expire_pending_tips()

                # Check subreddit comments for tips
                self.network.check_mentions(self)

                # Sleep
                if self.network.name == 'reddit':
                    lg.debug("CointipBot::main(): sleeping for %s seconds...", self.conf.misc.times.sleep_seconds)
                    time.sleep(self.conf.misc.times.sleep_seconds)

            except KeyboardInterrupt as e:
                sys.exit(1)
            except Exception as e:
                lg.error("CointipBot::main(): exception: %s", e)
                tb = traceback.format_exc()
                lg.error("CointipBot::main(): traceback: %s", tb)
                # Send a notification, if enabled
                if self.conf.misc.notify.enabled:
                    self.notify(_msg=tb)
