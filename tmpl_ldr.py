#!/usr/bin/env python3

#this is a simple template loader library
#it is primarily intended for html templates but can in theory be used for anything
#as long as the import syntax doesn't directly conflict with the file format syntax of the templates

#its name should be read as "TeMPLate LoaDeR"
#but because it can also be read as "TeMPLe LoaDeR" there might be some puns in here related to that :P

#it is intended to be much simpler than systems like jinja2 which I feel are very much overkill for the task

#it supports two types of substitutions:
#	{{$import}} statements, which recurse on the given file and substitute its contents where the import was found
#		ALL imports are pseudo-absolute paths relative to the project root (where your python script runs from)
#			i.e. an import within an import must still use the full path on each import
#	{{variable}} statements, which substitutethe value of the variable where the expression was found

#it intentionally does NOT support loops, variable definitions, multi-file inheritance, block overriding
#or any of the other totally unnecessary cruft found in most template systems

#all variable substitutions made when loading a template are GLOBAL
#the same variable cannot have a different value in a different file during a single load
#avoiding namespace collisions is the responsibility of the calling code, NOT this library


#external dependencies
import re

#global constants
IMPORT_FORMAT=re.compile(r'\{\{\$([^\{\}]+)\}\}')
VARIABLE_FORMAT=re.compile(r'\{\{([^\$][^\{\}]+)\}\}')
INDENT_DELIMITER=re.compile(r'[^\t ]{1}')

#gets the indent level of the data we're inserting
#this is equal to the whitespace between the given index of the given string and the preceeding newline (\n)
#using windows newlines in template files is Not My Problem :)
#args:
#	text: the text to search in
#	start_at: the start point for backwards search
#return:
#	returns a string which is all the preceeding whitespace data
#	before start_at point until any non-whitespace character or a newline
#side-effects:
#	None
def get_indent_for(text:str,start_at:int) -> str:
	#if start_at is after the end of the string
	if(start_at>=len(text)):
 		#then start at the end of the string
		start_at=len(text)-1
	
	acc=''
	#for each character between the start_at point (inclusive) and where the whitespace stops
	#NOTE: the whitespace also stops where the string stops; duh!
	while(start_at>=0 and (not re.match(INDENT_DELIMITER,text[start_at]))):
		#add it to the accumulator
		acc=text[start_at]+acc
		start_at-=1
	
	#return the accumulator string
	#which now contains the indentation
	#if start_at was (the first non-whitespace character on the line - 1)
	return acc

#applies the given indent level by prepending it to every line in the given text
#thus indenting it by the given string
#args:
#	text: the text to indent
#	indent: the string to prepend to each text line
#return:
#	returns a version of text with the given indent preceeding every line
#side-effects:
#	none
def apply_indent_to(text:str,indent:str) -> str:
	acc=''
	
	#add each line to an accumulator
	#with the preceeding indent
	for line_idx,line in enumerate(text.split("\n")):
		acc+=(indent if line_idx>0 else '')+line+"\n"
	
	#remove trailing newline
	acc=acc[0:len(acc)-1]
	
	#return the accumulator
	return acc.rstrip('\t \r\n')

#load a template file
#args:
#	tmpl_file: the relative path of the template file to load
#	skip_undefined: whether to skip substitutions for undefined varaibles or not (default False)
#		if False, undefined variables will raise a KeyError
#		if True, undefined variables will be passed through as their literal values
#	**kwargs: the variable substitutions to make, as name->value pairs
#return:
#	returns a string which contains the template contents with any necessary substitutions
#	if the file is not found an IOError occurs
#	if an import is not found an IOError occurs
#	if a variable substitution is expected but that variable is not given then a KeyError occurs
#side-effects:
#	no side-effects persist after return (reads the necessary template files during execution)
def load_tmpl(tmpl_file:str, skip_undefined=False, **kwargs) -> str:
	#load the file content itself into RAM
	fp=open(tmpl_file,'r')
	content=fp.read()
	fp.close()
	
	return load_tmpl_str(content=content, skip_undefined=skip_undefined, **kwargs)

