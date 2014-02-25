{% set user_from = '@' + a.u_from.name %}
{% set user_to = '@' + a.u_to.name %}
{% set user_bot = '@' + ctb.conf.network.auth.user %}
{% if a.coinval: %}
{%   set coin_amount = a.coinval %}
{% endif %}
{% set coinval_fmt = "%s%.6g %ss" % (ctb.conf.coins[a.coin].symbol, coin_amount, ctb.conf.coins[a.coin].name) %}
{% set expire_days_fmt = "%.2g" % ( ctb.conf.misc.times.expire_pending_hours / 24.0 ) %}
{{ user_to }}, {{ user_from }} sent you {{ coinval_fmt }}, reply with "+accept" to claim it after accepting my Follow Request.