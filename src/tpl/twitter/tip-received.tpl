{% set user_from = '@' + a.u_from.name %}
{% set user_to = '@' + a.u_to.name %}
{% if a.coinval: %}
{%   set coin_amount = a.coinval %}
{% endif %}
{% set coinval_fmt = "%s%.6g %ss" % (ctb.conf.coins[a.coin].symbol, coin_amount, ctb.conf.coins[a.coin].name) %}
{{ user_to }}, you have received a tip of {{ coinval_fmt }} from {{ user_from }}.