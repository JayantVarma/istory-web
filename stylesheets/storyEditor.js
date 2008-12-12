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

//create the image uploader object from the swf
//it has to be global
YAHOO.widget.Uploader.SWFURL = "uploader/uploader.swf";
var uploader = new YAHOO.widget.Uploader( "uploaderUI", "uploader/selectFileButton.png" );
//add handlers for the image uploader
uploader.addListener('contentReady', handleContentReady);
uploader.addListener('fileSelect',onFileSelect)
uploader.addListener('uploadStart',onUploadStart);
uploader.addListener('uploadProgress',onUploadProgress);
uploader.addListener('uploadCancel',onUploadCancel);
uploader.addListener('uploadComplete',onUploadComplete);
uploader.addListener('uploadCompleteData',onUploadResponse);
uploader.addListener('uploadError', onUploadError);

var resetWorkArea = function(updateStr, clear, nodeIndex) {
	var obj = YAHOO.util.Dom.get('workArea');
	obj.innerHTML = "";
	obj.className = null;
	if (updateStr) {
		obj.className = "workArea";
		obj.innerHTML = updateStr;
	}
	else if (!numPages) {
		obj.className = "workArea";
		obj.innerHTML = "Add a page to get started.";
	}
	else if (!clear) {
		obj.className = "workArea";
		obj.innerHTML = "Click on a page to work on it.";
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

//create and add the page element editing stuff to the work area
var addPageElementToWorkArea = function(pageElement, idx) {
	//idx is the node.index of the page element in the tree view
	var pageElementsWorkArea = YAHOO.util.Dom.get('pageElementsWorkArea');
	var newDiv = document.createElement('div');
	newDiv.id = "DIV" + idx;
	pageElementsWorkArea.appendChild(newDiv);
	//alert(pageElement.dataType);
	var myHTML = '<table><tr>';
	myHTML += '<td>';
	myHTML += divButtonFunction('up'+idx, 'icon-elUp');
	myHTML += divButtonFunction('disable'+idx, 'icon-elDelete');
	myHTML += divButtonFunction('down'+idx, 'icon-elDown');
	myHTML += divButtonFunction('save'+idx, 'icon-save');
	myHTML += '</td><td class="tdCenter">';
	if (pageElement.dataType == 1) {
		//text
		myHTML += '<textarea tabindex="' + tabIndex + '" id="dataA' + idx + '" name="dataA' + idx + '" rows="15" cols="60">';
		tabIndex++;
		if (pageElement.dataA) { myHTML += pageElement.dataA; }
		myHTML += '</textarea>';
	}
	else if (pageElement.dataType == 2) {
		//image
		//add the image uploader HTML
		var uploaderHTML = YAHOO.util.Dom.get('uploader');
		myHTML += uploaderHTML.innerHTML;
	}
	else if (pageElement.dataType == 3) {
		//choice
		myHTML += '<table class="table3"><tr><td>Choice Description:</td><td><input tabindex="' + tabIndex + '" type="text" name="dataA' + idx + '" id="dataA' + idx + '"';
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
	myHTML += '<div class="titleTD2" id="belowElWorkArea' + idx + '" style="text-align: center"></div>';
	myHTML += '</td></tr></table><hr>';
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

// THIS IS ALL FOR THE IMAGE UPLOADER
function handleContentReady () {
	// Allows the uploader to send log messages to trace, as well as to YAHOO.log
	uploader.setAllowLogging(true);
	
	// Restrict selection to a single file (that's what it is by default,
	// just demonstrating how).
	uploader.setAllowMultipleFiles(false);
	
	// New set of file filters.
	var ff = new Array({description:"Images", extensions:"*.jpg;*.png;*.gif"});
	                   //{description:"Videos", extensions:"*.avi;*.mov;*.mpg"});
	                   
	// Apply new set of file filters to the uploader.
	uploader.setFileFilters(ff);
}
var fileID;
function onFileSelect(event) {
	for (var item in event.fileList) {
	    if(YAHOO.lang.hasOwnProperty(event.fileList, item)) {
			YAHOO.log(event.fileList[item].id);
			fileID = event.fileList[item].id;
		}
	}
	uploader.disable();
	
	var filename = document.getElementById("fileName");
	filename.innerHTML = event.fileList[fileID].name;
	
	var progressbar = document.getElementById("progressBar");
	progressbar.innerHTML = "";
}
function upload() {
	if (fileID != null) {
		uploader.upload(fileID, "http://www.yswfblog.com/upload/upload_simple.php");
		fileID = null;
	}
}
function handleClearFiles() {
	uploader.clearFileList();
	uploader.enable();
	fileID = null;
}
function onUploadProgress(event) {
	var prog = Math.round(300*(event["bytesLoaded"]/event["bytesTotal"]));
	var progbar = "<div style=\"background-color: #f00; height: 5px; width: " + prog + "px\"/>";
	var progressbar = document.getElementById("progressBar");
	progressbar.innerHTML = progbar;
}
function onUploadComplete(event) {
	uploader.clearFileList();
	uploader.enable();
	var progbar = "<div style=\"background-color: #f00; height: 5px; width: 300px\"/>";
	var progressbar = document.getElementById("progressBar");
	progressbar.innerHTML = progbar;
}
function onUploadStart(event) {	
}
function onUploadError(event) {
}
function onUploadCancel(event) {
}
function onUploadResponse(event) {
}
//DONE WITH IMAGE UPLOADER




var pageElUp = function(e) {
	alert('pageElUp');
}
var pageElDown = function(e) {
	alert('pageElDown');
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
	var workArea = YAHOO.util.Dom.get('workArea');
	var pageWorkArea = YAHOO.util.Dom.get('pageWorkArea');
	workArea.innerHTML = pageWorkArea.innerHTML;
	YAHOO.util.Event.addListener("addPageElementText", "click", addPageElement);
	YAHOO.util.Event.addListener("addPageElementImage", "click", addPageElement);
	YAHOO.util.Event.addListener("addPageElementChoice", "click", addPageElement);
	//new YAHOO.widget.Tooltip("tooltipAddText", { showdelay: 500, context:"addPageElementText", text:"Add A Text Page Element"} );
	//new YAHOO.widget.Tooltip("tooltipAddImage", { showdelay: 500, context:"addPageElementImage", text:"Add An Image Page Element"} );
	//new YAHOO.widget.Tooltip("tooltipAddChoice", { showdelay: 500, context:"addPageElementChoice", text:"Add A Choice Page Element"} );

}	
var addPageElement = function(e) {
	var targetObj = YAHOO.util.Event.getTarget(e);
	if (!targetObj.id) {
		targetObj = targetObj.parentNode;
	}
	var dataType = pageElementIdToTypeMap[targetObj.id];
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
	obj.innerHTML = '<form id="addPageForm" method="post" action="javascript:addPageSubmitFunction()"><table class="table1"><tr height="50"><td class="titleTD2">Name of page:<br><input type="text" id="newPageName"' + pageNameHTML + '></td><td class="myButton">' + divButtonFunction('addPageSubmit', 'icon-save') + 'Save</td></tr></table></form>';
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