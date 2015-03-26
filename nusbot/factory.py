from collections import defaultdict
from twisted.internet.protocol import ClientFactory, ReconnectingClientFactory
from nusbot.protocol import NusbotHubProtocol, NusbotFilelistDownloadClientProtocol


class NusbotFilelistDownloadClientFactory(ClientFactory):
    protocol = NusbotFilelistDownloadClientProtocol

    def __init__(self, hub_factory):
        self.hub_factory = hub_factory


class NusbotHubFactory(ReconnectingClientFactory):
    protocol = NusbotHubProtocol

    def __init__(self, scan_interval, storage):
        self.protocol_instance = None
        self.scan_interval = scan_interval
        self.storage = storage
        self.filelist_download_factory = NusbotFilelistDownloadClientFactory(self)
        self.user_infos = defaultdict(dict)
        self.client_connections = defaultdict(dict)


