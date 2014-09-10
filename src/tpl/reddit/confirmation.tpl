{% set title_fmt = "^__[%s]__:" % title %}
{% set user_from_fmt = " ^/u/%s" % a.u_from.name %}
{% set arrow_fmt = " ^->" %}
{% if a.u_to: %}
{%   set user_to_fmt = " ^/u/%s" % a.u_to.name %}
{% endif %}
{% if a.addr_to: %}
{%   set ex = ctb.conf.coins[a.coin].explorer %}
{%   set user_to_fmt = " ^[%s](%s%s)" % (a.addr_to, ex.address, a.addr_to) %}
{%   set arrow_fmt = " ^[->](%s%s)" % (ex.transaction, a.txid) %}
{% endif %}
{% if a.coinval: %}
{%   set coin_name = ctb.conf.coins[a.coin].name %}
{%   set coin_symbol = ctb.conf.coins[a.coin].symbol %}
{%   set coin_amount_fmt = " __^%s%.6g ^%ss__" % (coin_symbol, a.coinval, coin_name) %}
{% endif %}
{% if ctb.conf.network.help.enabled: %}
{%   set help_link_fmt = " ^[[help]](%s)" % ctb.conf.network.help.url %}
{% endif %}
{% if a.type == 'givetip' and a.keyword and ctb.conf.keywords[a.keyword].message %}
{%   set txt = ctb.conf.keywords[a.keyword].message %}
{%   if stats_user_from_fmt %}
{%     set txt = txt | replace("{USER_FROM}", user_from_fmt + stats_user_from_fmt) %}
{%   else %}
{%     set txt = txt | replace("{USER_FROM}", user_from_fmt) %}
{%   endif %}
{%   if stats_user_to_fmt %}
{%     set txt = txt | replace("{USER_TO}", user_to_fmt + stats_user_to_fmt) %}
{%   else %}
{%     set txt = txt | replace("{USER_TO}", user_to_fmt) %}
{%   endif %}
{%   if fiat_amount_fmt %}
{%     set txt = txt | replace("{AMOUNT}", coin_amount_fmt + fiat_amount_fmt) %}
{%   else %}
{%     set txt = txt | replace("{AMOUNT}", coin_amount_fmt) %}
{%   endif %}
{{   txt }}
{% else %}
{{   title_fmt }}{{ user_from_fmt }}{{ arrow_fmt }}{{ user_to_fmt }}{{ coin_amount_fmt }}{{ help_link_fmt }}
{% endif %}
