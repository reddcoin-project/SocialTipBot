__author__ = 'laudney'

import logging
from dateutil.parser import parse
from twython import TwythonStreamer

from ctb_network import CtbNetwork
import ctb_action
import ctb_misc


lg = logging.getLogger('cointipbot')


class TwitterStreamer(TwythonStreamer):
    def on_success(self, data):
        fields = ['created_at', 'user', 'entities', 'text']
        if all(field in data for field in fields):
            created_at = parse(data['created_at'])
            author = data['user']['screen_name']
            mentions = [um['screen_name'] for um in data['entities']['user_mentions']]
            msg = data['text']
            print created_at, author, mentions, msg

    def on_error(self, status_code, data):
        print status_code

    def on_timeout(self):
        pass


class TwitterNetwork(CtbNetwork):
    def __init__(self, conf, db):
        CtbNetwork.__init__(self, "twitter")
        self.conf = conf
        self.db = db
        self.user = conf.auth.user
        self.app_key = conf.auth.app_key
        self.app_secret = conf.auth.app_secret
        self.oauth_token = conf.auth.oauth_token
        self.oauth_token_secret = conf.auth.oauth_token_secret
        self.conn = None

    def connect(self):
        """
        Returns a Twitter stream object
        """
        lg.debug('TwitterNetwork::connect(): connecting to Twitter...')
        self.conn = TwitterStreamer(self.app_key, self.app_secret, self.oauth_token, self.oauth_token_secret)
        lg.info("TwitterNetwork::connect(): logged in to Twitter")
        return self.conn

    def is_user_banned(self, user):
        return False

    def send_msg(self, user_to, subject, body, editor, msgobj):
        pass

    def reply_msg(self, body, msgobj):
        pass

    def check_mentions(self, ctb):
        self.conn.user()
