__author__ = 'laudney'


from datetime import date, datetime
from pprint import pprint
import praw
import praw.helpers
import sys
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


if __name__ == '__main__':
    reddit = _login()
    subreddit = reddit.get_subreddit('rddtest')
    stream = praw.helpers.comment_stream(reddit, 'rddtest', limit=None, verbosity=3)
    for comment in stream:
        text = comment.body.lower()
        if '#socialcurrency' in text:
            already = False
            replies = comment.replies
            for r in replies:
                if str(r.author) == 'ReddcoinRewards':
                    already = True
                    break

            if not already:
                comment.reply('I hear you!!')
