"""
	X- use find-replace in formatSql
	
	X- fix parameter class xml split - keeping the trailing "/>"
	
	- special parameter value cases
		--use passed-in converter fns in JrxmlParameterConverter
		--run value converter FIRST
	 	-- valueConverters (run in order)
			--add a default value grabber from the BIR list
				> if none available, use --NEEDS VALUE--
			X--add a replacer for today-3 in java
				X> yyyy/mm/dd works on both (post/sql)
			X--add a replacer for today's date in java
				X> yyyy/mm/dd works on both (post/sql)
			X--add a quote map of javaType:needsQuotes
				X> ignore if comment, $P/X{, java., == detected
			--precede ==,'new ',?: with --NEEDS VALUE--
		-- typeConverters
			--
			
	- don't just parse $P!{} for extra parameters. 
			- parse every parameter
			- do find-replace of param names inside all p.pvalues
			- make sure they get added to the sql params list
			
	N- add another case, like $P!, to ignore collection-typed parameters
		N- don't need to, they won't be in sql $P{} statements :)
	
	N- rename headers to "<env> <format> replacements"
	
	X- completely change how $P!{} works, as it can evaluate java expr.
		X-- no replacing them in the query
		X-- add a section to the header to pass in the $P!{} list
		X-- --Sql Workbench $P!{} Replacements--
		X-- --Find and replace with appropriate SQL expressions:
		X-- each line: -- $P!{<p>} = "value"
		X-- $P!{} may contain parameters internally, maybe even ones 
		   Xnot used elsewhere
				X> findSqlParams should use '\n'-separated concat
				X  of the main query and all $P!{} content
				XIFF we want to format params inside $P!{}:
				X> move non-header part of formatSql to formatAnySql();
				  X run it on $P!{} values before passing to header builder.
				  NNN $P!{} has to go last in findSqlParams for it to work.
	
	X- implement a way to remove $X statements
		Xe.g. make them all boolean parameters, set to true
			X-- keep them in a separate pCollection
			X-- add them to sql headers; the "summary" print fn
		Xname: XIN_[id] type: java.lang.boolean value: true --<expr>
		X(!)
			X--fix regex, can no longer match \w (word)
			X--create a list of parameters (see above) from the list
			X--add the list of parameters to sql header (merged pCollection)
		
		
			
	- split file
		--classes + implementation-agnostic fns (lib/jrxmlquery)
		--common implementation (lib/common)
		--data definitions e.g. BIR defaults list (lib/data)
		--postgres-workbench application (jrxml2postgres)
		--sqlserver-studio application (jrxml2sqlserver)
	OR - maintain structure
		--on start: prompt to type <num> = <language>
					prompt to enter jrxml data
					clear terminal, output result
TODO
	- gather data from reports (default parameters)
		--validate at work
	X- implement a a way to use the BIR parameters to get default values
		Xadd a convertValue function in JrxmlParameterConverter
	X- implement a way to distinguish between collection/single
		Ne.g. store as single, override to collection depending on report
		Ntype will vary, use BIR defaults to check?
		X--add to ignore list
	X- implement a way to handle $P!{} containing more $P{} expressions
		X--$P!{} may even contain parameters not used elsewhere
		N--use intermediate sql just called 'sql', do the $P!{} pass first
		  Nand separate to rest
	X- implement a way to handle string encapsulation in queries
		Xi.e. sql needs quotes on certain fields
			X--add a quote map of javaType:needsQuotes
	- build a list of unwanted parameters for the exclude list
		e.g. AccessibleOrganisationCodes
	X- implement a special case for $P! type (direct string insert)
	X- implement a special case for the 3-days-ago parameter default
		X--handle in passed-in converter fn in JrxmlParameterConverter
	X- make sure date formatting is correct (for my defaul values)
		Xi.e. test out sql headers at work
	X- implement the ParameterParser
		Xuses an excluded parameter list; recognises <p></p> or <p/>
	X- implement existing interfaces
"""