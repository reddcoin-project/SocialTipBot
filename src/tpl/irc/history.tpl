{% set user = '@' + a.u_from.name %}
{% set suffix = '(s)' if limit > 1 else '' %}
{% if history|length == 0: %}
{{ user }} your have 0 transaction so far.
{% else %}
{{ user }} your last {{ limit }} transaction{{ suffix }}:
{%   for h in history %}
{{     "|".join(h) }}
{%   endfor %}
{% endif %}