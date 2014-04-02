__author__ = 'laudney'


import praw
from collections import defaultdict
import pandas as pd
import numpy as np


if __name__ == '__main__':
    ignore_users = ['reddtipbot', 'ReddcoinRewards']
    r = praw.Reddit(user_agent='Reddcoin Karma Tipbot')
    subreddit = r.get_subreddit('reddCoin')
    submissions = subreddit.search('*', period='day', sort='new', limit=None)

    submission_obj = []
    submission_score = defaultdict(dict)
    comment_score = defaultdict(dict)
    reply_score = {}

    for s in submissions:
        submission_obj.append(s)
        submission_score[str(s.author)][s.name] = s.score

    for s in submission_obj:
        comments = praw.helpers.flatten_tree(s.comments)
        for c in comments:
            author = str(c.author)
            comment_score[author][c.name] = c.score
            reply_score[author] = reply_score.get(author, 0) + len(c.replies)

    s_submission = pd.Series({k: np.sum(v.values()) for k, v in submission_score.items()})
    s_comment = pd.Series({k: np.sum(v.values()) for k, v in comment_score.items()})
    s_reply = pd.Series(reply_score)

    s_submission.name = 'submission_net_votes'
    s_comment.name = 'comment_net_votes'
    s_reply.name = 'comment_replies'
    full_score = pd.concat([s_submission, s_comment, s_reply], axis=1).fillna(value=0)
    full_score['total_score'] = full_score.sum(axis=1)
    full_score = full_score.ix[full_score.index - ignore_users]
    full_score.sort(columns='total_score', ascending=False, inplace=True)
