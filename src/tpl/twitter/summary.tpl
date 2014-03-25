{% set user = '@' + a.u_from.name %}
{% set coin_name = ctb.conf.coins[a.coin].name %}
{{ user }} you have tipped total {{ total_sent }} and received total {{ total_received }} {{ coin_name }}.