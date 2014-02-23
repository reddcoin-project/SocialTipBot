{% set user = '@' + a.u_from.name %}
{% set suffix = '(s)' if limit > 1 else '' %}
{{ user }} your last {{ limit }} txid{{ suffix }}:

{% for h in history %}
{{ h.txid }}
{% endfor %}
