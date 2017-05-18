#!/usr/bin/python3

import sys, urllib.request, urllib.parse, base64
from bs4 import BeautifulSoup, Tag 

include_remote_files = True

#def convert_file(htmlfile,outfile):
#    convert(urllib.request.pathname2url(htmlfile),outfile)

link_attrs = [ ['a','href'], ['img','src'], ['script','src'], ['style','src'] ]

def make_data_url(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.path == "": return url
    if parsed.scheme != "":
        if not include_remote_files: return url
        content = urllib.request.urlopen(url).read()
    else:
        content = open(parsed.path,'rb').read()
    frag = "#"+parsed.fragment if parsed.fragment != "" else ""
    new_url = "data:;base64,"+base64.b64encode(content).decode('ascii')+frag
    return new_url

def make_style_element(soup,url,typ):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "": return url
    if parsed.path == "": return url
    #print(parsed)
    content = open(parsed.path,'rb').read()

    style = soup.new_tag("style")
    style.append("\n"+content.decode('utf-8')+"\n")
    style['type'] = typ

    return style

def convert(infile,outfile):
    content = open(infile,'rb').read()
    soup = BeautifulSoup(content,'lxml')
    for tagattr in link_attrs:
        tag = tagattr[0]
        attrs = tagattr[1:]
        for elem in soup.find_all(tag):
            for attr in attrs:
                val = elem.get(attr)
                if val==None: continue
                elem[attr] = make_data_url(val)

    for elem in soup.find_all('link'):
        print("X",elem['rel'])
        if elem['rel'] != ['stylesheet']: continue
        href = elem['href']
        if not href: continue
        style = make_style_element(soup,href,elem['type'])
        if not style: continue
        elem.replaceWith(style)
    
    with open(outfile,'wb') as f:
        f.write(soup.encode())
    
#soup = BeautifulSoup(open("www/index.html"))




(_,file,outfile) = sys.argv
print("URL",file,"OUTFILE",outfile)
convert(file,outfile)
