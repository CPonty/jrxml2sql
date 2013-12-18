#! /usr/bin/env python

# query2workbench.py
# Source for the Jasper Query to SQL Workbench converter tool
#
# Written by Chris Ponticello (2013) under the GPL v2 License
#  christopher.ponticello@uqconnect.edu.au

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import re
import os
import sys
from math import floor, ceil
argc = len(sys.argv)

#------------------------------------------------------------------------------
# Constants, Configuration, Setup
#------------------------------------------------------------------------------

CFG_DEBUG = False           # True or False
CFG_SHOW_CONSOLE = True     # True or False
CFG_LOG = True              # True or False

CFG_SPLASHTEXT = """
*** JasperReport Query to SQL Workbench converter ***
"""

CFG_EXITTEXT = """
Press enter key to exit"""

UNIT_TEST = False

f_log = None
f_jasper = None
f_workbench = None
q_jasper = ''
q_workbench = '--No SQL (blank jasper query file)'

# lazy config file load. Override defaults above
try: from settings import * 
except Exception as e: print2("[WARN] Failed to load settings.py - using defaults")

# start log file
try: f_log = open('convert.log', 'w')
except IOError:	print2("[WARN] Failed to open convert.log")

#------------------------------------------------------------------------------
# Basic utility functions
#------------------------------------------------------------------------------

def print2(s):
	"""Print to console and/or logfile, depending on settings."""
	if CFG_SHOW_CONSOLE: 
		print s
	if (CFG_LOG and f_log):
		f_log.write(s+'\n')
	
def exit2():
	"""Print message & close logfile before exiting."""
	print2("""[EXIT]""")
	if f_log: f_log.close()
	sys.exit()

#------------------------------------------------------------------------------
# Helper classes
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# Main classes
#------------------------------------------------------------------------------

class QueryToWorkbench(object):
	jasper = ''
	
	def __init__(self, jasper):
		self.jasper = str(jasper)
		
	def convert(self):
		return str(self.jasper)

#------------------------------------------------------------------------------
# Test suite
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# Application
#------------------------------------------------------------------------------

print2(CFG_SPLASHTEXT)

# Read query
print2("""[INFO] Reading jasper.sql""")
if not(os.path.isfile('jasper.sql')):
	try:
		# create jasper.sql
		f_jasper = open('jasper.sql', 'w')
		f_jasper.close()
	except IOError:
		# Couldn't create file
		print2("[WARN] Cannot re-create missing jasper.sql (is the file locked?)")
		exit2()
try:
	# Read jasper.sql
	f_jasper = open('jasper.sql', 'r')
	q_jasper = f_jasper.read()
	f_jasper.close()
except IOError:
	# Couldn't read file
	print2("[WARN] Cannot read jasper.sql (is the file locked?)")
	exit2()

# Convert query
print2("""[INFO] Converting to Workbench format...""")
if len(q_jasper.strip())>0:
	converter = QueryToWorkbench(q_jasper)
	q_workbench = converter.convert()
	print2("""[INFO] Conversion Complete.""")
else:
	print2("""[INFO] Query is blank.""")

# Write result (create workbench.sql if missing)
print2("""[INFO] Writing workbench.sql""")
try:
	f_workbench = open('workbench.sql', 'w')
	f_workbench.write(q_workbench)
	f_workbench.close()
except IOError:
	# Couldn't write to file
	print2("[WARN] Cannot write workbench.sql (is the file locked?)")
	exit2()

# Press enter to exit (console mode only)
print2(CFG_EXITTEXT)
if CFG_SHOW_CONSOLE:
	try: input()
	except: pass
exit2()

#------------------------------------------------------------------------------

"""NOTES

 - 
"""