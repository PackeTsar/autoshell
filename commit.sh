# BASH script for commiting Autoshell code to PyPi

nano autoshell/__version__.py
python3 -m venv commit_env
source ./commit_env/bin/activate
python2 setup.py sdist bdist_wheel
python3 -m pip install wheel
python3 -m pip install twine
python3 setup.py sdist bdist_wheel
twine upload dist/*

deactivate

rm -rf ./autoshell.egg-info
rm -rf build
rm -rf commit_env
rm -rf dist
find . -name "*.pyc" -type f -delete
find . -name "*.log" -type f -delete
