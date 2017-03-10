from setuptools import setup

setup(name='PyAlertMe',
      version='0.1.3',
      description='Python AlertMe',
      url='https://github.com/jamesleesaunders/PyAlertMe',
      author='James Saunders',
      author_email='james@saunders-family.net',
      license='MIT',
      packages=['pyalertme'],
      zip_safe=False,
      install_requires=['pyserial', 'xbee'],
      test_suite='nose.collector',
      tests_require=['nose']
)