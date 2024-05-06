from robottelo.config import settings
from robottelo.logging import logger


def test_ipv6_poc():
    logger.info(f'hostname for IPA set in settings: {settings.ipa.hostname}')
