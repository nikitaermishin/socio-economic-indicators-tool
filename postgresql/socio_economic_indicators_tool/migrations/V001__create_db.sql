/* create schema */
CREATE SCHEMA socio_economic_indicators_tool;

/* create tables */

CREATE TABLE IF NOT EXISTS socio_economic_indicators_tool.users (
    user_id         INTEGER NOT NULL,
    login           TEXT NOT NULL,
    password_hash   TEXT NOT NULL,
    created_ts      TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY(user_id)
);

CREATE INDEX IF NOT EXISTS idx__socio_economic_indicators_tool__users__login
    ON socio_economic_indicators_tool.users (login);