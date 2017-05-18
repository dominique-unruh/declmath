#!/usr/bin/python

import sys, re, string


########## Symbol index generation code #############

def fail(msg):
    print >>sys.stderr, msg
    exit(1)

symbols = dict()

def load_symbols(file):
    global symbols
    with open(file,'rt') as f:
        for line in f:
            m = re.match(r"([0-9]+)\.([a-z]+)=(.*)",line)
            if not m: fail("Malformatted line {0} in {1}".format(line,file))
            id = m.group(1); key = m.group(2); val = m.group(3)
            if not id in symbols: symbols[id] = dict()
            if not key+"*" in symbols[id]: symbols[id][key+"*"] = []
            symbols[id][key+"*"].append(val)
            symbols[id][key] = val

def write_index(basename):
    global symbols
    with open(basename+".sdx",'wt') as f:
        for id in symbols:
            sym = symbols[id]
            if "noindex" in sym: continue
            if "variantof" in sym: continue
            if not "macro" in sym: fail("id {0} has no macro definition".format(id))
            macro = sym["macro"]
            if "placeholder" in sym: placeholder=sym["placeholder"]
            elif "code" in sym: placeholder=sym["code"]
            else: placeholder=macro
            if not "description" in sym: fail("id {0} (macro {1}) has no description".format(id,macro))
            description=sym["description"]
            pages = sym["page*"] if "page*" in sym else []
            pages = ["\\symbolindexpage{{{0}}}{{{1}--symbolindex}}".format(*string.split(p,",")) for p in pages]
            pages = string.join(pages,", ")
            f.write("\\symbolindexentry{{{0}}}{{{1}}}{{{2}}}{{{3}}}\n".
                    format(id,placeholder,description,pages))
        f.write("""%%% {0} Variables:
%%% mode: latex
%%% coding: latin-1
%%% TeX-master: "{1}"
%%% End:""".format("Local",basename))



################# PDF popup generation code ##########################


popup_pdf = None
pdf_popup_config = {'compress':False,
                    'popuplinkcolor':None, # (r,g,b). None for disable

                    # None: no background link for closing all popups
                    # 'front': In front of normal links (problem with Evince: deactivates other links
                    #          even when bg link is inactive, because in Evince hidden links are still
                    #          clickable)
                    # 'back': Behind all links
                    'backgroundlink':'back',

                    # True makes the backgroundlink not cover the whole page and
                    # have a thick red border. For testing purposes
                    'backgroundlink-debug':False,
                }

def popups_read_pdf(file):
    from pdfrw import PdfReader
    global popup_pdf
    popup_pdf = PdfReader(file)

def popups_write_pdf(file):
    from pdfrw import PdfWriter
    w = PdfWriter(version='1.5',compress=pdf_popup_config['compress'])
    w.trailer = popup_pdf
    w.write(file)

def popup_removepages(pdf,remove):
    from pdfrw import PdfDict, PdfArray, PdfName
    def removein(node):
        if node.Type == PdfName.Pages:
            num = 0
            for p in tuple(node.Kids):
                n = removein(p)
                if n==0: node.Kids.remove(p)
                num += n
            node.Count = num
            return num
        elif node.Type == PdfName.Page:
            if id(node) in map(id,remove): return 0 # Then parent-call will remove node from pages
            return 1
                
    num = removein(popup_pdf.Root.Pages)
    popup_pdf.private.pages = popup_pdf.readpages(popup_pdf.Root)
    if num!=len(popup_pdf.pages):  # Sanity check, should never fail
        raise RuntimeError((num,len(popup_pdf.pages)))

def popup_getpopup_xobjs():
    from pdfrw.buildxobj import pagexobj
    popups = {}
    toremove = []
    for page in popup_pdf.pages:
        if page['/SYMIDX.POPUP']:
            popupid = page['/SYMIDX.POPUP'].decode()
            if popupid in popups: 
                raise RuntimeError("Duplicated /SYMIDX.POPUP: {}".format(popupid))
            xobj = pagexobj(page)
            popups[popupid] = xobj
            toremove.append(page)
    
    popup_removepages(popup_pdf,toremove)
    return popups

