__author__ = 'laudney'

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
                   'created_utc': calendar.timegm(parse(resp['created_at']).utctimetuple()),
                   'author': {'name': resp['screen_name']},
                   'body': '+register'}

            action = ctb_action.eval_message(ctb_misc.DotDict(msg), self.ctb)
            print action

    def _parse_event(self, data):
        self.follow_followers()

    def _parse_mention(self, data):
        msg = {'id': str(data['id']),
               'created_utc': calendar.timegm(parse(data['created_at']).utctimetuple()),
               'author': {'name': data['user']['screen_name']}}

        mentions = [um['screen_name'] for um in data['entities']['user_mentions']]
        targets = set(mentions).difference({msg['author']['name'], self.username})

        text = data['text']
        tokens = re.split('\s+', text)
        commands = [t for t in tokens if t[0] != '@']
        final_tokens = ['@' + self.username]
        if len(targets) > 0:
            final_tokens.append('[' + ' '.join(list(targets)) + ']')

        final_tokens.append(' '.join(commands))
        msg['body'] = ' '.join(final_tokens)
        print msg

        action = ctb_action.eval_message(ctb_misc.DotDict(msg), self.ctb)
        print action
        return action

    def _parse_direct_msg(self, data):
        msg = {'id': str(data['id']),
               'created_utc': calendar.timegm(parse(data['created_at']).utctimetuple()),
               'author': {'name': data['sender']['screen_name']}}

        text = data['text']
        tokens = re.split('\s+', text)
        mentions = [t[1:] for t in tokens if t[0] == '@']
        targets = set(mentions).difference({msg['author']['name'], self.username})
        commands = [t for t in tokens if t[0] != '@']
        final_tokens = ['@' + self.username]
        if len(targets) > 0:
            final_tokens.append('[' + ' '.join(list(targets)) + ']')

        final_tokens.append(' '.join(commands))
        msg['body'] = ' '.join(final_tokens)
        print msg

        action = ctb_action.eval_message(ctb_misc.DotDict(msg), self.ctb)
        print action
        return action

    def on_success(self, data):
        fields = ['created_at', 'id', 'user', 'entities', 'text']
        if all(field in data for field in fields):
            # received a mention
            self._parse_mention(data)
        elif 'direct_message' in data:
            # received a direct message
            self._parse_direct_msg(data['direct_message'])
        elif 'event' in data:
            self._parse_event(data)
        else:
            print data

    def on_error(self, status_code, data):
        print status_code
        self.follow_followers()

    def on_timeout(self):
        pass


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
        self.stream = TwitterStreamer(self.app_key, self.app_secret, self.oauth_token, self.oauth_token_secret)
        self.conn.username = self.stream.username = self.user
        self.stream.conn = self.conn
        self.stream.ctb = self.ctb

        lg.info("TwitterNetwork::connect(): logged in to Twitter")
        return None

    def init(self):
        self.stream.follow_followers()

    def is_user_banned(self, user):
        return False

    def send_msg(self, user_to, subject, body, editor, msgobj):
        pass

    def reply_msg(self, body, msgobj):
        pass

    def check_mentions(self, ctb):
        self.stream.user()
