import asyncio
import logging
import sys

from nusbot.adc import HubConnectionInstance
from nusbot.config import config

logging.basicConfig(
    format='%(asctime)s %(levelname)-7s %(message)s',
    stream=sys.stdout,
    level=logging.INFO
)

logging.getLogger('asyncio').setLevel(logging.ERROR)

logger = logging.getLogger(__name__)


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(loop.create_connection(
        lambda: HubConnectionInstance,
        config['hub_host'],
        config.getint('hub_port')
    ))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        logger.info('Shutting down.')
        loop.close()


if __name__ == '__main__':
    main()
