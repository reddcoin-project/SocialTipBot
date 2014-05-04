__author__ = 'laudney'


from datetime import date, datetime
import time
import sys
import re
import traceback

import praw
import praw.helpers
from praw.handlers import MultiprocessHandler

from sqlitedict import SqliteDict
import smtplib
from email.mime.text import MIMEText

import gevent
import gevent.monkey
gevent.monkey.patch_all()


ignored_users = ['ReddcoinRewards', 'reddtipbot', 'dogecointip', 'bitcointip']
db_campaign = SqliteDict('tipping_campaign.db', autocommit=True)
db_progress = SqliteDict('tipping_progress.db', autocommit=True)


def _login():
    reddit = praw.Reddit(user_agent='Reddcoin Comment Stream Tipbot', handler=MultiprocessHandler())
    reddit.login('ReddcoinRewards', 'phd51blognewstartreddr')
    return reddit


def _regex():
    init = '(\+?/u/ReddcoinRewards)'
    subreddit = '(\w{3,20})'
    keyword = '(\#?\w{3,20})'
    number = '([0-9]{1,6})'
    amount = '([0-9]{1,6})'
    regex = '%s %s %s %s %s' % (init, subreddit, keyword, number, amount)
    return re.compile(regex, re.IGNORECASE | re.DOTALL)


def _campaign(author, subreddit, keyword, number, amount):
    reddit = _login()
    key = '_'.join((author, subreddit, keyword))
    print 'Campaign started: %s' % key

    stream = praw.helpers.comment_stream(reddit, subreddit, limit=None, verbosity=3)
    for comment in stream:
        author = comment.author.name
        if author in ignored_users:
            continue

        text = comment.body.lower()
        if keyword in text:
            already = False
            for r in comment.replies:
                if str(r.author) == 'ReddcoinRewards':
                    already = True
                    break

            if not already:
                confo = '+/u/reddtipbot %s RDD' % amount
                comment.reply(confo)
                if db_progress[key] == 1:
                    break
                else:
                    db_progress[key] -= 1


if __name__ == '__main__':
    reddit = _login()
    stream = praw.helpers.comment_stream(reddit, 'rddtest', limit=None, verbosity=3)
    rg = _regex()
    for comment in stream:
        author = comment.author.name
        if author in ignored_users:
            continue

        text = comment.body.lower()
        m = rg.search(text)
        if m:
            subreddit, keyword, number, amount = m.groups()[1:]
            already = False
            for r in comment.replies:
                if str(r.author) == 'ReddcoinRewards':
                    already = True
                    break

            if not already:
                key = '_'.join((author, subreddit, keyword))
                db_campaign[key] = (number, amount)
                fmt = 'confirmed: %s giving %s people in /r/%s %s RDD for keyword %s'
                confo = fmt % (author, number, subreddit, amount, keyword)
                comment.reply(confo)

                db_progress[key] = int(number)
                gevent.spawn(_campaign, author, subreddit, keyword, number, amount)
