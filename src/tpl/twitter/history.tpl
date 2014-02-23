{% set user = '@' + a.u_from.name %}
{% set suffix = '(s)' if limit > 1 else '' %}
{% if history is None or len(history) == 0: %}
{{ user }} your have 0 transaction so far.
{% else %}
{{ user }} your last {{ limit }} transaction ID{{ suffix }}:
{%   for h in history %}
{{   h.txid }}
{%   endfor %}
{% endif %}