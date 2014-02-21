import logging
import praw
import time
from requests.exceptions import HTTPError, ConnectionError, Timeout
from praw.errors import ExceptionList, APIException, InvalidCaptcha, InvalidUser, RateLimitExceeded
from socket import timeout

import ctb_action
import ctb_misc


lg = logging.getLogger('cointipbot')


class CtbNetwork(object):
    def __init__(self, name):
        self.name = name

    def connect(self):
        pass

    def is_connected(self, user):
        return False

    def send_msg(self, from_user, to_user, msg):
        pass


class RedditNetwork(CtbNetwork):
    @classmethod
    def praw_call(cls, praw_func, *extra_args, **extra_kwargs):
        """
        Call prawFunc() with extraArgs and extraKwArgs
        Retry if Reddit is down
        """
        while True:
            try:
                res = praw_func(*extra_args, **extra_kwargs)
                return res

            except (HTTPError, ConnectionError, Timeout, timeout) as e:
                if str(e) in ["400 Client Error: Bad Request",
                              "403 Client Error: Forbidden",
                              "404 Client Error: Not Found"]:
                    lg.warning("praw_call(): Reddit returned error (%s)", e)
                    return False
                else:
                    lg.warning("praw_call(): Reddit returned error (%s), sleeping...", e)
                    time.sleep(30)
                    pass
            except RateLimitExceeded as e:
                lg.warning("praw_call(): rate limit exceeded, sleeping for %s seconds", e.sleep_time)
                time.sleep(e.sleep_time)
                time.sleep(1)
                pass
            except APIException as e:
                if str(e) == "(DELETED_COMMENT) `that comment has been deleted` on field `parent`":
                    lg.warning("praw_call(): deleted comment: %s", e)
                    return False
                else:
                    raise
            except Exception as e:
                raise

        return True

    def __init__(self, conf, db):
        CtbNetwork.__init__(self, "reddit")
        self.conf = conf
        self.db = db
        self.user = conf.auth.user
        self.password = conf.auth.password
        self.conn = None

    def connect(self):
        """
        Returns a praw connection object
        """
        lg.debug('RedditNetwork::connect(): connecting to Reddit...')

        conn = praw.Reddit(user_agent=self.user)
        conn.login(self.user, self.password)
        self.conn = conn

        lg.info("RedditNetwork::connect(): logged in to Reddit as %s", self.user)
        return conn

    def is_user_banned(self, user):
        if self.conf.banned_users:
            if self.conf.banned_users.method == 'subreddit':
                for u in self.conn.get_banned(self.conf.banned_users.subreddit):
                    if user.lower() == u.name.lower():
                        return True
            elif self.conf.banned_users.method == 'list':
                for u in self.conf.banned_users.list:
                    if user.lower() == u.lower():
                        return True
        return False

    def get_parent_author(self, comment, sleep_seconds):
        """
        Return author of comment's parent comment
        """
        lg.debug("> RedditNetwork::get_parent_author()")
        lg.debug("> RedditNetwork::get_parent_author()")

        while True:
            try:
                parentpermalink = comment.permalink.replace(comment.id, comment.parent_id[3:])
                if hasattr(comment, 'link_id'):
                    commentlinkid = comment.link_id[3:]
                else:
                    comment2 = self.conn.get_submission(comment.permalink).comments[0]
                    commentlinkid = comment2.link_id[3:]
                parentid = comment.parent_id[3:]

                if commentlinkid == parentid:
                    parentcomment = self.conn.get_submission(parentpermalink)
                else:
                    parentcomment = self.conn.get_submission(parentpermalink).comments[0]

                if parentcomment and hasattr(parentcomment, 'author') and parentcomment.author:
                    lg.debug("< RedditNetwork::get_parent_author(%s) -> %s", comment.id, parentcomment.author.name)
                    return parentcomment.author.name
                else:
                    lg.warning("< RedditNetwork::get_parent_author(%s) -> NONE", comment.id)
                    return None
            except (IndexError, APIException) as e:
                lg.warning("RedditNetwork::get_parent_author(): couldn't get author: %s", e)
                return None
            except (HTTPError, RateLimitExceeded, timeout) as e:
                if str(e) in ["400 Client Error: Bad Request", "403 Client Error: Forbidden",
                              "404 Client Error: Not Found"]:
                    lg.warning("RedditNetwork::get_parent_author(): Reddit returned error (%s)", e)
                    return None
                else:
                    lg.warning("get_parent_author(): Reddit returned error (%s), sleeping...", e)
                    time.sleep(sleep_seconds)
                    pass
            except Exception:
                raise

        lg.error("RedditNetwork::get_parent_author(): returning None (should not get here)")
        return None

    def init_subreddits(self):
        """
        Determine a list of subreddits and create a PRAW object
        """
        lg.debug("> RedditNetwork::init_subreddits()")

        try:
            if not hasattr(self.conf, 'subreddits'):
                if hasattr(self.conf.scan, 'these_subreddits'):
                    # Subreddits are specified in conf.yml
                    my_reddits_list = list(self.conf.scan.these_subreddits)

                elif self.conf.scan.my_subreddits:
                    # Subreddits are subscribed to by bot user
                    my_reddits = self.praw_call(self.conn.get_my_subreddits, limit=None)
                    my_reddits_list = []
                    for my_reddit in my_reddits:
                        my_reddits_list.append(my_reddit.display_name.lower())
                    my_reddits_list.sort()

                else:
                    # No subreddits configured
                    lg.debug("< RedditNetwork::init_subreddits() DONE (no subreddits configured to scan)")
                    return False

                # Build subreddits string
                my_reddits_string = "+".join(my_reddits_list)

                # Get multi-reddit PRAW object
                lg.debug("RedditNetwork::init_subreddits(): multi-reddit string: %s", my_reddits_string)
                self.conf.subreddits = self.praw_call(self.conn.get_subreddit, my_reddits_string)
        except Exception as e:
            lg.error("RedditNetwork::init_subreddits(): couldn't get subreddits: %s", e)
            raise

        lg.debug("< RedditNetwork::init_subreddits() DONE")
        return True

    def check_subreddits(self):
        """
        Evaluate new comments from self.configured subreddits
        """
        lg.debug("> RedditNetwork::check_subreddits()")
        updated_last_processed_time = 0

        try:
            # Process comments until old comment reached
            # Get last_processed_comment_time if necessary
            if not hasattr(self.conf, 'last_processed_comment_time') or self.conf.last_processed_comment_time <= 0:
                self.conf.last_processed_comment_time = ctb_misc.get_value(conn=self.db,
                                                                           param0='last_processed_comment_time')

            # Fetch comments from subreddits
            my_comments = self.praw_call(self.conf.subreddits.get_comments, limit=self.conf.scan.batch_limit)

            # Match each comment against regex
            counter = 0
            for c in my_comments:
                # Stop processing if old comment reached
                #lg.debug("check_subreddits(): c.id %s from %s, %s <= %s", c.id, c.subreddit.display_name, c.created_utc, self.conf.last_processed_comment_time)
                if c.created_utc <= self.conf.last_processed_comment_time:
                    lg.debug("RedditNetwork::check_subreddits(): old comment reached")
                    break
                counter += 1
                if c.created_utc > updated_last_processed_time:
                    updated_last_processed_time = c.created_utc

                # Ignore duplicate comments (may happen when bot is restarted)
                if ctb_action.check_action(msg_id=c.id, ctb=self):
                    lg.warning("RedditNetwork::check_inbox(): duplicate action detected (comment.id %s), ignoring",
                               c.id)
                    continue

                # Ignore comments from banned users
                if c.author and self.conf.banned_users:
                    lg.debug("RedditNetwork::check_subreddits(): checking whether user '%s' is banned..." % c.author)
                    if self.is_user_banned(c.author.name):
                        lg.info("RedditNetwork::check_subreddits(): ignoring banned user '%s'" % c.author)
                        continue

                # Attempt to evaluate comment
                action = ctb_action.eval_comment(c, self)

                # Perform action, if found
                if action:
                    lg.info("RedditNetwork::check_subreddits(): %s from %s (%s)", action.type, action.u_from.name, c.id)
                    lg.debug("RedditNetwork::check_subreddits(): comment body: <%s>", c.body)
                    action.do()
                else:
                    lg.info("RedditNetwork::check_subreddits(): no match")

            lg.debug("RedditNetwork::check_subreddits(): %s comments processed", counter)
            if counter >= self.conf.scan.batch_limit - 1:
                lg.warning(
                    "RedditNetwork::check_subreddits(): conf.reddit.scan.batch_limit (%s) was not " +
                    "large enough to process all comments", self.conf.scan.batch_limit)

        except (HTTPError, RateLimitExceeded, timeout) as e:
            lg.warning("RedditNetwork::check_subreddits(): Reddit is down (%s), sleeping", e)
            time.sleep(self.conf.misc.times.sleep_seconds)
            pass
        except Exception as e:
            lg.error("RedditNetwork::check_subreddits(): coudln't fetch comments: %s", e)
            raise

        # Save updated last_processed_time value
        if updated_last_processed_time > 0:
            self.conf.last_processed_comment_time = updated_last_processed_time
        ctb_misc.set_value(conn=self.db, param0='last_processed_comment_time',
                           value0=self.conf.last_processed_comment_time)

        lg.debug("< RedditNetwork::check_subreddits() DONE")
        return True