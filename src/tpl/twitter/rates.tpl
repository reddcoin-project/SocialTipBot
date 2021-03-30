{{ '@' + a.u_from.name }}
{% for c in coins %}
{{ "%s/BTC:" % c.upper() }}
{%   for e in exchanges %}
{{   "%.1f satoshi@%s" % (rates[c][e].btc * 100000000, e) }}
{%   endfor %}
{% endfor %}