import codecs
import os
import re
from pathlib import Path

from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with codecs.open(os.path.join(here, *parts), "r") as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(
        r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="ppromptor",
    version=find_version("ppromptor", "__init__.py"),
    url="https://github.com/pikho/ppromptor",
    author="Pikho Tan",
    author_email="pikho.tan@gmail.com",
    description="An autonomous agent framework for prompt engineering",
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(exclude=["*_private_llms*"]),
    package_data={"ppromptor": ["examples/*"]},
    scripts=['scripts/ppromptor-cli.py'],
    install_requires=[
        "langchain", "loguru", "dataclasses_json",
        "requests", "openai", "sqlalchemy",
        "beautifulsoup4",
        "streamlit", "streamlit-diff-viewer", "streamlit-autorefresh",
        "streamlit-aggrid"
    ],
    include_package_data=True,
    extras_require={
        'docs': ['sphinx'],
        'test': ['pytest'],
        'local-llms': ["torch", "auto_gptq", "transformers"]
    },
    python_requires=">=3.8",
)
