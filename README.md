Originally cloned from https://bitbucket.org/hibbelig/dired

Although, I am rewriting a lot of it and adding more of the functionality that I use in emacs dired.

# Dired -- A directory browser in a Sublime Text 2 plugin

The main entry point is `super+k, super+d` on OS X, which brings up a directory browser for the current directory (the directory of the current view).  You can then navigate to the next/previous line with the cursor keys, or with `n/p`, or with `j/k`.

You can open the file on the current line with `Enter`.  If there is a directory on the current line, a new directory browser is created for that directory.

# Supported operations

## Dired-Mode

### OS X
`<Enter>` : Open file

`i` : expand directory

`s, n` : sort name

`s, d` : sort date

`s, r` : revers sort

`q` : quit

`/` : open panel

`super+shift+u` : move up a directory

# License

Copyright (c) 2011 Kai Grossjohann

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.