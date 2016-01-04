import urllib
from xml.etree import ElementTree


def format_bytes(num):
    for x in ['B', 'KB', 'MB', 'GB', 'TB', 'PT']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


class Node(object):
    def __init__(self, name, size, parent=None):
        self.name = name
        self.size = size
        self.parent = parent

    def __repr__(self):
        if self.parent is None:
            return ''
        else:
            return '%s/%s' % (self.parent, self.name.encode('utf-8'))

    def as_message(self, **kwargs):
        return '%s [%s]' % (self, format_bytes(self.size))

    def __eq__(self, other):
        return other is not None and self.name == other.name

    def __ne__(self, other):
        return other is not None and self.name != other.name

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

    def as_message(self, **kwargs):
        msg = ''
        if kwargs.pop('magnet_enabled', False):
            msg += ' magnet:?' + urllib.urlencode({
                'xt': 'urn:tree:tiger:' + self.tth,
                'xl': self.size,
                'dn': self.name
            })
        return super(File, self).as_message(**kwargs) + msg


def parse_filelist(data):
    def parse(node):
        if node.tag in ('FileListing', 'Directory'):
            children = set(parse(c) for c in node)
            size = sum(c.size for c in children)
            return Directory(name=node.attrib.get('Name', node.tag), size=size, children=children)
        elif node.tag == 'File':
            return File(name=node.attrib['Name'], size=int(node.attrib['Size']), tth=node.attrib['TTH'])

    return parse(ElementTree.fromstring(data))


def diff_filelists(old_filelist, new_filelist, magnet_enabled=False):
    def recursive_diff(old, new):
        if None in [old, new] or old != new or old.size == new.size:
            return set(), set()
        # must be directory with changed children
        deletions = old.children - new.children
        additions = new.children - old.children
        for old_child, new_child in zip(sorted(old.children - deletions), sorted(new.children - additions)):
            child_deletions, child_additions = recursive_diff(old_child, new_child)
            deletions |= child_deletions
            additions |= child_additions
        return deletions, additions

    # format as lists of strings
    deletions, additions = recursive_diff(old_filelist, new_filelist)
    format = lambda n: n.as_message(magnet_enabled=magnet_enabled)
    return map(format, deletions), map(format, additions)
