b:
	python3 setup.py bdist_wheel sdist
i:
	pip3 install .
tcheck:
	twine check dist/*