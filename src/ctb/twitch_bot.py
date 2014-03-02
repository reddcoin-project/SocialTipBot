from irc.dict import IRCDict
from irc.client import SimpleIRCClient
from irc.bot import Channel, ServerSpec


class TwitchChatBot(SimpleIRCClient):
    """A single-server IRC bot class.

    The bot tries to reconnect if it is disconnected.

    The bot keeps track of the channels it has joined, the other
    clients that are present in the channels and which of those that
    have operator or voice modes.  The "database" is kept in the
    self.channels attribute, which is an IRCDict of Channels.
    """

    def __init__(self, server_list, channel_list, nickname, reconnection_interval=5, **connect_params):
        """Constructor for SingleServerIRCBot objects.

        Arguments:

            server_list -- A list of ServerSpec objects or tuples of
                           parameters suitable for constructing ServerSpec
                           objects. Defines the list of servers the bot will
                           use (in order).

            nickname -- The bot's nickname.

            reconnection_interval -- How long the bot should wait
                                     before trying to reconnect.

            **connect_params -- parameters to pass through to the connect
                                method.
        """

        super(TwitchChatBot, self).__init__()
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
        except irc.client.ServerConnectionError:
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
        print '%s ====>> %s' % (nick, ch)

    def on_part(self, c, e):
        ch = e.target
        nick = e.source.nick
        print '%s <<<<== %s' % (nick, ch)
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
                print '%s changed nickname to %s' % (before, after)

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        for ch in self.channel_list:
            c.join(ch)

    def on_privmsg(self, c, e):
        print 'privmsg: %s' % ' '.join(e.arguments)

    def on_pubmsg(self, c, e):
        print 'pubmsg: %s' % ' '.join(e.arguments)

    def disconnect(self, msg="disconnecting"):
        """Disconnect the bot.

        The bot will try to reconnect after a while.

        Arguments:

            msg -- Quit message.
        """
        self.connection.disconnect(msg)

    def jump_server(self, msg="Changing servers"):
        """Connect to a new server, possibly disconnecting from the current.

        The bot will skip to next server in the server_list each time
        jump_server is called.
        """
        if self.connection.is_connected():
            self.connection.disconnect(msg)

        self.server_list.append(self.server_list.pop(0))
        self._connect()

    def start(self):
        self._connect()
        super(TwitchChatBot, self).start()


if __name__ == "__main__":
    server = 'irc.twitch.tv'
    port = 6667
    ch = '#reynad27'
    nickname = 'tipreddcoin'
    password = 'oauth:pi5oz89kcioi5650yo1qeo5xwppawq3'

    bot = TwitchChatBot([(server, port, password)], [ch], nickname)
    bot.start()
