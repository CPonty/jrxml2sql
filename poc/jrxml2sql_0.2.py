import datetime
import re
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

def quote(s): 
	return "\'%s\'"%(str(s))
	
def has_quotes(s): 
	return (s[0]=="'" and s[-1]=="'") or (s[0]=='"' and s[-1]=='"')

def rm_quotes(s):
	if has_quotes(s): return s[1:-1]
	return s

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
		return "\n".join([k+": "+str(v) for k,v in self.params.iteritems()])
		
	def __getitem__(self, k):
		return self.params[k]
		
	def __setitem__(self, k, value):
		if type(value)!=JrxmlParameter:
			raise TypeError("subscripted item should be a JrxmlParameter")
		self.params[k]=value
		
	def join(self, pCollection):
		if type(pCollection)!=JrxmlParameterCollection:
			raise TypeError("argument 'pCollection' should be a JrxmlParameterCollection")
		self.params=dict(self.params.items() + pCollection.params.items())
		
	def add(self, p):
		if type(p)!=JrxmlParameter:
			raise TypeError("argument 'p' should be a JrxmlParameter")
		self.params[p.pname]=p

	def add(self, pname, ptype, pvalue):
		self.params[pname]=JrxmlParameter(pname, ptype, pvalue)
		
	def rm(self, pname):
		self.params.pop(pname,None)
		
	def filter(self, exclusionList=[]):
		for exclude in exclusionList: self.rm(exclude)
		
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
		
class JrxmlParameterConverter(object):
	def __init__(self, typeMap, valueMap):
		self.typeMap=dict(typeMap)
		self.valueMap=dict(valueMap)

	def convertType(self, ptype):
		return self.typeMap.get(ptype,ptype)

	def convertValue(self, pvalue):
		return self.valueMap.get(pvalue,pvalue)

	def convert(self, pCollection):
		if type(pCollection)!=JrxmlParameterCollection:
			raise TypeError("argument 'pCollection' should be a JrxmlParameterCollection")
		pc=pCollection
		for k in pc.keys():
			pc[k].ptype=self.convertType(pc[k].ptype)
			pc[k].pvalue=self.convertValue(pc[k].pvalue)
		return pc
		
#------------------------------------------------------------------------------

class SqlParameterFormatter(object):

	def __init__(self, func_format_parameter=lambda pname: pname,
				func_format_header=lambda pCollection: "",
				languageName="SQL",
				editorName="unknown"):
		self.func_format_parameter=func_format_parameter
		self.func_format_header=func_format_header
		self.languageName=str(languageName)
		self.editorName=str(editorName)

	def language(self):
		return self.languageName

	def editor(self):
		return self.editorName

	def parameter_sql(self, pname):
		return self.func_format_parameter(str(pname))

	def header(self, pCollection):
		if type(pCollection)!=JrxmlParameterCollection:
			raise TypeError("argument 'pCollection' should be a JrxmlParameterCollection")
		if pCollection.count()==0: 
			return ""
		return self.func_format_header(pCollection)

#------------------------------------------------------------------------------

def parseXmlCDATA(xmlStr, tagname, rmquotes=True):
	pstart=[ss.start() for ss in re.finditer("<%s>"%(tagname),xmlStr)]
	pend=[ss.end() for ss in re.finditer("</%s>"%(tagname),xmlStr)]
	if (len(pstart)>1 or len(pend)>1): 
		raise JrxmlParseException(
			"too many '%s' tags"%(tagname))
	if (len(pstart)<1 != len(pend)<1): 
		raise JrxmlParseException(
			"'%s' tag malformed"%(tagname))
	if (len(pstart)<1 and len(pend)<1): 
		#no value
		return ""
	s=xmlStr[pstart[0]:pend[0]]
	value=""
	try: value= s.split("![CDATA[")[1].split("]]>")[0]
	except: raise JrxmlParseException(
			"Error parsing parameter CDATA: not found or bad format")
	if rmquotes: value=rm_quotes(value)
	return value

#------------------------------------------------------------------------------

