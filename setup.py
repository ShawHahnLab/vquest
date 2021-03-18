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
    url="https://github.com/ressy/vquest",
    packages=setuptools.find_packages(),
    package_data={"vquest": ["data/*"]},
    entry_points={"console_scripts": [
        "vquest = vquest.__main__:main"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
    ],
    install_requires=["biopython", "PyYAML", "requests", "requests-html"],
    python_requires='>=3.6',
)
