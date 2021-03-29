__author__ = 'bren'

import time
import random
import traceback
from twython import Twython, TwythonStreamer, TwythonRateLimitError, TwythonError
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, Numeric, UnicodeText
from sqlalchemy.pool import SingletonThreadPool
import yaml


if __name__ == '__main__':
    # connect to database
    metadata = MetaData()
    #dsn_url = 'sqlite:///../db/twitter-live1.db'
    with open(r'../conf/db.yml') as file:
        conf = yaml.full_load(file)

    dsn_url = "mysql+mysqldb://%s:%s@%s:%s/%s?charset=utf8" % (conf["auth"]["user"], conf["auth"]["password"], conf["auth"]["host"], conf["auth"]["port"], conf["auth"]["dbname"])
    engine = create_engine(dsn_url, echo_pool=True, poolclass=SingletonThreadPool,
                           execution_options={'autocommit': True})
    metadata.create_all(engine)
    db = engine.connect()

    # find all successfully registered users
    registered = []
    sql = "SELECT from_user FROM t_action WHERE type = 'register' AND state = 'completed'"
    for sqlrow in db.execute(sql):
        registered.append(sqlrow['from_user'])

    # now follow these registered users
    with open(r'../conf/twitter/twitter.yml') as file:
        conf = yaml.full_load(file)
    user = conf["auth"]["user"]
    app_key = conf["auth"]["app_key"]
    app_secret = conf["auth"]["app_secret"]
    oauth_token = conf["auth"]["oauth_token"]
    oauth_token_secret = conf["auth"]["oauth_token_secret"]

    twitter = Twython(app_key, app_secret, oauth_token, oauth_token_secret)

    followers = []
    for fid in twitter.cursor(twitter.get_followers_ids, count=5000):
        followers.append(fid)

    print("Followers Count: ", len(followers))

    friends = []
    for fid in twitter.cursor(twitter.get_friends_ids, count=5000):
        friends.append(fid)

    print("Friends Count: ",len(friends))

    pending = []
    for fid in twitter.cursor(twitter.get_outgoing_friendship_ids):
        pending.append(fid)

    print("Pending Count: ",len(pending))

    to_follow = [f for f in registered if f not in friends and f not in pending]

    print("To Follow Count: ",len(to_follow))

    for screen_name in to_follow:
        if screen_name == 'tipreddcoin':
            continue

        try:
            print("Requesting to follow: ", screen_name)
            twitter.create_friendship(screen_name=screen_name)
        except TwythonError as e:
            # either really failed (e.g. sent request before) or already friends
            print("failed to follow user %s: %s" % (screen_name, e.msg))
            # tb = traceback.format_exc()
            # print(tb)

        # random interval
        time.sleep(random.randrange(5, 15))

