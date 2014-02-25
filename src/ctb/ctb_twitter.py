__author__ = 'laudney'


import traceback
import calendar
import re
import logging
from dateutil.parser import parse
from twython import Twython, TwythonStreamer, TwythonError

from ctb_network import CtbNetwork
import ctb_action
import ctb_misc


lg = logging.getLogger('cointipbot')


class TwitterStreamer(TwythonStreamer):
    @classmethod
    def _timestamp_utc(cls, dt):
        if isinstance(dt, basestring):
            dt = parse(dt)

        return calendar.timegm(dt.utctimetuple())

    def follow_followers(self):
        lg.debug('TwitterStreamer::follow_followers(): checking followers...')

        followers = []
        for fid in self.conn.cursor(self.conn.get_followers_ids):
            followers.append(fid)

        friends = []
        for fid in self.conn.cursor(self.conn.get_friends_ids):
            friends.append(fid)

        pending = []
        for fid in self.conn.cursor(self.conn.get_outgoing_friendship_ids):
            pending.append(fid)

        to_follow = list(set(followers).difference(set(friends)).difference(set(pending)))

        actions = []
        for user_id in to_follow:
            try:
                resp = self.conn.create_friendship(user_id=user_id)
            except TwythonError as e:
                # either really failed (e.g. sent request before) or already friends
                lg.warning("TwitterStreamer::follow_followers: failed to follow user %s: %s", user_id, e.msg)
                continue
            else:
                lg.debug('TwitterStreamer::follow_followers(): just sent request to follow user %s', user_id)

            msg = {'id': str(user_id),
                   'created_utc': self._timestamp_utc(resp['created_at']),
                   'author': {'name': resp['screen_name']},
                   'body': '+register',
                   'type': 'mention'}
            # make the msg id unique
            msg['id'] += ('@' + str(msg['created_utc']))

            action = ctb_action.eval_message(ctb_misc.DotDict(msg), self.ctb)
            actions.append(action)

        return actions

    def _parse_event(self, data):
        actions = self.follow_followers()
        return actions

    def _parse_mention(self, data):
        author_name = data['user']['screen_name']
        if author_name == self.username or '@' + self.username not in data['text']:
            return None

        # we do allow the bot to issue commands
        msg = {'created_utc': self._timestamp_utc(data['created_at']),
               'author': {'name': author_name},
               'type': 'mention'}
        msg['id'] = str(data['id'] + msg['created_utc'])

        text = data['text']
        msg['body'] = text.replace('@' + self.username, '').strip()
        print msg

        action = ctb_action.eval_message(ctb_misc.DotDict(msg), self.ctb)
        return action

    def _parse_direct_msg(self, data):
        # ignore direct message from the bot itself
        author_name = data['sender']['screen_name']
        if author_name == self.username:
            return None

        msg = {'created_utc': self._timestamp_utc(data['created_at']),
               'author': {'name': author_name},
               'type': 'direct_message'}
        msg['id'] = str(data['id'] + msg['created_utc'])

        text = data['text']
        msg['body'] = text.replace('@' + self.username, '').strip()
        print msg

        action = ctb_action.eval_message(ctb_misc.DotDict(msg), self.ctb)
        return action

    def on_success(self, data):
        fields = ['created_at', 'id', 'user', 'entities', 'text']
        if all(field in data for field in fields):
            # received a mention
            actions = self._parse_mention(data)
        elif 'direct_message' in data:
            # received a direct message
            actions = self._parse_direct_msg(data['direct_message'])
        elif 'event' in data:
            actions = self._parse_event(data)
        else:
            print data
            return

        if not isinstance(actions, list):
            actions = [actions]

        for action in actions:
            if action:
                lg.info("TwitterStreamer::on_success(): %s from %s", action.type, action.u_from.name)
                lg.debug("TwitterStreamer::on_success(): comment body: <%s>", action.msg.body)
                action.do()

    def on_error(self, status_code, data):
        print status_code

    def on_timeout(self):
        actions = self.follow_followers()
        for action in actions:
            if action:
                lg.info("TwitterStreamer::on_timeout(): %s from %s", action.type, action.u_from.name)
                lg.debug("TwitterStreamer::on_timeout(): comment body: <%s>", action.msg.body)
                action.do()


