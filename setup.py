from setuptools import setup, find_packages
from safas import __version__

setup(
    name='safas',
    version=__version__,
    author='Ryan MacIver',
    author_email='rmcmaciver@hotmail.com',
    packages=find_packages(),
    long_description=open('README.md').read(),
)
