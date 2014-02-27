{% set user = '@' + a.u_from.name %}
{{ user }}
{% for c in coins %}
{{ "%s/BTC:" % c.upper() }}
{%   for e in exchanges %}
{{   "%.1f santoshi@%s" % (rates[c][e].btc * 100000000, e) }}
{%   endfor %}
{% endfor %}