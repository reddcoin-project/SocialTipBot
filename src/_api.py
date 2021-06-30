#!/usr/bin/env python
"""
    This file is part of SocialTipBot.

    SocialTipBot is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    SocialTipBot is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with SocialTipBot.  If not, see <http://www.gnu.org/licenses/>.
"""

from flask import Flask, jsonify, render_template
import json

import cointipbot, logging
from ctb import ctb_stats
from pymemcache.client import base


logging.basicConfig()
lg = logging.getLogger('cointipbot')
lg.setLevel(logging.INFO)

ctb = cointipbot.CointipBot(self_checks=False, init_reddit=False, init_twitch=True, init_coins=False, init_exchanges=False, init_db=True, init_logging=False)

app = Flask(__name__)

class JsonSerde(object):
    def serialize(self, key, value):
        if isinstance(value, str):
            return value.encode('utf-8'), 1
        return json.dumps(value).encode('utf-8'), 2

    def deserialize(self, key, value, flags):
        if flags == 1:
            return value.decode('utf-8')
        if flags == 2:
            return json.loads(value.decode('utf-8'))
        raise Exception("Unknown serialization format")


# connect to memcached
memclient = base.Client(('reddcoin-memcached', 11211), serde=JsonSerde(),timeout=60)

# start with cold cache
memclient.delete('stats')
memclient.delete('tips')
memclient.delete('history')

def get_stats_data():
    result = memclient.get('stats')
    if result is None:
        # Cache is empty, retrieve from db
        result = ctb_stats.update_stats_json(ctb=ctb)
        # Cache result
        memclient.set('stats', result, expire=60)

    return result

def get_tips_data():
    result = memclient.get('tips')
    if result is None:
        # Cache is empty, retrieve from db
        result = ctb_stats.update_tips_json(ctb=ctb)
        # Cache result
        memclient.set('tips', result, expire=60)

    return result

def get_history_data():
    result = memclient.get('history')
    if result is None:
        # Cache is empty, retrieve from db
        result = ctb_stats.update_history_json(ctb=ctb)
        # Cache result
        memclient.set('history', result, expire=60)

    return result

@app.route("/leaderboard", methods=["GET"])
def getleaderboardpage():
    result = get_stats_data()
    return render_template('leaderboard.html', my_stats=result)

@app.route("/stats", methods=["GET"])
def getstatspage():
    result = get_stats_data()
    return render_template('stats.html', my_stats=result)

@app.route("/stats", methods=["GET"])
def getstats():
    result = get_stats_data()
    return jsonify({"result": result})

@app.route("/tips", methods=["GET"])
def gettips():
    result = get_tips_data()
    return jsonify({"result": result})

@app.route("/history", methods=["GET"])
def gethistory():
    result = get_history_data()
    return jsonify({"result": result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4567, debug=False)