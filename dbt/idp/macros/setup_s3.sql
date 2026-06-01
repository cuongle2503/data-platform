{% macro setup_s3() %}
    {% set minio_endpoint = env_var('MINIO_ENDPOINT', 'localhost:9000') %}
    {% set minio_access_key = env_var('MINIO_ACCESS_KEY', 'minioadmin') %}
    {% set minio_secret_key = env_var('MINIO_SECRET_KEY', 'minioadmin') %}

    LOAD 'httpfs';

    SET s3_endpoint='{{ minio_endpoint }}';
    SET s3_access_key_id='{{ minio_access_key }}';
    SET s3_secret_access_key='{{ minio_secret_key }}';
    SET s3_use_ssl=false;
    SET s3_url_style='path';
{% endmacro %}
