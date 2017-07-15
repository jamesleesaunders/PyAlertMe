from setuptools import setup

setup(
    name='PyAlertMe',
    version='0.2.2',
    description='Python AlertMe',
    url='https://github.com/jamesleesaunders/PyAlertMe',
    author='James Saunders',
    author_email='james@saunders-family.net',
    license='MIT',
    packages=['pyalertme'],
    keywords='_xbee zigbee hive alertme lowes iris',
    zip_safe=False,
    install_requires=['pyserial', '_xbee'],
    test_suite='nose.collector',
    tests_require=['nose']
)

