import datetime
from os import linesep
endl=linesep

#"""description
#
#@param arg: description
#@type	arg: type
#
#@returns
#"""

#------------------------------------------------------------------------------
# JRXML Parsing helper classes

class JrxmlParseException(Exception): pass

class JrxmlParameter:

	def __init__(self, pname, ptype, pvalue):
		self.pname=str(pname).upper()
		self.ptype=str(ptype)
		self.pvalue=str(pvalue)
		
	def __str__(self):
		return str((self.pname, self.ptype, self.pvalue))

class JrxmlParameterCollection:
	
	def __init__(self):
		self.params={} #Dict {"name": JrxmlParameter}
		
	def __str__(self):
		return ",\n".join([k+":"+str(v) for k,v in self.params.iteritems()])
		
	def __getitem__(self, k):
		return self.params[k]
		
	def __setitem__(self, k, value):
		self.params[k]=value
		
	def add(self, p):
		if type(p)!=JrxmlParameter:
			raise TypeError("argument 'p' of 'add' should be a JrxmlParameter")
		self.params[p.pname]=p
		
	def add(self, pname, ptype, pvalue):
		self.params[pname]=JrxmlParameter(pname, ptype, pvalue)
		
	def has(self, pname):
		return (pname in self.params)

#------------------------------------------------------------------------------
# dictionary of BIR parameters and their default type/value

BIRParameters=JrxmlParameterCollection()

BIRParameters.add("AS_AT", "java.util.Date", datetime.date.today())
BIRParameters.add("EXEC_DATE", "java.util.Date", datetime.date.today())
BIRParameters.add("ORG_CODE", "java.lang.String", "TP4064")
#BIRParameters.add("BRANCH_ID", "java.lang.String", "")
BIRParameters.add("ADV_CODE", "java.lang.String", "01")
#BIRParameters.add("", "", )
#BIRParameters.add("", "", )
#BIRParameters.add("", "", )
#BIRParameters.add("", "", )

#------------------------------------------------------------------------------
# map of Java types to postgres datatypes

typeMapPostgres={} #Dict {"JavaType: "PostType"}

#TODO

def type2postgres(t): return typeMapPostgres.get(t,t)

#------------------------------------------------------------------------------
# map of Java types to sqlserver datatypes

typeMapSqlserver={} #Dict {"JavaType: "SqlType"}

#TODO

def type2sqlserver(t): return typeMapSqlserver.get(t,t)

#------------------------------------------------------------------------------
"""
class SqlParameterFormatter:

	def __init__(self):
		raise NotImplementedError("SqlParser is an abstract class"
		", don't instantiate!")

	def editor_name(self):
		raise NotImplementedError("editor_name behaviour not defined")

	def format_parameter(self, pname):
		raise NotImplementedError("format_parameter behaviour not defined")

	def format_header(self, parameters):
		raise NotImplementedError("format_header behaviour not defined")


class PostgresSqlParameters(SqlParameters):
	editorName="SQL Workbench"

	def __init__(self): pass

	def editor_name(self): return self.editorName

	def format_parameter(self, pname): return "'%[%s]'"%(pname.lower())

	def format_header(self, parameters):
		if len(parameters)==0: return ""
		#TODO

class SqlserverSqlParameters(SqlParameters):
	editorName="Microsoft SQL Management Studio"

	def __init__(self): pass

	def editor_name(self): return self.editorName

	def format_parameter(self, pname): return "@%s"%(pname.lower())

	def format_header(self, parameters):
		if len(parameters)==0: return ""
		#TODO
"""
#------------------------------------------------------------------------------

class SqlParameterFormatter:

	def __init__(self, func_format_parameter=lambda pname: pname,
				 func_format_header=lambda parameters: "",
				 languageName="SQL",
				 editorName="unknown"):
		self.func_format_parameter=func_format_parameter
		self.func_format_header=func_format_header
		self.languageName=languageName
		self.editorName=editorName

	def language(self):
		return self.languageName

	def editor(self):
		return self.editorName

	def parameter(self, pname):
		return self.func_format_parameter(pname)

	def header(self, parameters):
		return self.func_format_header(parameters)

#------------------------------------------------------------------------------

def postgres_parameter(pname):
	return "'%[%s]'"%(pname.lower())

def sqlserver_parameter(pname):
	return "@%s"%(pname.lower())

def workbench_header(parameters):
	#TODO
	pass

def sqlmanagerstudio_header(parameters):
	#TODO
	pass

postgres=SqlParameterFormatter(
	postgres_parameter, workbench_header, 
	"Postgresql", "SQL Workbench"
)

sqlserver=SqlParameterFormatter(
	sqlserver_parameter, sqlmanagerstudio_header, 
	"SQLServer", "SQL Management Studio"
)

#------------------------------------------------------------------------------

#TEST
print BIRParameters
#print postgres.header( {"AS_AT": BIRParameters["AS_AT"]})
#print sqlserver.header({"AS_AT": BIRParameters["AS_AT"]})

#------------------------------------------------------------------------------

class ParameterParser:
	#TODO
	pass

#------------------------------------------------------------------------------

class JrxmlParser:
	#TODO
	pass

#------------------------------------------------------------------------------
# APPLICATION

#------------------------------------------------------------------------------

"""
TODO
	- gather data from reports (default parameters)
		--validate at work
	- implement a way to distinguish between collection/single
		e.g. store as single, override to collection depending on report
	- implement a way to handle string encapsulation in queries
	- implement existing interfaces
	- implement a way to remove $X statements
		e.g. make them all boolean vars, set to true
"""