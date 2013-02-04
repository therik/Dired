import sublime
import sublime_plugin
import os
import os.path
from os import path
from os import listdir
from os.path import dirname
from os.path import isdir
from os.path import commonprefix
from os.path import relpath
from os.path import join
import grp
import pwd
from datetime import datetime
from stat import *


class Entry(object):
    """docstring for Entry"""
    def __init__(self, root, name):
        super(Entry, self).__init__()
        self.root = root
        self.name = name
        self.is_parent = (self.name == '..')

        if self.is_parent:
            self.full = dirname(self.root)
        else:
            self.full = join(self.root, self.name)

        try:
            self.stat_info = os.stat(self.full)
        finally:
            self.stat_info = os.lstat(self.full)

    def __str__(self):
        return (self.get_permission_string() + "\t"
            + self.get_owner() + "\t"
            + self.get_group() + "\t"
            + self.get_size() + "\t"
            + self.get_last_modified() + "\t"
            + self.name)

    def __getitem__(self, index):
        if index == 'root':
            return self.root
        elif index == 'name':
            return self.name
        elif index == 'is_parent':
            return self.is_parent
        elif index == 'full':
            return self.full
        elif index == 'mtime':
            return self.mtime
        elif index == 'size':
            return self.size

    def get_permission_string(self):
        pref_string = list('----------')
        if path.isdir(self.full):
            pref_string[0] = 'd'
        elif path.islink(self.full):
            pref_string[0] = 'l'

        permissions = os.stat(self.full)[ST_MODE]
        if (permissions & S_IRUSR) > 0:
            pref_string[1] = 'r'
        if (permissions & S_IWUSR) > 0:
            pref_string[2] = 'w'
        if (permissions & S_IXUSR) > 0:
            pref_string[3] = 'x'

        if (permissions & S_IRGRP) > 0:
            pref_string[4] = 'r'
        if (permissions & S_IWGRP) > 0:
            pref_string[5] = 'w'
        if (permissions & S_IXGRP) > 0:
            pref_string[6] = 'x'

        if (permissions & S_IROTH) > 0:
            pref_string[7] = 'r'
        if (permissions & S_IWOTH) > 0:
            pref_string[8] = 'w'
        if (permissions & S_IXOTH) > 0:
            pref_string[9] = 'x'

        return ''.join(pref_string)

    def get_size(self):
        suffixes = ['b', 'k', 'M', 'G']
        i = 0
        size = self.stat_info.st_size
        while (i < len(suffixes) and size > 1024):
            i += 1
            size = size / 1024
        if (i >= len(suffixes)):
            i = -1 + len(suffixes)
        return '{0:>8.1f}'.format(size) + suffixes[i]

    def get_last_modified(self):
        return str(datetime.fromtimestamp(self.stat_info.st_mtime))

    def get_owner(self):
        uid = self.stat_info.st_uid
        return pwd.getpwuid(uid)[0]

    def get_group(self):
        gid = self.stat_info.st_gid
        return grp.getgrgid(gid)[0]


class DiredView(object):
    """docstring for DiredView"""
    def __init__(self, window=None, directory=None, view=None):
        super(DiredView, self).__init__()
        self.directory = directory

        self.view = view
        if not self.view:
            # check to see if the view already exists
            for view in window.views():
                if "Dired: " + directory == view.name():
                    self.view = view

        # create a new view if we did not return an existing one
        if not self.view:
            self.view = window.new_file()
            self.view.settings().set('default_dir', directory)
            self.view.settings().set('dired_expanded', [])
            self.view.settings().set('dired_sort', 'name')
            self.view.settings().set('dired_sort_reverse', False)
            self.view.settings().set('command_mode', False)
            self.view.settings().set('dired_current_line', 0)

        self.entries = self.get_entries(self.view)

    def draw(self):
        region = sublime.Region(0, -1 + self.view.size())
        edit = self.view.begin_edit()
        self.view.erase(edit, region)
        self.view.end_edit(edit)
        self.view.set_name("Dired: " + self.directory)
        self.view.set_scratch(True)
        self.view.set_syntax_file("Packages/Dired/Dired.tmLanguage")
        self.view.settings().set('dired_directory', self.directory)

        edit = self.view.begin_edit()
        pt = 0
        for entry in self.entries:
            pt += self.view.insert(edit, pt, str(entry) + "\n")
        self.view.end_edit(edit)
        line = self.view.settings().get('dired_current_line')
        pt = self.view.text_point(line, 0)
        self.view.sel().clear()
        self.view.sel().add(sublime.Region(pt))
        self.view.show_at_center(pt)
        self.view.set_read_only(True)

    def get_entries(self, view):
        root = self.directory
        expanded = view.settings().get('dired_expanded')
        sort_key = view.settings().get('dired_sort')
        sort_reverse = view.settings().get('dired_sort_reverse')
        unsorted = []
        top_level = listdir(root)
        for t in top_level:
            unsorted.append(Entry(root, t))
        for sub in expanded:
            subroot = join(root, sub)
            if not os.path.isdir(subroot):
                continue
            sublist = listdir(subroot)
            for x in sublist:
                unsorted.append(
                    Entry(root, relpath(join(subroot, x), root))
                )
        return ([Entry(root, '..')] +
            sorted(unsorted, key=lambda x: x[sort_key], reverse=sort_reverse))