class JrxmlParameterParser(object):
	DEBUG=0 #0..9

	def __init__(self, exclusionList=[]):
		self.exclusionList=list(exclusionList)
		self.jrxmlStr=""
		self.pCollection=JrxmlParameterCollection()

	def params(self):
		return self.pCollection

	def parseTag(self, tagStr, attribute):
		args=[ss.replace('"','') for ss in tagStr.split(' ') \
			if ss.find("%s="%(attribute))==0]
		if (len(args)>1): 
			raise JrxmlParseException(
				"Invalid <parameter>: too many '%s' attributes"%(attribute))
		if (len(args)<1): 
			raise JrxmlParseException(
				"Invalid <parameter>: '%s' attribute not found"%(attribute))
		value=args[0][len("%s="%(attribute)):]
		if len(value)==0:
			raise JrxmlParseException(
				"<parameter> %s parse failed"%(attribute))
		return value

	def parse(self, jrxmlStr):
		self.pCollection=JrxmlParameterCollection()
		self.jrxmlStr=str(jrxmlStr)
		jstr=jrxmlStr

		if self.DEBUG>0: print "<START PARAMETER PARSE>"
		# find each occurence of <parameter
		for i in [ss.start() for ss in re.finditer("<parameter name=",jstr)]:
			i_endtag =jstr.find('>',i)
			i_endtag2=jstr.find('</parameter>',i)
			if self.DEBUG>2: print i, jstr[i:i_endtag+1]
			#get name, type
			s=jstr[i:i_endtag]
			pname=self.parseTag(s,"name")
			ptype=self.parseTag(s,"class")
			#get value: depends on xml tag format
			if jstr[i_endtag-1]=='/':
				# the xml tag style is <tag/>, no default value
				pvalue=""
			else:
				# the xml tag style is <tag></tag>
				s2=jstr[i_endtag:i_endtag2]
				pvalue=""
				pvalue=parseXmlCDATA(s2,"defaultValueExpression")

			#add parameter to collection
			self.pCollection.add(pname,ptype,pvalue)

		#filter out bad parameters
		self.pCollection.filter(self.exclusionList)

		if self.DEBUG>0: print "<END PARAMETER PARSE>"
		if self.DEBUG>1: print '\n', self.pCollection

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
#  Parameter formatter for Postgres,Sqlserver

SORT_PARAMETERS=False

def postgres_parameter(pname):
	return "'$[%s]'"%(pname)

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
# parameter parser, with a list of excluded parameter names
ExcludedParameters=[]

ExcludedParameters.append("LoggedInUser")
ExcludedParameters.append("LoggedInUserRoles")
ExcludedParameters.append("LoggedInUserFrontOfficeId")
ExcludedParameters.append("AccessibleSharesAdvisorCodes")
ExcludedParameters.append("AccessibleSharesAdvisorIds")
ExcludedParameters.append("AccessibleSharesBranchIds")
ExcludedParameters.append("AccessibleOrganisationCodes")

pParser=JrxmlParameterParser(ExcludedParameters)

#------------------------------------------------------------------------------

