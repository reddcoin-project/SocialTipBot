{{ "%s/BTC:" % c.upper() }}
{% for e in exchanges %}
{{ "%.1f santoshi @ %s" % (rates[c][e].btc * 1e8, e) }}
{% endfor %}