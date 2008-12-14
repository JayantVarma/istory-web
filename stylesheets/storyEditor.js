//Add an onDOMReady handler to build the tree when the document is ready
YAHOO.util.Event.onDOMReady(treeInit);

//global variable to allow console inspection of tree:
var tree;

//we also expect the variable MY_ADVENTURE_KEY to be set from the footer
var adventureKey = '';
if (MY_ADVENTURE_KEY) {
	adventureKey = MY_ADVENTURE_KEY;
}

var labelClick = false;
var currentPage = {
	name : null,
	key : null,
	nodeIndex : null
};
var tabIndex = 1;
var numPages = 0;
var currentNodeIndex = null;
var pageElementTypeToNameMap = {
	1: "Text",
	2: "Image",
	3: "Choice"
};
var pageElementIdToTypeMap = {
	"addPageElementText": 1,
	"addPageElementImage": 2,
	"addPageElementChoice": 3
}
var keyToNodeMap = {};
var nodeToKeyMap = {};
var domIdToKeyMap = {};
var domIdToNodeIndexMap = {};

var resetWorkArea = function(updateStr, clear, nodeIndex) {
	var workAreaHelper = YAHOO.util.Dom.get('workAreaHelper');
	var workArea = YAHOO.util.Dom.get('workArea');
	workAreaHelper.innerHTML = "";
	workArea.innerHTML = "";
	workArea.className = null;
	enableIcons();
	if (updateStr) {
		workArea.className = "workArea";
		workAreaHelper.innerHTML = updateStr;
	}
	else if (!numPages) {
		workArea.className = "workArea";
		workAreaHelper.innerHTML = "Create a new page to get started.";
		disableIcons();
	}
	else if (!clear && numPages) {
		workArea.className = "workArea";
		addPageElementsHelper();
	}
	else if (!clear) {
		workArea.className = "workArea";
	}
	if (nodeIndex) {
		var myLastNode = tree.getNodeByIndex(currentNodeIndex);
		myLastNode.label = currentPage.name;
		tree.draw();
	}
}

var divButtonFunction = function(id, iconName) {
	return '<div class="' + iconName + '" alt="Delete Element" id="' + id + '" onmouseover="this.className=\'' + iconName + 'MO\'" onmouseout="this.className=\'' + iconName + '\'"></div>';
}

var addPageElementsHelper = function() {
	enableIcons();
	var workAreaHelper = YAHOO.util.Dom.get('workAreaHelper');
	workAreaHelper.innerHTML = "";
	if (currentNodeIndex) {
		var myNode = tree.getNodeByIndex(currentNodeIndex);
		var myNodeChildren = myNode.children.length;
		if (myNodeChildren == 0) {
			workAreaHelper.innerHTML = "Add some text, an image, or a choice to this page.";
		}
	}
	else {
		workAreaHelper.innerHTML = "Click on a page from the Table of Contents to work on it.";
		disableIcons();
	}
}

var disableIcons = function()
{
	disableDiv('addPageElementText');
	disableDiv('addPageElementImage');
	disableDiv('addPageElementChoice');
	disableDiv('deletePage');
	disableDiv('editPage');
}
var enableIcons = function()
{
	enableDiv('addPageElementText');
	enableDiv('addPageElementImage');
	enableDiv('addPageElementChoice');
	enableDiv('deletePage');
	enableDiv('editPage');
}

var iconMO = function(td) {
	if (currentNodeIndex || td.id == 'addPage') {
		td.className = 'iconBG-light';
		var icon = td.firstChild;
		icon.className = icon.id + 'MO';
	}
}
var iconMOreset = function(td) {
	if (currentNodeIndex || td.id == 'addPage') {
		td.className = 'iconBG-dark';
		var icon = td.firstChild;
		icon.className = icon.id;
	}
}
var iconDisable = function(td) {
	td.className = 'iconBG-disabled';
	var icon = td.firstChild;
	icon.className = icon.id + 'D';
}

var disableDiv = function(name) {
	var td = YAHOO.util.Dom.get(name);
	iconDisable(td);
}
var enableDiv = function(name) {
	var td = YAHOO.util.Dom.get(name);
	iconMOreset(td);
}

