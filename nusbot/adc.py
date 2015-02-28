import asyncio
import io
import logging
import random
import string
import sys

from datetime import datetime

from nusbot.config import config, convert_to_timedelta
from nusbot.filelist import FileListHandler


escape = lambda v: v.replace(' ', '\s')
unescape = lambda v: v.replace('\s', ' ')

logger = logging.getLogger(__name__)

INF = {
    'ID': 'SXX4RUEEB263P3EX7VAGSMHGO4XVDBTQOJZNONI',
    'PD': '4MH2IBPDTOP34ELXWSXRY35CSTHDR3PCOMWZPMI',
    'CT': '1',
    'NI': config['nickname'],
    'VE': 'nusbot\s0.1.1',
    'DE': 'I\'m\sa\sbot,\stype\s"$help"\sinto\sthe\schat!',
    'SU': 'TCP4'
}


class ClientConnection(asyncio.Protocol):
    COMMANDS, DATASTREAMING = range(2)

    def __init__(self):
        self.infos = {}
        self.state = self.COMMANDS
        self.expected_data_length = None
        self.filelist = None
        self.filelist_size = 0

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        if self.state == self.COMMANDS:
            for chunk in data.decode().splitlines():
                self.parse(chunk)
        else:  # expect data streaming
            self.filelist.write(data)
            self.filelist_size += len(data)
            if self.filelist_size >= self.expected_data_length:
                diff = FileListHandler.new_filelist(self.infos['ID'], self.filelist.getvalue())
                HubConnectionInstance.announce_diff(self.infos['ID'], diff)
                logger.info('Closing connection to %s' % self.infos['ID'])
                self.filelist.close()
                self.transport.close()
                HubConnectionInstance.client_connections.pop(self.infos['ID']).close()

    def parse(self, chunk):
        cmd, args = chunk[:4], chunk[5:]
        if cmd == 'CSUP':
            self.transport.write('CSUP ADBASE ADTIGR\n'.encode())
        elif cmd == 'CINF':
            self.infos = {a[:2]: unescape(a[2:]) for a in args.split()}
            # send bot's info
            self.transport.write(('CINF ID%s\n' % INF['ID']).encode())
            # request complete filelist
            self.transport.write('CGET list / 0 -1 RE1\n'.encode())
        elif cmd == 'CSND':
            data_type, path, start, end = args.split()
            assert data_type == 'list'
            assert path == '/'
            assert start == '0'
            self.expected_data_length = int(end)
            self.state = self.DATASTREAMING
            self.filelist = io.BytesIO()
            self.filelist_size = 0
        elif cmd == 'CSTA':
            status, code, args = args[0], args[1:2], args[3:]
            if status != '0':
                logger.error('Client code: %s: %s', code, args)
        else:
            logger.warn('unhandled client cmd: %s', chunk)


