from collections import defaultdict
import random
import io
from bz2 import BZ2Decompressor

from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver
from twisted.python import log

import nusbot


escape = lambda v: v.replace(' ', '\s')
unescape = lambda v: v.replace('\s', ' ')


class ADCProtocol(LineReceiver):
    delimiter = '\n'

    adc_msg_type = None
    adc_features = ['BASE', 'TIGR']
    adc_inf = {
        'ID': 'SXX4RUEEB263P3EX7VAGSMHGO4XVDBTQOJZNONI',
        'PD': '4MH2IBPDTOP34ELXWSXRY35CSTHDR3PCOMWZPMI',
        'CT': '1',
        'NI': 'nusbot',
        'VE': 'nusbot\s%s' % nusbot.__version__,
        'DE': 'I\'m\sa\sbot,\stype\s"nusbot"\sinto\sthe\schat!',
        'SU': 'TCP4'
    }

    def __init__(self):
        self.infos = defaultdict(dict)

    def connectionMade(self):
        self.send_SUP()

    def rawDataReceived(self, data):
        pass

    def lineReceived(self, line):
        try:
            msg_type, cmd, args = line[0], line[1:4], line[5:]
        except:
            log.err('Error parsing line "%s"' % line)
        else:
            handler = 'handle_%s' % cmd
            if hasattr(self, handler):
                getattr(self, handler)(msg_type, args)
            else:
                log.msg('ignoring command: %s' % line)

    def send_SUP(self):
        self.sendLine(' '.join(
            ['%sSUP' % self.adc_msg_type] +
            map(lambda f: 'AD%s' % f, self.adc_features)
        ))

    def handle_SUP(self, msg_type, args):
        pass

    def handle_INF(self, msg_type, args):
        self.infos.update(**{
            a[:2]: unescape(a[2:]) for a in args.split()
        })

    def handle_STA(self, msg_type, args):
        code, txt = args[:3], args[4:]
        if code[0] != '0':
            log.msg('Error %s: %s' % (code, unescape(txt)))


class ADCClient2HubProtocol(ADCProtocol):
    adc_msg_type = 'H'

    def __init__(self):
        ADCProtocol.__init__(self)
        self.sid = None

    def connectionMade(self):
        ADCProtocol.connectionMade(self)
        self.factory.protocol_instance = self

    def handle_SID(self, msg_type, args):
        self.sid = args

    def handle_INF(self, msg_type, args):
        if msg_type == 'B':  # prefixed with SID
            sid, args = args[:4], args[5:]
            self.factory.user_infos[sid].update(**{
                a[:2]: unescape(a[2:]) for a in args.split()
            })
            user_info = self.factory.user_infos.get(sid, None)
            if user_info:
                log.msg('User update for %s : %r' % (user_info['NI'], user_info))
                self.on_user_info(sid, self.factory.user_infos[sid])
        else:
            ADCProtocol.handle_INF(self, msg_type, args)
            self.send_INF()
            self.on_connected()

    def handle_QUI(self, msg_type, args):
        sid, args = args[:4], args[5:]
        if sid in self.factory.user_infos:
            log.msg('User %s has left the hub.' % self.factory.user_infos[sid]['NI'])
            del self.factory.user_infos[sid]

    def handle_MSG(self, msg_type, args):
        sid, txt = args[:4], args[5:]
        user_info = self.factory.user_infos.get(sid, None)
        if user_info:
            self.chat_received(unescape(txt), sid, user_info['ID'], user_info['NI'])

    def handle_CTM(self, msg_type, args):
        target_sid, my_sid, proto, port, token = args.split()
        addr = (self.factory.user_infos[target_sid]['I4'], int(port))
        self.factory.client_connections[addr] = dict(cid=target_sid, token=token)
        reactor.connectTCP(addr[0], addr[1], self.factory.filelist_download_factory)

    def send_INF(self):
        self.sendLine(' '.join(
            ['BINF', self.sid] +
            [''.join(e) for e in self.adc_inf.items()]
        ))

    # --- upstream api to be consumed be implementor

    def get_user(self, sid=None, cid=None, nick=None):
        for user in self.get_all_users():
            if sid is not None and sid == user['sid']:
                return user
            if cid is not None and cid == user['cid']:
                return user
            if nick is not None and nick == user['nick']:
                return user

    def get_all_users(self):
        return [
            dict(sid=sid, cid=values['ID'], nick=values['NI'])
            for sid, values in self.factory.user_infos.items()
        ]

    def say(self, txt, target_sid=None):
        for txt_line in txt.split('\n'):
            if target_sid is None:
                line = ['BMSG', self.sid]
            else:
                line = ['DMSG', self.sid, target_sid]

            line.append(escape(txt_line))
            self.sendLine(str(' '.join(line)))

    def request_client_connection(self, target_sid):
        log.msg('Requesting client connection to %s' % (self.get_user(sid=target_sid)['nick']))
        token = str(random.randint(100000000, 999999999))
        self.sendLine(' '.join(
            ['DRCM', self.sid, target_sid, 'ADC/1.0', token]
        ))

    # --- abstract methods to implement

    def on_connected(self):
        raise NotImplementedError()

    def on_user_info(self, sid, user_info):
        pass

    def chat_received(self, text, sid, cid, user_info):
        raise NotImplementedError()


class ADCClient2ClientProtocol(ADCProtocol):
    adc_msg_type = 'C'

    def __init__(self):
        ADCProtocol.__init__(self)
        self.expected_data_length = 0
        self.filelist = None
        self.filelist_size = 0
        self.extenions = []
        self.bzip = False
        self.bz2 = None

    def handle_SUP(self, msg_type, args):
        info = self.factory.hub_factory.client_connections[self.transport.addr]
        self.sendLine('CINF ID%s TO%s' % (self.adc_inf['ID'], info['token']))
        self.extenions = [a.lstrip('AD') for a in args.split() if a.startswith('AD')]

    def handle_INF(self, msg_type, args):
        ADCProtocol.handle_INF(self, msg_type, args)
        self.on_connected()

    def handle_SND(self, msg_type, args):
        data_type, path, start, end = args.split()
        if data_type == 'list':
            assert path == '/'
            assert start == '0'
        elif data_type == 'file':
            assert path == 'files.xml.bz2'
            assert start == '0'
            self.bzip = True
            self.bz2 = BZ2Decompressor()
        self.expected_data_length = int(end)
        self.filelist = io.BytesIO(end)
        self.filelist_size = 0
        self.setRawMode()

    def rawDataReceived(self, data):
        self.filelist_size += len(data)
        self.filelist.write(self.bz2.decompress(data) if self.bzip else data)
        if self.filelist_size >= self.expected_data_length:
            self.setLineMode()
            self.on_filelist(self.infos['ID'], self.filelist.getvalue())
            self.filelist.close()

    def connectionLost(self, reason):
        if self.transport.addr in self.factory.hub_factory.client_connections:
            del self.factory.hub_factory.client_connections[self.transport.addr]

    # --- upstream api to be consumed be implementor

    def request_filelist(self):
        if 'BZIP' in self.extenions:
            self.sendLine('CGET file files.xml.bz2 0 -1')
        else:
            self.sendLine('CGET list / 0 -1 RE1')

    # --- abstract methods to implement

    def on_connected(self):
        raise NotImplementedError()

    def on_filelist(self, cid, data):
        raise NotImplementedError()