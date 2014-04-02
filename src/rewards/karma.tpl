{{ "|".join(df.columns) }}
{{ "|".join([":---"] * (df.columns|length)) }}
{% for i, row in df.iterrows(): %}
{{   "|".join(row) }}
{% endfor %}
