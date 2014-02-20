import logging
import time
import re


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
