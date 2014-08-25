__author__ = 'laudney'


from datetime import date, datetime
from pprint import pprint
import praw
import sys
import time
import traceback


def get_parent_author(conn, comment):
    """
    Return author of comment's parent comment
    """

    while True:
        try:
            parentpermalink = comment.permalink.replace(comment.id, comment.parent_id[3:])
            if hasattr(comment, 'link_id'):
                commentlinkid = comment.link_id[3:]
            else:
                comment2 = conn.get_submission(comment.permalink).comments[0]
                commentlinkid = comment2.link_id[3:]
            parentid = comment.parent_id[3:]

            if commentlinkid == parentid:
                parentcomment = conn.get_submission(parentpermalink)
            else:
                parentcomment = conn.get_submission(parentpermalink).comments[0]

            if parentcomment and hasattr(parentcomment, 'author') and parentcomment.author:
                print "< RedditNetwork::get_parent_author(%s) -> %s" % (comment.id, parentcomment.author.name)
                return parentcomment.author.name
            else:
                print "< RedditNetwork::get_parent_author(%s) -> NONE" % comment.id
                return None
        except (IndexError, APIException) as e:
            print "RedditNetwork::get_parent_author(): couldn't get author: %s" % e
            return None
        except (HTTPError, RateLimitExceeded, timeout) as e:
            if str(e) in ["400 Client Error: Bad Request", "403 Client Error: Forbidden",
                          "404 Client Error: Not Found"]:
                print "RedditNetwork::get_parent_author(): Reddit returned error (%s)" % e
                return None
            else:
                print "get_parent_author(): Reddit returned error (%s), sleeping..." % e
                # time.sleep(sleep_seconds)
                pass
        except Exception:
            raise

    print "RedditNetwork::get_parent_author(): returning None (should not get here)"
    return None


if __name__ == '__main__':
    conn = praw.Reddit(user_agent='Debugging')
    # submission = conn.get_submission(submission_id='2dze20')
    # comment = submission.comments[0].replies[0].replies[0]
    submission = conn.get_submission(submission_id='2eemgq')
    comment = submission.comments[1].replies[0].replies[0]

    get_parent_author(conn, comment)