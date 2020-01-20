__author__ = 'gnasher'

import logging
import calendar
import re
import time
import logging
import random
from datetime import datetime
from dateutil.parser import parse
from twitterwebhooks import TwitterWebhookAdapter
from twython import TwythonStreamer, TwythonRateLimitError, TwythonError
import ctb.ctb_action as ctb_action
import ctb.ctb_misc as ctb_misc
import json

lg = logging.getLogger('cointipbot')


class TwitterWebHooks(object):
    app_secret = None
    logger = None
    events_adapter = None
    bot_id = None
    conn = None

    @classmethod
    def _timestamp_utc(cls, dt):
        if isinstance(dt, basestring):
            dt = parse(dt)

        return calendar.timegm(dt.utctimetuple())

    @classmethod
    def _timestamp_utc_now(cls):
        dt = datetime.utcnow()
        return calendar.timegm(dt.utctimetuple())

    def __init__(self, conn, app_secret, account_id):

        lg.info("TwitterWebHooks::__init__()...")

        self.app_secret = app_secret
        self.bot_id = account_id
        self.conn = conn
        self.events_adapter = TwitterWebhookAdapter(self.app_secret, "/webhooks/twitter")

    def follow_followers(self):
        lg.debug('TwitterWebHooks::follow_followers(): started')

        # only get the latest followers but this relies on Twitter returns the latest followers first
        followers = []
        for fid in self.conn.cursor(self.conn.get_followers_ids, count=5000):
            followers.append(fid)

        friends = []
        for fid in self.conn.cursor(self.conn.get_friends_ids, count=5000):
            friends.append(fid)

        pending = []
        for fid in self.conn.cursor(self.conn.get_outgoing_friendship_ids):
            pending.append(fid)

        lg.debug('TwitterWebHooks::follow_followers(): looking for new followers')
        to_follow = [f for f in followers[:100] if f not in friends and f not in pending]
        lg.debug('TwitterWebHooks::follow_followers(): about to send follow request')

        # only follow 10 at a time
        actions = []
        for user_id in to_follow[:10]:
            try:
                resp = self.conn.create_friendship(user_id=user_id)
                time.sleep(1)
            except TwythonError as e:
                # either really failed (e.g. sent request before) or already friends
                lg.warning("TwitterWebHooks::follow_followers: failed to follow user %s: %s", user_id, e.msg)
                continue
            else:
                lg.debug('TwitterWebHooks::follow_followers(): just sent request to follow user %s', user_id)

            msg = {'id': str(user_id),
                   'created_utc': self._timestamp_utc_now(),
                   'author': {'name': resp['screen_name']},
                   'body': '+register',
                   'type': 'mention'}
            # make the msg id unique
            msg['id'] += ('@' + str(msg['created_utc']))

            action = ctb_action.eval_message(ctb_misc.DotDict(msg), self.ctb)
            actions.append(action)

        return actions

    def _parse_event(self, event_data):

        # check pending tips
        if (datetime.utcnow() - self.last_expiry).seconds > 60 * 60:
            self.ctb.expire_pending_tips()
            self.last_expiry = datetime.utcnow()

        # do not process event more than once per minute
        if (datetime.utcnow() - self.last_event).seconds > 60:
            # actions = self.follow_followers()
            # self.ctb.last_event = datetime.utcnow()
            # return actions
            return None
        else:
            return None

    def _parse_mention(self, event_data):

        event = event_data['event']
        author_name = event['user']['screen_name']

        # we do allow the bot to issue commands
        msg = {'created_utc': self._timestamp_utc_now(),
               'author': {'name': author_name},
               'type': 'mention'}
        msg['id'] = event['id_str'] + str(msg['created_utc'])[(30-len(event['id_str'])):]

        text = event['text']
        msg['body'] = text.replace('@' + self.username, '').strip()
        lg.debug(msg)

        action = ctb_action.eval_message(ctb_misc.DotDict(msg), self.ctb)
        return action

    def _parse_direct_message(self, event_data):

        event = event_data['event']
        recipient_id = event['message_create']['target']['recipient_id']
        sender_id = event['message_create']['sender_id']
        sender_screen_name = event_data['users'][sender_id]['screen_name']
        recipient_screen_name = event_data['users'][recipient_id]['screen_name']
        message_text = event['message_create']['message_data']['text']

        msg = {'created_utc': self._timestamp_utc_now(),
               'author': {'name': sender_screen_name},
               'recipient_id': sender_id,
               'type': 'direct_message'}
        msg['id'] = event['id'] + str(msg['created_utc'])[(30-len(event['id'])):]

        text = event['message_create']['message_data']['text']
        msg['body'] = text.replace('@' + self.username, '').strip()
        lg.debug(msg)

        action = ctb_action.eval_message(ctb_misc.DotDict(msg), self.ctb)

        return action

    def send_dm(self, recipient_id, message_text):
        # Helper for sending DMs
        event = {
            "event": {
                "type": "message_create",
                "message_create": {
                    "target": {
                        "recipient_id": recipient_id
                    },
                    "message_data": {
                        "text": message_text
                    }
                }
            }
        }

        response = self.conn.post('direct_messages/events/new', json.dumps(event))
        return response

    def run(self):
        """
        Returns a Twitter webhook object
        """

        @self.events_adapter.on("direct_message_events")
        def handle_message(event_data):
            event = event_data['event']
            if event['type'] == 'message_create':
                recipient_id = event['message_create']['target']['recipient_id']
                sender_id = event['message_create']['sender_id']
                sender_screen_name = event_data['users'][sender_id]['screen_name']
                recipient_screen_name = event_data['users'][recipient_id]['screen_name']
                message_text = event['message_create']['message_data']['text']

                # Filter out bot messages
                if str(sender_id) == str(self.bot_id):
                    lg.info("IGNORING [Event {}] Incoming DM: To {} from {} \"{}\"".format(
                        event['id'],
                        recipient_screen_name,
                        sender_screen_name,
                        message_text
                    ))
                else:
                    lg.info("[Event {}] Incoming DM: To {} from {} \"{}\"".format(
                        event['id'],
                        recipient_screen_name,
                        sender_screen_name,
                        message_text
                    ))
                    try:
                        # dm_id = self.send_dm(sender_id, "ACK! {}".format(event['id']))['event']['id']
                        actions = self._parse_direct_message(event_data)

                        if not actions:
                            return

                        if not isinstance(actions, list):
                            actions = [actions]

                        for action in actions:
                            if action:
                                lg.info("TwitterWebHook::on_success(): %s from %s", action.type, action.u_from.name)
                                lg.debug("TwitterWebHook::on_success(): comment body: <%s>", action.msg.body)
                                action.do()

                    except Exception as e:
                        lg.info("An error occurred sending DM: {}".format(e))

        @self.events_adapter.on("tweet_create_events")
        def handle_message(event_data):
            event = event_data['event']

            # tweet_create_events (@mentions)
            fields = fields = ['created_at', 'id', 'user', 'entities', 'text']
            if all(field in event for field in fields):
                # received tweet_create_events (@mentions)

                # ignore retweets
                if event['retweeted'] == True:
                    return None
                recipient_id = event_data['for_user_id']
                sender_id = event['user']['id_str']
                sender_screen_name = event['user']['screen_name']
                message_text = event['text']
                author_name = event['user']['screen_name']

                # if author was tipbot, return
                if author_name == self.username or '@' + self.username not in event['text']:
                    return None
                else:
                    lg.info("[Event {}] Incoming Mention: From {} \"{}\"".format(
                        event['id'],
                        sender_screen_name,
                        message_text
                    ))
                    try:
                        actions = self._parse_mention(event_data)

                        if not actions:
                            return

                        if not isinstance(actions, list):
                            actions = [actions]

                        for action in actions:
                            if action:
                                lg.info("TwitterWebHook::on_success(): %s from %s", action.type, action.u_from.name)
                                lg.debug("TwitterWebHook::on_success(): comment body: <%s>", action.msg.body)
                                action.do()

                    except Exception as e:
                        lg.info("An error occurred responding to Mention: {}".format(e))

        @self.events_adapter.on("favorite_events")
        def handle_message(event_data):
            event = event_data['event']
            faved_status = event['favorited_status']
            faved_status_id = faved_status['id']
            faved_status_screen_name = faved_status['user']['screen_name']
            faved_by_screen_name = event['user']['screen_name']
            lg.info("@{} faved @{}'s tweet: {}".format(faved_by_screen_name, faved_status_screen_name, faved_status_id))
            # print(json.dumps(event_data, indent=4, sort_keys=True))

        @self.events_adapter.on("any")
        def handle_message(event_data):
            # Loop through events array and log received events
            for s in filter(lambda x: '_event' in x, list(event_data)):
                lg.info("[any] Received event: {}".format(s))

            actions = self._parse_event(event_data)

            if not actions:
                return

            if not isinstance(actions, list):
                actions = [actions]

            for action in actions:
                if action:
                    lg.info("TwitterWebHooks::on_success(): %s from %s", action.type, action.u_from.name)
                    lg.debug("TwitterWebHooks::on_success(): comment body: <%s>", action.msg.body)
                    action.do()


        # Handler for error events
        @self.events_adapter.on("error")
        def error_handler(err):
            print("ERROR: " + str(err))

        lg.info("TwitterWebHooks::connecting(): Listening for Events")
        self.events_adapter.start(port=3000)