//create and add the page element editing stuff to the work area
var addPageElementToWorkArea = function(pageElement, idx) {
	//remove the help text
	addPageElementsHelper();

	//idx is the node.index of the page element in the tree view
	var pageElementsWorkArea = YAHOO.util.Dom.get('pageElementsWorkArea');
	var newDiv = document.createElement('div');
	newDiv.id = "DIV" + idx;
	pageElementsWorkArea.appendChild(newDiv);
	var myHTML = '<div>';
	if (pageElement.dataType == 1) {
		//text
		myHTML += '<textarea tabindex="' + tabIndex + '" id="dataA' + idx + '" name="dataA' + idx + '" rows="15" cols="48">';
		tabIndex++;
		if (pageElement.dataA) { myHTML += pageElement.dataA; }
		myHTML += '</textarea>';
	}
	else if (pageElement.dataType == 2) {
		//image
		//redirect you to the image manager
		myHTML += '<a href="/imageManager?myAdventureKey=' + MY_ADVENTURE_KEY + '">Image Manager</a>';
	}
	else if (pageElement.dataType == 3) {
		//choice
		myHTML += '<table class="tableChoice"><tr><td>Choice Description:</td><td><input size="30" maxlength="50" tabindex="' + tabIndex + '" type="text" name="dataA' + idx + '" id="dataA' + idx + '"';
		tabIndex++;
		if (pageElement.dataA) { myHTML += ' value="' + pageElement.dataA + '"'; }
		myHTML += '></tr>';
		myHTML += '<tr><td>Go To:</td><td><select tabindex="' + tabIndex + '" name="dataB' + idx + '" id="dataB' + idx + '">';
		tabIndex++;
		//use the tree view to loop through the nodes and build a select list of every "page"
		for (var i = 0; i < tree.getRoot().children.length; i++) {
			var myChildNode = tree.getRoot().children[i];
			//set the option value's description to the node label
			//unless the node is the selected node, then it's label will be bold
			//so we need to get the name from the currentPage object
			var myNodeName = myChildNode.label;
			if (myChildNode.index == currentNodeIndex) {
				myNodeName = currentPage.name;
			}
			myHTML += '  <option value="' + myChildNode.value + '"';
			if (pageElement.dataB == myChildNode.value) {
				myHTML += ' SELECTED';
			}
			myHTML += '>' + myNodeName;
		}
		myHTML += '</select></td></tr></table>';
	}
	else {
		alert("tried to add pageElement of unknown type: " + pageElement.dataType);
	}
	myHTML += '</div><div class="pageElementMenu"><table><tr>';
	myHTML += "<td>Don't forget to save!</td>";
	myHTML += '<td>' + divButtonFunction('up'+idx, 'icon-elUp') + '</td>';
	myHTML += '<td>' + divButtonFunction('disable'+idx, 'icon-elDelete') + '</td>';
	myHTML += '<td>' + divButtonFunction('down'+idx, 'icon-elDown') + '</td>';
	myHTML += '<td>' + divButtonFunction('save'+idx, 'icon-save') + '</td>';
	myHTML += '</tr></table></div>';

	myHTML += '<div class="belowWorkArea" id="belowElWorkArea' + idx + '"></div>';
	myHTML += '<hr>';
	newDiv.innerHTML += myHTML;
	domIdToKeyMap['up' + idx] = pageElement.key;
	domIdToKeyMap['disable' + idx] = pageElement.key;
	domIdToKeyMap['delete' + idx] = pageElement.key;
	domIdToKeyMap['down' + idx] = pageElement.key;
	domIdToKeyMap['save' + idx] = pageElement.key;
	domIdToNodeIndexMap['up' + idx] = idx;
	domIdToNodeIndexMap['disable' + idx] = idx;
	domIdToNodeIndexMap['delete' + idx] = idx;
	domIdToNodeIndexMap['down' + idx] = idx;
	domIdToNodeIndexMap['save' + idx] = idx;
	YAHOO.util.Event.addListener("up" + idx, "click", pageElUp);
	YAHOO.util.Event.addListener("disable" + idx, "click", pageElDisable);
	YAHOO.util.Event.addListener("down" + idx, "click", pageElDown);
	YAHOO.util.Event.addListener("save" + idx, "click", pageElSave);
	new YAHOO.widget.Tooltip("tooltipUp", { showdelay: 500, context:"up" + idx, text:"Move Up"} );
	new YAHOO.widget.Tooltip("tooltipDisable", { showdelay: 500, context:"disable" + idx, text:"Disable Element"} );
	new YAHOO.widget.Tooltip("tooltipDown", { showdelay: 500, context:"down" + idx, text:"Move Down"} );
	new YAHOO.widget.Tooltip("tooltipSave", { showdelay: 500, context:"save" + idx, text:"Save"} );

	//set the focus to the dropdown box if its there (for choice elements), so the screen moves down a bit further
	if (!pageElement.dataA && pageElement.dataType != 2) {
		//set the focus to the newly created text box
		focusObject('dataB' + idx);
		focusObject('dataA' + idx);
	}
	else if (pageElement.dataType == 1)
	{
		focusObject('dataA' + idx);
	}
	//if the page element is already disabled, we need to disable it in the html
	if (pageElement.enabled && pageElement.enabled == 0) { markPageElAsDisabled(idx); }
}

