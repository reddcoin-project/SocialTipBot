from irc.dict import IRCDict
from irc.client import SimpleIRCClient
from irc.bot import Channel, ServerSpec


class TwitchChannel(Channel):
    """ A Twitch.tv Chat Channel

    Supported commands at http://www.twitch.tv/chat_commands.html
    """

    def __init__(self):
        super(TwitchChannel, self).__init__()

        # /slow interval: Require that chatters wait <interval> seconds between lines of chat
        #   interval: The number of seconds that users must wait between chatting
        # /slowoff: Don't require that chatters wait between lines of chat anymore
        #
        # by default never set below 2 seconds.
        # anyone posting >=20 messages in 30 seconds is banned globally for 8 hours
        self.slow_interval = 2

        # /subscribers: Turn on subscribers-only mode, which keeps people who have not purchased
        #   channel subscriptions to this channel from talking in chat
        # /subscribersoff: Turn off subscribers-only mode
        self.subscribers_only = False

        # /ban name-of-user: Ban the given user from your channel
        #   name-of-user: The username of the user to ban from your channel
        # /unban name-of-user: Lift a ban or a time-out that has been given to the given user
        #   name-of-user: The username of the user to lift the ban or time-out on
        self.bandict = IRCDict()

        # /ignore name-of-user: Make lines of chat coming from the given user invisible to you
        #   name-of-user: The username of the user whose chat you never want to see again
        # /unignore name-of-user: Make lines of chat written by the given user visible again
        #   name-of-user: The username of the user whose chat you want to see again
        self.ignoredict = IRCDict()

        # /mods: Get a list of all of the moderators in the current channel
        # /mod name-of-user: Grant moderator status to the given user
        #   name-of-user: The username of the user that you want to grant moderator status
        # /unmod name-of-user: Revoke moderator status from the given user
        #   name-of-user: The username of the user that you want to revoke moderator status from

    def ban_user(self, nick):
        self.bandict[nick] = 1

    def unban_user(self, nick):
        if nick in self.bandict:
            del self.bandict[nick]

    def is_banned(self, nick):
        return nick in self.bandict

    def banned_users(self):
        return self.bandict.keys()

    def ignore_user(self, nick):
        self.ignoredict[nick] = 1

    def unignore_user(self, nick):
        if nick in self.ignoredict:
            del self.ignoredict[nick]

    def is_ignored(self, nick):
        return nick in self.ignoredict

    def ignored_users(self):
        return self.ignoredict.keys()


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

        self.nickname = nickname
        self.commands = ['disconnect', 'join', 'part', 'nick', 'slow', 'slowoff',
                         'subscribers', 'subscribersoff', 'ban', 'unban', 'ignore', 'unignore', 'mod', 'unmod']

        for i in self.commands:
            self.connection.add_global_handler(i, getattr(self, "_on_" + i), -10)

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

    def _on_disconnect(self, c, e):
        self.channels = IRCDict()
        self.connection.execute_delayed(self.reconnection_interval,
                                        self._connected_checker)

    def _on_join(self, c, e):
        ch = e.target
        nick = e.source.nick
        if nick == c.get_nickname():
            self.channels[ch] = TwitchChannel()
        self.channels[ch].add_user(nick)
        print 'joined %s' % ch

    def _on_part(self, c, e):
        channel = e.target
        nick = e.source.nick
        if nick == c.get_nickname():
            del self.channels[channel]
        else:
            self.channels[channel].remove_user(nick)

    def _on_nick(self, c, e):
        before = e.source.nick
        after = e.target
        for ch in self.channels.values():
            if ch.has_user(before):
                ch.change_nick(before, after)

    def _on_slow(self, c, e):
        print 'slow %s' % e.arguments[0]
        channel = e.target
        try:
            channel.slow_interval = max(2, int(e.arguments[0]))
        except:
            pass

    def _on_slowoff(self, c, e):
        channel = e.target
        channel.slow_interval = 2
        print 'slowoff'

    def _on_subscribers(self, c, e):
        channel = e.target
        channel.subscribers_only = True
        print 'subscribers'

    def _on_subscribersoff(self, c, e):
        channel = e.target
        channel.subscribers_only = False
        print 'subscribersoff'

    def _on_ban(self, c, e):
        channel = e.target
        nick = e.arguments[0]
        channel.ban_user(nick)
        print 'ban %s' % nick

    def _on_unban(self, c, e):
        channel = e.target
        nick = e.arguments[0]
        channel.unban_user(nick)
        print 'unban %s' % nick

    def _on_ignore(self, c, e):
        channel = e.target
        nick = e.arguments[0]
        channel.ignore_user(nick)
        print 'ignore %s' % nick

    def _on_unignore(self, c, e):
        channel = e.target
        nick = e.arguments[0]
        channel.unignore_user(nick)
        print 'unignore %s' % nick

    def _on_mod(self, c, e):
        channel = e.target
        nick = e.arguments[0]
        channel.set_mode('o', nick)
        print 'mod %s' % nick

    def _on_unmod(self, c, e):
        channel = e.target
        nick = e.arguments[0]
        channel.clear_mode('o', nick)
        print 'unmod %s' % nick

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        for ch in self.channel_list:
            c.join(ch)

    def on_privmsg(self, c, e):
        print 'privmsg: %s' % ' '.join(e.arguments)

    def on_pubmsg(self, c, e):
        print 'pubmsg: %s' % ' '.join(e.arguments)

    def on_dccmsg(self, c, e):
        pass

    def on_dccchat(self, c, e):
        pass

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