class TwitterNetwork(CtbNetwork):
    def __init__(self, conf, ctb):
        CtbNetwork.__init__(self, "twitter")
        self.conf = conf
        self.ctb = ctb
        self.db = ctb.db
        self.user = conf.auth.user
        self.app_key = conf.auth.app_key
        self.app_secret = conf.auth.app_secret
        self.oauth_token = conf.auth.oauth_token
        self.oauth_token_secret = conf.auth.oauth_token_secret
        self.conn = None
        self.stream = None

    def connect(self):
        """
        Returns a Twitter stream object
        """
        lg.debug('TwitterNetwork::connect(): connecting to Twitter...')

        self.conn = Twython(self.app_key, self.app_secret, self.oauth_token, self.oauth_token_secret)
        self.stream = TwitterStreamer(self.app_key, self.app_secret, self.oauth_token, self.oauth_token_secret,
                                      timeout=30)
        self.conn.username = self.stream.username = self.user
        self.stream.conn = self.conn
        self.stream.ctb = self.ctb

        lg.info("TwitterNetwork::connect(): logged in to Twitter")
        return None

    def is_user_banned(self, user):
        return False

    def send_msg(self, user_to, subject, body, editor=None, msgobj=None):
        try:
            if msgobj:
                self.reply_msg(body, msgobj)
            else:
                lg.debug("< TwitterNetwork::send_msg: sending direct message to %s: %s", user_to, body)
                self.conn.send_direct_message(screen_name=user_to, text=body[:140])
                lg.debug("< TwitterNetwork::send_msg to %s DONE", user_to)

        except TwythonError as e:
            lg.error("TwitterNetwork::send_msg: exception: %s", e)
            tb = traceback.format_exc()
            lg.error("TwitterNetwork::send_msg: traceback: %s", tb)
            return False
        else:
            return True

    def reply_msg(self, body, msgobj):
        try:
            if msgobj is None:
                pass
            elif msgobj.type == 'mention':
                body += ' #ReddCoin'
                lg.debug("< TwitterNetwork::reply_msg: sending tweet to %s: %s", msgobj.author.name, body)
                self.conn.update_status(status=body[:140])
                lg.debug("< TwitterNetwork::reply_msg to %s DONE", msgobj.author.name)
            elif msgobj.type == 'direct_message':
                lg.debug("< TwitterNetwork::reply_msg: sending direct message to %s: %s", msgobj.author.name, body)
                self.conn.send_direct_message(screen_name=msgobj.author.name, text=body[:140])
                lg.debug("< TwitterNetwork::reply_msg to %s DONE", msgobj.author.name)

        except TwythonError as e:
            lg.error("TwitterNetwork::reply_msg: exception: %s", e)
            tb = traceback.format_exc()
            lg.error("TwitterNetwork::reply_msg: traceback: %s", tb)
            return False
        else:
            return True

    def check_mentions(self, ctb):
        actions = self.stream.follow_followers()
        for action in actions:
            if action:
                lg.info("TwitterNetwork::check_mentions(): %s from %s", action.type, action.u_from.name)
                lg.debug("TwitterNetwork::check_mentions(): comment body: <%s>", action.msg.body)
                action.do()

        self.stream.user()

    def invite(self, user):
        try:
            resp = self.conn.create_friendship(screen_name=user)

        except TwythonError as e:
            # either really failed (e.g. sent request before) or already friends
            lg.warning("TwitterNetwork::invite: failed to follow user %s: %s", user, e.msg)
            lg.error("TwitterNetwork::invite: exception: %s", e)
            tb = traceback.format_exc()
            lg.error("TwitterNetwork::invite: traceback: %s", tb)
            return False
        else:
            lg.debug('TwitterNetwork::invite(): just sent request to follow user %s', user)
            return True
