{% set user_from = '@' + a.u_from.name %}
{% set coin_name = a.coin.upper() %}
{% set address = a.addr_to %}
{{ user_from }}, {{ coin_name }}|{{ address | escape }} appears to be invalid.