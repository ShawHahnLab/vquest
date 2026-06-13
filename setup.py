import setuptools
import vquest

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="vquest",
    version=vquest.__version__,
    author="Jesse Connell",
    author_email="jesse@ressy.us",
    description="Automate IMGT V-QUEST usage on imgt.org",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/shawhahnlab/vquest",
    packages=setuptools.find_packages(),
    package_data={"vquest": ["data/*"]},
    entry_points={"console_scripts": [
        "vquest = vquest.__main__:main"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
    ],
    # (requests-html requires a module from lxml that is now packaged
    # separately, as lxml-html-clean, but evidently requests-html doesn't yet
    # list that other package as a requirement)
    install_requires=["biopython", "PyYAML", "requests", "requests-html", "lxml-html-clean"],
    python_requires='>=3.6',
)