var focusObject = function (focusObject) {
	var focusOBJ = YAHOO.util.Dom.get(focusObject);
	if (focusOBJ) { focusOBJ.focus(); }	
}

var pageElUp = function(e) {
	var obj = YAHOO.util.Event.getTarget(e);
	//get key of current page element
	var myKey = domIdToKeyMap[obj.id];
	var myPage = tree.getNodeByIndex(currentNodeIndex);
	var myChildren = myPage.children;
	var newOrder = 0;
	for (var i = 0; i < myChildren.length; i++) {
		childNodeIndex = myChildren[i].index;
		nodeKey = nodeToKeyMap[childNodeIndex];
		//alert("pageUP " + i + " " + myChildren[i] + " " + nodeKey);
		if (nodeKey == myKey) {
			//alert("this is the node we clicked on");
			//this is the page element that we clicked on
			//get the previous sibling, remove this node from the tree, then insert it before the previous sibling
			var myNode = myChildren[i];
			var previousSibling = myNode.previousSibling;
			if (previousSibling) {
				tree.removeNode(myNode, false);
				//alert("inserting node(" + myNode + ") before old node(" + previousSibling + ")");
				var insertedNode = myNode.insertBefore(previousSibling);
				//alert(insertedNode);
				//now we just need to re-order the html DIVs so the work area display is adjusted with the new order
				//DIV ID is DIV + node index
				//get the previous DIV, remove this DIV from the parent DIV, then insert it before the previous DIV
				myDiv = YAHOO.util.Dom.get('DIV' + childNodeIndex);
				myParentDiv = myDiv.parentNode;
				myPreviousDiv = YAHOO.util.Dom.getPreviousSibling(myDiv);
				if (myPreviousDiv) {
					removedNode = myParentDiv.removeChild(myDiv);
					myParentDiv.insertBefore(removedNode, myPreviousDiv);
				}
			}
			var myHTML = "myElKey=" + myKey + "&myNewOrder=" + (newOrder-1);
			YAHOO.util.Connect.asyncRequest('POST', '/movePageElement', moveCallbacks, myHTML);
			break;
		}
		newOrder++;
	}
	tree.draw();
}
var moveCallbacks = {
	success : function (o) {
		YAHOO.log("RAW JSON DATA: " + o.responseText);
		// Process the JSON data returned from the server
		var pageElement = [];
		try {
			pageElement = YAHOO.lang.JSON.parse(o.responseText);
		}
		catch (x) {
			alert("JSON Parse failed! " + x);
			return;
		}
		YAHOO.log("PARSED DATA: " + YAHOO.lang.dump(pageElement.key + ' ' + pageElement.name));
		{
		}
	},
	failure : function (o) {
		alert("MovePageElement was not successful.");
	},
	argument : { },
	timeout : 3000
}
var pageElDown = function(e) {
	var obj = YAHOO.util.Event.getTarget(e);
	//get key of current page element
	var myKey = domIdToKeyMap[obj.id];
	var myPage = tree.getNodeByIndex(currentNodeIndex);
	var myChildren = myPage.children;
	var newOrder = 0;
	for (var i = 0; i < myChildren.length; i++) {
		childNodeIndex = myChildren[i].index;
		nodeKey = nodeToKeyMap[childNodeIndex];
		if (nodeKey == myKey) {
			//this is the page element that we clicked on
			//get the next sibling, remove this node from the tree, then insert it after the next sibling
			var myNode = myChildren[i];
			var nextSibling = myNode.nextSibling;
			if (nextSibling) {
				tree.removeNode(myNode, false);
				myNode.insertAfter(nextSibling);
				//now we just need to re-order the html DIVs so the work area display is adjusted with the new order
				//DIV ID is DIV + node index
				//get the next DIV, remove this DIV from the parent DIV, then insert it after the next DIV
				myDiv = YAHOO.util.Dom.get('DIV' + childNodeIndex);
				myParentDiv = myDiv.parentNode;
				myNextDiv = YAHOO.util.Dom.getNextSibling(myDiv);
				if (myNextDiv) {
					removedNode = myParentDiv.removeChild(myDiv);
					myParentDiv.insertBefore(removedNode, myNextDiv.nextSibling);
				}
			}
			var myHTML = "myElKey=" + myKey + "&myNewOrder=" + (newOrder+1);
			YAHOO.util.Connect.asyncRequest('POST', '/movePageElement', moveCallbacks, myHTML);
			break;
		}
		newOrder++;
	}
	tree.draw();
}
var pageElDisable = function(e) {
	var obj = YAHOO.util.Event.getTarget(e);
	var myKey = domIdToKeyMap[obj.id];
	if (myKey) {
		var myHTML = "myElKey=" + myKey;
		pageElDisableCallbacks.argument.key = myKey
		pageElDisableCallbacks.argument.nodeIndex = keyToNodeMap[myKey].index;
		YAHOO.util.Connect.asyncRequest('POST', '/disablePageElement', pageElDisableCallbacks, myHTML);			
	}
	else {
		markPageElAsDisabled(domIdToNodeIndexMap[obj.id]);
	}
}
var markPageElAsDisabled = function(idx) {
	var newDiv = document.createElement('div');
	var belowWorkArea = YAHOO.util.Dom.get('belowElWorkArea' + idx);
	belowWorkArea.innerHTML = '';
	belowWorkArea.appendChild(newDiv);
	newDiv.innerHTML = '<table class="table2"><tr><td>This element is disabled. Delete it?<br>To re-enable, just save.</td><td class="myButton">' + divButtonFunction('delete'+idx, 'icon-delete') + '</td></tr></table>';
	//newDiv.innerHTML += '<br>To re-enable, just save.'
	YAHOO.util.Event.addListener("delete" + idx, "click", pageElDelete);
	new YAHOO.widget.Tooltip("tooltipDelete", { showdelay: 500, context:"delete" + idx, text:"Delete Element"} );		
}
var pageElDisableCallbacks = {
	success : function (o) {
		YAHOO.log("RAW JSON DATA: " + o.responseText);
		var m = [];
		try { m = YAHOO.lang.JSON.parse(o.responseText); }
		catch (x) {
			alert("JSON Parse failed! " + x);
			return;
		}
		markPageElAsDisabled(o.argument.nodeIndex);
	},
	failure : function (o) {
		alert("disablePageElement was not successful.");
	},
	argument : {
		"nodeIndex": null,
		"key": null
	},
	timeout : 3000
}
var removePageElementNodeFromTree = function(nodeIndex) {
	var myNode = tree.getNodeByIndex(nodeIndex);
	if (myNode) {
		tree.removeNode(myNode, true);
	}
	tree.draw();
	var pageElementsWorkArea = YAHOO.util.Dom.get('pageElementsWorkArea');
	var myDiv = YAHOO.util.Dom.get('DIV' + nodeIndex);
	pageElementsWorkArea.removeChild(myDiv);
}
var pageElDelete = function(e) {
	var obj = YAHOO.util.Event.getTarget(e);
	var myKey = domIdToKeyMap[obj.id];
	if (myKey) {
		var myHTML = "myElKey=" + myKey;
		pageElDeleteCallbacks.argument.key = myKey
		pageElDeleteCallbacks.argument.nodeIndex = keyToNodeMap[myKey].index;
		YAHOO.util.Connect.asyncRequest('POST', '/deletePageElement', pageElDeleteCallbacks, myHTML);
	}
	else {
		var nodeIndex = domIdToNodeIndexMap[obj.id];
		removePageElementNodeFromTree(nodeIndex);
	}
}
var pageElDeleteCallbacks = {
	success : function (o) {
		YAHOO.log("RAW JSON DATA: " + o.responseText);
		// Process the JSON data returned from the server
		var m = [];
		try {
			m = YAHOO.lang.JSON.parse(o.responseText);
		}
		catch (x) {
			alert("JSON Parse failed! " + x);
			return;
		}
		YAHOO.log("PARSED DATA: " + YAHOO.lang.dump(m.key + ' ' + m.name));
		removePageElementNodeFromTree(o.argument.nodeIndex);
	},
	failure : function (o) {
		alert("deletePageElement was not successful.");
	},
	argument : {
		"nodeIndex": null,
		"key": null
	},
	timeout : 3000
}
var pageElSave = function(e) {
	var obj = YAHOO.util.Event.getTarget(e);
	var myPageElKey = domIdToKeyMap[obj.id];
	var myPageKey = nodeToKeyMap[currentNodeIndex];
	var myPageElNodeIndex = domIdToNodeIndexMap[obj.id];
	var myHTML = "myPageKey=" + myPageKey;
	if (myPageElKey) {
		//existing node
		myHTML += "&myPageElKey=" + myPageElKey;
		pageElSaveCallbacks.argument.key = myPageElKey
	}
	else {
		//new node
		var myNode = tree.getNodeByIndex(myPageElNodeIndex);
		myHTML += "&elementType=" + myNode.value.dataType;
			+ "&pageOrder=" + myNode.parent.children.length;
	}
	pageElSaveCallbacks.argument.nodeIndex = myPageElNodeIndex;
	pageElSaveCallbacks.argument.pageKey = myPageKey;
	pageElSaveCallbacks.argument.pageNodeIndex = currentNodeIndex;
	var dataA = YAHOO.util.Dom.get('dataA' + myPageElNodeIndex);
	if (dataA) {
		myHTML += "&dataA=" + escape(dataA.value);		
	}
	var dataB = YAHOO.util.Dom.get('dataB' + myPageElNodeIndex);
	if (dataB) {
		myHTML += "&dataB=" + escape(dataB.value);		
	}
	YAHOO.util.Connect.asyncRequest('POST', '/savePageElement', pageElSaveCallbacks, myHTML);
}
var pageElSaveCallbacks = {
	success : function (o) {
		YAHOO.log("RAW JSON DATA: " + o.responseText);
		// Process the JSON data returned from the server
		var pageElement = [];
		try {
			pageElement = YAHOO.lang.JSON.parse(o.responseText);
		}
		catch (x) {
			alert("JSON Parse failed! " + x);
			return;
		}
		YAHOO.log("PARSED DATA: " + YAHOO.lang.dump(pageElement.key + ' ' + pageElement.name));
		{
			var belowWorkArea = YAHOO.util.Dom.get('belowElWorkArea' + o.argument.nodeIndex);
			belowWorkArea.innerHTML = 'Saved.';
			var myTreeNode = tree.getNodeByIndex(o.argument.nodeIndex);
			addOrUpdateChildNode(pageElement.dataA, pageElement.dataType, null, pageElement, myTreeNode);
		}
	},
	failure : function (o) {
		alert("savePageElement was not successful.");
	},
	argument : {
		"nodeIndex": null,
		"key": null,
		"pageNodeIndex": null,
		"pageKey": null
	},
	timeout : 3000
}

