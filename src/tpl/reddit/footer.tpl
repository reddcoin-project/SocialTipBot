{% if not user and a %}
{%   set user = a.u_from.name %}
{% endif %}
{% if not user_bot and ctb %}
{%   set user_bot = ctb.conf.network.auth.user %}
{% endif %}
{% set compose_url = "http://www.reddit.com/message/compose?to=%s&subject=%s&message=%%2B%s" %}
{% set i_url = compose_url % (user_bot, "info", "info") %}
{% set h_url = compose_url % (user_bot, "history", "history") %}
{% set w_url = compose_url % (user_bot, "withdraw", "withdraw%20ADDRESS%20AMOUNT%20COIN_NAME") %}
{% set r_url = compose_url % (user_bot, "rates", "rates") %}
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
*****

^Helpful ^Links|&nbsp;
:---|:---
{% if a and a.msg and a.msg.permalink %}
^Source ^comment|^[[link]]({{ a.msg.permalink }})
{% elif source_link %}
^Source ^comment|^[[link]]({{ source_link }})
{% endif %}
^Quick ^commands|**^[+info]({{ i_url }})** ^[+history]({{ h_url }}) ^[+rates]({{ r_url }}) ^[+withdraw]({{ w_url }})
^Resources|{{ help_link }}{{ contact_link }}{{ stats_user_link }}{{ stats_global_link }}

{% include 'announcement.tpl' %}
