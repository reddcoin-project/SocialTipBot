{% set user_from_fmt = '@' + a.u_from.name %}
{% set arrow_fmt = " -->>" %}
{% if a.u_to: %}
{%   set user_to_fmt = '@' + a.u_to.name %}
{% endif %}
{% if a.addr_to: %}
{%   set user_to_fmt = a.addr_to %}
{%   set txid = " txid=%s" % a.txid %}
{% else %}
{%   set txid = "" %}
{% endif %}
{% if a.coinval: %}
{%   if a.coinval < 0.0001 %}
{%     set coin_amount = ( a.coinval * 100000000.0 ) %}
{%     set amount_prefix_short = "s" %}
{%     set amount_prefix_long = "satoshi" %}
{%   elif a.coinval < 1.0 %}
{%     set coin_amount = ( a.coinval * 1000.0 ) %}
{%     set amount_prefix_short = "m" %}
{%     set amount_prefix_long = "milli" %}
{%   elif a.coinval >= 1000.0 %}
{%     set coin_amount = ( a.coinval / 1000.0 ) %}
{%     set amount_prefix_short = "K" %}
{%     set amount_prefix_long = "kilo" %}
{%   else %}
{%     set coin_amount = a.coinval %}
{%   endif %}
{%   set coin_name = ctb.conf.coins[a.coin].name %}
{%   set coin_symbol = ctb.conf.coins[a.coin].symbol %}
{%   set coin_amount_fmt = " %s%s%.6g %s%ss" % (amount_prefix_short, coin_symbol, coin_amount, amount_prefix_long, coin_name) %}
{% endif %}
{% if a.type == 'givetip' and a.keyword and ctb.conf.keywords[a.keyword].message %}
{%   set txt = ctb.conf.keywords[a.keyword].message %}
{%   set txt = txt | replace("{USER_FROM}", user_from_fmt) %}
{%   set txt = txt | replace("{USER_TO}", user_to_fmt) %}
{%   set txt = txt | replace("{AMOUNT}", coin_amount_fmt) %}
{{   txt }}
{% else %}
{{ user_from_fmt }} confirmed: {{ arrow_fmt }}{{ user_to_fmt }}{{ coin_amount_fmt }}{{ txid }}
{% endif %}