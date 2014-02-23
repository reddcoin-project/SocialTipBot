{% if ctb and ctb.conf.network.help.enabled %}
{%   set help_link = "[verify syntax](%s)" % ctb.conf.network.help.url %}
{% else %}
{%   set help_link = "verify syntax" %}
{% endif %}
{{ '@' + user_from }} I didn't understand your {{ what }}. Please {{ help_link }} and try again.