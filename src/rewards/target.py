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

        text = comment.body
        if keyword.lower() in text.lower():
            already = False
            for r in comment.replies:
                if str(r.author) == 'ReddcoinRewards':
                    already = True
                    break

            if not already:
                confo = '+/u/reddtipbot @%s %s RDD' % (author, amount)
                reddit.send_message('reddtipbot', key, confo)
                if db_progress[key] <= 1:
                    break
                else:
                    db_progress[key] -= 1


def _send_email(msg=None):
    if not msg:
        return

    # Construct MIME message
    msg = MIMEText(msg)
    addr = 'tipreddcoin@gmail.com'
    msg['Subject'] = 'Target Tipbot Error'
    msg['From'] = addr
    msg['To'] = addr

    # Send MIME message
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(addr, 'phd51blognewstarttipg')
    server.sendmail(addr, addr, msg.as_string())
    server.quit()


def _load():
    print 'Loading campaigns:'

    for key, val in iter(db_campaign.items()):
        author, subreddit, keyword = key.split('_')
        number, amount = val
        print author, subreddit, keyword, number, amount
        gevent.spawn(_campaign, author, subreddit, keyword, number, amount)

    print 'Finished loading campaigns.'

if __name__ == '__main__':
    # _load()

    reddit = _login()
    stream = praw.helpers.comment_stream(reddit, 'reddcoinVIP', limit=None, verbosity=3)
    rg = _regex()
    for comment in stream:
        try:
            author = comment.author.name
            if author in ignored_users:
                continue

            text = comment.body
            m = rg.search(text)
            if m:
                subreddit, keyword, number, amount = m.groups()[1:]
                number = int(number)
                amount = int(amount)
                already = False
                for r in comment.replies:
                    if str(r.author) == 'ReddcoinRewards':
                        already = True
                        break

                if not already:
                    key = '_'.join((author, subreddit, keyword))
                    db_campaign[key] = (number, amount)

                    spawn = True
                    if key in db_progress:
                        spawn = False

                    db_progress[key] = number
                    if spawn:
                        gevent.spawn(_campaign, author, subreddit, keyword, number, amount)

                    fmt = 'confirmed: %s giving %s people in /r/%s %s RDD for keyword %s'
                    confo = fmt % (author, number, subreddit, amount, keyword)
                    comment.reply(confo)

        except Exception as e:
            tb = traceback.format_exc()
            print tb
            _send_email(msg=tb)
            print '%s: Sleeping for 60s' % datetime.utcnow()
            time.sleep(60)
