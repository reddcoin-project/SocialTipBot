__author__ = 'laudney'

import traceback
import calendar
import re
import logging
import pytz
from datetime import datetime
from dateutil.parser import parse

from irc.dict import IRCDict
from irc.client import SimpleIRCClient, ServerConnectionError
from irc.bot import Channel, ServerSpec

from ctb.ctb_network import CtbNetwork
import ctb.ctb_action as ctb_action
import ctb.ctb_misc as ctb_misc


lg = logging.getLogger('cointipbot')


class IRCChatBot(SimpleIRCClient):
    def __init__(self, server_list, channel_list, nickname, reconnection_interval=5, **connect_params):
        """Constructor for IRCChatBot objects.

        Arguments:

            server_list -- A list of ServerSpec objects or tuples of
                           parameters suitable for constructing ServerSpec
                           objects. Defines the list of servers the bot will
                           use (in order).

            channel_list -- A list of channel names to join

            nickname -- The bot's nickname.

            reconnection_interval -- How long the bot should wait
                                     before trying to reconnect.

            **connect_params -- parameters to pass through to the connect
                                method.
        """

        super(IRCChatBot, self).__init__()
        self.connection.set_rate_limit(0.5)

        self.nickname = nickname
        self.__connect_params = connect_params

        self.channels = IRCDict()
        self.channel_list = channel_list

        self.server_list = [
            ServerSpec(*server) if isinstance(server, (tuple, list)) else server for server in server_list
        ]
        assert all(isinstance(server, ServerSpec) for server in self.server_list)

        if not reconnection_interval or reconnection_interval < 0:
            reconnection_interval = 2 ** 31
        self.reconnection_interval = reconnection_interval

    def _connected_checker(self):
        if not self.connection.is_connected():
            self.connection.execute_delayed(self.reconnection_interval,
                                            self._connected_checker)
            self.jump_server()

    def _connect(self):
        server = self.server_list[0]
        try:
            self.connect(server.host, server.port, self.nickname, server.password,
                         ircname=self.nickname, **self.__connect_params)
        except ServerConnectionError:
            pass

    def on_disconnect(self, c, e):
        self.channels = IRCDict()
        self.connection.execute_delayed(self.reconnection_interval,
                                        self._connected_checker)

    def on_join(self, c, e):
        ch = e.target
        nick = e.source.nick
        if nick == c.get_nickname():
            self.channels[ch] = Channel()
        self.channels[ch].add_user(nick)
        lg.debug('IRCChatBot::on_join: %s =====>>> %s', nick, ch)

    def on_part(self, c, e):
        ch = e.target
        nick = e.source.nick
        lg.debug('IRCChatBot::on_part: %s <<<===== %s', nick, ch)
        if nick == c.get_nickname():
            del self.channels[ch]
        else:
            self.channels[ch].remove_user(nick)

    def on_nick(self, c, e):
        before = e.source.nick
        after = e.target
        for ch in self.channels.values():
            if ch.has_user(before):
                ch.change_nick(before, after)
                print('%s changed nickname to %s' % (before, after))

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        for ch in self.channel_list:
            c.join(ch)

    def on_privmsg(self, c, e):
        nick = e.source.nick
        text = ' '.join(e.arguments)

        lg.debug('IRCChatBot::on_privmsg(): %s: %s', nick, text)

        # ignore my own message
        if nick == self.username:
            return None

        # commands must start with +
        if text[0] != '+':
            return None

        now = datetime.utcnow().replace(tzinfo=pytz.utc)
        msg = {'created_utc': calendar.timegm(now.utctimetuple()), 'author': {'name': nick}, 'channel': e.target}
        msg['id'] = str(msg['created_utc'])
        msg['body'] = text
        print(msg)

        action = ctb_action.eval_message(ctb_misc.DotDict(msg), self.ctb)
        if action:
            lg.info("IRCChatBot::on_pubmsg(): %s from %s", action.type, action.u_from.name)
            lg.debug("IRCChatBot::on_pubmsg(): comment body: <%s>", action.msg.body)
            action.do()

    def on_pubmsg(self, c, e):
        ch = e.target
        nick = e.source.nick
        text = ' '.join(e.arguments)

        lg.debug('IRCChatBot::on_pubmsg(): %s on %s: %s', nick, ch, text)

        # ignore my own message
        if nick == self.username:
            return None

        # commands must start with +
        if text[0] != '+':
            return None

        now = datetime.utcnow().replace(tzinfo=pytz.utc)
        msg = {'created_utc': calendar.timegm(now.utctimetuple()), 'author': {'name': nick}}
        msg['id'] = str(msg['created_utc'])
        msg['body'] = text
        print(msg)

        action = ctb_action.eval_message(ctb_misc.DotDict(msg), self.ctb)
        if action:
            lg.info("IRCChatBot::on_pubmsg(): %s from %s", action.type, action.u_from.name)
            lg.debug("IRCChatBot::on_pubmsg(): comment body: <%s>", action.msg.body)
            action.do()

    def disconnect(self, msg="disconnecting"):
        self.connection.disconnect(msg)

    def jump_server(self, msg="switching server"):
        """Connect to a new server, possibly disconnecting from the current.

        The bot will skip to next server in the server_list each time
        jump_server is called.
        """
        if self.connection.is_connected():
            self.connection.disconnect(msg)

        self.server_list.append(self.server_list.pop(0))
        self._connect()

    def send_msg(self, recipient, msg):
        self.connection.privmsg(recipient, msg)

    def start(self):
        self._connect()
        super(IRCChatBot, self).start()