//ADD PAGE ELEMENTS TO THE ADVENTURE PAGE
var setupWorkArea = function() {
	//look at the current node index and see if there are any child elements
	//if there are, that means we already have page elements
	//if not, we should display the getting started text
	var workArea = YAHOO.util.Dom.get('workArea');
	workArea.innerHTML = '<div id="pageElementsWorkArea"></div>';
	YAHOO.util.Event.addListener("addPageElementText", "click", addPageElement);
	YAHOO.util.Event.addListener("addPageElementImage", "click", addPageElement);
	YAHOO.util.Event.addListener("addPageElementChoice", "click", addPageElement);
	//new YAHOO.widget.Tooltip("tooltipAddText", { showdelay: 500, context:"addPageElementText", text:"Add A Text Page Element"} );
	//new YAHOO.widget.Tooltip("tooltipAddImage", { showdelay: 500, context:"addPageElementImage", text:"Add An Image Page Element"} );
	//new YAHOO.widget.Tooltip("tooltipAddChoice", { showdelay: 500, context:"addPageElementChoice", text:"Add A Choice Page Element"} );
	addPageElementsHelper();	
}	
var addPageElement = function(e) {
	var targetObj = YAHOO.util.Event.getTarget(e);
	var dataType = pageElementIdToTypeMap[targetObj.id];
	if (!dataType) {
		targetObj = targetObj.parentNode;
		dataType = pageElementIdToTypeMap[targetObj.id];
	}
	var myNode = tree.getNodeByIndex(currentNodeIndex);
	var pageElement = {
		"dataType": dataType
	}
	var newNodeIndex = addOrUpdateChildNode("New " + pageElementTypeToNameMap[dataType], dataType, myNode, pageElement);
	var newNode = tree.getNodeByIndex(newNodeIndex);
	addPageElementToWorkArea(pageElement, newNodeIndex);
}

