#!/usr/bin/env python

## -*-Pyth-*-
 # ###################################################################
 #  FiPy - a finite volume PDE solver in Python
 # 
 #  FILE: "setup.py"
 #                                    created: 4/6/04 {1:24:29 PM} 
 #                                last update: 9/3/04 {10:43:42 PM} 
 #  Author: Jonathan Guyer <guyer@nist.gov>
 #  Author: Daniel Wheeler <daniel.wheeler@nist.gov>
 #  Author: James Warren <jwarren@nist.gov>
 #    mail: NIST
 #     www: http://ctcms.nist.gov
 #  
 # ========================================================================
 # This document was prepared at the National Institute of Standards
 # and Technology by employees of the Federal Government in the course
 # of their official duties.  Pursuant to title 17 Section 105 of the
 # United States Code this document is not subject to copyright
 # protection and is in the public domain.  setup.py
 # is an experimental work.  NIST assumes no responsibility whatsoever
 # for its use by other parties, and makes no guarantees, expressed
 # or implied, about its quality, reliability, or any other characteristic.
 # We would appreciate acknowledgement if the document is used.
 # 
 # This document can be redistributed and/or modified freely
 # provided that any derivative works bear some notice that they are
 # derived from it, and any modified versions bear some notice that
 # they have been modified.
 # ========================================================================
 #  
 # ###################################################################
 ##

import glob
import os
import string

from distutils.core import setup
from distutils.core import Command

class build_docs (Command):

    description = "build the FiPy api documentation"

    # List of option tuples: long name, short name (None if no short
    # name), and help string.
    user_options = [('latex', None, "compile the LaTeX variant of the apis"),
		    ('html', None, "compile the HTML variant of the apis"),
		    ('manual', None, "compile the manual"),
		    ('all', None, "compile both the LaTeX and HTML variants of the apis"),
                    ('webpage', None, "compile the html for the web page")
		   ]


    def initialize_options (self):
	self.latex = 0
	self.html = 0
	self.manual = 0
	self.all = 0
        self.webpage = 0
    # initialize_options()


    def finalize_options (self):
	if self.all:
	    self.latex = 1
	    self.html = 1
	    self.manual = 1
	    self.webpage = 1
            
    # finalize_options()

    def _initializeDirectory(self, dir, type = 'latex'):
	dir = os.path.join(dir, type)
	
	try:
	    for root, dirs, files in os.walk(dir, topdown=False): 
		for name in files: 
		    os.remove(os.path.join(root, name)) 
		for name in dirs: 
		    os.rmdir(os.path.join(root, name)) 
	    os.rmdir(dir)
	except:
	    pass
	    
	os.makedirs(dir)
	
    def _epydocFiles(self, module, dir = None, type = 'latex'):
	dir = os.path.join(dir, type)
	
        command = "epydoc --" + type + " --output " + dir + " --name FiPy " + module
        
	os.system(command)

    def _buildTeXAPIs(self):
	dir = os.path.join('documentation', 'manual', 'api')
	self._initializeDirectory(dir = dir, type = 'latex')
	self._epydocFiles(module = 'fipy/', dir = dir, type = 'latex')
	
        savedir = os.getcwd()
        try:
            
            os.chdir(os.path.join('documentation','manual'))
            f = open('api.tex', 'w')
            f.write("% This file is created automatically by:\n")
            f.write("% 	python setup.py build_doc --latex\n\n")
            for root, dirs, files in os.walk(os.path.join('api','latex'), topdown=True):
                
                if 'api.tex' in files:
                    files.remove('api.tex')
		    
		if 'fipy-module.tex' in files:
		    files.remove('fipy-module.tex')

                
                ## Added because linux does not sort files in the same order
                files.sort()
                
