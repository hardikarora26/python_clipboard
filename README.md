# python_clipboard API
It is an cross-platform API to access content from the clipboard and put content to clipboard in different clipboatd formats such as rtf, unicode text, html format.
For MacOS there is an existing python project, richxerox, that meet the requirements, however, for windows there wasn't one available, therfore, I created this project.

How it Works?

r = "{\\rtf1\\ansi\\ansicpg1252\\cocoartf1187\\cocoasubrtf390\n" \
    "{\\fonttbl\\f0\\froman\\fcharset0 Times-Roman;}\n{\\colortbl;" \
    "\\red255\\green255\\blue255;}\n\\deftab720\n\\pard\\pardeftab720" \
    "\n\n\\f0\\fs24 \\cf0 This is \n\\b good\n\\b0 !}"
    
h = "this is <strong>good</strong>!"
 
 
copy('this is good!')                     # put content on clipboard as text

copy('this is good!', rtf=r, html=h)      # Putting string as a first argument will put it as text, puts r as rtf and h as html

copy(text="this is good!", html=h, rtf=r) # works same as above
 
 
print(paste())                     # get data in the text format (Unicode)

print(paste('rtf'))                # get RTF

print(paste('html'))               # get HTML
 
 
 
#Other than text, html and rtf, you may pass any other format to the copy() and paste() functions depending upon the operating system. For Mac it will be a uti for that format and for windows it will be a string, e.g for html it is 'HTML Format'.
