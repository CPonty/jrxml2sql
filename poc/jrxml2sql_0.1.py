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

def quote(s): return "\'%s\'"%(str(s))

class JrxmlParseException(Exception): pass

class JrxmlParameter(object):

	def __init__(self, pname, ptype, pvalue):
		self.pname=str(pname)
		self.ptype=str(ptype)
		self.pvalue=str(pvalue)
		
	def __str__(self):
		return str((self.pname, self.ptype, self.pvalue))

class JrxmlParameterCollection(object):
	
	def __init__(self):
		self.params={} #Dict {"name": JrxmlParameter}
		
	def __str__(self):
		return "\n".join([k+":"+str(v) for k,v in self.params.iteritems()])
		
	def __getitem__(self, k):
		return self.params[k]
		
	def __setitem__(self, k, value):
		if type(value)!=JrxmlParameter:
			raise TypeError("subscripted item should be a JrxmlParameter")
		self.params[k]=value
		
	def join(self, pCollection):
		if type(p)!=JrxmlParameterCollection:
			raise TypeError("argument 'pCollection' should be a JrxmlParameterCollection")
		self.params=dict(self.params.items() + pCollection.items())
		
	def add(self, p):
		if type(p)!=JrxmlParameter:
			raise TypeError("argument 'p' should be a JrxmlParameter")
		self.params[p.pname]=p
		
	def add(self, pname, ptype, pvalue):
		self.params[pname]=JrxmlParameter(pname, ptype, pvalue)
		
	def has(self, pname):
		return (pname in self.params)
		
	def count(self):
		return len(self.params)
		
	def keys(self):
		return self.params.keys()
		
	def vals(self):
		return self.params.values()
		
	def plist(self, ordered=False):
		ls = [(p.pname,p.ptype,p.pvalue) for p in self.vals()]
		if ordered: ls.sort()
		return ls

#------------------------------------------------------------------------------
# collection of BIR parameters and their default type/value

BIRParameters=JrxmlParameterCollection()

BIRParameters.add("AS_AT", "java.util.Date", quote(datetime.date.today()))
BIRParameters.add("EXEC_DATE", "java.util.Date", quote(datetime.date.today()))
BIRParameters.add("YEAR", "java.lang.Integer", quote(datetime.date.today().year))

BIRParameters.add("ORG_CODE", "java.lang.String", quote("ALL"))
#BIRParameters.add("BRANCH_ID", "java.lang.String", "")
BIRParameters.add("BRANCH_CODE", "java.lang.String", quote("ALL"))
#BIRParameters.add("ADV_ID", "java.lang.String", "")
BIRParameters.add("ADV_CODE", "java.lang.String", quote("ALL"))

BIRParameters.add("MARKET", "java.lang.String", quote("ASX"))
BIRParameters.add("CURRENCY", "java.lang.String", quote("AUD"))
BIRParameters.add("DETAIL", "java.lang.Integer", "0")
BIRParameters.add("FIX", "java.lang.Boolean", "false")

BIRParameters.add("START_SEC", "java.lang.String", quote("A"))
BIRParameters.add("END_SEC", "java.lang.String", quote("ZZZZZZ"))

#BIRParameters.add("", "", )
#BIRParameters.add("", "", )
#BIRParameters.add("", "", )
#BIRParameters.add("", "", )

#------------------------------------------------------------------------------
# list of excluded parameter names
ExcludedParameters=[]

ExcludedParameters.append("LoggedInUserRoles")
ExcludedParameters.append("LoggedInUserRoles")
ExcludedParameters.append("LoggedInUserFrontOfficeId")
ExcludedParameters.append("AccessibleSharesAdvisorCodes")
ExcludedParameters.append("AccessibleSharesAdvisorIds")
ExcludedParameters.append("AccessibleSharesBranchIds")
ExcludedParameters.append("AccessibleOrgainsationCodes")

#------------------------------------------------------------------------------
class JrxmlParameterConverter(object):
	def __init__(self, typeMap, valueMap):
		self.typeMap=typeMap
		self.valueMap=valueMap
	
	def convertType(self, ptype):
		return self.typeMap.get(ptype,ptype)
	
	def convertValue(self, pvalue):
		return self.valueMap.get(pvalue,pvalue)
		
	def convertCollection(self, pCollection):
		if type(pCollection)!=JrxmlParameterCollection:
			raise TypeError("argument 'pCollection' should be a JrxmlParameterCollection")
		pc=pCollection
		for k in pc.keys():
			pc[k].ptype=self.convertType(pc[k].ptype)
			pc[k].pvalue=self.convertValue(pc[k].pvalue)
		return pc
		
#------------------------------------------------------------------------------

# Parameter Converter for postgres,sqlserver
# uses map of Java types/values to postgres,sqlserver types/values