# Finds all links with key /SYMIDX.SHOW and for each one returns:
# (page,popupname,rect)
# popupname = argument of /SYMIDX.SHOW
# page = a PDF page object
# rect = the rectangle of the link
# The links themselves are removed
def popup_getlinks():
    links = []
    for page in popup_pdf.pages:
        if page.Annots:
            for annot in list(page.Annots):
                if annot['/SYMIDX.SHOW']:
                    links.append((page,annot['/SYMIDX.SHOW'].decode(),annot.Rect))
                    page.Annots.remove(annot)
    return links

# Computes "n choose k"
def choose(n,k):
    acc = 1
    for i in range(k):
        acc *= n-i
    for i in range(k):
        acc /= i+1
    return acc

# Makes a number of OCGs for combining.
# num: minimum size of the resulting code
def popup_make_ocgs(num):
    from pdfrw import PdfDict, PdfArray, PdfName

    n=2
    while choose(n,n/2)<num: n += 1

    ocgs = []
    
    for i in range(n):
        ocg = PdfDict(Type=PdfName.OCG,Name="OCG {}".format(i),indirect=True)
        ocgs.append(ocg)

    if popup_pdf.Root.OCProperties:
        print "Root.OCProperties already exists"
    ocgs = PdfArray(ocgs)
    #ocgs.indirect = True
    popup_pdf.Root.OCProperties = PdfDict(OCGs=ocgs,
                                    D=PdfDict(Order=ocgs,ON=[],OFF=ocgs))

    code = [([],[])]
    for ocg in ocgs:
        code = [(c+[ocg],d) if take else (c,d+[ocg])
                for c,d in code for take in (True,False)]
    code = [(c,d) for c,d in code if len(c) == n/2]

    # code is now an array of all different pairs (c,d)
    # where c contains floor(n/2) OCGs and d the rest of the OCGs

    hide_ocmd = PdfDict(indirect=True,
                        Type=PdfName.OCMD,
                        OCGs=ocgs,
                        P=PdfName.AllOff)

    show_ocmd = PdfDict(indirect=True,
                        Type=PdfName.OCMD,
                        OCGs=ocgs,
                        P=PdfName.AnyOn)

    return code, ocgs, hide_ocmd, show_ocmd

curr_unique_id = 0
def popup_unique_id():
    global curr_unique_id
    curr_unique_id += 1
    return curr_unique_id

# Creates a popup in the document
# page: where to create the popup? (PDF page object)
# rect: the area which should open the popup? [x y w h]
# popupname: a unique identifier for this popup
#   (i.e., different invokcations of make_popup have the same "popupname"
#          iff they have the same "popup")
# popup: an XObject containing the graphics that should pop up
# code: A pair (on,off), each a list of OCGs.
#       on+off should be all OCGs used for controlling the popups
#       and the popup will be shown iff all OCGs in on are active.
#       This pair should be unique for each make_popup call.
#       And no "on" from one call should be a subset of "on" from another call.
#
# This function installs the popup XObject below the link and makes
# the link activate/deactivate the OCGs for/not for the current popup
def make_popup(page,rect,popupname,popup,code):
    from pdfrw import PdfDict, PdfArray, PdfName
    from pdfrw.uncompress import uncompress
    codeword_on,codeword_off = code

    show_action = PdfDict(S=PdfName.SetOCGState,
                          State=PdfArray([PdfName.OFF]+codeword_off+[PdfName.ON]+codeword_on))

    link = PdfDict(indirect=True,
                   Type=PdfName.Annot,
                   H=PdfName.I,
                   Subtype=PdfName.Link,
                   A=show_action,
                   Rect=rect)

    if pdf_popup_config['popuplinkcolor']:
        link.C = PdfArray(pdf_popup_config['popuplinkcolor'])
    else:
        link.Border = [0,0,0]

    page.Annots.append(link)

    ocmd = PdfDict(Type=PdfName.OCMD,
                   OCGs=codeword_on,
                   P=PdfName.AllOn)

    popup_pdfname = '/SPopup'+popupname
    ocmd_pdfname = '/SPopupOCMD{}'.format(popup_unique_id())
    
    if not page.Resources.Properties: page.Resources.Properties = PdfDict()
    if not page.Resources.XObject: page.Resources.XObject = PdfDict()

    page.Resources.XObject[popup_pdfname] = popup
    page.Resources.Properties[ocmd_pdfname] = ocmd
    if page.Contents.Filter:
        uncompress([page.Contents]) # Important. Otherwise appending to stream add plain text to compressed stream
    page.Contents.stream += "q /OC {ocmd} BDC 1 0 0 1 {x} {y} cm {popup} Do EMC Q\n".\
                            format(x=rect[0],y=float(rect[1])-popup.BBox[3],
                                   ocmd=ocmd_pdfname,
                                   popup=popup_pdfname)

