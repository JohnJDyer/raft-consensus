from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

__version__ = "0.0.2"

requirements = [req.strip() for req in open('requirements.txt').readlines()]

setup(
    name="raft-consensus",
    version=__version__,
    author="Dyer, John",
    author_email="johnjohn2718@gmail.com",
    description="Raft Consensus",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JohnJDyer/raft",
    keywords=['python', 'raft', 'consensus', 'replication', 'raft-consensus'],
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 2 - Pre-Alpha",
        "Topic :: System :: Distributed Computing"
    ],
    python_requires='>=3.7',
)