class DiredCommand(sublime_plugin.WindowCommand):
    def update_status(self, view):
        view.set_status('dired_sort', 'Sort by '
            + view.settings().get('dired_sort'))
        if view.settings().get('dired_sort_reverse'):
            view.set_status('dired_sort_reverse', 'reverse')
        else:
            view.erase_status('dired_sort_reverse')

    def determine_directory(self, directory):
        if (not directory):
            active_view = self.window.active_view()
            if (active_view.settings().get('dired_directory')):
                return active_view.settings().get('dired_directory')
            else:
                return dirname(active_view.file_name())
        else:
            return directory

    def run(self, directory=False):
        directory = self.determine_directory(directory)
        self.diredView = DiredView(window=self.window, directory=directory)
        self.diredView.draw()
        self.update_status(self.diredView.view)
        self.window.focus_view(self.diredView.view)


class DiredProjectCommand(DiredCommand):
    def determine_directory(self, directory):
        prefix = commonprefix(self.window.folders())
        return prefix

    def new_view(self, directory):
        result = super(DiredProjectCommand, self).new_view(directory)
        folders = self.window.folders()
        if (len(folders) > 1):
            result.settings().set('dired_expanded',
                map(lambda x: relpath(x, directory), self.window.folders()))
        return result


class DiredLineParser(sublime_plugin.TextCommand):
    def get_entry(self):
        line_number = self.view.rowcol(self.view.sel()[0].begin())[0]
        result = self.view.settings().get('dired_entries')[line_number]
        return result

    def record_point(self):
        pt = self.view.sel()[0].begin()
        line, _ = self.view.rowcol(pt)
        self.view.settings().set('dired_current_line', line)

    def dired(self, directory=False):
        if not directory:
            directory = self.view.settings().get('dired_directory')
        self.view.window().run_command('dired', {
            'directory': directory,
        })


class DiredOpenFileCommand(DiredLineParser):
    def run(self, edit):
        directory = self.view.settings().get('dired_directory')
        print directory
        self.diredView = DiredView(directory=directory, view=self.view)
        self.record_point()
        entry = self.diredView.entries[self.view.settings().get('dired_current_line')]
        v = self.view
        f = entry['full']
        if (isdir(f)):
            self.dired(directory=f)
        else:
            v.window().open_file(f)


class DiredOpenParentDirectory(sublime_plugin.TextCommand):
    def run(self, directory=False):
        directory = self.view.settings().get('dired_directory')
        directory = os.path.dirname(directory)
        self.view.window().run_command('dired', {
            'directory': directory,
        })


class DiredExpandDirectoryCommand(DiredLineParser):
    def run(self, edit):
        self.record_point()
        f = self.get_entry()
        if (f['is_parent']):
            raise TypeError("Cannot expand '..'")
        v = self.view
        if (not isdir(f['full'])):
            raise TypeError(
                'dired_expand_directory can only be called on directories: '
                + f['full'])
        expanded = v.settings().get('dired_expanded')
        if (f['name'] not in expanded):
            expanded.append(f['name'])
        v.settings().set('dired_expanded', expanded)
        self.dired()


class DiredSortCommand(DiredLineParser):
    """Sort the listing as per the specified criteria.
    Argument 'sort' can be one of the following strings:
        'name': sort by name
        'mtime': sort by last-modified time
    Argument 'reverse' must be true or false."""
    def run(self, edit, sort, reverse):
        v = self.view
        v.settings().set('dired_sort', sort)
        v.settings().set('dired_sort_reverse', reverse)
        self.dired()


class DiredReverseSortCommand(DiredLineParser):
    """Reverse the sort direction."""
    def run(self, edit):
        v = self.view
        reverse = v.settings().get('dired_sort_reverse')
        v.settings().set('dired_sort_reverse', not reverse)
        self.dired(False)
