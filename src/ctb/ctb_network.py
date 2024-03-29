import logging
import praw
import time
import random
from requests.exceptions import HTTPError, ConnectionError, Timeout
from praw.exceptions import RedditAPIException, ClientException

import socket

import ctb.ctb_action as ctb_action
import ctb.ctb_misc as ctb_misc


lg = logging.getLogger('cointipbot')


class CtbNetwork(object):
    def __init__(self, name):
        self.name = name

    def connect(self):
        pass

    def init(self):
        pass

    def is_user_banned(self, user):
        pass

    def send_msg(self, user_to, subject, body, editor=None, msgobj=None):
        pass

    def reply_msg(self, body, msgobj):
        pass

    def invite(self, user):
        pass

    def check_mentions(self, ctb):
        pass

    def check_inbox(self, ctb):
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

            except (HTTPError, ConnectionError, Timeout, socket.timeout) as e:
                if str(e) in ["400 Client Error: Bad Request",
                              "403 Client Error: Forbidden",
                              "404 Client Error: Not Found"]:
                    lg.warning("praw_call(): Reddit returned error (%s)", e)
                    return False
                else:
                    lg.warning("praw_call(): Reddit returned error (%s), sleeping...", e)
                    time.sleep(30)
                    pass
            except ClientException as e:
                lg.warning("praw_call(): rate limit exceeded, sleeping for %s seconds", e.sleep_time)
                time.sleep(e.sleep_time)
                time.sleep(1)
                pass
            except RedditAPIException as e:
                if str(e) == "(DELETED_COMMENT) `that comment has been deleted` on field `parent`":
                    lg.warning("praw_call(): deleted comment: %s", e)
                    return False
                else:
                    raise
            except Exception:
                raise

        return True

    def __init__(self, conf, ctb):
        CtbNetwork.__init__(self, "reddit")
        self.conf = conf
        self.ctb = ctb
        self.db = ctb.db
        self.user = conf.auth.user
        self.password = conf.auth.password
        self.client_id = conf.auth.client_id
        self.client_secret = conf.auth.client_secret
        self.callback = conf.auth.callback
        self.user_agent = conf.auth.user_agent
        self.refresh_token = conf.auth.refresh_token
        self.port = conf.auth.port
        self.conn = None

    def connect(self):
        """
        Returns a praw connection object
        """
        def receive_connection():
            """Wait for and then return a connected socket..

            Opens a TCP connection on port 65010, and waits for a single client.

            """
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("localhost", self.port))
            server.listen(1)
            client = server.accept()[0]
            server.close()
            return client

        def send_message(client, message):
            """Send message to client and close the connection."""
            print(message)
            client.send(f"HTTP/1.1 200 OK\r\n\r\n{message}".encode("utf-8"))
            client.close()

        lg.debug('RedditNetwork::connect(): connecting to Reddit...')
        conn = praw.Reddit(client_id=self.client_id, client_secret=self.client_secret, redirect_uri=self.callback, user_agent=self.user_agent, refresh_token=self.refresh_token)
        # state = str(random.randint(0, 65000))

        # print("Use this url to authenticate bot on reddit: ", conn.auth.url(['*'], state, duration="permanent"))
        # # print auth url and wait for connection
        # client = receive_connection()
        # data = client.recv(1024).decode("utf-8")
        # param_tokens = data.split(" ", 2)[1].split("?", 1)[1].split("&")
        # params = {
        #     key: value for (key, value) in [token.split("=") for token in param_tokens]
        # }
        # if state != params["state"]:
        #     send_message(
        #         client,
        #         f"State mismatch. Expected: {state} Received: {params['state']}",
        #     )
        #     return 1
        # elif "error" in params:
        #     send_message(client, params["error"])
        #     return 1
        #
        # self.refresh_token = conn.auth.authorize(params["code"])
        # lg.info("RedditNetwork::connect(): Received token %s", self.refresh_token)
        # send_message(client, f"Refresh token: {self.refresh_token}")

        self.conn = conn
        lg.info("RedditNetwork::connect(): logged in to Reddit as %s", conn.user.me())
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

    def send_msg(self, user_to, subject, body, editor=None, msgobj=None):
        """
        Send a Reddit message to user
        """
        lg.debug("> RedditNetwork::send_msg from %s to %s", self.user, user_to)

        if not subject or not body:
            raise Exception("RedditNetwork::send_msg(%s): subject or body not set", user_to)

        if msgobj:
            lg.debug("RedditNetwork::send_msg(%s): replying to message", msgobj.id)
            self.praw_call(msgobj.reply, body)
        else:
            lg.debug("RedditNetwork::send_msg(%s): sending message", user_to)
            if editor is None:
                editor = self.praw_call(self.conn.redditor, user_to)

            if not isinstance(editor, bool):
                self.praw_call(editor.message, subject, body)

        lg.debug("< RedditNetwork::send_msg(%s) DONE", user_to)
        return True

    def reply_msg(self, body, msgobj):
        self.praw_call(msgobj.reply, body)

    def get_parent_author(self, comment, sleep_seconds):
        """
        Return author of comment's parent comment
        """
        lg.debug("> RedditNetwork::get_parent_author()")
        lg.debug("> RedditNetwork::get_parent_author()")

        while True:
            try:
                parentcomment = comment.parent()
                if parentcomment and hasattr(parentcomment, 'author') and parentcomment.author:
                    lg.debug("< RedditNetwork::get_parent_author(%s) -> %s", comment.id, parentcomment.author.name)
                    return parentcomment.author.name
                else:
                    lg.warning("< RedditNetwork::get_parent_author(%s) -> NONE", comment.id)
                    return None
            except (IndexError, RedditAPIException) as e:
                lg.warning("RedditNetwork::get_parent_author(): couldn't get author: %s", e)
                return None
            except (HTTPError, ClientException, socket.timeout) as e:
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

    def init(self):
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
                    my_reddits = self.praw_call(self.conn.subreddits, limit=None)
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
                self.conf.subreddits = self.praw_call(self.conn.subreddit, my_reddits_string)
        except Exception as e:
            lg.error("RedditNetwork::init_subreddits(): couldn't get subreddits: %s", e)
            raise

        lg.debug("< RedditNetwork::init_subreddits() DONE")
        return True

    def check_mentions(self, ctb):
        """
        Evaluate new comments from self.configured subreddits
        """
        if not (self.conf.scan.my_subreddits or hasattr(self.conf.scan, 'these_subreddits')):
            lg.debug("> RedditNetwork::check_mentions(): nothing to check. return now.")
            return True

        lg.debug("> RedditNetwork::check_mentions()")
        updated_last_processed_time = 0

        try:
            # Process comments until old comment reached
            # Get last_processed_comment_time if necessary
            if not hasattr(self.conf, 'last_processed_comment_time') or self.conf.last_processed_comment_time <= 0:
                self.conf.last_processed_comment_time = ctb_misc.get_value(conn=self.db,
                                                                           param0='last_processed_comment_time')

            # Fetch comments from subreddits
            my_comments = self.praw_call(self.conf.subreddits.comments, limit=self.conf.scan.batch_limit)

            # Match each comment against regex
            counter = 0
            for c in my_comments:
                # Stop processing if old comment reached
                #lg.debug("check_mentions(): c.id %s from %s, %s <= %s", c.id, c.subreddit.display_name, c.created_utc, self.conf.last_processed_comment_time)
                if c.created_utc <= self.conf.last_processed_comment_time:
                    lg.debug("RedditNetwork::check_mentions(): old comment reached")
                    break
                counter += 1
                if c.created_utc > updated_last_processed_time:
                    updated_last_processed_time = c.created_utc

                # Ignore duplicate comments (may happen when bot is restarted)
                if ctb_action.check_action(msg_id=c.id, ctb=ctb):
                    lg.warning("RedditNetwork::check_inbox(): duplicate action detected (comment.id %s), ignoring",
                               c.id)
                    continue

                # Ignore comments from banned users
                if c.author and self.conf.banned_users:
                    lg.debug("RedditNetwork::check_mentions(): checking whether user '%s' is banned..." % c.author)
                    if self.is_user_banned(c.author.name):
                        lg.info("RedditNetwork::check_mentions(): ignoring banned user '%s'" % c.author)
                        continue

                # Attempt to evaluate comment
                action = ctb_action.eval_reddit_comment(c, ctb)

                # Perform action, if found
                if action:
                    lg.info("RedditNetwork::check_mentions(): %s from %s (%s)", action.type, action.u_from.name, c.id)
                    lg.debug("RedditNetwork::check_mentions(): comment body: <%s>", c.body)
                    action.do()
                else:
                    lg.info("RedditNetwork::check_mentions(): no match")

            lg.debug("RedditNetwork::check_mentions(): %s comments processed", counter)
            if counter >= self.conf.scan.batch_limit - 1:
                lg.warning(
                    "RedditNetwork::check_mentions(): conf.network.scan.batch_limit (%s) was not " +
                    "large enough to process all comments", self.conf.scan.batch_limit)

        except (HTTPError, ClientException, socket.timeout) as e:
            lg.warning("RedditNetwork::check_mentions(): Reddit is down (%s), sleeping", e)
            time.sleep(self.ctb.conf.misc.times.sleep_seconds)
            pass
        except Exception as e:
            lg.error("RedditNetwork::check_mentions(): coudln't fetch comments: %s", e)
            raise

        # Save updated last_processed_time value
        if updated_last_processed_time > 0:
            self.conf.last_processed_comment_time = updated_last_processed_time
        ctb_misc.set_value(conn=self.db, param0='last_processed_comment_time',
                           value0=self.conf.last_processed_comment_time)

        lg.debug("< RedditNetwork::check_mentions() DONE")
        return True

    def check_inbox(self, ctb):
        """
        Evaluate new messages in inbox
        """
        lg.debug('> RedditNetwork::check_inbox()')

        try:
            # Try to fetch some messages
            messages = list(self.praw_call(self.conn.inbox.unread, limit=self.conf.scan.batch_limit))
            messages.reverse()

            # Process messages
            for m in messages:
                # Sometimes messages don't have an author (such as 'you are banned from' message)
                if not m.author:
                    lg.info("RedditNetwork::check_inbox(): ignoring msg with no author")
                    self.praw_call(m.mark_read)
                    continue

                lg.info("RedditNetwork::check_inbox(): %s from %s", "comment" if m.was_comment else "message",
                        m.author.name)

                # Ignore duplicate messages (sometimes Reddit fails to mark messages as read)
                if ctb_action.check_action(msg_id=m.id, ctb=ctb):
                    lg.warning("RedditNetwork::check_inbox(): duplicate action detected (msg.id %s), ignoring", m.id)
                    self.praw_call(m.mark_read)
                    continue

                # Ignore self messages
                if m.author and m.author.name.lower() == self.user.lower():
                    lg.debug("RedditNetwork::check_inbox(): ignoring message from self")
                    self.praw_call(m.mark_read)
                    continue

                # Ignore messages from banned users
                if m.author and self.conf.banned_users:
                    lg.debug("RedditNetwork::check_inbox(): checking whether user '%s' is banned..." % m.author)
                    if self.is_user_banned(m.author.name):
                        lg.info("RedditNetwork::check_inbox(): ignoring banned user '%s'" % m.author)
                        self.praw_call(m.mark_read)
                        continue

                if m.was_comment:
                    # Attempt to evaluate as comment / mention
                    action = ctb_action.eval_reddit_comment(m, ctb)
                else:
                    # Attempt to evaluate as inbox message
                    action = ctb_action.eval_message(m, ctb)

                # Perform action, if found
                if action:
                    lg.info("RedditNetwork::check_inbox(): %s from %s (m.id %s)", action.type, action.u_from.name, m.id)
                    lg.debug("RedditNetwork::check_inbox(): message body: <%s>", m.body)
                    action.do()
                else:
                    lg.info("RedditNetwork::check_inbox(): no match")
                    if self.conf.messages.sorry and not m.subject in ['post reply', 'comment reply']:
                        tpl = self.ctb.jenv.get_template('didnt-understand.tpl')
                        msg = tpl.render(user_from=m.author.name, what='comment' if m.was_comment else 'message',
                                         source_link=m.permalink if hasattr(m, 'permalink') else None, ctb=ctb)
                        lg.debug("RedditNetwork::check_inbox(): %s", msg)
                        self.send_msg(user_to=m.author.name, subject='What?', body=msg, editor=m.author,
                                      msgobj=m if not m.was_comment else None)

                # Mark message as read
                self.praw_call(m.mark_read)
        except (HTTPError, ConnectionError, Timeout, socket.timeout) as e:
            lg.warning("RedditNetwork::check_inbox(): Reddit is down (%s), sleeping", e)
            time.sleep(self.ctb.conf.misc.times.sleep_seconds)
            pass
        except ClientException as e:
            lg.warning("RedditNetwork::check_inbox(): rate limit exceeded, sleeping for %s seconds", e.sleep_time)
            time.sleep(e.sleep_time)
            time.sleep(1)
            pass
        except Exception as e:
            lg.error("RedditNetwork::check_inbox(): %s", e)
            raise

        lg.debug("< RedditNetwork::check_inbox() DONE")
        return True
