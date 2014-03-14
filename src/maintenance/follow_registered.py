__author__ = 'bren'


import time
import random
import traceback
from twython import Twython, TwythonStreamer, TwythonRateLimitError, TwythonError
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, Numeric, UnicodeText
from sqlalchemy.pool import SingletonThreadPool


if __name__ == '__main__':
    # connect to database
    metadata = MetaData()
    dsn_url = 'sqlite:///../db/twitter-live1.db'
    engine = create_engine(dsn_url, echo_pool=True, poolclass=SingletonThreadPool,
                           execution_options={'autocommit': True})
    metadata.create_all(engine)
    db = engine.connect()

    # find all successfully registered users
    registered = []
    sql = "SELECT from_user FROM t_action where type = 'register' and state = 'completed'"
    for sqlrow in db.execute(sql):
        registered.append(sqlrow['from_user'])

    # now follow these registered users
    user = 'tipreddcoin'
    app_key = '9HDzugNwT22Xlcw0EGQfg'
    app_secret = '8OjJWIdIpErtBd8RcYAhwt9kixoIfOPA1GiM6mf0M'
    oauth_token = '2357688096-NtaUt52rHmqCCX2hz9t1gEcTjMnEbsvdX0pRZqp'
    oauth_token_secret = 'TjUHsf68MWCRzCtjjhB05S6OEdCjPMQIU00rL8dH0SH5a'

    twitter = Twython(app_key, app_secret, oauth_token, oauth_token_secret)
    for screen_name in registered:
        if screen_name == 'tipreddcoin':
            continue

        try:
            twitter.create_friendship(screen_name=screen_name)
        except TwythonError as e:
            # either really failed (e.g. sent request before) or already friends
            print "failed to follow user %s: %s" % (user, e.msg)
            tb = traceback.format_exc()
            print tb
            break

        # random interval
        time.sleep(random.randrange(5, 15))
