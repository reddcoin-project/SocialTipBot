#!/usr/bin/env python

import cointipbot
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('network', help='[reddit, twitter,twitch, irc]')
args = parser.parse_args()

if __name__ == '__main__':
    if args.network.lower() == 'reddit':
        cb = cointipbot.CointipBot(init_reddit=True)
    elif args.network.lower() == 'twitter':
        cb = cointipbot.CointipBot(init_twitter=True)
    elif args.network.lower() == 'twitch':
        cb = cointipbot.CointipBot(init_twitch=True)
    elif args.network.lower() == 'irc':
        cb = cointipbot.CointipBot(init_irc=True)
    else:
        cb = cointipbot.CointipBot()
    cb.main()
