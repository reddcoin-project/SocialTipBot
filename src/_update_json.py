"""
    This file is part of ALTcointip.

    ALTcointip is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    ALTcointip is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with ALTcointip.  If not, see <http://www.gnu.org/licenses/>.
"""

import cointipbot, logging
from ctb import ctb_stats
import json

logging.basicConfig()
lg = logging.getLogger('cointipbot')
lg.setLevel(logging.DEBUG)

ctb = cointipbot.CointipBot(self_checks=False, init_reddit=False, init_twitch=True, init_coins=False, init_exchanges=False, init_db=True, init_logging=False)

# Update stats json
result = {}
result["result"] = ctb_stats.update_stats_json(ctb=ctb)
lg.debug(json.dumps(result))

# Update tips page
result["result"] = ctb_stats.update_tips_json(ctb=ctb)
lg.debug(json.dumps(result))

