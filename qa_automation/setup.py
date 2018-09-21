from setuptools import setup, find_packages

install_requires = ['python3-indy==1.6.5']
tests_require = ['pytest', 'python3-indy==1.6.5']
setup(
        name='qa_automation',
        version="0.0.1",
        description='qa automation tools for the sovrin foundation',
        packages=find_packages(),
        install_requires=install_requires,
        setup_requires=['pytest-runner'],
        tests_require=tests_require,
        zip_safe=False
)
