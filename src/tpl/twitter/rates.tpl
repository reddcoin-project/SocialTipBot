coin|average{% for e in exchanges %}{{ "|" + e }}{% endfor %}

:---|---:{% for e in exchanges %}{{ "|---:" }}{% endfor %}
{% for c in coins %}
{{ "\n%s|%s%.1e" % (c.upper(), ctb.conf.coins.btc.symbol, rates[c]['average'].btc) }}{% for e in exchanges %}
{%     if rates[c][e].btc and rates[c][e][fiat] %}
{{ "|%s%.1e" % (ctb.conf.coins.btc.symbol, rates[c][e].btc) }}
{%     else %}
{{ "|-" }}
{%     endif %}
{%   endfor %}
{% endfor %}