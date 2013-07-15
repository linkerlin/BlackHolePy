from distutils.core import setup
from setuptools import find_packages

URL = "https://github.com/linkerlin/BlackHolePy"

setup(
    name='BlackHolePy',
    version='1.0',
    packages=find_packages(exclude=["tests.*", "tests"]),
    py_modules=['dnsproxy','servers','config','caches','bg_worker','__init__','dnsserver'],
    license='MIT',
    author='linkerlin',
    author_email='linker.lin@me.com',
    url=URL,
    description='A DNS proxy which using tcp as transport protocol.'
                'It also has a cache which can speed up the process of dns queries.',
    long_description=file("README.md").readlines(),
)
