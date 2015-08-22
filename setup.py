
try:
    # I hate extra stuff, but pip looks at "install_requires" which is
    # only from setuptools.  Importing it will monkeypatch the dist
    # system and keep it from complaining about an unknown keyword.
    from setuptools import setup, Command
except:
    from distutils.core import Command, setup

import versioneer

import subprocess
from os.path import abspath, join, dirname, exists

class TestCommand(Command):

    # This is temporary until we get proper unit tests.  It just makes
    # it easier to fire up the "e1" test from the root directory.

    description = 'runs e1'
    user_options = []
    def initialize_options(self): pass
    def finalize_options(self): pass
    def run(self):
        cmd = 'python3 e1.py'
        p = subprocess.Popen(args=cmd, cwd=join(dirname(abspath(__file__)), 'example'), shell=True)
        p.wait()


class PyLintCommand(Command):
    description = "Runs pylint"

    user_options = [
        ('bad-functions=', 'f', 'functions that are reported (e.g. print)'),
        ('allow-unused=', 'u', 'a regexp of variables that can be unused'),
        ('errors-only', 'E', 'errors only'),
        ('no-reports', 'n', 'do not print reports'),
        ('ignore-docstring', 'd', 'ignore missing doc string message'),
        ('exclude-noisy', 'x', 'exclude docstring and fixme messages and disable reports')
    ]

    def initialize_options(self):
        self.errors_only  = None
        self.no_reports   = None
        self.bad_functions = None
        self.allow_unused = None
        self.ignore_docstring = None
        self.exclude_noisy = None

    def finalize_options(self):
        self.no_reports   = bool(self.no_reports)
        self.ignore_docstring = bool(self.ignore_docstring)
        self.exclude_noisy = bool(self.exclude_noisy)

    def run(self):

        cmd = ['pylint']

        # The shared .pylintrc file is stored in this package.
        rcfile = join(dirname(abspath(__file__)), '.pylintrc')
        if exists(rcfile):
            cmd.append('--rcfile={}'.format(rcfile))

        if self.errors_only:
            cmd.append('-E')

        if self.no_reports or self.exclude_noisy:
            cmd.append('-rn')

        if self.bad_functions:
            cmd.append("--bad-functions={}".format(self.bad_functions))
        if self.allow_unused:
            cmd.append("--dummy-variables-rgx={}".format(self.allow_unused))

        if self.exclude_noisy:
            cmd.append("--disable=C0111,fixme")
        elif self.ignore_docstring:
            cmd.append("--disable=C0111")

        cmd.append('servant')

        if self.verbose >= 2:
            print('cmd:', ' '.join(cmd))

        return subprocess.call(cmd)


cmdclass = versioneer.get_cmdclass()
cmdclass.update({
    'lint' : PyLintCommand,
    'test' : TestCommand,
})

setup(
    name        = 'Servant',
    description = 'Python 3 asyncio web server',
    version=versioneer.get_version(),
    packages    = ['servant', 'servant.middleware'],
    install_requires = [
        'cookies'
    ],
    cmdclass = cmdclass
)
