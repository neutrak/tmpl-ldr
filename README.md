Temple Template Loader

This is a complete template loader system for python.  

* By complete, we mean that it has all the features it's ever intended to have and will never have additional features added.  
It will still have maintenance and updates as needed for security or speed improvments, or to better integrate with particular toolchains.  
But it will not support any additional syntax or concepts beyond what is documented here.  

The basic concept is that templates are loaded with the `load_tmpl` function.  
`load_tmpl` does two things:
	First, substitute all imports of the format `{{$path/to/other/template}}` with the values contained within that file.  
	Second, substitute all variables of the format `{{variable}}` with the value provided to load_tmpl as a keyword argument.  

Imports are recursive, meaning that a template can import a template which imports a template, up to the recursion limit imposed by the python interpreter.  
If you attempt to include a template file inside of itself, you will get a "Maximum Recursion Depth Exceeded" error (exception).  
Import paths are always relative to the directory python is executing from, and are not relative to the path of other templates they are included by.  
All variables which exist in the template MUST be provided as keyword arguments; variables are not defaulted to empty string or None as they might be in other templating systems.  
All variables are global; variables do not have scope when being substituted into the template.  
If you want variables within the same loaded template to have different values, you must instead have different variables, each with a unique name.  

Here is a simple example template, `views/example.tmpl.html`:
```html
{{$views/header.tmpl.html}}
<h1>{{page_title}}</h1>
<hr />
<p>
	{{page_content}}
</p>
{{$views/footer.tmpl.html}}
```

And here is the `views/header.tmpl.html` that it includes:
```html
<html>
<head>
	<title>{{title}}</title>
</head>
<body>
```

And the `views/footer.tmpl.html`:
```html
</body>
</html>
```

To load this, we would run the following python:
```python3
import tmpl_ldr
output=tmpl_ldr.load_tmpl(
	tmpl_file='views/example.tmpl.html',
	page_title='Example Page Title',
	page_content='This is some example page content.',
)

#this could be sent to network or output to the console or whatever works for you
#for demonstration purposes we're just outputting it to the console
print(output)
```


The reason that loops, conditions, and other control structures are not included is because they already exist in python.  
For example, to make a list of items, each of which has its own display, you could write the following in python:
```python3
	#for each item in a list
	item_views=[]
	for item in item_list:
		#load the template for that item, with appropriate variables
		item_views.append(tmpl_ldr.load_tmpl(
			tmpl_file='views/item_view_template.tmpl.html',
			value_a=item.value_a,
			value_b=('' if item.value_b is None else item.value_b),
		))
	
	#then use the generated html for each item as input in another template
	#to get the complete result
	full_view=tmpl_ldr.load_tmpl(
		tmpl_file='views/full_view_template.tmpl.html',
		item_views="\n".join(item_views)
	)
	
	#full_view now has the populated html as a string
	#and we can output it however we please
	print(full_view)
```

Therefore a template system does not need to include these control structures itself.  
We rely on the python implementation of any loops or conditions, rather than re-implementing them in the template system.  

NOTE: doing this for very large loops can be I/O heavy since every `load_tmpl` call currently reads a file from disk.  
We might break out the substitution step into its own function in order to avoid reading the template more than once in this case.  
This will be done if there is sufficient demand.  It constitutes an optimization but not a feature addition.  

NOTE: although for example purposes we have used html, and we intend that to be the primary use case, this system is in no way tied to html.  
You can make templates of any file format as long as the syntax of the file itself does not directly conflict with the variable and import syntax described above.  

NOTE: by convention file names for temple templates end in .tmpl.file-type but there's no hard requirement for this and you can use arbitrary file names if needed.  

As a design goal, this library's internal code should never be more than 1500 lines in total.  
That shouldn't be difficult to acheive since at the time of writing it is 164 lines of code and it already does everything it needs to do.  

