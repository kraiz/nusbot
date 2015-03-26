from datetime import date, datetime, timedelta
from twisted.internet import task
from twisted.python import log
from nusbot.adc import ADCClient2HubProtocol, ADCClient2ClientProtocol
from nusbot.filelist import parse_filelist, diff_filelists


class NusbotHubProtocol(ADCClient2HubProtocol):

    def __init__(self):
        ADCClient2HubProtocol.__init__(self)
        self.scan_loop = None

    def on_connected(self):
        self.scan_loop = task.LoopingCall(self.scan)
        self.scan_loop.start(self.factory.scan_interval)

    def scan(self, nick=None):
        if nick is not None:
            user = self.get_user(nick=nick)
            self.request_client_connection(user['sid'])
        else:
            for user in self.get_all_users():
                self.request_client_connection(user['sid'])

    def chat_received(self, text, sid, cid, nick):
        if text.startswith('nusbot'):
            args = text[6:].split()
            if not args:
                self.say('Usage: nusbot <command>')
                self.say('Commands:')
                self.say('scan <nick>      scan a user\'s filelist, default: yourself')
                self.say('show <since>     Show changes since (in days), default: 7')
            else:
                cmd = args.pop(0)
                if cmd == 'scan':
                    user = args.pop(0) if args else nick
                    self.say('Scanning %s (not anouncing empty changes)...' % user)
                    self.scan(user)
                elif cmd == 'show':
                    try:
                        days = int(args.pop(0))
                    except:
                        days = 7
                    since = date.today() - timedelta(days=days)
                    self.say('Changes since %s:' % since.isoformat())
                    for user_cid, timestamp, diff in self.factory.storage.get_changes(since):
                        self.announce_changes(user_cid, diff, timestamp=timestamp)
                else:
                    self.say('Unknown command: %s' % cmd)

    def announce_changes(self, user_cid, diff, timestamp=None):
        user = self.get_user(cid=user_cid)
        time = timestamp.date().isoformat() if timestamp else ''
        for added in diff[1]:
            self.say('Added %s: <%s>%s' % (time, user['nick'], added))
        for deleted in diff[0]:
            self.say('Deleted %s: <%s>%s' % (time, user['nick'], deleted))



class NusbotFilelistDownloadClientProtocol(ADCClient2ClientProtocol):

    def on_connected(self):
        self.request_filelist()

    def on_filelist(self, cid, data):
        storage = self.factory.hub_factory.storage

        # get old, save new
        old = storage.get_filelist(cid)
        storage.save_filelist(cid, datetime.now(), data)

        if old is not None:
            # parse and diff
            old_list = parse_filelist(old)
            new_list = parse_filelist(data)
            diff = diff_filelists(old_list, new_list)
            log.msg('got filelist of %s and with deletions/additions:' % cid, diff)

            # if there are changes, save them too
            deletions, additions = diff
            if len(deletions) > 0 or len(additions) > 0:
                self.factory.hub_factory.protocol_instance.announce_changes(cid, diff)
                storage.save_change(cid, datetime.now(), diff)

        # we're done, so close client connection
        self.transport.loseConnection()

