{% set user_from = '@' + a.u_from.name %}
{{ user_from }} your account info:

{% for i in info %}
{%   set name_fmt = "%s (%s)" % (ctb.conf.coins[i.coin].name, i.coin.upper()) %}
{%   set address_fmt = i.address %}
{%   set coin_bal_fmt = "%.9g" % i.balance %}
coin={{ name_fmt }}
address={{ address_fmt }}
balance={{ coin_bal_fmt }}
{% endfor %}