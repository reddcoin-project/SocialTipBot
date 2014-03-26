{% set user = '@' + a.u_from.name %}
{% set coin_name = 'RDD' %}
{{ user }} you have sent {{ count_sent }} tips, total {{ total_sent }} and received {{ count_received }} tips, total {{ total_received }} {{ coin_name }}.