from setuptools import setup, find_packages
import re

from safas import __version__

def get_property(prop, project):
    """ properties are stored in safas/__init__.py """
    result = re.search(r'{}\s*=\s*[\'"]([^\'"]*)[\'"]'.format(prop), open(project + '/__init__.py').read())
    return result.group(1)

name = "safas"
setup(
    name=name,
    version = get_property('__version__', name),
    author='M. Ryan MacIver',
    author_email='rmcmaciver@hotmail.com',
    url='https://rmaciver.github.io/safas/',
    packages=find_packages(),
    long_description=open('README.md').read(),
    entry_points={
          'console_scripts': [
              'safas = safas.app:main'
          ]
      },
    include_package_data=True,

)