class IRCNetwork(CtbNetwork):
    def __init__(self, conf, ctb):
        CtbNetwork.__init__(self, "irc")
        self.conf = conf
        self.ctb = ctb
        self.db = ctb.db
        self.user = conf.auth.user
        self.password = conf.auth.password
        self.server = conf.auth.server
        self.port = conf.auth.port
        self.channel_list = conf.channels.list
        self.conn = None

    def connect(self):
        """
        Returns a IRC Chat Bot object
        """
        lg.debug('IRCNetwork::connect(): connecting to IRC Chat IRC Server...')

        self.conn = IRCChatBot([(self.server, self.port, self.password)], self.channel_list, self.user)
        lg.info('IRCNetwork::connect(): connected to IRC Chat IRC Server.')

        self.conn.username = self.user
        self.conn.ctb = self.ctb
        return None

    def is_user_banned(self, user):
        return False

    def send_msg(self, user_to, subject, body, editor=None, msgobj=None):
        try:
            if msgobj:
                self.reply_msg(body, msgobj)
            else:
                self.conn.send_msg(user_to, body)

        except Exception as e:
            lg.error("IRCNetwork::send_msg: exception: %s", e)
            tb = traceback.format_exc()
            lg.error("IRCNetwork::send_msg: traceback: %s", tb)
            return False
        else:
            return True

    def reply_msg(self, body, msgobj):
        # IRC PRIVMSG doesn't allow \n
        body = body.replace('\n', ' ')
        try:
            if msgobj is None:
                pass
            elif msgobj.channel:
                lg.debug("< IRCNetwork::reply_msg: sending message to %s on %s: %s",
                         msgobj.author.name, msgobj.channel, body)
                self.conn.send_msg(msgobj.channel, body)
                lg.debug("< IRCNetwork::reply_msg to %s on %s DONE", msgobj.author.name, msgobj.channel)
            else:
                lg.debug("< IRCNetwork::reply_msg: sending private message to %s", msgobj.author.name)
                self.conn.send_msg(msgobj.author.name, body)

        except Exception as e:
            lg.error("IRCNetwork::reply_msg: exception: %s", e)
            tb = traceback.format_exc()
            lg.error("IRCNetwork::reply_msg: traceback: %s", tb)
            return False
        else:
            return True

    def check_mentions(self, ctb):
        lg.info("IRCNetwork::check_mentions(): starting")
        self.conn.start()


if __name__ == "__main__":
    server = 'gamma.elitebnc.org'
    port = 1338
    nickname = 'tipreddcoin'
    password = 'tipreddcoin:wgf01k68'

    bot = IRCChatBot([(server, port, password)], [], nickname)
    bot.start()