class JrxmlSqlParser(object):
	DEBUG=0
	
	def __init__(self, name, sqlParameterFormatter, parameterParser, 
		parameterConverter):
		if type(name)!=str:
			raise TypeError("argument 'name' should be a str")
		if type(sqlParameterFormatter)!=SqlParameterFormatter:
			raise TypeError("argument 'sqlParameterFormatter' should be a SqlParameterFormatter")
		if type(parameterParser)!=JrxmlParameterParser:
			raise TypeError("argument 'parameterParser' should be a JrxmlParameterParser")
		if type(parameterConverter)!=JrxmlParameterConverter:
			raise TypeError("argument 'parameterConverter' should be a JrxmlParameterConverter")
		self.name=str(name)
		self.sqlParameterFormatter=sqlParameterFormatter
		self.parameterParser=parameterParser
		self.parameterConverter=parameterConverter
		
		self.jrxmlStr=""
		self.sqlStr=""
		self.sqlParamPosList=[] #list of (start,end) positions
		self.sqlParamNameSet=set([]) #unique parameter names
		self.jrxmlParams=JrxmlParameterCollection()
		self.sqlParams=JrxmlParameterCollection()
		
	def rawSql(self):
		return self.sqlStr
		
	def formatSql(self):
		formatStr=self.sqlParameterFormatter.header(self.sqlParams)
		i=0
		for (start,end) in self.sqlParamPosList:
			formatStr+=self.sqlStr[i:start]
			formatStr+=self.sqlParameterFormatter.parameter_sql(
				self.sqlStr[start+3:end-1])
			i=end
		formatStr+=self.sqlStr[i:]
		return formatStr
		
	def findSqlParams(self):
		self.sqlParamNameSet=set([])
		self.sqlParamPosList=[]
		i=0
		match=re.search(r'\$P{\w+}', self.sqlStr[i:])
		while match!=None:
			s=self.sqlStr[i+match.start()+3:i+match.end()-1]
			self.sqlParamNameSet.add(s)
			self.sqlParamPosList.append((i+match.start(),i+match.end()))
			if self.DEBUG>1: 
				print i, s#, self.sqlStr[i+match.start():i+match.end()]
			i+=match.end()
			match=re.search(r'\$P{\w+}', self.sqlStr[i:])
		
	def parse(self, jrxmlStr):
		self.jrxmlStr=jrxmlStr
		jstr=jrxmlStr
		
		#get sql string
		self.sqlStr=parseXmlCDATA(jstr,"queryString")
		
		#get jrxml parameters
		self.parameterParser.parse(jstr)
		self.jrxmlParams=self.parameterParser.params()
		self.jrxmlParams=self.parameterConverter.convert(self.jrxmlParams)
		if self.DEBUG>0:
			print "\n--JRXMLPARAMS (%d)--\n"%(self.jrxmlParams.count()), self.jrxmlParams
		
		#get sql parameters
		self.findSqlParams()
		
		#filter jrxml parameters by sql parameters
		rmlist=[pname for pname in self.jrxmlParams.keys() \
			if not pname in self.sqlParamNameSet]
		self.sqlParams=JrxmlParameterCollection()
		self.sqlParams.join(self.jrxmlParams)
		self.sqlParams.filter(rmlist)
		
		#special cases
		#TODO
		#TODO
		#TODO
		
		if self.DEBUG>0:
			print "\n--SQLPARAMS (%d)--\n"%(self.sqlParams.count()), self.sqlParams
			print "\n--EXCLUSIONS (%d)--\n"%(len(rmlist)), rmlist
		
postgresEngine=JrxmlSqlParser(
	"postgres", postgresFormat, pParser, postgresMap)
sqlserverEngine=JrxmlSqlParser(
	"sqlserver", sqlserverFormat, pParser, sqlserverMap)

#------------------------------------------------------------------------------
# APPLICATION

#------------------------------------------------------------------------------
# TEST SUITE

jstr = open('cnotebrokeragesummary_jrxml.data', 'r').read()

#print BIRParameters
#print postgresMap.convert(BIRParameters)
#print sqlserverMap.convert(BIRParameters)

#print postgresFormat.header(postgresMap.convert(BIRParameters))
#print sqlserverFormat.header(sqlserverMap.convert(BIRParameters))

#pParser.parse(jstr)
#print pParser.params()
#print sqlserverFormat.header(sqlserverMap.convert(pParser.params()))

postgresEngine.parse(jstr)
print postgresEngine.formatSql()
#print postgresEngine.rawSql()

#------------------------------------------------------------------------------

"""

	- special parameter value cases
		--handle in a passed-in converter fn in JrxmlParameterConverter

TODO
	- gather data from reports (default parameters)
		--validate at work
	- implement a way to distinguish between collection/single
		e.g. store as single, override to collection depending on report
	- implement a way to handle string encapsulation in queries
		i.e. sql needs quotes on certain fields
			--add a quote map of javaType:needsQuotes
	- implement a way to exclude unwanted parameters
		e.g. AccessibleOrganisationCodes
	- implement a special case for $P! type (direct string insert)
	- implement a special case for the 3-days-ago parameter default
		--handle in passed-in converter fn in JrxmlParameterConverter
	- make sure date formatting is correct (for my defaul values)
		i.e. test out sql headers
	X- implement the ParameterParser
		Xuses an excluded parameter list; recognises <p></p> or <p/>
	- implement a way to remove $X statements
		e.g. make them all boolean vars, set to true
	- implement existing interfaces
"""