# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import pytest
from gosa.backend.main import *
from gosa.common.env import make_session


def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true", help="run slow tests")
    parser.addoption("--travis", action="store_true", default=False, help="Use travis config for tests")


def pytest_configure(config):
    sys._called_from_test = True


def pytest_unconfigure(config):
    del sys._called_from_test
    PluginRegistry.getInstance('HTTPService').srv.stop()
    shutdown()


@pytest.fixture(scope="session", autouse=True)
def use_test_config():
    Environment.reset()
    if pytest.config.getoption("--travis") is True:
        Environment.config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "travis_conf")
    else:
        Environment.config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "test_conf")
    Environment.noargs = True

    Environment.getInstance()
    if not sys.stdout.encoding:
        sys.stdout = codecs.getwriter('utf8')(sys.stdout)
    if not sys.stderr.encoding:
        sys.stderr = codecs.getwriter('utf8')(sys.stderr)

    pkg_resources.require('gosa.common==%s' % VERSION)
    main()
    # check for trigger
    with make_session() as session:
        if session.execute("select * from pg_trigger WHERE tgname LIKE 'so_index%'").rowcount == 0:
            print("creating trigger")
            # create trigger
            session.execute("CREATE OR REPLACE FUNCTION public.so_index_search_vector_update() RETURNS trigger AS $BODY$ BEGIN NEW.search_vector = ((setweight(to_tsvector('pg_catalog.simple', regexp_replace(coalesce(NEW.title, ''), '[-@.]', ' ', 'g')), 'A') || setweight(to_tsvector('pg_catalog.simple', regexp_replace(coalesce(NEW.description, ''), '[-@.]', ' ', 'g')), 'C')) || setweight(to_tsvector('pg_catalog.simple', regexp_replace(coalesce(NEW.search, ''), '[-@.]', ' ', 'g')), 'C')) || setweight(to_tsvector('pg_catalog.simple', regexp_replace(coalesce(NEW.types, ''), '[-@.]', ' ', 'g')), 'B'); RETURN NEW; END $BODY$ LANGUAGE plpgsql VOLATILE COST 100; ALTER FUNCTION public.so_index_search_vector_update() OWNER TO admin;")

    # sync index
    index = PluginRegistry.getInstance("ObjectIndex")
    index.sync_index()

    with make_session() as session:
        res = session.execute("SELECT search_vector from \"so_index\" LIMIT 1").fetchone()
        assert res[0] is not None
