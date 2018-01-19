#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE USER admin WITH SUPERUSER PASSWORD 'secret';
    CREATE DATABASE gosa-test WITH OWNER 'admin' TEMPLATE 'template0' ENCODING 'UTF8';
    GRANT ALL PRIVILEGES ON DATABASE gosa-test TO admin;
    \c gosa-test
    CREATE EXTENSION fuzzystrmatch;
EOSQL
