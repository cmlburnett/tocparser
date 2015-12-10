from distutils.core import setup

majv = 1
minv = 0

setup(
	name = 'tocparser',
	version = "%d.%d" %(majv,minv),
	description = "Python module to parse TOC files from CDs",
	author = "Colin ML Burnett",
	author_email = "cmlburnett@gmail.com",
	url = "",
	packages = ['tocparser'],
	package_data = {'tocparser': ['tocparser/__init__.py', 'tocparser/lex.py']},
	classifiers = [
		'Programming Language :: Python :: 3.4'
	]
)
