#!/usr/bin/env python

from setuptools import setup
import os


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


extras = {
    "standard": ["pandas", "rtree", "pyyaml", "snakemake"],
    "dev": ["pytest", "black==20.8b1", "coverage", "flake8", "geopandas"],
}

extras["full"] = list(set(extras["standard"] + extras["dev"]))


setup(
    name="oemof-B3",
    version="0.0.0",
    description="",
    long_description=read("README.md"),
    packages=["oemof_b3"],
    install_requires=[
        "oemoflex @ git+https://git@github.com/rl-institut/oemoflex@dev#egg=oemoflex",
    ],
    extras_require=extras,
)
