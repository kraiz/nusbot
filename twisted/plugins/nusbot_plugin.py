from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from twisted.application import internet

from nusbot.factory import NusbotHubFactory
from nusbot.storage import SqliteStorage


class Options(usage.Options):
    optFlags = [
        ['magnet', 'm', 'Add magnet links to file changes']
    ]
    optParameters = [
        ['host', 'h', '10.10.0.1', 'The hub host/ip to connect to.'],
        ['port', 'p', 1511, 'The hub port to connect on.', int],
        ['db', 'd', '~/.nusbot/nusbot.db', 'Path the to database file.'],
        ['interval', 'i', 60, 'Minutes after which a user filelist will be scanned for changes.', int],
    ]


class NusbotServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = 'nusbot'
    description = 'Start\'s the bot and let it connect to the given hub.'
    options = Options

    def makeService(self, options):
        return internet.TCPClient(
            options['host'], options['port'],
            NusbotHubFactory(
                scan_interval=options['interval'] * 60,
                magnet_enabled=options['magnet'],
                storage=SqliteStorage(options['db'])
            )
        )


serviceMaker = NusbotServiceMaker()
