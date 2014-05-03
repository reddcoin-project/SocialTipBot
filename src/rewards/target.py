__author__ = 'laudney'


from datetime import date, datetime
from pprint import pprint
import praw
import praw.helpers
import sys
import re
import time
import traceback
from jinja2 import Environment, FileSystemLoader
import smtplib
from email.mime.text import MIMEText
from collections import defaultdict
import pandas as pd
import numpy as np


def _login():
    reddit = praw.Reddit(user_agent='Reddcoin Comment Stream Tipbot')
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


if __name__ == '__main__':
    reddit = _login()
    stream = praw.helpers.comment_stream(reddit, 'rddtest', limit=None, verbosity=3)
    rg = _regex()
    for comment in stream:
        author = comment.author
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
                confo = 'confirmed: %s giving %s people in /r/%s %s RDD for keyword %s' % (author, number, subreddit,
                                                                                        amount, keyword)
                comment.reply(confo)
