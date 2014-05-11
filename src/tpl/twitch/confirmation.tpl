{% set user_from_fmt = '@' + a.u_from.name %}
{% set arrow_fmt = " -->>" %}
{% if a.u_to: %}
{%   if to_unregistered: %}
{%     set user_to_fmt = a.u_to.name %}
{%   else %}
{%     set user_to_fmt = '@' + a.u_to.name %}
{%   endif %}
{% endif %}
{% if a.addr_to: %}
{%   set user_to_fmt = a.addr_to %}
{%   set txid = " txid=%s" % a.txid %}
{% else %}
{%   set txid = "" %}
{% endif %}
{% if a.coinval: %}
{%   set coin_amount = a.coinval %}
{%   set coin_name = ctb.conf.coins[a.coin].name %}
{%   set coin_symbol = ctb.conf.coins[a.coin].symbol %}
{%   set coin_amount_fmt = " %s%.6g %ss" % (coin_symbol, coin_amount, coin_name) %}
{% endif %}
{% if to_unregistered: %}
{%   set reminder = ". Please remind the recipient to send me \"+accept\" to claim it." %}
{% else %}
{%   set reminder = "" %}
{% endif %}
{% if expired: %}
{%   set verb = " expired: " %}
{% else %}
{%   set verb = " confirmed: " %}
{% endif %}
{% if a.type == 'givetip' and a.keyword and ctb.conf.keywords[a.keyword].message %}
{%   set txt = ctb.conf.keywords[a.keyword].message %}
{%   set txt = txt | replace("{USER_FROM}", user_from_fmt) %}
{%   set txt = txt | replace("{USER_TO}", user_to_fmt) %}
{%   set txt = txt | replace("{AMOUNT}", coin_amount_fmt) %}
{{   txt }}{{ reminder }}
{% else %}
{{ user_from_fmt }}{{ verb }}{{ arrow_fmt }}{{ user_to_fmt }}{{ coin_amount_fmt }}{{ txid }}{{ reminder }}
{% endif %}