var addPageElementCallbacks = {
	success : function (o) {
		YAHOO.log("RAW JSON DATA: " + o.responseText);
		// Process the JSON data returned from the server
		var m = [];
		try {
			m = YAHOO.lang.JSON.parse(o.responseText);
		}
		catch (x) {
			alert("JSON Parse failed!");
			alert(x);
			return;
		}
		YAHOO.log("PARSED DATA: " + YAHOO.lang.dump(m.key + ' ' + m.name));
	},
	failure : function (o) {
		alert("addPageElement was not successful.");
	},
	argument : { "nodeIndex": null },
	timeout : 3000
}
var getDescForChildNode = function(description, datatype) {
	var nodeDesc = null;
	if (description) {
		var prefix = 't: ';
		if (datatype == 2) { prefix = 'i: '; }
		else if (datatype == 3) { prefix = 'c: '; }
		nodeDesc = description.substr(0, 9);
		nodeDesc = prefix + nodeDesc.replace(/\n/g, ' ');
	}
	else {
		nodeDesc = pageElementTypeToNameMap[datatype];
	}
	return nodeDesc;		
}
var addOrUpdateChildNode = function(description, datatype, node, pageElement, currentNode) {
	//pageElement is from the data model, adventureModel.py
	var nodeDesc = getDescForChildNode(description, datatype);
	if (!currentNode) {
		currentNode = new YAHOO.widget.TextNode(nodeDesc, node, true);
	}
	else {
		currentNode.label = nodeDesc;
	}
	if (pageElement) {
		nodeToKeyMap[currentNode.index] = pageElement.key;
		keyToNodeMap[pageElement.key] = currentNode;
		currentNode.value = pageElement;
	}
	tree.draw()
	return currentNode.index;
}

