from setuptools import setup

setup(name='dlink2750u',
      version='0.1',
      description='A library to communicate with DLink2750U model routers',
      url='https://github.com/5j9/dlink2750u',
      author='5j9',
      author_email='5j9@users.noreply.github.com',
      license='GPLv3',
      packages=['dlink2750u'],
      install_requires=['requests', 'beautifulsoup4'],
      python_requires='>=3.6',
      zip_safe=True)