# Deactivates all links when a popup is active
# hide_ocmd: A OCMD that is active only if no popup is active
#            (I.e., if all OCGs in the code are inactive)
def popup_hide_links(hide_ocmd):
    for page in popup_pdf.pages:
        for annot in page.Annots if page.Annots else ():
            if annot.OC:
                print "Annotation {} already has an /OC-entry. Ignoring.".format(annot.OC)
            annot.OC = hide_ocmd

# Creates, on each page, a whole page link that deactivates all OCGs
# show_ocmd: an OCMD that is active if a popup is shown
#            (i.e., if some OCG is active)
# ocgs: all OCGs
def popup_bg_links(show_ocmd,ocgs):
    from pdfrw import PdfDict, PdfArray, PdfName
    if not pdf_popup_config['backgroundlink']: return
    if pdf_popup_config['backgroundlink'] not in ('front','back'):
        raise ValueError("pdf_popup_config['backgroundlink'] must be front or back or None")

    for page in popup_pdf.pages:
        rect = page.MediaBox
        if pdf_popup_config['backgroundlink-debug']: rect = [90,800,180,200]
        link = PdfDict(indirect=True,
                       Type=PdfName.Annot,
                       H=PdfName.N,
                       Subtype=PdfName.Link,
                       Rect=rect,
                       #F=2, # Link is hidden
                       Border=[0,0,10] if pdf_popup_config['backgroundlink-debug'] else [0,0,0],
                       C=[1,0,0] if pdf_popup_config['backgroundlink-debug'] else None,
                       OC=show_ocmd,
                       A=PdfDict(S=PdfName.SetOCGState,
                         State=PdfArray([PdfName.OFF]+ocgs)),
                   )

        if page.Annots==None: page.Annots = PdfArray()
        if pdf_popup_config['backgroundlink']=='back':
            page.Annots.insert(0,link)
        elif pdf_popup_config['backgroundlink']=='front':
            page.Annots.append(link)
        else:
            raise RuntimeException("Unexpected value")



def install_popups():
    # Must be before getlinks() and hide_links(), since otherwise getlinks/hide_links finds links in popup-pages
    popups = popup_getpopup_xobjs()

    links = popup_getlinks()
    code,ocgs,hide_ocmd,show_ocmd = popup_make_ocgs(len(links))

    popup_hide_links(hide_ocmd)
    popup_bg_links(show_ocmd,ocgs)

    idx = 0
    for page,popupname,link in links:
        make_popup(page,link,popupname,popups[popupname],code[idx])
        idx += 1



if len(sys.argv)<=1: fail("Invocation: makesymind.py <basename>")
if sys.argv[1] == 'install-popups':
    if len(sys.argv)!=3: fail("Invocation: makesymind.py install-popups <pdf-file>")
    popups_read_pdf(sys.argv[2]); install_popups(); popups_write_pdf(sys.argv[2])
else:
    if len(sys.argv)!=2: fail("Invocation: makesymind.py <basename>")
    basename = sys.argv[1]
    load_symbols(basename+".syi")
    write_index(basename)