var deletePage = function(e) {
	resetWorkArea(null, 1);
	if (!currentPage.key) {
		return;
	}
	var obj = YAHOO.util.Dom.get('workArea');
	obj.innerHTML = "<table class=\"table1\"><tr height=\"50\"><td>Are you sure you want to delete page \"" + currentPage.name + "\"?<br>This operation cannot be undone.</td><td class=\"myButton\">" +  divButtonFunction('deletePageSubmit', 'icon-delete') + "Delete</td></tr></table>";
	YAHOO.util.Event.addListener("deletePageSubmit", "click", deletePageSubmit);
	//new YAHOO.widget.Tooltip("tooltipDeletePageSubmit", { showdelay: 500, context:"deletePageSubmit", text:"Delete This Page For Good"} );
}
var addPage = function(e) {
	//obj = YUE.getTarget(e);
	resetWorkArea(null, 1, currentNodeIndex);
	if (currentPage.key) {
		var curPage = YAHOO.util.Dom.get('currentPage');
		curPage.innerHTML = '';
	}
	currentPage.name = '';
	currentPage.key = '';
	currentPage.nodeIndex = '';
	currentNodeIndex = '';
	addOrUpdatePage();
}
var editPage = function(e) {
	if (currentPage.key) {
		addOrUpdatePage();
	}
	else {
		//alert("no page selected");
	}
}
var addOrUpdatePage = function(pageKey) {
	resetWorkArea(null, 1);
	var pageNameHTML = '';
	var pageKeyHTML = '';
	if (currentPage.key) {
		pageNameHTML = ' value="' + currentPage.name + '"';
	}
	var obj = YAHOO.util.Dom.get('workArea');
	obj.innerHTML = '<form id="addPageForm" method="post" action="javascript:addPageSubmitFunction()"><table class="table1"><tr><td>Name of page:<br><input type="text" id="newPageName"' + pageNameHTML + '></td><td class="myButton">' + divButtonFunction('addPageSubmit', 'icon-save') + 'Save</td></tr></table></form>';
	YAHOO.util.Event.addListener("addPageSubmit", "click", addPageSubmit);
	YAHOO.util.Event.on('addPageForm', 'submit', function(e) {
		YAHOO.util.Event.stopEvent(e);
		addPageSubmit();
	});
	YAHOO.util.Dom.get('newPageName').focus();
	//new YAHOO.widget.Tooltip("tooltipAddPageSubmit", { showdelay: 500, context:"addPageSubmit", text:"Save"} );
}
		
