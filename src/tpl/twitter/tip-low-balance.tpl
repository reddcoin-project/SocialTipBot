{% set user_from = '@' + a.u_from.name %}
{% set balance_fmt = "%.9f %s" % (balance, a.coin.upper()) %}
{{ user_from }}, your balance of {{ balance_fmt }} (net of transaction cost) is insufficient for this {{ action_name }}.