from setuptools import setup,find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="MLOPS-PROJECT-2nd",
    version="0.1",
    author="Bilal",
    packages=find_packages(),
    install_requires = requirements,
)