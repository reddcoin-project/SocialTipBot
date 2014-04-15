__author__ = 'laudney'


from datetime import date, datetime
from pprint import pprint
import praw
import sys
import time
import traceback
from jinja2 import Environment, FileSystemLoader
import smtplib
from email.mime.text import MIMEText
from collections import defaultdict
import pandas as pd
import numpy as np


_ignore_users = ['reddtipbot', 'ReddcoinRewards']
_vote_threshold = 20


def _login():
    reddit = praw.Reddit(user_agent='Reddcoin Karma Tipbot')
    reddit.login('ReddcoinRewards', 'phd51blognewstartreddr')
    return reddit


def _full_score(subreddit):
    submissions = subreddit.search('*', period='day', sort='new', limit=None)

    submission_obj = []
    submission_score = defaultdict(dict)
    comment_score = defaultdict(dict)
    reply_score = {}

    for s in submissions:
        submission_obj.append(s)
        submission_score[str(s.author)][s.name] = s.score

    for s in submission_obj:
        s.replace_more_comments(limit=None)
        comments = praw.helpers.flatten_tree(s.comments)
        for c in comments:
            author = str(c.author)
            if author not in _ignore_users:
                comment_score[author][c.name] = c.score
                reply_score[author] = reply_score.get(author, 0) + len(c.replies)

    s_submission = pd.Series({k: np.sum(v.values()) for k, v in submission_score.items()})
    s_comment = pd.Series({k: np.sum(v.values()) for k, v in comment_score.items()})
    s_reply = pd.Series(reply_score)

    s_submission.name = 'submission_net_votes'
    s_comment.name = 'comment_net_votes'
    s_reply.name = 'comment_replies'
    full_score = pd.concat([s_submission, s_comment, s_reply], axis=1).fillna(value=0)
    full_score['total_karma'] = full_score.sum(axis=1)
    full_score = full_score.ix[full_score.index - _ignore_users]
    full_score.sort(columns='total_karma', ascending=False, inplace=True)
    full_score.index.name = 'username'
    full_score.reset_index(inplace=True)
    full_score.index = map(str, range(1, len(full_score) + 1))
    full_score.index.name = 'ranking'
    full_score.set_index('username', append=True, inplace=True)
    return full_score


def _top_posts(subreddit):
    submissions = subreddit.search('*', period='day', sort='new', limit=None)

    # just to make sure returned posts are not double-counted
    submission_rewards = {}
    comment_rewards = defaultdict(list)

    for s in submissions:
        if not s.stickied and s.score >= _vote_threshold:
            submission_rewards[s.name] = s

    for k, s in submission_rewards.iteritems():
        comment_authors = []
        s.replace_more_comments(limit=None)
        comments = praw.helpers.flatten_tree(s.comments)
        for c in comments:
            if c.body == '[deleted]':
                continue

            author = str(c.author)
            if _already_awarded(c):
                comment_authors.append(author)
            elif author not in _ignore_users and author not in comment_authors and c.score > 0:
                comment_rewards[k].append(c)
                comment_authors.append(author)

    return submission_rewards, comment_rewards


def _already_awarded(content):
    if isinstance(content, praw.objects.Comment):
        a = content.replies
    elif isinstance(content, praw.objects.Submission):
        a = content.comments
    else:
        return True

    for r in a:
        if str(r.author) == 'ReddcoinRewards':
            return True

    return False


def _send_email(msg=None):
    # Construct MIME message
    msg = MIMEText(msg)
    addr = 'tipreddcoin@gmail.com'
    msg['Subject'] = 'Karma Tipbot Error'
    msg['From'] = addr
    msg['To'] = addr

    # Send MIME message
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(addr, 'phd51blognewstarttipg')
    server.sendmail(addr, addr, msg.as_string())
    server.quit()


if __name__ == '__main__':
    reddit = _login()
    subreddit = reddit.get_subreddit('reddCoin')
    jenv = Environment(trim_blocks=True, loader=FileSystemLoader('.'))

    while True:
        try:
            if datetime.utcnow().hour == 22:
                full_score = _full_score(subreddit)
                df = full_score.applymap(lambda x: str(int(x))).iloc[:10].reset_index()
                msg = jenv.get_template('karma.tpl').render(df=df)
                subject = 'Top Contributors %s' % date.today()
                post = reddit.submit(subreddit, subject, msg)
        except Exception as e:
            tb = traceback.format_exc()
            print tb
            _send_email(msg=tb)

        try:
            submission_rewards, comment_rewards = _top_posts(subreddit)
            for k, comment in comment_rewards.items():
                s = submission_rewards[k]
                if not _already_awarded(s):
                    # print '================================'
                    # print s.title
                    # print '================================'
                    s.add_comment("**Reddcoin Bonus Rewards have been unlocked for this post!!** +/u/reddtipbot 100 RDD")

                for c in comment:
                    if not _already_awarded(c):
                        # print '---------------------------------'
                        # print c.body
                        # print '---------------------------------'
                        text = "You are receiving Reddcoin Bonus Rewards for active participation in community."
                        text += " Thank you. +/u/reddtipbot 100 RDD"
                        c.reply(text)

            print '%s: Sleeping for 1h' % datetime.utcnow()
            time.sleep(3600)
        except KeyboardInterrupt as e:
            sys.exit(1)
        except Exception as e:
            tb = traceback.format_exc()
            print tb
            _send_email(msg=tb)
            print '%s: Sleeping for 1h' % datetime.utcnow()
            time.sleep(3600)