#run template substitutions on an already-loaded string
#as opposed to reading it from a file first
#args:
#	content: the template file content as a string
#	skip_undefined: whether to skip substitutions for undefined varaibles or not (default False)
#		if False, undefined variables will raise a KeyError
#		if True, undefined variables will be passed through as their literal values
#	**kwargs: the variable substitutions to make, as name->value pairs
#return:
#	returns a string which contains the template contents with any necessary substitutions
#	if an import is not found an IOError occurs
#	if a variable substitution is expected but that variable is not given then a KeyError occurs
#side-effects:
#	no side-effects
def load_tmpl_str(content:str, skip_undefined=False, **kwargs) -> str:
	#find the first import via regex
	#NOTE: this doesn't find all imports right away
	#because the content length changes after an import substitution is made
	#and that means that after one import all subsequent import regex matches would be invalid
	#since they would have incorrect start and end points
	imp=re.search(IMPORT_FORMAT,content)
	
	#for each import in the template
	#for each imp in the temple (oh no!)
	while(not (imp is None)):
		#NOTE: we know that the group(1) will be defined because if the regex matched
		#then there must be a parenthesized subgroup which defines the file name
		#and that's what we're interested in for import purposes
		
		#recurse; an import is just another template loading operation
		#NOTE: kwargs is passed through to do global variable substitution within imports as well
		imp_content=load_tmpl(
			tmpl_file=imp.group(1),
			skip_undefined=skip_undefined,
			**kwargs
		)

		#preserve indentation on the import statement if it was preceeded by whitespace
		#i.e. if the import statement was indented by two tabs then all the import content should be indented by the same amount
		indent=get_indent_for(text=content,start_at=(imp.start()-1))
		imp_content=apply_indent_to(text=imp_content,indent=indent)
		
		#once the template is loaded put the content where it's expected
		content=content[0:imp.start()]+imp_content+content[imp.end():]
		
		#find the next import statement, if any exist
		imp=re.search(IMPORT_FORMAT,content)

	#if we are skipping undefined variables
	#then make substitutions by looking for the GIVEN arguments in the temple
	#where arguments are wont to occur
	#instead of looking for what variables are in the temple first and THEN looking for what was given as arguments
	if(skip_undefined):
		for var in kwargs:
			if(content.find('{{'+var+'}}')>=0):
				content=content.replace('{{'+var+'}}',kwargs[var])
	else:
		#now that the imports are handled, handle the variable substitutions
		var=re.search(VARIABLE_FORMAT,content)
		
		#for each variable in the template
		while(not (var is None)):
			#NOTE: if a variable substitution is expected in the template but no such variable was given
			#then this will throw/raise a KeyError exception
			var_content=kwargs[var.group(1)]

			#preserve indentation on the variable substitution statement if it was preceeded by whitespace
			#i.e. if the variable statement was indented by two tabs then all the variable content should be indented by the same amount
			indent=get_indent_for(text=content,start_at=(var.start()-1))
			var_content=apply_indent_to(text=var_content,indent=indent)
			
			content=content[0:var.start()]+var_content+content[var.end():]
			
			#find the next variable substitution, if any exist
			var=re.search(VARIABLE_FORMAT,content)
	
	#now that all imports and substituions have been performed
	#the generated content is complete
	#so return it
	#and exit the temple
	return content

if(__name__=='__main__'):
	print('Running internal test (example template)...')
	
	#try to load the example
	output=load_tmpl(
		tmpl_file='views/example.tmpl.html',
		page_title='Example Page Title',
		page_content='This is some example page content.',
	)

	#this output could be sent to network or output to the console or whatever works for you
	
	#verify that it loads as expected
	assert(output=='''<html>
<head>
        <title>Example Page Title</title>
</head>
<body>
<h1>Example Page Title</h1>
<hr />
<p>
        This is some example page content.
</p>
</body>
</html>
''')
	print('Internal test successful; tmpl_ldr is working as expected.')

