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

from flask import Flask, jsonify

import cointipbot, logging
from ctb import ctb_stats

logging.basicConfig()
lg = logging.getLogger('cointipbot')
lg.setLevel(logging.INFO)

ctb = cointipbot.CointipBot(self_checks=False, init_reddit=False, init_twitch=True, init_coins=False, init_exchanges=False, init_db=True, init_logging=False)

app = Flask(__name__)

@app.route("/stats", methods=["GET"])
def getstats():
    result = ctb_stats.update_stats_json(ctb=ctb)
    return jsonify({"result": result})

@app.route("/tips", methods=["GET"])
def gettips():
    result = ctb_stats.update_tips_json(ctb=ctb)
    return jsonify({"result": result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4567, debug=False)