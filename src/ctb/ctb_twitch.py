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


class TwitchChatBot(SimpleIRCClient):
    def __init__(self, server_list, channel_list, nickname, reconnection_interval=5, **connect_params):
        """Constructor for TwitchChatBot objects.

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

        super(TwitchChatBot, self).__init__()
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
            self.reactor.scheduler.execute_after(self.reconnection_interval,
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
        self.reactor.scheduler.execute_after(self.reconnection_interval,
                                        self._connected_checker)

    def on_join(self, c, e):
        ch = e.target
        nick = e.source.nick
        if nick == c.get_nickname():
            self.channels[ch] = Channel()
        self.channels[ch].add_user(nick)
        lg.debug('TwitchChatBot::on_join: %s =====>>> %s', nick, ch)

    def on_part(self, c, e):
        ch = e.target
        nick = e.source.nick
        lg.debug('TwitchChatBot::on_part: %s <<<===== %s', nick, ch)
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
            c.cap('REQ', ':twitch.tv/tags')
            c.cap('REQ', ':twitch.tv/commands')
            c.join(ch)

    def on_privmsg(self, c, e):
        print('privmsg: %s' % ' '.join(e.arguments))

    def on_pubmsg(self, c, e):
        ch = e.target
        nick = e.source.nick
        text = ' '.join(e.arguments)

        lg.debug('TwitchChatBot::on_pubmsg(): %s on %s: %s', nick, ch, text)

        # ignore my own message
        if nick == self.username:
            return None

        # for messages on my own channel, command must start with +
        if ch == '#' + self.username and text[0] != '+':
            return None

        # for messages on other channels, command contain my name
        if ch != '#' + self.username and '@' + self.username not in text:
            return None

        now = datetime.utcnow().replace(tzinfo=pytz.utc)
        msg = {'created_utc': calendar.timegm(now.utctimetuple()), 'author': {'name': nick}, 'channel': e.target}
        msg['id'] = str(msg['created_utc'])
        msg['body'] = text
        print(msg)

        action = ctb_action.eval_message(ctb_misc.DotDict(msg), self.ctb)
        if action:
            lg.info("TwitchChatBot::on_pubmsg(): %s from %s", action.type, action.u_from.name)
            lg.debug("TwitchChatBot::on_pubmsg(): comment body: <%s>", action.msg.body)
            action.do()

    def on_whisper(self, c, e):
        lg.info('TwitchChatBot::on_whisper():: %s from %s' % (e.arguments, e.source.nick))
        # twitch prevents bots from sending whispers
        msg = '@%s copy that (%s)' % (e.source.nick, e.arguments)
        lg.info('TwitchChatBot::on_whisper():: Sending %s to %s' % (msg, e.source.nick))
        # self.send_msg('#%s' % e.target, msg)

    def on_pubnotice(self, c, e):
        lg.info('TwitchChatBot::on_pubnotice():: %s from %s' % (e.arguments, e.source))

    def on_privnotice(self, c, e):
        lg.info('TwitchChatBot::on_privnotice():: %s from %s' % (e.arguments, e.source))

    # def on_all_raw_messages(self, c, e):
    #     lg.info('TwitchChatBot::on_all_raw_messages():: %s from %s' % (e.arguments, e.source))

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

    def send_msg(self, channel, msg):
        self.connection.privmsg(channel, msg)

    def start(self):
        self._connect()
        super(TwitchChatBot, self).start()


class TwitchNetwork(CtbNetwork):
    def __init__(self, conf, ctb):
        CtbNetwork.__init__(self, "twitch")
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
        Returns a Twitch Chat Bot object
        """
        lg.debug('TwitchNetwork::connect(): connecting to Twitch Chat IRC Server...')

        self.conn = TwitchChatBot([(self.server, self.port, self.password)], self.channel_list, self.user)
        self.conn.username = self.user
        self.conn.ctb = self.ctb

        lg.info('TwitchNetwork::connect(): connected to Twitch Chat IRC Server.')
        return None

    def is_user_banned(self, user):
        return False

    def send_msg(self, user_to, subject, body, editor=None, msgobj=None):
        try:
            if msgobj:
                self.reply_msg(body, msgobj)
            else:
                lg.debug("< TwitchNetwork::send_msg: missing channel when sending msg to %s: %s", user_to, body)

        except Exception as e:
            lg.error("TwitchNetwork::send_msg: exception: %s", e)
            tb = traceback.format_exc()
            lg.error("TwitchNetwork::send_msg: traceback: %s", tb)
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
                lg.debug("< TwitchNetwork::reply_msg: sending message to %s on %s: %s",
                         msgobj.author.name, msgobj.channel, body)
                self.conn.send_msg(msgobj.channel, body)
                lg.debug("< TwitchNetwork::reply_msg to %s on %s DONE", msgobj.author.name, msgobj.channel)
            else:
                s = "< TwitchNetwork::reply_msg: missing channel when sending message to %s: %s"
                raise Exception(s % (msgobj.author.name, body))

        except Exception as e:
            lg.error("TwitchNetwork::reply_msg: exception: %s", e)
            tb = traceback.format_exc()
            lg.error("TwitchNetwork::reply_msg: traceback: %s", tb)
            return False
        else:
            return True

    def check_mentions(self, ctb):
        lg.info("TwitchNetwork::check_mentions(): starting")
        self.conn.start()


if __name__ == "__main__":
    server = 'irc.twitch.tv'
    port = 6667
    ch = '#tipredd'
    nickname = 'tipreddcoin'
    password = 'oauth:pi5oz89kcioi5650yo1qeo5xwppawq3'

    bot = TwitchChatBot([(server, port, password)], [ch], nickname)
    bot.start()
