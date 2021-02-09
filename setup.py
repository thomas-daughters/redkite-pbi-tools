from setuptools import setup, find_packages

setup(
    name='redkite-pbi-tools',
    version='0.0.1',
    packages=find_packages(exclude=['tests*']),
    license='MIT',
    description='Redkite DevOps tools for working with PBI',
    long_description=open('README.md').read(),
    install_requires=['pbi @ git+https://github.com/thomas-daughters/pbi-tools@main'],
    url='https://github.com/thomas-daughters/redkite-pbi-tools',
    author='Sam Thomas',
    author_email='sam.thomas@redkite.com'
)