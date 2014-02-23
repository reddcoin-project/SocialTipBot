{% set user_from = '@' + a.u_from.name %}
{% set amount_fmt = "%.9f %s" % (a.coinval, a.coin.upper()) %}
{% set min_fmt = "%.9g" % min_value %}
{% set coin_name = ctb.conf.coins[a.coin].name %}
{{ user_from }}, your tip/withdraw of {{ amount_fmt }} is below minimum of {{ min_fmt }}. I cannot process very small transactions because of high network fee requirement.