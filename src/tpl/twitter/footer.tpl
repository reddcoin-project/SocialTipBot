{% if not user and a %}
{%   set user = a.u_from.name %}
{% endif %}
{% if not user_bot and ctb %}
{%   set user_bot = ctb.conf.network.auth.user %}
{% endif %}
{% if ctb and ctb.conf.network.help.enabled %}
{%   set help_link = " ^[[help]](%s)" % ctb.conf.network.help.url %}
{% endif %}
{% if ctb and ctb.conf.network.contact.enabled %}
{%   set contact_link = " ^[[contact]](%s)" % ctb.conf.network.contact.url %}
{% endif %}
{% if ctb and ctb.conf.network.stats.enabled %}
{%   set stats_user_link = " **^[[your_stats]](%s_%s)**" % (ctb.conf.network.stats.url, user) %}
{%   set stats_global_link = " ^[[global_stats]](%s)" % ctb.conf.network.stats.url %}
{% endif %}
{{ help_link }}
