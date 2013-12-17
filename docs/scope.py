"""
	jrxml2sql v0
	 - parameter extractor only; don't attempt full parser (yet?)
	 - query2workbench.py: "dumb" conversion
	 - jrxml2sql.py: extract query & parameter types from tags
	 - usage:
		> if no arguments provided, open as CLI:
			-- splash screen with name/purpose of script
			-- paste text to terminal
			-- run remainder as if file was provided
		> if argument provided, treat as file, convert file
			-- validate file exists
			-- print minimal progress to terminal
			-- print "created files: query_postges.sql, query_sqlserver.sql"
			-- prompt for next query
			-- ctrl-c / ctrl-d / q / exit / quit exits
		> drag-n-drop is the same as providing one argument
		> -d flag: debug mode, detailed progress printed to terminal
	 - components:
		> mappings_[language].py files
			//-- map parameter to default type, per language
			//-- map parameter to $X{} default value, per language
			-- map parameter to $P{} default value (+ type), per language
			-- map java type to sql type, per language
		> classes
			-- parameter, incl. java type & converted type per language
			-- $X statement - original string, value, parameter 
	 - jrxml2sql steps:
		> load and verify config file, jrxml file
		> extract query, parameter types from jrxml
		> extract $P, $P!, $X parameters from query
		> extract a set of unique $X statements from query
		> map java type to sql type for query parameters (reference jrxml)
		> generate default value based on above mapping (if unknown: ???)
		> make a copy of the query
		> replace $P with editor-specific variable
		> replace $X with editor-specific variable
		> generate output - only include parameters in the query.
			-- $P (single-value parameters) with default values
			--divider--
			-- $X (multi-value parameters) with:
				~~~ true as default, allow user to replace expression.
					Follow with original $X{} expr, commented out
			--divider--
			-- $P! variables with:
				~~~ note for user to find and replace these
			--divider--
			-- fixed query
			--divider
			-- original query, commented out
		> write file(s), terminal dump etc
		
-----------------------------------------------------------------------
	conundrums
		- we will *not* know the query language (even from the jrxml)
		- we can try and extract clues, but it won't work for everything
		- solution: config file!
			editor="" # "workbench", "sqlstudio" or "all"
			language="" # "postgres", "sqlserver" or "all"
			debug=False # True or False
		- no oracle support at first :(

-----------------------------------------------------------------------
	query2workbench.py:
		- "dumb" conversion - doesn't try to match parameter types
			and default values; doesn't support sql studio; don't care
			about language	
		- config file:
			language="" # "postgres", "sqlserver" or "all"
			debug=False # True or False
		- no mappings_[language].py files
	 - jrxml2sql steps:
		> load and verify config file
		> extract $P, $P!, $X parameters from query
		> extract a set of unique $X statements from query
		> make a copy of the query
		> replace $P with editor-specific variable
		> replace $X with editor-specific variable
		> generate output
			-- $P (single-value parameters) = "???";
			--divider--
			-- $X (multi-value parameters) with:
				~~~ true as default, allow user to replace expression.
					Follow with original $X{} expr, commented out
			--divider--
			-- $P! variables with:
				~~~ note for user to find and replace these
			--divider--
			-- fixed query
			--divider
			-- original query, commented out
		> write file(s), terminal dump etc