##                 for module in modules[::-1]:
##                     formattedModule = string.replace(module,'/','.') + '-module.tex'
##                     if formattedModule in files:
##                         files.remove(formattedModule)
##                         files.insert(0, formattedModule)

		import re
		mainModule = re.compile(r"(fipy\.[^.-]*)-module\.tex")
		subModule = re.compile(r"(fipy(\.[^.-]*)+)-module\.tex")
                for name in files:
		    mainMatch = mainModule.match(name)
		    if mainMatch:
			f.write("\\chapter{Module " + mainMatch.group(1) + "}\n")
			
		    subMatch = subModule.match(name)
		    if subMatch:
			module = open(os.path.join(root, name))
			
			# epydoc tends to prattle on and on with empty module pages, so 
			# we eliminate all but those that actually contain something relevant.
			functionLine = re.compile(r"\\subsection{(Functions|Variables|Class)")
			keepIt = False
			for line in module:
			    if functionLine.search(line):
				keepIt = True
				break
				
			module.close
			if not keepIt:
			    continue
			
		    split = os.path.splitext(name)
		    if split[1] == ".tex":
			f.write("\\input{" + os.path.join(root, os.path.splitext(name)[0]) + "}\n\\newpage\n")

            f.close()
        except:
            pass
        
        os.chdir(savedir)

    def _LatexWriter(self):
	from docutils.writers.latex2e import LaTeXTranslator, Writer as LaTeXWriter
	from docutils import languages

	class NotStupidLaTeXTranslator(LaTeXTranslator):
	    pass

	class IncludedLaTeXWriter(LaTeXWriter):
	    def write(self, document, destination):
		self.document = document
		self.language = languages.get_language(
		    document.settings.language_code)
		self.destination = destination
		self.translate()
		output = self.destination.write(''.join(self.body))
		return output
		
	    def translate(self):
		visitor = NotStupidLaTeXTranslator(self.document)
		self.document.walkabout(visitor)
		self.output = visitor.astext()
		self.head_prefix = visitor.head_prefix
		self.head = visitor.head
		self.body_prefix = visitor.body_prefix
		self.body = visitor.body
		self.body_suffix = visitor.body_suffix

        return  IncludedLaTeXWriter()

    def _htmlWriter(self):
        from docutils.writers.html4css1 import Writer as htmlWriter
        return htmlWriter()
    
    def _translateTextFiles(self, type = 'latex', source_dir = '.', destination_dir = '.', files = []):
	from docutils import core

        if type == 'html':
            writer = self._htmlWriter()
        elif type == 'latex':
            writer = self._LaTeXWriter()

        for file in files:

            destination_path = os.path.join(destination_dir, string.lower(file) + '.' + type)
            source_path = os.path.join(source_dir, file + '.txt')

            core.publish_file(source_path= source_path,
                              destination_path = destination_path,
                              reader_name = 'standalone',
                              parser_name = 'restructuredtext',
                              writer = writer,
                              settings_overrides = {'use_latex_toc': True,
                                                    'footnote_references': 'superscript'
                                                    })

##    def _translateTextFiles(self):
##	from docutils.writers.latex2e import LaTeXTranslator, Writer as LaTeXWriter
##	from docutils import languages

##	class NotStupidLaTeXTranslator(LaTeXTranslator):
##	    pass

##	class IncludedLaTeXWriter(LaTeXWriter):
##	    def write(self, document, destination):
##		self.document = document
##		self.language = languages.get_language(
##		    document.settings.language_code)
##		self.destination = destination
##		self.translate()
##		output = self.destination.write(''.join(self.body))
##		return output
		
##	    def translate(self):
##		visitor = NotStupidLaTeXTranslator(self.document)
##		self.document.walkabout(visitor)
##		self.output = visitor.astext()
##		self.head_prefix = visitor.head_prefix
##		self.head = visitor.head
##		self.body_prefix = visitor.body_prefix
##		self.body = visitor.body
##		self.body_suffix = visitor.body_suffix

##	from docutils import core

##	core.publish_file(source_path='../../INSTALLATION.txt',
##			  destination_path='installation.tex',
##			  reader_name='standalone',
##			  parser_name='restructuredtext',
##			  writer=IncludedLaTeXWriter(),
##			  settings_overrides = {
##			      'use_latex_toc': True,
##			      'footnote_references': 'superscript'
##			  })

##        core.publish_file(source_path='../../README.txt',
##			  destination_path='readme.tex',
##			  reader_name='standalone',
##			  parser_name='restructuredtext',
##			  writer=IncludedLaTeXWriter(),
##			  settings_overrides = {
##			      'use_latex_toc': True,
##			      'footnote_references': 'superscript'
##			  })


    def run (self):

        restructuredTextFiles = ['INSTALLATION',
                                 'README']
        
	if self.latex:
	    self._buildTeXAPIs()
	    dir = os.path.join('documentation', 'manual', 'examples')
	    self._initializeDirectory(dir = dir, type = 'latex')
	    for module in ['examples/diffusion/',
			   'examples/convection/',
			   'examples/phase/',
			   'examples/levelSet/',
			   'examples/elphf/',
                           'examples/cahnHilliard/'
			   ]:
		self._epydocFiles(module = module, dir = dir, type = 'latex')


	if self.html:
	    dir = os.path.join('documentation', 'manual', 'api')
	    self._initializeDirectory(dir = dir, type = 'html')
	    self._epydocFiles(module = 'fipy/', dir = dir, type = 'html')

	if self.manual:
	    savedir = os.getcwd()
	    
	    try:
		os.chdir(os.path.join('documentation','manual'))
		
		f = open('version.tex', 'w')
		f.write("% This file is created automatically by:\n")
		f.write("% 	python setup.py build_doc --manual\n\n")
		f.write("\\newcommand{\\Version}{" + self.distribution.metadata.get_version() + "}\n")
		f.close()

