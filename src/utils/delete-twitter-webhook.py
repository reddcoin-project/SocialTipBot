__author__ = 'gnasher'

import os
import sys

import logging
import yaml
import glob
import ntpath
import json
from twython import Twython, TwythonStreamer, TwythonRateLimitError, TwythonError

# Hack around absolute paths
current_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.abspath(current_dir + "/../")

sys.path.insert(0, parent_dir)

from ctb import ctb_log, ctb_misc

# Configure logger
logging.basicConfig()
lg = logging.getLogger('cointipbot')


def init_logging():
    """
    Initialize logging handlers
    """

    levels = ['warning', 'info', 'debug']
    bt = logging.getLogger('bitcoin')

    # Get handlers
    handlers = {}
    for l in levels:
        if conf.logs.levels[l].enabled:
            handlers[l] = logging.FileHandler(conf.logs.levels[l].filename,
                                              mode='a' if conf.logs.levels[l].append else 'w')
            handlers[l].setFormatter(logging.Formatter(conf.logs.levels[l].format))

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

def parse_config():
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


conf = parse_config()
twitter_conf = conf.twitter.twitter
init_logging()

CONSUMER_KEY = twitter_conf.auth.app_key
CONSUMER_SECRET = twitter_conf.auth.app_secret

ACCESS_TOKEN = twitter_conf.auth.oauth_token
ACCESS_TOKEN_SECRET = twitter_conf.auth.oauth_token_secret

ENVNAME = twitter_conf.auth.envname
WEBHOOK_ID = twitter_conf.auth.webhook_id

twitterconn = Twython(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

resp = resp = twitterconn.delete('account_activity/all/%s/webhooks/%s' % (ENVNAME, WEBHOOK_ID))


