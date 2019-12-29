from setuptools import setup, find_packages
from safas import __version__
#https://chriswarrick.com/blog/2014/09/15/python-apps-the-right-way-entry_points-and-scripts/
setup(
    name='safas',
    version=__version__,
    author='M. Ryan MacIver',
    author_email='rmcmaciver@hotmail.com',
    url='https://rmaciver.github.io/safas/',
    packages=find_packages(),
    long_description=open('README.md').read(),
    entry_points={
          'console_scripts': [
              'safas = safas.__main__:main'
          ]
      },
    include_package_data=True,

)
