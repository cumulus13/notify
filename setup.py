# cython: language_level=3

#import io
#import re
from __future__ import print_function
from setuptools import setup, Command
from setuptools.extension import Extension
from Cython.Build import cythonize  
import os, sys
import shutil

os.environ['CL'] = '/Zm2000'
#os.environ['CC'] = r'gcc.exe'
#os.environ['CXX'] = r'g++.exe'

#os.add_dll_directory(r'c:\TOOLS\msys64\usr\bin')

import __version__
version = __version__.version

NAME = "xnotify"

extensions = [
    Extension(
        "xnotify.notify",
        ["xnotify/notify.pyx"],
        extra_compile_args=['/O2', '/EHsc', '/bigobj'],
        extra_link_args=['/LARGEADDRESSAWARE']
    )
]

#sys.argv.extend(['build', '--compiler=mingw32'])

#ext_modules = cythonize(extensions)
ext_modules = [Extension('notify', sources = ['xnotify/notify.py'])]

def get_version():
    """Get version and version_info without importing the entire module."""
    print("NAME:", NAME)
    path = os.path.join(os.path.dirname(__file__), NAME, '__meta__.py')

    if sys.version_info.major == 3:
        import importlib.util

        spec = importlib.util.spec_from_file_location("__meta__", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        vi = module.__version_info__
        return vi._get_canonical(), vi._get_dev_status()
    else:
        import imp
        vi = imp.load_source("meta", "__meta__.py")
        return vi.__version__, vi.__status__



def get_requirements(req):
    """Load list of dependencies."""

    install_requires = []
    with open(req) as f:
        for line in f:
            if not line.startswith("#"):
                install_requires.append(line.strip())
    return install_requires


def get_description():
    """Get long description."""

    desc = ''

    if os.path.isfile('README.md'):
        with open("README.md", 'r') as f:
            desc = f.read()
    return desc

VER, DEVSTATUS = get_version()

try:
    os.remove(os.path.join('xnotify', '__version__.py'))
except:
    pass
shutil.copy2('__version__.py', 'xnotify')

# with io.open("README.rst", "rt", encoding="utf8") as f:
#     readme = f.read()

# with io.open("__version__.py", "rt", encoding="utf8") as f:
    # version = re.search(r"version = \'(.*?)\'", f.read()).group(1)
import __version__
version = __version__.version

setup(
    name=NAME,
    version=version,
    url="https://bitbucket.org/licface/xnotify",
    project_urls={
        "Documentation": "https://github.com/cumulus13/xnotify",
        "Code": "https://github.com/cumulus13/xnotify",
    },
    license="MIT License",
    author="Hadi Cahyadi LD",
    author_email="cumulus13@gmail.com",
    maintainer="cumulus13 Team",
    maintainer_email="cumulus13@gmail.com",
    description="Send notification to growl libnotify pushbullet NotifyMyDevice",
    # long_description=readme,
    # long_description_content_type="text/markdown",
    packages=[NAME],
    keywords = "send notification to growl, NMD, Pushbullet, syslog, NTFY", 
    include_package_data=True,
    zip_safe=False,
    ext_modules=ext_modules,
    install_requires=[
        'make_colors>=3.12',
        'configset',
        'argparse',
        'configparser',
        'sendgrowl',
        'pydebugger',
        'pushbullet_py',
        'playsound',
        'requests'
    ],
    entry_points = {
         "console_scripts": [
             "xnotify = xnotify:usage",
         ]
    },
    python_requires=">=2.7",
    classifiers=[
        'Development Status :: %s' % DEVSTATUS,
        'Environment :: Console',
        "Intended Audience :: Developers",
        'License :: OSI Approved :: MIT License',
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
