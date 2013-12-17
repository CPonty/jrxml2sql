import datetime
import re
from os import linesep
from math import floor, ceil
endl=linesep

HELP_TEXT=True

#"""description
#
#@param arg: description
#@type	arg: type
#
#@returns
#"""

#------------------------------------------------------------------------------
# Utility functions

def has_quotes(s): 
	s=str(s)
	if len(s)==0: return False
	return (s[0]=="'" and s[-1]=="'") or (s[0]=='"' and s[-1]=='"')

def quote(s): 
	s=str(s)
	if not has_quotes(s): return "\'%s\'"%(s)
	return s
	
def rm_quotes(s):
	s=str(s)
	if has_quotes(s): return s[1:-1]
	return s
	
def sql_date2str(d):
	return d.strftime('\'%Y/%m/%d\'')
	
def sql_str2date(s):
	return s.strftime('%Y/%m/%d')
	
#------------------------------------------------------------------------------
# JRXML Parsing helper classes

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
		
	def addp(self, p):
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
		
	def keysByType(self, ptype, ordered=False):
		ls = [p.pname for p in self.vals() if p.ptype==ptype]
		if ordered: ls.sort()
		return ls
		
#------------------------------------------------------------------------------
		
class JrxmlParameterConverter(object):
	def __init__(self, typeMap, valueMap, typeConverters=[], valueConverters=[]):
		self.typeMap=dict(typeMap)
		self.valueMap=dict(valueMap)
		self.typeConverters=list(typeConverters)
		self.valueConverters=list(valueConverters)

	def convertType(self, p):
		# takes in a java-style report parameter, converts its type
		p.ptype=self.typeMap.get(p.ptype,p.ptype)
		for typeConverter in self.typeConverters:
			p.ptype=typeConverter(p)
		return p.ptype

	def convertValue(self, p):
		# takes in a java-style report parameter, converts its value
		p.pvalue=self.valueMap.get(p.pvalue,p.pvalue)
		for valueConverter in self.valueConverters:
			p.pvalue=valueConverter(p)
		return p.pvalue

	def convert(self, pCollection):
		if type(pCollection)!=JrxmlParameterCollection:
			raise TypeError("argument 'pCollection' should be a JrxmlParameterCollection")
		pc=pCollection
		for k in pc.keys():
			pc[k].pvalue=self.convertValue(pc[k])
			pc[k].ptype=self.convertType(pc[k])
		return pc
		
#------------------------------------------------------------------------------

