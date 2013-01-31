import sublime, sublime_plugin, os, os.path
from os import listdir, lstat
from os.path import dirname, isdir, islink, join, realpath, relpath, commonprefix

class DiredCommand(sublime_plugin.WindowCommand):
	def find_view(self, directory):
		for v in self.window.views():
			if "Dired: " + directory == v.name():
				return self.init_view(v, directory)
		return self.init_view(self.new_view(directory), directory)

	def new_view(self, directory):
		result = self.window.new_file()
		result.settings().set('default_dir', directory)
		result.settings().set('dired_expanded', [])
		result.settings().set('dired_sort', 'name')
		result.settings().set('dired_sort_reverse', False)
		result.settings().set('command_mode', False)
		result.settings().set('dired_current_line', 0)
		return result
	
	def init_view(self, view, directory):
		r = sublime.Region(0, -1 + view.size())
		edit = view.begin_edit()
		view.erase(edit, r)
		view.end_edit(edit)
		view.set_name("Dired: " + directory)
		view.set_scratch(True)
		view.set_syntax_file("Packages/Dired/Dired.tmLanguage")
		view.settings().set('dired_directory', directory)
		return view
	
	def create_entry(self, root, name):
		is_parent = (name == '..')
		if is_parent:
			full = dirname(root)
		else:
			full = join(root, name)
		st = os.stat(full)
		mtime = st.st_mtime
		size = st.st_size
		return {
			'root': root,
			'name': name,
			'is_parent': is_parent,
			'full': full,
			'mtime': mtime,
			'size': size,
		}
	
	def get_entries(self, view):
		root = view.settings().get('dired_directory')
		expanded = view.settings().get('dired_expanded')
		sort_key = view.settings().get('dired_sort')
		sort_reverse = view.settings().get('dired_sort_reverse')
		unsorted = []
		top_level = listdir(root)
		for t in top_level:
			unsorted.append(self.create_entry(root, t))
		for sub in expanded:
			subroot = join(root, sub)
			if not os.path.isdir(subroot): continue
			sublist = listdir(subroot)
			for x in sublist:
				unsorted.append(self.create_entry(root, relpath(join(subroot, x), root)))
		return ([self.create_entry(root, '..')] +
			sorted(unsorted, key=lambda x: x[sort_key], reverse=sort_reverse))

	def update_status(self, view):
		view.set_status('dired_sort', 'Sort by ' + view.settings().get('dired_sort'))
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
		suffixes = ['b', 'k', 'M', 'G']
		directory = self.determine_directory(directory)
		v = self.find_view(directory)
		entries = self.get_entries(v)
		v.settings().set('dired_entries', entries)
		edit = v.begin_edit()
		pt = 0
		for fil in entries:
			filpath = fil['full']
			size = fil['size']
			i = 0
			while (i < len(suffixes) and size > 1024):
				i += 1
				size = size / 1024
			if (i >= len(suffixes)): i = -1 + len(suffixes)
			size_str = '{0:>8.1f}'.format(size) + suffixes[i]
			if (islink(filpath)):
				type = '@'
			elif (isdir(filpath)):
				type = '/'
			else:
				type = ' '
			pt += v.insert(edit, pt, size_str + " |: " + fil['name'] + type + "\n")
		v.end_edit(edit)
		line = v.settings().get('dired_current_line')
		pt = v.text_point(line, 0)
		v.sel().clear()
		v.sel().add(sublime.Region(pt))
		v.show_at_center(pt)
		self.update_status(v)
		self.window.focus_view(v)

class DiredProjectCommand(DiredCommand):
	def determine_directory(self, directory):
		prefix = commonprefix(self.window.folders())
		return prefix

	def new_view(self, directory):
		result = super(DiredProjectCommand, self).new_view(directory)
		folders = self.window.folders()
		if (len(folders)>1):
			result.settings().set('dired_expanded', map(lambda x: relpath(x, directory), self.window.folders()))
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
		self.record_point()
		entry = self.get_entry()
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
			raise TypeError('dired_expand_directory can only be called on directories: ' + f['full'])
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
