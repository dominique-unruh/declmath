var mouseMoveHandlerLastElement = null;
var hoverMathBar = null;
var hoverMathPopup = null;
var hoverMathPopupShown = false;

/** Given the OpenMath name (e.g., "arith1.plus") of a math symbol,
    return a span containing a visual representation of the symbol index entry
    for that symbol.

    Returns null if no symbol index entry could be found.
*/
function csymbolToDescription(name) {
    var span = $("<span>");
    var idxentry = document.getElementById("symbolindexentry-"+name);
    if (idxentry !== null) {
	idxentry = $(idxentry);
	var placeholder = idxentry.children().eq(0);
	var description = idxentry.children().eq(1);
	var placeholderSpan = $("<span>").addClass('symbolIndexPlaceholder').
	    append(placeholder.clone().contents())
	var descriptionSpan = $("<span>").addClass('symbolIndexDescription').
	    append(description.clone().contents());
	span.append(placeholderSpan,": ",descriptionSpan,"; ");
    } else {
	console.warn("Symbol '"+name+"' not found; ");
	return null;
    }
    return span;
}


/** Given the OpenMath name (e.g., "arith1.plus") of a math symbol,
    return a table row containing a visual representation of the symbol index entry
    for that symbol.

    Returns null if no symbol index entry could be found.
*/
function csymbolToDescriptionTR(name) {
    var span = $("<tr>");
    var idxentry = document.getElementById("symbolindexentry-"+name);
    if (idxentry !== null) {
	idxentry = $(idxentry);
	var placeholder = idxentry.children().eq(0);
	var description = idxentry.children().eq(1);
	var links = idxentry.children().eq(2);
	var placeholderSpan = $("<td>").addClass('symbolIndexPlaceholder').
	    append(placeholder.clone().contents())
	var descriptionSpan = $("<td>").addClass('symbolIndexDescription').
	    append(description.clone().contents());
	var linkSpan = $("<td>").addClass('symbolIndexLinks').
	    append(links.clone().contents());
	span.append(linkSpan,placeholderSpan,descriptionSpan);
    } else {
	console.warn("Symbol '"+name+"' not found; ");
	return null;
    }
    return span;
}


/** Given a DOM element, return the OpenMath name of the it if it corresponds to an
    OpenMath symbol, or undefined otherwise */
function getSymbolAtElem(elem) {
    if (elem.namespaceURI != "http://www.w3.org/1998/Math/MathML") return;
    var xref = elem.getAttribute('xref');
    if (xref === null) return;
    var cmml = document.getElementById(xref);
    if (cmml === null) return;

    if (cmml.tagName == 'csymbol') {
	return cmml.getAttribute("cd")+"."+cmml.textContent;
    } else if (cmml.tagName == 'apply') {
	var head = cmml.firstChild;
	if (head.tagName == 'csymbol')
	    return head.getAttribute("cd")+"."+head.textContent;
    } else if (cmml.tagName == 'cn') {
	return;
    } else if (cmml.tagName == 'ci') {
	// TODO: add information about variables, if available
	return;
    } else if (cmml.tagName == 'plus') {
	return ("arith1.plus");
    } else if (cmml.tagName == 'subset') {
	return ("set1.subset");
    } else if (cmml.tagName == 'eq') {
	return ("relation1.eq");
    } else if (cmml.tagName == 'neq') {
	return ("relation1.neq");
    } else if (cmml.tagName == 'geq') {
	return ("relation1.geq");
    } else if (cmml.tagName == 'leq') {
	return ("relation1.leq");
    } else if (cmml.tagName == 'compose') {
	return ("fns1.left_compose");
    } else if (cmml.tagName == 'infinity') {
	return ("nums1.infinity");
    } else if (cmml.tagName == 'sum') {
	return ("arith1.sum");
    } else if (cmml.tagName == 'in') {
	if (cmml.getAttribute("type") == "multiset")
	    return ("multiset1.in");
	return ("set1.in");
    } else if (cmml.tagName == 'notin') {
	if (cmml.getAttribute("type") == "multiset")
	    return ("multiset1.notin");
	return ("set1.notin");
    } else if (cmml.tagName == 'notsubset') {
	if (cmml.getAttribute("type") == "multiset")
	    return ("multiset1.notsubset");
	return ("set1.notsubset");
    } else if (cmml.tagName == 'notprsubset') {
	if (cmml.getAttribute("type") == "multiset")
	    return ("multiset1.notprsubset");
	return ("set1.notprsubset");
    } else {
	console.warn("Unsupported Content MathML tag "+cmml.tagName,cmml);
	return;
    }
}

/** Given a DOM element, return the OpenMath name of the it if it corresponds to an
    OpenMath symbol, and the same for all ancestors. 
    The result is returned as a list without duplicates. */
function getSymbolsAtElem(elem) {
    var syms = [];
    var seen = new Set();
    for (; elem!==null; elem = elem.parentElement) {
	var symName = getSymbolAtElem(elem);
	if (symName !== undefined) {
	    if (seen.has(symName)) continue;
	    seen.add(symName);
	    syms.push(symName);
	}
    }
    return syms;
}

function mouseMoveHandler(event) {
    var x = event.clientX, y = event.clientY;
    var elem = document.elementFromPoint(x,y);
    if (elem === mouseMoveHandlerLastElement) return;
    mouseMoveHandlerLastElement = elem;
    
    hoverMathBar.empty();
    
    var syms = getSymbolsAtElem(elem);
    //console.log(syms);
    syms.forEach(function (name) {
	hoverMathBar.append(csymbolToDescription(name));
    });

    if (syms.length==0)
	hoverMathBar.html("<small>Hover over math symbols to see their definition here.<small>");
};

function mouseClickHandler(event) {
    var x = event.clientX, y = event.clientY;
    var elem = document.elementFromPoint(x,y);

    if ($(elem).parents("math").length==0) {
	if (hoverMathPopupShown) {
	    console.log("click - hiding popup");
	    hoverMathPopup.css('display','none');
	    hoverMathPopupShown = false;
	}
	return;
    }
    
    console.log("click - showing popup");

    hoverMathPopup.empty();
    hoverMathPopup.css('left',event.pageX+10);
    hoverMathPopup.css('top',event.pageY+20);
    var syms = getSymbolsAtElem(elem);

    var empty = true;
    syms.forEach(function (name) {
	var entry = csymbolToDescriptionTR(name);
	if (entry) {
	    empty = false;
	    hoverMathPopup.append(entry);
	}
    });

    if (empty)
	hoverMathPopup.html("<tr><td>No symbol with index entry here</td></tr>");

    hoverMathPopup.css('display','initial');
    hoverMathPopupShown = true;
}

function initHoverMath() {
    console.log("loaded");
    $(document).mousemove(mouseMoveHandler);
    $(document).click(mouseClickHandler);
    hoverMathBar = $('<div class="symbolIndexBar">').appendTo($("body"));
    hoverMathPopup = $('<table class="symbolIndexPopup">').appendTo($("body"));
};

$(document).ready(initHoverMath);