##		self._translateTextFiles()
                self._translateTextFiles(files = restructuredTextFiles, source_dir = '../..')

		os.system("pdflatex fipy.tex")
		os.system("pdflatex fipy.tex")
	    except:
		pass
	    os.chdir(savedir)

        if self.webpage:
            dir = os.path.join('documentation', 'www')
            self._translateTextFiles(files = restructuredTextFiles, type = 'html', destination_dir = dir)

            headObj = open(os.path.join(dir, 'head.html'))
            tailObj = open(os.path.join(dir, 'tail.html'))

            s0 = headObj.read()
            s2 = tailObj.read()

            for file in restructuredTextFiles:
                file = os.path.join(dir, string.lower(file))
                fileObj = open(file + '.html', 'r')
                s1 = fileObj.read()
                fileObj.close()
                os.remove(file + '.html')
                fileObj = open(string.lower(file) + '.html', 'w')
                fileObj.write(s0 + s1 + s2)
                fileObj.close()

            import shutil

            shutil.move(os.path.join(dir, 'readme.html'), os.path.join(dir, 'index.html'))

                
    # run()

class test(Command):
    description = "test FiPy and its examples"

    # List of option tuples: long name, short name (None if no short
    # name), and help string.
    user_options = [('inline', None, "run FiPy with inline compilation enabled"),
		    ('all', None, "run all FiPy tests (default)"),
		    ('examples', None, "test FiPy examples"),
		    ('modules', None, "test FiPy code modules"),
		    ('terse', None, "give limited output during tests"),
		   ]


    def initialize_options (self):
	self.inline = False
	self.verbosity = 0
	self.terse = False
	self.all = False
	self.doExamples = True
	self.doModules = True
	self.examples = False
	self.modules = False

    def finalize_options (self):
	if self.verbose:
	    self.verbosity = 2
	if self.terse:
	    self.verbosity = 1
	if self.all:
	    self.examples = True
	    self.modules = True
	if self.examples and not self.modules:
	    self.doModules = False
	if self.modules and not self.examples:
	    self.doExamples = False
	
    def run (self):
	import unittest
	theSuite = unittest.TestSuite()
	
	if self.doModules:
	    import fipy.test
	    theSuite.addTest(fipy.test.suite())
	
	if self.doExamples:
	    import examples.test
	    theSuite.addTest(examples.test.suite())
	
	testRunner = unittest.TextTestRunner(verbosity=self.verbosity)
	result = testRunner.run(theSuite)
	
	import sys
	sys.exit(not result.wasSuccessful())

	    
long_description = """
A finite volume PDE solver in Python.

The authors and maintainers of this package are:
    
Daniel Wheeler <daniel.wheeler@nist.gov>
Jonathan Guyer <guyer@nist.gov>
Jim Warren <jwarren@nist.gov>
"""

setup(	name = "FiPy",
	version = "0.1",
	author = "Jonathan Guyer, Daniel Wheeler, & Jim Warren",
	author_email = "guyer@nist.gov",
	url = "http://ctcms.nist.gov",
	description = "A finite volume PDE solver in Python",
	long_description = long_description,
	cmdclass = {
	    'build_docs':build_docs,
	    'test':test
	},
	packages = ['fipy', 
			'fipy.boundaryConditions',
			'fipy.equations',
			'fipy.iterators',
			'fipy.meshes',
			    'fipy.meshes.common',
			    'fipy.meshes.numMesh',
			    'fipy.meshes.pyMesh',
			'fipy.models',
			    'fipy.models.elphf',
			    'fipy.models.levelSet',
				'fipy.models.levelSet.advection',
				'fipy.models.levelSet.distanceFunction',
			    'fipy.models.phase',
				'fipy.models.phase.phase',
				'fipy.models.phase.temperature',
				'fipy.models.phase.theta',
                            'fipy.models.cahnHilliard',
			'fipy.solvers',
			'fipy.terms',
			'fipy.tests',
			'fipy.tools',
			    'fipy.tools.dimensions',
			    'fipy.tools.inline',
			    'fipy.tools.profiler',
			'fipy.variables',
			'fipy.viewers'
	]
)
