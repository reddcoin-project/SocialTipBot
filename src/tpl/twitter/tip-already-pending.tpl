{% set user_from = '@' + a.u_from.name %}
{% set user_to = '@' + a.u_to.name %}
{% set coin_name = '@' + ctb.conf.coins[a.coin].name %}
{{ user_from }}, {{ user_to }} already has a pending {{ coin_name }} tip from you. Please wait until it's accepted, declined, or expired.