import sys
from cx_Freeze import setup, Executable

base = None
if sys.platform == 'win32':
    base = None

options = {
    'build_exe': {
        'include_msvcr': True,
        'includes': 'atexit'
    }
}

executables = [
    Executable('test.py', base=base)
]

setup(name='test',
      version='0.1',
      description='test',
      options=options,
      executables=executables
      )
