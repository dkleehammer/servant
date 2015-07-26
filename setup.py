
from distutils.core import Command, setup
from distutils.errors import *
import subprocess, os
from os.path import abspath, isdir, join, dirname, exists

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

        env = dict(os.environ)

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

        import subprocess
        return subprocess.call(cmd, env=env)


setup(
    name        = 'Servant',
    description = 'Python 3 asyncio web server',
    version     = '1.0.0',
    cmdclass = {
        'lint' : PyLintCommand,
    }
)
