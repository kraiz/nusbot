import logging
import shelve
import os
import xml.etree.ElementTree as ET

from datetime import datetime, timedelta, MINYEAR

from nusbot.config import config, config_dir, convert_to_timedelta, format_bytes


logger = logging.getLogger(__name__)


class Node(object):
    def __init__(self, name, size, parent=None):
        self.name = name
        self.size = size
        self.parent = None

    def __repr__(self):
        if self.parent is None:
            return ''
        else:
            return '%s/%s' % (self.parent, self.name)

    def as_message(self):
        return '%r [%s]' % (self, format_bytes(self.size))

    def __eq__(self, other):
        return other is not None and self.name == other.name

    def __lt__(self, other):
        return self.name < other.name

class Directory(Node):
    def __init__(self, children, *args, **kwargs):
        super(Directory, self).__init__(*args, **kwargs)
        self.children = children
        for child in children:
            child.parent = self

    def __hash__(self):
        name = getattr(self, 'name', None)
        return hash(name) if name else hash(super(Directory, self))

    def __iter__(self):
        return iter(self.children)

    def __contains__(self, item):
        return item in self.children


class File(Node):
    def __init__(self, tth, *args, **kwargs):
        super(File, self).__init__(*args, **kwargs)
        self.tth = tth

    def __hash__(self):
        tth = getattr(self, 'tth', None)
        return hash(tth) if tth else hash(super(File, self))

    def __eq__(self, other):
        return self.tth == getattr(other, 'tth', None)


class _FileListHandler(object):

    def __init__(self):
        self.db = shelve.open(os.path.join(config_dir, 'database'), protocol=4)
        self.news = shelve.open(os.path.join(config_dir, 'news'), protocol=4)
        if 'changes' not in self.news:
            self.news['changes'] = []
        self.update_interval = convert_to_timedelta(config['filelist_update'])

    def new_filelist(self, cid, data):
        new_filelist = self.parse_filelist(data)
        diff = self.diff_filelists(self.db[cid]['filelist'], new_filelist)
        self.db[cid] = dict(time=datetime.now(), filelist=new_filelist)
        self.remeber_news(cid, diff)
        return diff

    def remeber_news(self, cid, diff):
        deletions, additions = diff
        if len(deletions) > 0 or len(additions) > 0:
            changes = self.news['changes']
            changes.append(dict(time=datetime.now(), cid=cid, diff=diff))
            self.news['changes'] = changes

    def iter_changes_since(self, since):
        for change in self.news['changes']:
            if change['time'] > since:
                yield change

    def is_filelist_update_needed(self, cid):
        if cid not in self.db:
            self.db[cid] = dict(time=datetime(MINYEAR, 1, 1), filelist=None)
        return self.db[cid]['time'] + self.update_interval < datetime.now()

    def parse_filelist(self, data):
        def parse(node):
            if node.tag in ('FileListing', 'Directory'):
                children = set(parse(c) for c in node)
                size = sum(c.size for c in children)
                return Directory(name=node.attrib.get('Name', node.tag), size=size, children=children)
            elif node.tag == 'File':
                return File(name=node.attrib['Name'], size=int(node.attrib['Size']), tth=node.attrib['TTH'])
        return parse(ET.fromstring(data.decode()))

    def diff_filelists(self, old, new):
        if None in [old, new] or old != new or old.size == new.size:
            return set(), set()
        # must be directory with changed children
        deletions = old.children - new.children
        additions = new.children - old.children
        for old_child, new_child in zip(sorted(old.children - deletions), sorted(new.children - additions)):
            child_deletions, child_additions = self.diff_filelists(old_child, new_child)
            deletions |= child_deletions
            additions |= child_additions
        return deletions, additions

FileListHandler = _FileListHandler()
