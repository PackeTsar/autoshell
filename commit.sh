# BASH script for commiting Autoshell code to PyPi

nano autoshell/__version__.py
virtualenv commit_env
source ./commit_env/bin/activate
python setup.py sdist bdist_wheel
python3 setup.py sdist bdist_wheel
twine upload dist/*

deactivate

rm -rf ./autoshell.egg-info
rm -rf build
rm -rf commit_env
rm -rf dist
