{% set user_from = '@' + a.u_from.name %}
{% set user_bot = '#' + ctb.conf.network.auth.user %}
{{ user_from }} please send "+register" to {{ user_bot }} first.