class HubConnection(asyncio.Protocol):
    INITIAL, PROTOCOL, IDENTIFY, VERIFY, NORMAL, DATA = range(6)

    def __init__(self, *args, **kwargs):
        super(HubConnection, self).__init__(*args, **kwargs)
        self.ports = range(39000, 42000)
        self.inf = INF
        self.sid = None
        self.hub = dict()
        self.users = dict()
        self.client_connections = {}
        self.state = self.INITIAL

    def connection_made(self, transport):
        self.transport = transport
        self.transport.write('HSUP ADBASE ADTIGR\n'.encode())

    def data_received(self, data):
        for chunk in data.decode().splitlines():
            self.parse(chunk)

    def connection_lost(self, exc):
        asyncio.get_event_loop().stop()

    def parse(self, chunk):
        try:
            msg_type, cmd, args = chunk[0], chunk[1:4], chunk[5:]
        except:
            logger.exception('Parsing "%s"' % chunk)
        else:
            handler = 'handle_%s' % cmd
            if hasattr(self, handler):
                getattr(self, handler)(msg_type, args)
            else:
                logger.info('ignoring unknown command: %s%s %r', msg_type, cmd, args)

    def handle_SUP(self, msg_type, args):
        pass

    def handle_SID(self, msg_type, args):
        self.sid = args
        self.state = self.IDENTIFY

    def handle_INF(self, msg_type, args):
        if msg_type == 'B':
            # prefixed with SID
            sid, args = args[:4], args[5:]
        else:
            sid = None

        infos = {a[:2]: unescape(a[2:]) for a in args.split()}

        if msg_type == 'B' and sid is not None:
            self.users[sid] = infos
        else:
            self.hub = infos

    def handle_STA(self, msg_type, args):
        code, txt = args[:3], args[4:]
        logger.log(
            logging.INFO if code[0] == '0' else logging.ERROR,
            'Received: ' + unescape(txt)
        )
        if self.state == self.IDENTIFY:
            self.transport.write(('BINF %s %s\n' % (
                self.sid,
                ' '.join(''.join(e) for e in self.inf.items())
            )).encode())
            self.state = self.NORMAL
            logger.info('Successfully connected to hub: %(NI)s (%(VE)s)', self.hub)
            asyncio.get_event_loop().call_later(5, self.refresh_user_file_lists)

    def handle_MSG(self, msg_type, args):
        sid, txt = args[:4], args[5:]
        if txt.startswith('$'):
            bot_cmd, *bot_args = txt.split()
            if bot_cmd == '$help':
                self.say('$news [1w] - Shows news since the given time, f.e. 6h, 1d, 2w, 1y')
            elif bot_cmd == '$news':
                delta = '1w' if len(bot_args) == 0 else bot_args[0]
                try:
                    since = datetime.now() - convert_to_timedelta(delta)
                except Exception:
                    self.say('Given time isn\'t valid: %s' % delta, sid)
                else:
                    self.say('Changes since %s:' % since.isoformat(), sid)
                    for change in FileListHandler.iter_changes_since(since):
                        self.announce_diff(change['cid'], change['diff'], sid)


    def refresh_user_file_lists(self):
        loop = asyncio.get_event_loop()
        loop.call_later(30, self.refresh_user_file_lists)

        for sid, info in self.users.items():
            if sid != self.sid and 'ID' in info and info['ID'] not in self.client_connections \
                    and FileListHandler.is_filelist_update_needed(info['ID']):
                # choose random port and token
                port = random.choice(self.ports)
                token = ''.join(random.choice(string.ascii_lowercase) for i in range(9))
                # start listing for incoming connection
                server = loop.create_server(ClientConnection, self.users[self.sid]['I4'], port)
                asyncio.async(server)
                # remember
                self.client_connections[info['ID']] = server
                # tell user to connect to us
                self.transport.write(
                    ' '.join(['DCTM', self.sid, sid, 'ADC/1.0', str(port), token, '\n']).encode()
                )
                logger.info('Asking %s for its filelist', info['NI'])

    def get_user_by_cid(self, cid):
        for sid, info in self.users.items():
            if info.get('ID', None) == cid:
                return info

    def say(self, txt, sid=None):
        broadcast = sid is None
        line = ['BMSG' if broadcast else 'DMSG', self.sid]
        if not broadcast:
            line.append(sid)
        line.append('%s\n' % escape(txt))
        self.transport.write(' '.join(line).encode())

    def announce_diff(self, cid, diff, sid=None):
        user = self.get_user_by_cid(cid)
        if user is None:
            logger.error('announce_diff but user with cid "%s" is unknown. diff: %r', cid, diff)
        else:
            deletions, additions = diff
            for added in additions:
                message = '[Added][%s]: %s' % (user['NI'], added.as_message())
                logger.info(message)
                self.say(message, sid)
            for removed in deletions:
                message = '[Removed][%s]: %s' % (user['NI'], removed.as_message())
                logger.info(message)
                self.say(message, sid)


HubConnectionInstance = HubConnection()
