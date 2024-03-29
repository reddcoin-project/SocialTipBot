__author__ = 'laudney'


from lxml.html import fromstring
from socketIO_client import SocketIO, BaseNamespace
import cookielib
import urllib
import urllib2


class Namespace(BaseNamespace):

    def initialize(self):
        self.response = None
        self.args_by_event = {}
        self.called_on_disconnect = False

    def on_disconnect(self):
        print 'disconnected'
        self.called_on_disconnect = True

    def on_message(self, data):
        print data
        self.response = data

    def on_event(self, event, *args):
        print event
        self.args_by_event[event] = args


if __name__ == "__main__":
    host = 'https://sio2.plug.dj'
    port = 443
    twitter_user = 'itipyou'
    twitter_passwd = 'phd51blognewstarttipt'
    room = 'reddcoin-com-r-reddcoin'

    # socketio = SocketIO(host, port)

    # preserve cookies
    jar = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))

    url1 = 'http://plug.dj/authenticate/oauth/?next=http%3A%2F%2Fplug.dj%2F'
    req1 = urllib2.Request(url1)
    req1.add_header('User-agent', 'Chrome 36.0.1944.0')
    params1 = urllib.urlencode({'provider': 'twitter'})
    f1 = opener.open(req1, params1)
    html = f1.read()
    dom = fromstring(html)
    credentials = {
        'authenticity_token': dom.cssselect('input[name="authenticity_token"]')[0].value,
        'oauth_token': dom.cssselect('input[name="oauth_token"]')[0].value,
        'session[username_or_email]': twitter_user,
        'session[password]': twitter_passwd
    }

    url2 = 'https://api.twitter.com/oauth/authenticate'
    req2 = urllib2.Request(url2)
    req2.add_header('User-agent', 'Chrome 36.0.1944.0')
    params2 = urllib.urlencode(credentials)
    f2 = opener.open(req2, params2)
    html = f2.read()
    dom = fromstring(html)
    meta = dom.cssselect('meta[http-equiv="refresh"]')[0]
    plug_login_url = meta.get('content').split('url=')[1]

    req3 = urllib2.Request(plug_login_url)
    req3.add_header('User-agent', 'Chrome 36.0.1944.0')
    f3 = opener.open(req3)

    for cookie in jar:
        if cookie.name == 'usr':
            break

    jar_plug = cookielib.CookieJar()
    jar_plug.set_cookie(cookie)
    plug_room_url = 'http://plug.dj/' + room

    req4 = urllib2.Request(plug_room_url)
    req4.add_header('User-agent', 'Chrome 36.0.1944.0')
    jar_plug.add_cookie_header(req4)
    f4 = opener.open(req4)
    html = f4.read()
    dom = fromstring(html)