typeMapPostgres={} #Dict {"JavaType:  "PostType" }
valueMapPostgres={}#Dict {"JavaValue: "PostValue"}

typeMapPostgres['java.lang.Boolean']='boolean'
typeMapPostgres['java.lang.Integer']='int'
typeMapPostgres['java.lang.String']='varchar'
typeMapPostgres['java.util.Date']='date'

typeMapSqlserver={} #Dict {"JavaType:  "SqlType" }
valueMapSqlserver={}#Dict {"JavaValue: "SqlValue"}

typeMapSqlserver['java.lang.Boolean']='bit'
typeMapSqlserver['java.lang.Integer']='int'
typeMapSqlserver['java.lang.String']='nvarchar(max)'
typeMapSqlserver['java.util.Date']='datetime'

valueMapSqlserver['false']='0'
valueMapSqlserver['true']='1'

postgresMap  = JrxmlParameterConverter(typeMapPostgres,valueMapPostgres)
sqlserverMap = JrxmlParameterConverter(typeMapSqlserver,valueMapSqlserver)

#------------------------------------------------------------------------------

class SqlParameterFormatter(object):

	def __init__(self, func_format_parameter=lambda pname: pname,
				func_format_header=lambda pCollection: "",
				func_convert_parameter=lambda pCollection: pCollection,
				languageName="SQL",
				editorName="unknown"):
		self.func_format_parameter=func_format_parameter
		self.func_format_header=func_format_header
		self.func_convert_parameter=func_convert_parameter
		self.languageName=languageName
		self.editorName=editorName

	def language(self):
		return self.languageName

	def editor(self):
		return self.editorName

	def parameter_sql(self, pname):
		return self.func_format_parameter(pname)
		
	def parameter_convert(self, pCollection):
		return self.funct_convert_parameter(pCollection)

	def header(self, pCollection):
		if type(pCollection)!=JrxmlParameterCollection:
			raise TypeError("argument 'pCollection' should be a JrxmlParameterCollection")
		if pCollection.count()==0: 
			return ""
		return self.func_format_header(pCollection)

#------------------------------------------------------------------------------
#  Parameter formatter for Postgres,Sqlserver

SORT_PARAMETERS=False

def postgres_parameter(pname):
	return "'%[%s]'"%(pname.lower())

def sqlserver_parameter(pname):
	return "@%s"%(pname.lower())

def workbench_header(pCollection):
	header= "\n".join(["WbVarDef %s=CAST(%s AS %s)"%(n,v,t) for n,t,v in \
		pCollection.plist(SORT_PARAMETERS)])
	return '--SQL Workbench Parameters--\n'+header+'\n\n'

def sqlmanagerstudio_header(pCollection):
	header="DECLARE %s;\n\n"%(
		", \n\t".join(["@%s as %s"%(n,t) for n,t,v in \
		pCollection.plist(SORT_PARAMETERS)]))
	header+="\n".join(["SET @%s = %s;"%(n,v) for n,t,v in \
		pCollection.plist(SORT_PARAMETERS)])
	return '--SQL Management Studio Parameters--\n'+header+'\n\n'

postgresFormat=SqlParameterFormatter(
	postgres_parameter, workbench_header, 
	"Postgresql", "SQL Workbench"
)

sqlserverFormat=SqlParameterFormatter(
	sqlserver_parameter, sqlmanagerstudio_header, 
	"SQLServer", "SQL Management Studio"
)

#------------------------------------------------------------------------------

class ParameterParser(object):
	#TODO
	pass

#------------------------------------------------------------------------------

class JrxmlParser(object):
	#TODO
	pass

#------------------------------------------------------------------------------
# APPLICATION

#------------------------------------------------------------------------------
# TEST SUITE

#print BIRParameters
#print postgresMap.convertCollection(BIRParameters)
#print sqlserverMap.convertCollection(BIRParameters)
print postgresFormat.header(postgresMap.convertCollection(BIRParameters))
print sqlserverFormat.header(sqlserverMap.convertCollection(BIRParameters))
#print postgres.header( {"AS_AT": BIRParameters["AS_AT"]})
#print sqlserver.header({"AS_AT": BIRParameters["AS_AT"]})

#------------------------------------------------------------------------------

"""
TODO
	- gather data from reports (default parameters)
		--validate at work
	- implement a way to distinguish between collection/single
		e.g. store as single, override to collection depending on report
	- implement a way to handle string encapsulation in queries
		i.e. sql needs quotes on string fields
	- implement a way to exclude unwanted parameters
		e.g. AccessibleOrganisationCodes
	- make sure date formatting is correct (for my defaul values)
	- implement existing interfaces
	- implement a way to remove $X statements
		e.g. make them all boolean vars, set to true
"""