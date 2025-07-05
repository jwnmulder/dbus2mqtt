import logging


def pytest_runtest_logstart(nodeid, location):
    # Switch to INFO during setup
    logging.getLogger().setLevel(logging.INFO)

def pytest_runtest_call(item):
    # Enable live logs during the call phase

    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger("tzlocal").setLevel(logging.INFO)

def pytest_runtest_teardown(item, nextitem):
    # Back to INFO during teardown
    logging.getLogger().setLevel(logging.INFO)
