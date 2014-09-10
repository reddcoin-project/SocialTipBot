__author__ = 'laudney'


import time
import urllib2
import simplejson


if __name__ == '__main__':
    accounts = simplejson.load(open('/Users/bren/reddit_accounts'))

    for name in accounts.keys():
        try:
            urllib2.urlopen('http://www.reddit.com/user/' + name)
        except urllib2.HTTPError as e:
            print e.code
            if e.code == 404:
                print name, accounts[name]

        time.sleep(5)