var addPageSubmit = function(e) {
	//myAdventureKey myPageKey pageName
	var pageKeyHTML = '';
	if (currentPage.key) {
		pageKeyHTML = "&myPageKey=" + currentPage.key;
	}
	addPageCallbacks.argument.nodeIndex = currentNodeIndex;
	YAHOO.util.Connect.asyncRequest('POST', '/addPage', addPageCallbacks,
		"myAdventureKey=" + adventureKey
		+ pageKeyHTML
		+ "&pageName=" + YAHOO.util.Dom.get('newPageName').value
	);
}
var addPageCallbacks = {
	success : function (o) {
		YAHOO.log("RAW JSON DATA: " + o.responseText);
		// Process the JSON data returned from the server
		var m = [];
		try {
			m = YAHOO.lang.JSON.parse(o.responseText);
		}
		catch (x) {
			alert("JSON Parse failed!");
			alert(x);
			return;
		}
		YAHOO.log("PARSED DATA: " + YAHOO.lang.dump(m.key + ' ' + m.name));
		{
			//alert(m.key + ' ' + m.name);
			//alert(currentNodeIndex + '|' + o.argument.nodeIndex);
			var myNode = tree.getNodeByIndex(o.argument.nodeIndex);
			if (myNode) {
				myNode.label = m.name;
			}
			else {
				myNode = new YAHOO.widget.TextNode(m.name, tree.getRoot(), false);
				myNode.value = m.key;
			}
			currentPage.name = myNode.label;
			nodeClick(myNode);
		}
	},
	failure : function (o) {
		alert("addPage was not successful.");
	},
	argument : { "nodeIndex": null },
	timeout : 3000
}

var deletePageSubmit = function(e) {
	//alert("addPageSubmit");
	//myAdventureKey myPageKey pageName
	var pageKeyHTML = "myPageKey=" + currentPage.key;
	deletePageCallbacks.argument.nodeIndex = currentNodeIndex;
	YAHOO.util.Connect.asyncRequest('POST', '/deletePage', deletePageCallbacks, pageKeyHTML);
}
var deletePageCallbacks = {
	success : function (o) {
		YAHOO.log("RAW JSON DATA: " + o.responseText);
		// Process the JSON data returned from the server
		var m = [];
		try {
			m = YAHOO.lang.JSON.parse(o.responseText);
		}
		catch (x) {
			alert("JSON Parse failed!");
			alert(x);
			return;
		}
		YAHOO.log("PARSED DATA: " + YAHOO.lang.dump(m.key + ' ' + m.name));
		{
			var myNode = tree.getNodeByIndex(o.argument.nodeIndex);
			if (myNode) {
				tree.removeNode(myNode, true);
			}
		}
		var curPage = YAHOO.util.Dom.get('currentPage');
		curPage.innerHTML = '';
		currentPage.key = null;
		currentPage.page = null;
		currentPage.nodeIndex = null;
		currentNodeIndex = null;
		tree.draw();
		resetWorkArea("Page deleted.");
	},
	failure : function (o) {
		alert("removePage was not successful.");
	},
	argument : { "nodeIndex": null },
	timeout : 3000
}

