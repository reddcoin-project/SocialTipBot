{% set user_from = '@' + a.u_from.name %}
{% if a.u_to %}
{%   set user_to_fmt = '@' + a.u_to.name %}
{% else %}
{%   set user_to_fmt = a.addr_to %}
{% endif %}
{% set coin_amount = a.coinval %}
{% set coin_name = ctb.conf.coins[a.coin].name %}
{% set coin_amount_fmt = "%.9f %s(s)" % (coin_amount, coin_name) %}
{{ user_from }}, error occurred in your tip/withdraw of {{ coin_amount_fmt }} to {{ user_to_fmt }}.