class SqlParameterFormatter(object):

	def __init__(self, func_format_parameter=lambda pname: pname,
				func_format_header=lambda pCollection,label: "",
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

	def header(self, pCollection_params, 
			pCollection_expressions=JrxmlParameterCollection(),
			pCollection_inserts=JrxmlParameterCollection()):
		if type(pCollection_params)!=JrxmlParameterCollection or\
			type(pCollection_expressions)!=JrxmlParameterCollection or\
			type(pCollection_inserts)!=JrxmlParameterCollection:
			raise TypeError("'pCollection' arguments should be a JrxmlParameterCollection")
		header=""
		if pCollection_params.count()>0: 
			header+="----"+self.editorName+" Parameters----\n"
			header+=self.func_format_header(pCollection_params)
		if pCollection_expressions.count()>0: 
			header+="----"+self.editorName+" $X{} Replacements----\n\n"
			if HELP_TEXT:
				header+="--\t$X{IN,_,_} expressions are now true/false placeholders.\n"
				header+="--\tFind-replace them with SQL expressions to add functionality.\n\n"
			header+=self.func_format_header(pCollection_expressions)
		if pCollection_inserts.count()>0: 	
			header+="----"+self.editorName+" $P!{} Replacements----\n\n"
			if HELP_TEXT:
				header+="--\t$P!{ substitutions need replacing in the query.\n"
				header+="--\tFind-replace with actual SQL *before* executing.\n"
				header+="--\tBe careful of java syntax!\n\n"
		for p in pCollection_inserts.vals():
			header+="--$P!{%s} = \"%s\"\n"%(p.pname,p.pvalue)
		return header+'\n'+'- '*32+'\n\n'

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
	#if len(xmlStr)<512: print "XMLCDATA_defaultparam||", xmlStr, "||, [[", value, "]]"
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
		split=tagStr.split(' ')
		split2=[]
		for s in split: split2+=s.split('/>')
		#print "SPLIT", split2
		args=[ss.replace('"','') for ss in split2 \
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
		#if attribute=="class": print "CLASSPARSE[[",tagStr,"]]"
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
			s=jstr[i:i_endtag+1]
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

BIRParameters.add("AS_AT", "java.util.Date", sql_date2str(datetime.date.today()))
BIRParameters.add("EXEC_DATE", "java.util.Date", sql_date2str(datetime.date.today()))
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
# Parameter,Type Converter functions

def valueConverterQuotes(p):
	if type(p)!=JrxmlParameter:
		raise JrxmlParseException("Type converter was passed a non-parameter object")
	#make sure the value is compatible with quotes
	unquotable=[re.search(r'--', p.pvalue), re.search(r'\$P{', p.pvalue),
				re.search(r'\$X{', p.pvalue), re.search(r'java.', p.pvalue),
				re.search(r'==', p.pvalue)]
	if len([i for i in unquotable if i!=None])>0: return p.pvalue
	quotable=['java.lang.String','java.util.Date']
	if p.ptype in quotable: 
		#print p.ptype+" quoted!"
		return quote(p.pvalue)
	else:
		#print p.ptype+" not quotable"
		return p.pvalue

def valueConverterDates(p):
	if type(p)!=JrxmlParameter:
		raise JrxmlParseException("Type converter was passed a non-parameter object")
	today=datetime.date.today()
	#test for the current date
	if 0<=p.pvalue.find('new java.util.Date()')<=2:
		return sql_date2str(today)
	#test for n days ago
	s=p.pvalue.replace(' ','').replace('\n','').replace('\r','').replace('\t','')
	idx1=s.find('newjava.util.Date(')
	idx2=s.find('java.lang.System.currentTimeMillis()')
	idx3=s.find('24*3600*1000')
	m=re.search(r'[0-9]{1,3}',s)
	if not (-1 in [idx1,idx2,idx3] or m==None) and (idx1<idx2<idx3):
		delta_days=-int(s[m.start():m.end()])
		return quote(today+datetime.timedelta(days=delta_days))
	return p.pvalue
	
#------------------------------------------------------------------------------

# Parameter,Type Converter for postgres,sqlserver
# uses map of Java types/values to postgres,sqlserver types/values

typeMapPostgres={} #Dict {"JavaType:  "PostType" }
valueMapPostgres={}#Dict {"JavaValue: "PostValue"}
typeConverterPostgres=[] #list of functions which takes p, returns str
valueConverterPostgres=[] #list of functions which takes p, returns str

typeMapPostgres['java.lang.Boolean']='boolean'
typeMapPostgres['java.lang.Integer']='int'
typeMapPostgres['java.lang.String']='varchar'
typeMapPostgres['java.util.Date']='date'

#TODO
valueConverterPostgres+=[valueConverterQuotes,valueConverterDates]

#TODO
typeConverterPostgres+=[lambda p:
	p.ptype
]

typeMapSqlserver={} #Dict {"JavaType:  "SqlType" }
valueMapSqlserver={}#Dict {"JavaValue: "SqlValue"}
typeConverterSqlserver=[] #list of functions which takes p, returns str
valueConverterSqlserver=[] #list of functions which takes p, returns str

typeMapSqlserver['java.lang.Boolean']='bit'
typeMapSqlserver['java.lang.Integer']='int'
typeMapSqlserver['java.lang.String']='varchar(max)'
typeMapSqlserver['java.util.Date']='datetime'

valueMapSqlserver['false']='0'
valueMapSqlserver['true']='1'

#TODO
valueConverterSqlserver+=[valueConverterQuotes,valueConverterDates]

#TODO
typeConverterSqlserver+=[lambda p:
	p.ptype
]

postgresMap  = JrxmlParameterConverter(typeMapPostgres,valueMapPostgres,
	typeConverterPostgres,valueConverterPostgres)
sqlserverMap = JrxmlParameterConverter(typeMapSqlserver,valueMapSqlserver,
	typeConverterSqlserver,valueConverterSqlserver)

#------------------------------------------------------------------------------
#  Parameter formatter for Postgres,Sqlserver

SORT_PARAMETERS=True

def postgres_parameter(pname):
	return "'$[%s]'"%(pname)

def sqlserver_parameter(pname):
	return "@%s"%(pname)

def workbench_header(pCollection):
	def wbvardef(n,v,t): 
		if len(v)>3 and v[:4] in ('true','false'):
			return "WbVarDef %s=%s;"%(n,v)
		return "WbVarDef %s=CAST(%s AS %s);"%(n,v,t)
		
	header= "\n".join([wbvardef(n,v,t) for n,t,v in \
		pCollection.plist(SORT_PARAMETERS)])
	return header+'\n\n'

def sqlmanagerstudio_header(pCollection):
	header="DECLARE %s;\n\n"%(
		", \n\t".join(["@%s as %s"%(n,t) for n,t,v in \
		pCollection.plist(SORT_PARAMETERS)]))
	header+="\n".join(["SET @%s = %s;"%(n,v) for n,t,v in \
		pCollection.plist(SORT_PARAMETERS)])
	return header+'\n\n'
	#--SQL Management Studio Parameters--

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
	FORMAT_INSERTS=False
	
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
		self.sqlParamNameSet=set([]) #unique parameter names
		self.sqlReplaceNameSet=set([]) #unique $P!{} names
		self.sqlXinList=[] #unique $X{} statements, list pos = id#
		self.rmlist=[] #list of pnames filtered out (jrxml->sql)
		self.jrxmlParams=JrxmlParameterCollection()
		self.sqlParams=JrxmlParameterCollection()
		self.sqlXinParams=JrxmlParameterCollection()
		self.sqlInsertParams=JrxmlParameterCollection()
		
	def rawSql(self):
		return self.sqlStr
		
	def formatAnySql(self, formatStr):
		#replace $P{}
		for pname in self.sqlParamNameSet:
			formatStr=formatStr.replace(
				"$P{%s}"%(pname),
				self.sqlParameterFormatter.parameter_sql(pname))
		#replace $X{}
		for i in xrange(len(self.sqlXinList)):
			xstr=self.sqlXinList[i]
			if self.DEBUG>1: print "rep "+self.sqlXinList[i]
			formatStr=formatStr.replace(
				self.sqlXinList[i],
				self.sqlParameterFormatter.parameter_sql("XIN_"+str(i+1)))
		return formatStr
		
	def formatSql(self):
		#find-replace the main query
		formatStr=self.formatAnySql(self.sqlStr)
		#find-replace each parameter acting as direct SQL injection???
		insertParams=JrxmlParameterCollection()
		insertParams.join(self.sqlInsertParams)
		if self.FORMAT_INSERTS:
			for pname in insertParams.keys():
				insertParams[pname].pvalue=\
					self.formatAnySql(insertParams[pname].pvalue)
		#create header
		header=self.sqlParameterFormatter.header(
			self.sqlParams,self.sqlXinParams, insertParams)
		return header+'--Query--\n'+formatStr
		
	def findSqlParams(self):
		self.sqlParamNameSet=set([])
		self.sqlReplaceNameSet=set([])
		self.sqlXinList=set([])
		self.sqlXinParams=JrxmlParameterCollection()
		self.sqlInsertParams=JrxmlParameterCollection()
		#find $P!{}
		i=0
		match=re.search(r'\$P!{\w+}', self.sqlStr[i:])
		while match!=None:
			s=self.sqlStr[i+match.start()+4:i+match.end()-1]
			if not s in self.sqlReplaceNameSet:
				self.sqlReplaceNameSet.add(s)
				self.sqlInsertParams.add(s, self.jrxmlParams[s].ptype,
					rm_quotes(self.jrxmlParams[s].pvalue))
			if self.DEBUG>1: 
				print i, s, '$P!{}'#, self.sqlStr[i+match.start():i+match.end()]
			i+=match.end()
			match=re.search(r'\$P!{\w+}', self.sqlStr[i:])
		#for the others: search rawSql+contnet of $P!{} inserts
		searchSql=self.sqlStr+'\n'+'\n'.join([p.pvalue for p in \
			self.sqlInsertParams.vals()])
		#find $P{}
		i=0
		match=re.search(r'\$P{\w+}', searchSql[i:])
		while match!=None:
			s=searchSql[i+match.start()+3:i+match.end()-1]
			self.sqlParamNameSet.add(s)
			if self.DEBUG>1: 
				print i, s#, self.sqlStr[i+match.start():i+match.end()]
			i+=match.end()
			match=re.search(r'\$P{\w+}', searchSql[i:])
		#find $X{}
		i=0
		match=re.search(r'\$X\{[^\}]{6,256}\}', searchSql[i:])
		while match!=None:
			s=searchSql[i+match.start():i+match.end()]
			#add a 'fake' parameter for it
			# original statement is attached as a comment
			if s not in self.sqlXinList:
				self.sqlXinList.add(s)
				xin_p=JrxmlParameter("XIN_"+str(len(self.sqlXinList)),
					"java.lang.Boolean", "true")
				xin_p.ptype=self.parameterConverter.convertType(xin_p)
				xin_p.pvalue=self.parameterConverter.convertValue(xin_p)
				xin_p.pvalue=xin_p.pvalue+"; --"+s
				self.sqlXinParams.addp(xin_p)
		
			if self.DEBUG>1: 
				print i, s#, self.sqlStr[i+match.start():i+match.end()]
			i+=match.end()
			match=re.search(r'\$X\{[^\}]{6,256}\}', searchSql[i:])
		self.sqlXinList=list(self.sqlXinList)
		
	def parse(self, jrxmlStr):
		self.jrxmlStr=jrxmlStr
		jstr=jrxmlStr
		
		#get sql string
		self.sqlStr=parseXmlCDATA(jstr,"queryString")
		
		#get jrxml parameters
		self.parameterParser.parse(jstr)
		self.jrxmlParams=self.parameterParser.params()
		self.jrxmlParams=self.parameterConverter.convert(self.jrxmlParams)

		#get sql parameters
		self.findSqlParams()
		
		#filter jrxml parameters for the query content
		self.rmlist=[pname for pname in self.jrxmlParams.keys() \
			if not (pname in self.sqlParamNameSet) \
			or (pname in self.sqlReplaceNameSet)
			or (pname in self.jrxmlParams.keysByType("java.util.Collection"))]
		self.sqlParams=JrxmlParameterCollection()
		self.sqlParams.join(self.jrxmlParams)
		self.sqlParams.filter(self.rmlist)

	def summary(self):
		s = "\n--JRXMLPARAMS (%d)--\n"%(self.jrxmlParams.count())
		s+= str(self.jrxmlParams)+'\n'
		s+= "\n--SQLPARAMS (%d)--\n"%(len(self.sqlParamNameSet))
		s+= str(list(self.sqlParamNameSet))+'\n'
		s+= "\n--REPLACESTRINGS (%d)--\n"%(len(self.sqlReplaceNameSet))
		s+= str(list(self.sqlReplaceNameSet))+'\n'
		unused=set(self.rmlist)
		unused.difference_update(self.sqlReplaceNameSet)
		s+= "\n--UNUSED (%d)--\n"%(len(unused))
		s+= str(list(unused))+'\n'
		collections=self.jrxmlParams.keysByType("java.util.Collection")
		s+= "\n--COLLECTIONS (%d)--\n"%(len(collections))
		s+= str(collections)+'\n'
		s+= "\n--$X{} (%d)--\n"%(len(self.sqlXinList))
		s+= str(self.sqlXinList)+'\n'
		return s
		
postgresEngine=JrxmlSqlParser(
	"postgres", postgresFormat, pParser, postgresMap)
sqlserverEngine=JrxmlSqlParser(
	"sqlserver", sqlserverFormat, pParser, sqlserverMap)

#------------------------------------------------------------------------------
# APPLICATION

#------------------------------------------------------------------------------
# TEST SUITE

jstr = open('cnotebrokeragesummary_jrxml.data', 'r').read()
#jstr = open('MonthToDateTradingStatistics_jrxml.data', 'r').read()

#print BIRParameters
#print postgresMap.convert(BIRParameters)
#print sqlserverMap.convert(BIRParameters)

#print postgresFormat.header(postgresMap.convert(BIRParameters))
#print sqlserverFormat.header(sqlserverMap.convert(BIRParameters))

#pParser.parse(jstr)
#print pParser.params()
#print sqlserverFormat.header(sqlserverMap.convert(pParser.params()))

def dash_header(msg, ln): 
	return "-"*int(floor((ln-len(msg))/2.0))\
	+msg+"-"*int(ceil((ln-len(msg))/2.0))
	
postgresEngine.parse(jstr)
sqlserverEngine.parse(jstr)
print postgresEngine.summary()
print '\n'+dash_header("SQL-RAW",72)+'\n'
print postgresEngine.rawSql()
print '\n'+dash_header("POSTGRES",72)+'\n'
print postgresEngine.formatSql()
print '\n'+dash_header("SQLSERVER",72)+'\n'
print sqlserverEngine.formatSql()

#------------------------------------------------------------------------------

