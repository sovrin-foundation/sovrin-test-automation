from setuptools import setup, find_packages

install_requires = ['python3-indy==1.6.1', 'aiohttp==3.4.2']

setup(name='minter',
      version="0.1",
      description='Blag blah',
      platforms=['POSIX'],
      packages=find_packages(),
      install_requires=install_requires,
      zip_safe=False)