// Define the callbacks for the asyncRequest
var callbacks = {
	success : function (o) {
		YAHOO.log("RAW JSON DATA: " + o.responseText);
		// Process the JSON data returned from the server
		var messages = [];
		try {
			messages = YAHOO.lang.JSON.parse(o.responseText);
		}
		catch (x) {
			alert("JSON Parse failed!");
			alert(x);
			return;
		}
		YAHOO.log("PARSED DATA: " + YAHOO.lang.dump(messages));
		tree = new YAHOO.widget.TreeView("treeDiv1");
		// The returned data was parsed into an array of objects.
		// Add a P element for each received message
		for (var i = 0, len = messages.length; i < len; ++i) {
			var m = messages[i];
			//m.name m.key
			var tmpNode = new YAHOO.widget.TextNode(m.name, tree.getRoot(), true);
			tmpNode.value = m.key;
			numPages++;
			for (var x = 0, xLen = m.elements.length; x < xLen; ++x) {
				var mm = m.elements[x];
				//this is how you build child nodes
				//new YAHOO.widget.TextNode("blah", tmpNode, true);
				// mm is the page element object from the data model
				addOrUpdateChildNode(mm.dataA, mm.dataType, tmpNode, mm);
			}
		}
		tree.draw();
		resetWorkArea();

		// Expand and collapse happen prior to the actual expand/collapse,
		// and can be used to cancel the operation
		tree.subscribe("expand", function(node) {
			// return false to cancel the expand
			return true;
		});

		tree.subscribe("collapse", function(node) {
			if (labelClick) {
				labelclick = false;
				return false;
			}
			labelClick = false;
			return true;
		});
		//tree.subscribe("clickEvent", function(node) {
		//	alert("clickEvent");
		//});
		// Trees with TextNodes will fire an event for when the label is clicked:
		tree.subscribe("labelClick", function(node) {
			nodeClick(node);
		});
       },

	failure : function (o) {
		if (!YAHOO.util.Connect.isCallInProgress(o)) {
			alert("Async call failed!");
		}
	},		
	timeout : 3000
}
var nodeClick = function(node) {
	labelClick = true;
	if (node.parent.toString() != "RootNode") {
		node = node.parent;
		if (node.parent.toString() != "RootNode") {
			return;
		}
	}
	tabIndex = 1;
	YAHOO.log(node.index + " label was clicked", "info", "example");
	resetWorkArea(null, 1, currentNodeIndex);
	var curPage = YAHOO.util.Dom.get('currentPage');
	curPage.innerHTML = node.label;
	currentPage.key = node.value;
	currentPage.name = node.label;
	currentPage.nodeIndex = node.index;
	currentNodeIndex = node.index;
	node.label = "<b>" + node.label + "</b>";
	nodeToKeyMap[node.index] = node.value;
	setupWorkArea();
	for (var x = 0; x < node.children.length; x++) {
		var childNode = node.children[x];
		//workAreaElementCount = workAreaElements.push(childNode.value);
		addPageElementToWorkArea(childNode.value, childNode.index);
	}
	tree.draw();		
}

//function to initialize the tree:
function treeInit() {
	// Make the call to the server for JSON data
	YAHOO.util.Connect.asyncRequest('GET',"/getPages?myAdventureKey=" + adventureKey, callbacks);
	YAHOO.util.Event.addListener("deletePage", "click", deletePage);
	YAHOO.util.Event.addListener("addPage", "click", addPage);
	YAHOO.util.Event.addListener("editPage", "click", editPage);
	resetWorkArea();
	//new YAHOO.widget.Tooltip("tooltipDeletePage", { showdelay: 500, context:"deletePage", text:"Delete This Page"} );
	//new YAHOO.widget.Tooltip("tooltipAddPage", { showdelay: 500, context:"addPage", text:"Add A New Page"} );
	//new YAHOO.widget.Tooltip("tooltipEditPage", { showdelay: 500, context:"editPage", text:"Edit This Page's Name"} );
}