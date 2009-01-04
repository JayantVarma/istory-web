//Add an onDOMReady handler to build the tree when the document is ready
YAHOO.util.Event.onDOMReady(treeInit);

var YUD = YAHOO.util.Dom, YUE = YAHOO.util.Event, YUC = YAHOO.util.Connect;

//if there is no console, set it to null
try { console.log('init console... done'); } catch(e) { console = { log: function() {} } }

//global variable to allow console inspection of tree:
var tree;

//we also expect the variable MY_ADVENTURE_KEY to be set from the footer
var adventureKey = '';
if (MY_ADVENTURE_KEY) {
	adventureKey = MY_ADVENTURE_KEY;
}
var myError = '';
if (MY_ERROR) {
	myError = MY_ERROR;
}

var loadingCounter = 0;
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
var imageCroppers = {};
var waitingForPage;

//cache for storing user images
var imgCache = {};

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

function collapse() {
	tree.collapseAll();
}

var tdButtonFunction = function(id, iconName) {
	return '<td id="TD' + id + '" title="pageElMenu" class="iconBG-dark2"><div title="' + iconName + '" class="' + iconName + '" id="' + id + '"></div></div>';
}
var divButtonFunction = function(id, iconName) {
	return '<div title="' + iconName + '" class="' + iconName + '" id="' + id + '"></div>';
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

var disableIcons = function(disableAll)
{
	//console.log("disabling icons");
	disableDiv('addPageElementText');
	disableDiv('addPageElementImage');
	disableDiv('addPageElementChoice');
	disableDiv('deletePage');
	disableDiv('editPage');
	if (disableAll) {
		disableDiv('addPage');
		disableDiv('playStory');
	}
}
var enableIcons = function()
{
	if (loadingCounter > 0) { return; }
	//console.log("enabling icons");
	enableDiv('addPageElementText');
	enableDiv('addPageElementImage');
	enableDiv('addPageElementChoice');
	enableDiv('deletePage');
	enableDiv('editPage');
	enableDiv('addPage');
	enableDiv('playStory');
}

var eventIconMO = function(e) {
	if (this.id) {
		//console.log(this.id);
		var override = false;
		if (this.title == 'pageElMenu') { override = true; }
		iconMO(this, override);
	}
}
var eventIconMOreset = function(e) {
	if (this.id) {
		var override = false;
		if (this.title == 'pageElMenu') { override = true; }
		iconMOreset(this, override);
	}
}

var iconMO = function(td, useValue) {
	//console.log("iconMO: " + this + " " + this.id);
	if (!td.id) { return }
	if (loadingCounter > 0) { return }
	if (currentNodeIndex || td.id == 'addPage' || td.id == 'playStory') {
		var icon = td.firstChild;
		if (useValue) {
			//this is for the page element menu, we store the normal class in the title attribute
			td.className = 'iconBG-light2';
			icon.className = icon.className + 'MO';
			//console.log("MO set: " + td.className + ', ' + icon.className + ', ' + icon.title);
		}
		else {
			//this is for the normal menu buttons
			td.className = 'iconBG-light';
			icon.className = icon.id + 'MO';
			//console.log("MO set: " + td.className + ', ' + icon.className);
		}
	}
}
var iconMOreset = function(td, useValue) {
	if (!td.id) { return }
	if (loadingCounter > 0) { return }
	if (currentNodeIndex || td.id == 'addPage' || td.id == 'playStory') {
		var icon = td.firstChild;
		if (useValue) {
			//this is for the page element menu, we store the normal class in the title attribute
			td.className = 'iconBG-dark2';
			if (icon.className.substr((icon.className.length-2), 2) == 'MO') {
				icon.className = icon.className.substr(0, (icon.className.length-2) );
			}
			if (icon.className.substr((icon.className.length-1), 1) == 'D') {
				icon.className = icon.className.substr(0, (icon.className.length-1) );
			}
			//console.log("MO reset: " + td.className + ', ' + icon.className + ', ' + icon.title);
		}
		else {
			//this is for the normal menu buttons
			td.className = 'iconBG-dark';
			icon.className = icon.id;
		}
	}
}
var iconDisable = function(td) {
	td.className = 'iconBG-disabled';
	var icon = td.firstChild;
	if (icon.className.substr((icon.className.length-2), 2) == 'MO') {
		icon.className = icon.className.substr(0, (icon.className.length-2) );
	}
	if (icon.className.substr((icon.className.length-1), 1) == 'D') {
		icon.className = icon.className.substr(0, (icon.className.length-1) );
	}
	icon.className = icon.id + 'D';
}

var disableDivPageEl = function(div) {
	div.className = 'iconBG-disabled2';
	var icon = div.firstChild;
	if (icon.className.substr((icon.className.length-2), 2) == 'MO') {
		icon.className = icon.className.substr(0, (icon.className.length-2) );
	}
	if (icon.className.substr((icon.className.length-1), 1) == 'D') {
		icon.className = icon.className.substr(0, (icon.className.length-1) );
	}
	icon.className = icon.className + 'D';
}
var enableDivPageEl = function(div) {
	iconMOreset(div, true);
}
var disableDiv = function(name) {
	var td = YAHOO.util.Dom.get(name);
	iconDisable(td);
}
var enableDiv = function(name) {
	var td = YAHOO.util.Dom.get(name);
	iconMOreset(td);
}

var playStory = function(e) {
	console.log("playStory");
	window.open('/playStory?myAdventureKey=' + MY_ADVENTURE_KEY + '&playLite=true', 'storyPlayer lite', 'toolbar=no,location=no,directories=no,status=yes,menubar=no,copyhistory=no,scrollbars=yes,resizable=yes,width=400,height=800');
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
		var imageRef = '';
		var imageName = '';
		var pageElKey = '';
		var orVariable = '';
		//if the page element already exists, show the current image
		var doesImageExist = false;
		if (pageElement.imageRef) {
			doesImageExist = true;
			imageRef = pageElement.imageRef;
			imageName = pageElement.dataA;
		}
		if (pageElement.key) {
			pageElKey = pageElement.key;
		}
		myHTML += '<div id="img' + idx + '">';
		myHTML += setupImage(idx, pageElement.imageRef, pageElement.dataA, doesImageExist);
		myHTML += '</div>';
		//start the form only if we don't already have an image (it's a new page element)
		if (!pageElKey) {
			myHTML += '<div id="cropInfo' + idx + '"></div>';
			myHTML += '<form id="imageForm' + idx + '" action="/upload" enctype="multipart/form-data" method="post">';
			myHTML += '<table class="imageUploadForm">';
			//if there are any images in the img cache, show them as a list
			if (imgCache.length > 0) {
				orVariable = 'Or ';
				myHTML += '<tr><th>Select An Existing Image</th></tr>';
				myHTML += '<td><select id="imageList' + idx + '" name="imageList" onchange="imgListChanged(this,this.value,' + idx + ')">';
				myHTML += '<option value="">-- Image List --';
				for (var key in imgCache) {
					if (key == 'length') { continue; }
					myHTML += '<option value="' + key + '"';
					if (key == imageRef) {
						myHTML += ' SELECTED';
					}
					myHTML += '>' + imgCache[key];
				}
				myHTML += '</select></td></tr>';
				//myHTML += '<tr><td><input type="submit" value="Use Image"></td></tr>';
			}
			//make the upload a new image form
			myHTML += '<tr><th>' + orVariable + 'Upload A New Image</th></tr>';
			myHTML += '<tr><td><input id="imageData' + idx + '" type="file" name="imageData" /></td></tr>';
			myHTML += '<tr><td>Image name: <input id="imageName' + idx + '" type="text" name="imageName" value="' + imageName + '"/></td></tr>';
			myHTML += '<tr><td><input id="submit' + idx + '" type="submit" value="Use / Upload / Rename Image" onclick="this.disabled=true"></td></tr></table>';
			//also put the page key and page element order into the form
			myHTML += '<input id="myPageElKey' + idx + '" type="hidden" name="myPageElKey" value="' + pageElKey + '">';
			myHTML += '<input id="myPageKey' + idx + '" type="hidden" name="myPageKey" value="' + nodeToKeyMap[currentNodeIndex] + '">';
			myHTML += '<input id="myPageOrder' + idx + '" type="hidden" name="myPageOrder" value="' + pageElement.pageOrder + '">';
			myHTML += '<input id="imageRef' + idx + '" type="hidden" name="imageRef" value="' + imageRef + '">';
			myHTML += '</form>';
		}
	}
	else if (pageElement.dataType == 3) {
		//choice
		myHTML += '<table class="tableChoice"><tr><td>Choice Description:</td><td><input size="30" maxlength="70" tabindex="' + tabIndex + '" type="text" name="dataA' + idx + '" id="dataA' + idx + '"';
		tabIndex++;
		if (pageElement.dataA) { myHTML += ' value="' + pageElement.dataA + '"'; }
		myHTML += '></tr>';
		myHTML += '<tr><td>Go To:</td><td><select tabindex="' + tabIndex + '" name="dataB' + idx + '" id="dataB' + idx + '">';
		tabIndex++;
		myHTML += '  <option value="new">-- New Page --';
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
	myHTML += '</div><div class="pageElementMenu"><table id="elementMenu"><tr>';
	myHTML += "<th>Don't forget to save!</th>";
	myHTML += tdButtonFunction('up'+idx, 'icon-elUp');
	myHTML += tdButtonFunction('disable'+idx, 'icon-elDelete');
	myHTML += tdButtonFunction('down'+idx, 'icon-elDown');
	myHTML += tdButtonFunction('save'+idx, 'icon-save');
	myHTML += '<td width="32px"><div class="loadElement"><img src="/stylesheets/load.gif"></div></td>';
	myHTML += '</tr></table></div>';

	myHTML += '<div class="belowWorkArea" id="belowElWorkArea' + idx + '"></div>';
	myHTML += '<hr>';
	newDiv.innerHTML += myHTML;
	if (pageElement.key) {
		domIdToKeyMap['DIV' + idx] = pageElement.key;
		domIdToKeyMap['up' + idx] = pageElement.key;
		domIdToKeyMap['disable' + idx] = pageElement.key;
		domIdToKeyMap['delete' + idx] = pageElement.key;
		domIdToKeyMap['down' + idx] = pageElement.key;
		domIdToKeyMap['save' + idx] = pageElement.key;
	}
	domIdToNodeIndexMap['DIV' + idx] = idx;
	domIdToNodeIndexMap['up' + idx] = idx;
	domIdToNodeIndexMap['disable' + idx] = idx;
	domIdToNodeIndexMap['delete' + idx] = idx;
	domIdToNodeIndexMap['down' + idx] = idx;
	domIdToNodeIndexMap['save' + idx] = idx;
	YAHOO.util.Event.addListener("up" + idx, "click", pageElUp);
	YAHOO.util.Event.addListener("disable" + idx, "click", pageElDisable);
	YAHOO.util.Event.addListener("down" + idx, "click", pageElDown);
	YAHOO.util.Event.addListener("save" + idx, "click", pageElSave);

	YAHOO.util.Event.addListener('TDup'+idx, "mouseover", eventIconMO);
	YAHOO.util.Event.addListener('TDup'+idx, "mouseout", eventIconMOreset);
	YAHOO.util.Event.addListener('TDdisable'+idx, "mouseover", eventIconMO);
	YAHOO.util.Event.addListener('TDdisable'+idx, "mouseout", eventIconMOreset);
	YAHOO.util.Event.addListener('TDdown'+idx, "mouseover", eventIconMO);
	YAHOO.util.Event.addListener('TDdown'+idx, "mouseout", eventIconMOreset);
	YAHOO.util.Event.addListener('TDsave'+idx, "mouseover", eventIconMO);
	YAHOO.util.Event.addListener('TDsave'+idx, "mouseout", eventIconMOreset);

	new YAHOO.widget.Tooltip("tooltipUp", { showdelay: 500, context:"up" + idx, text:"Move Up"} );
	new YAHOO.widget.Tooltip("tooltipDisable", { showdelay: 500, context:"disable" + idx, text:"Disable Element"} );
	new YAHOO.widget.Tooltip("tooltipDown", { showdelay: 500, context:"down" + idx, text:"Move Down"} );
	new YAHOO.widget.Tooltip("tooltipSave", { showdelay: 500, context:"save" + idx, text:"Save"} );

	//set the focus to the dropdown box if its there (for choice elements), so the screen moves down a bit further
	if (pageElement.dataType == 2) {
		focusObject('imageName' + idx);
	}
	else if (!pageElement.dataA) {
		//set the focus to the newly created text box
		focusObject('dataB' + idx);
		focusObject('dataA' + idx);
	}
	else if (pageElement.dataType == 1)
	{
		focusObject('dataA' + idx);
	}
	
	//setup the image cropper buttons
	setupImageCropperButtons(idx);

	//if the page element is already disabled, we need to disable it in the html
	if (pageElement.enabled && pageElement.enabled == 0) { markPageElAsDisabled(idx); }
	
	//now that the HTML is on the page, setup the image upload event handlers
	//YAHOO.util.Event.addListener("submit" + idx, "click", uploadImage);
	YAHOO.util.Event.on('imageForm' + idx, 'submit', function(e) {
		//console.log('imageForm: SUBMIT stopped event' + idx);
		YAHOO.util.Event.stopEvent(e);
		uploadImage(idx);
	});
	YAHOO.util.Event.on('submit' + idx, 'click', function(e) {
		//console.log('imageForm: BUTTON stopped event ' + idx);
		YAHOO.util.Event.stopEvent(e);
		uploadImage(idx);
	});	
}

var setupImage = function(idx, imageRef, dataA, doesImageExist) {
	//console.log("setting up image: " + idx + ',' + imageRef + ',' + dataA);
	//we need to support images not existing when this html is created, so we hide it instead
	var imageURL = '';
	if (imageRef) { imageURL = '/images?imageKey=' + imageRef; }
	var style = '';
	if (!doesImageExist) { style = ' style="display:none"'; }
	return ('<br><img' + style + ' id="imageReal' + idx + '" src="' + imageURL + '" alt="' + dataA + '"><br><input type="button" class="imageCropButton" id="imageCrop' + idx + '" value="Crop / Resize Image"' + style + '><input type="button" class="imageCropButton" id="imageCropCancel' + idx + '" value="Cancel Crop" style="display:none">');
}

var setupImageCropperButtons = function(idx) {
	//setup the image cropper button
	//console.log("setting up image cropper buttons: " + idx);
	YAHOO.util.Event.on('imageCrop' + idx, 'click', function(e) {
		var imageCrop = YUD.get('imageCrop' + idx);
		var imageCropCancel = YUD.get('imageCropCancel' + idx);
		//if we're not cropping, setup the crop
		if (imageCrop.value == 'Crop / Resize Image') {
			//console.log("image cropper starting: " + idx);
			imgCropper('imageReal' + idx);
			imageCrop.value = 'Crop Image!';
			imageCropCancel.style.display = 'inline';
		}
		else {
			//else we need to save the crop to the server
			//console.log("image cropper saving: " + idx);
			imageCrop.value = 'Crop / Resize Image';
			imageCropCancel.style.display = 'none';
			var cropArea = imageCroppers['imageReal' + idx].getCropCoords();
			//console.log(cropArea);
			//post the data to the form
			var myPOST = 'imageKey=' + YUD.get('imageRef' + idx).value;
			myPOST += '&left=' + cropArea.left;
			myPOST += '&top=' + cropArea.top;
			myPOST += '&height=' + cropArea.height;
			myPOST += '&width=' + cropArea.width;
			
			//store the src and index in the callback
			cropImageCallbacks.argument.idx = idx;
			setLoading();
			YAHOO.util.Connect.asyncRequest('POST', '/imageCropper', cropImageCallbacks, myPOST);
			//destroy the image cropper if it exists
			if (imageCroppers['imageReal' + idx]) {
				imageCroppers['imageReal' + idx].destroy();
			}
		}
	});
	//setup the image cropper cancel button
	YAHOO.util.Event.on('imageCropCancel' + idx, 'click', function(e) {
		//console.log("image cropper cancelling: " + idx);
		var imageCrop = YUD.get('imageCrop' + idx);
		var imageCropCancel = YUD.get('imageCropCancel' + idx);
		//set the button text back to normal
		imageCrop.value = 'Crop / Resize Image';
		imageCropCancel.style.display = 'none';
		//destroy the image cropper if it exists
		if (imageCroppers['imageReal' + idx]) {
			imageCroppers['imageReal' + idx].destroy();
		}
	});
}

var cropImageCallbacks = {
	success : function (o) {
		//just reset the image src so it reloads the image
		var imgReal = YUD.get('imageReal' + o.argument.idx);
		//we can add a # sign to the end of the url and that does the trick
		imgReal.src += '&x';
		//console.log("cropImage successful: " + imgReal.src);
		setLoaded();
	},
	failure : function (o) {
		alert("cropImage was not successful.");
	},
	argument : {
		"idx": null
	},
	timeout : 30000
}


var imgCropper = function(id) {
	//console.log('setting up image cropper: ' + id);
	var imgCrop = new YAHOO.widget.ImageCropper(id, {
		//"initHeight": 200,
		//"initWidth": 300,
		//"initialXY": [0, 0]
	});
	//save the image crop object so we can use it later, id is the dom ID of the image we're cropping (imageReal + idx)
	imageCroppers[id] = imgCrop;
	//console.log(imgCrop);
}

var imgListChanged = function(obj, value, idx) {
	//check to see if the selected item is the -- Image List -- option
	if (!value) { return; }
	updateImageInForm(idx, value, obj.options[obj.selectedIndex].innerHTML);
}

var updateImageInForm = function(idx, imageKey, alt) {
	//first cancel any crop requests
	var imageCropCancel = YUD.get('imageCropCancel' + idx);
	imageCropCancel.click();
	
	//change the src and alt of the existing image
	var imgReal = YUD.get('imageReal' + idx);
	imgReal.src = '/images?imageKey=' + imageKey;
	imgReal.alt = alt;
	imgReal.style.display = 'inline';
	//show the crop button
	var imgCrop = YUD.get('imageCrop' + idx);
	imgCrop.style.display = 'inline';

	//update the image name and ref in the form
	YUD.get('imageName' + idx).value = alt;
	YUD.get('imageRef' + idx).value = imageKey;
}

var focusObject = function (focusObject) {
	var focusOBJ = YAHOO.util.Dom.get(focusObject);
	if (focusOBJ) {
		focusOBJ.focus();
	}
}

var uploadImage = function(idx) {
	//console.log('uploadImage ' + idx);
	//figure out if the form has an image uploaded, so we can set the setForm boolean correctly
	var imageData = YAHOO.util.Dom.get('imageData' + idx);
	var formHasImageContent = false;
	if (imageData.value) { formHasImageContent = true; }
	//save the index for later and upload the image data
	YAHOO.util.Connect.setForm('imageForm' + idx, formHasImageContent);
	uploadImageCallbacks.argument.nodeIndex = idx;
	setLoading();
	YAHOO.util.Connect.asyncRequest('POST', '/upload', uploadImageCallbacks);//, myPOST);
}

var processImageCallback = function(o) {
	var m = [];
	try { m = YAHOO.lang.JSON.parse(o.responseText); }
	catch (x) {
		//alert("JSON Parse failed! " + x);
		alert(o.responseText);
		return;
	}
	var idx = o.argument.nodeIndex;
	//save the page element key, since it might be new
	domIdToKeyMap['up' + idx] = m.pageElement;
	domIdToKeyMap['disable' + idx] = m.pageElement;
	domIdToKeyMap['delete' + idx] = m.pageElement;
	domIdToKeyMap['down' + idx] = m.pageElement;
	//console.log('save' + idx + ': ' + m.pageElement);
	domIdToKeyMap['save' + idx] = m.pageElement;

	updateImageInForm(idx, m.key, m.imageName);

	//add the new pageElement key to the value of the myPageElKey hidden form input
	YUD.get('myPageElKey' + idx).value = m.pageElement;
	console.log(m.pageElement)
	console.log("processImageCallback: set myPageElKey to " + YUD.get('myPageElKey' + idx).value + " for element: ")
	console.log(YUD.get('myPageElKey' + idx))

	//fire off a page element save, pass in the dom ID of the save button
	pageElSave('save' + idx);
	
	//put the crop info into the cropInfo div
	YUD.get('cropInfo' + idx).innerHTML = 'You must crop the image if it is bigger than 320 pixels wide. Using the cropping tool will automatically resize it to a maximium size of 320 pixels.';
}

var uploadImageCallbacks = {
	upload : function (o) {
		processImageCallback(o);
		setLoaded();
	},
	success : function (o) {
		processImageCallback(o);
		setLoaded();
	},
	failure : function (o) {
		alert("uploadImage was not successful.");
	},
	argument : {
		"nodeIndex": null
	},
	timeout : 30000
}

var pageElUp = function(e) {
	if (loadingCounter > 0) { return }
	var obj = YAHOO.util.Event.getTarget(e);
	var myIndex = domIdToNodeIndexMap[obj.id];
	//use myIndex to get the dom object of the page element DIV we're moving
	var myMovingDiv = YUD.get("DIV" + myIndex);
	//get parent div for the work area, where all the page elements are
	var pageElements = YUD.get("pageElementsWorkArea");
	console.log("obj: " + obj + ", parent: " + parent);
	//loop through the parent div's children (the page elements)
	for (var i = pageElements.childNodes.length-1; i >= 0;  i--) {
		console.log("MOVE PAGE EL UP: " + i);
		pageEl = pageElements.childNodes[i];
		console.log(pageEl);
		//is this the node we're moving?
		if (myMovingDiv == pageEl) {
			console.log("   this is the div we're moving");
			//this is the page element that we clicked on
			//get the next DIV, remove this DIV from the parent DIV, then insert it before the previous DIV
			myPreviousDiv = YUD.getPreviousSibling(myMovingDiv);
			if (myPreviousDiv) {
				console.log("got previous div:");
				console.log(myPreviousDiv);
				myPreviousDivNode = tree.getNodeByIndex(domIdToNodeIndexMap[myPreviousDiv.id]);
				myPreviousDivNode.value.pageOrder = i;
				removedDiv = pageElements.removeChild(myMovingDiv);
				removedDivNode = tree.getNodeByIndex(domIdToNodeIndexMap[removedDiv.id]);
				removedDivNode.value.pageOrder = i-1;
				YUD.insertBefore(removedDiv, myPreviousDiv);
				console.log("   moved div to pageOrder: " + removedDivNode.value.pageOrder);
				console.log("   moved next sibling div to pageOrder: " + myPreviousDivNode.value.pageOrder);
				if (removedDivNode.value.key) {
					var myHTML = "myElKey=" + removedDivNode.value.key + "&myNewOrder=" + removedDivNode.value.pageOrder;
					console.log(myHTML);
					setLoading();
					YAHOO.util.Connect.asyncRequest('POST', '/movePageElement', moveCallbacks, myHTML);
				}
				if (myPreviousDivNode.value.key) {
					var myHTML = "myElKey=" + myPreviousDivNode.value.key + "&myNewOrder=" + myPreviousDivNode.value.pageOrder;
					console.log(myHTML);
					setLoading();
					YAHOO.util.Connect.asyncRequest('POST', '/movePageElement', moveCallbacks, myHTML);
				}
				//increase the counter because we handled the next DIV already
				i--;
				//now move the node in the tree
				tree.removeNode(removedDivNode, false);
				removedDivNode.insertBefore(myPreviousDivNode);
			}
			else {
				//the node is already at the top so
				//assign this div's node an up to date pageOrder
				myNode = tree.getNodeByIndex(domIdToNodeIndexMap[pageEl.id]);
				myNode.value.pageOrder = i;
				console.log("   the node of this div: " + myNode + ", pageOrder: " + myNode.value.pageOrder);
				if (myNode.value.key) {
					var myHTML = "myElKey=" + myNode.value.key + "&myNewOrder=" + myNode.value.pageOrder;
					console.log(myHTML);
					setLoading();
					YAHOO.util.Connect.asyncRequest('POST', '/movePageElement', moveCallbacks, myHTML);
				}
			}
		}
		else {
			//this is not the node we're moving so just
			//assign this div's node an up to date pageOrder
			myNode = tree.getNodeByIndex(domIdToNodeIndexMap[pageEl.id]);
			myNode.value.pageOrder = i;
			console.log("   the node of this div: " + myNode + ", pageOrder: " + myNode.value.pageOrder);
			if (myNode.value.key) {
				var myHTML = "myElKey=" + myNode.value.key + "&myNewOrder=" + myNode.value.pageOrder;
				console.log(myHTML);
				setLoading();
				YAHOO.util.Connect.asyncRequest('POST', '/movePageElement', moveCallbacks, myHTML);
			}
		}
	}
	tree.draw();
}

var moveCallbacks = {
	success : function (o) {
		// Process the JSON data returned from the server
		var pageElement = [];
		try {
			pageElement = YAHOO.lang.JSON.parse(o.responseText);
		}
		catch (x) {
			alert("JSON Parse failed! " + x);
			return;
		}
		setLoaded();
	},
	failure : function (o) {
		alert("MovePageElement was not successful.");
	},
	argument : { },
	timeout : 30000
}

var pageElDown = function(e) {
	if (loadingCounter > 0) { return }
	var obj = YAHOO.util.Event.getTarget(e);
	var myIndex = domIdToNodeIndexMap[obj.id];
	//use myIndex to get the dom object of the page element DIV we're moving
	var myMovingDiv = YUD.get("DIV" + myIndex);
	//get parent div for the work area, where all the page elements are
	var pageElements = YUD.get("pageElementsWorkArea");
	console.log("obj: " + obj + ", parent: " + parent);
	//loop through the parent div's children (the page elements)
	for (var i = 0; i < pageElements.childNodes.length; i++) {
		pageEl = pageElements.childNodes[i];
		console.log(pageEl);
		//is this the node we're moving?
		if (myMovingDiv == pageEl) {
			console.log("   this is the div we're moving");
			//this is the page element that we clicked on
			//get the next DIV, remove this DIV from the parent DIV, then insert it after the next DIV
			myNextDiv = YUD.getNextSibling(myMovingDiv);
			if (myNextDiv) {
				myNextDivNode = tree.getNodeByIndex(domIdToNodeIndexMap[myNextDiv.id]);
				myNextDivNode.value.pageOrder = i;
				removedDiv = pageElements.removeChild(myMovingDiv);
				removedDivNode = tree.getNodeByIndex(domIdToNodeIndexMap[removedDiv.id]);
				removedDivNode.value.pageOrder = i+1;
				YUD.insertAfter(removedDiv, myNextDiv);
				console.log("   moved div to pageOrder: " + removedDivNode.value.pageOrder);
				console.log("   moved next sibling div to pageOrder: " + myNextDivNode.value.pageOrder);
				if (removedDivNode.value.key) {
					var myHTML = "myElKey=" + removedDivNode.value.key + "&myNewOrder=" + removedDivNode.value.pageOrder;
					console.log(myHTML);
					setLoading();
					YAHOO.util.Connect.asyncRequest('POST', '/movePageElement', moveCallbacks, myHTML);
				}
				if (myNextDivNode.value.key) {
					var myHTML = "myElKey=" + myNextDivNode.value.key + "&myNewOrder=" + myNextDivNode.value.pageOrder;
					console.log(myHTML);
					setLoading();
					YAHOO.util.Connect.asyncRequest('POST', '/movePageElement', moveCallbacks, myHTML);
				}
				//increase the counter because we handled the next DIV already
				i++;
				//now move the node in the tree
				tree.removeNode(removedDivNode, false);
				removedDivNode.insertAfter(myNextDivNode);
			}
			else {
				//the node is already at the bottom so
				//assign this div's node an up to date pageOrder
				myNode = tree.getNodeByIndex(domIdToNodeIndexMap[pageEl.id]);
				myNode.value.pageOrder = i;
				console.log("   the node of this div: " + myNode + ", pageOrder: " + myNode.value.pageOrder);
				if (myNode.value.key) {
					var myHTML = "myElKey=" + myNode.value.key + "&myNewOrder=" + myNode.value.pageOrder;
					console.log(myHTML);
					setLoading();
					YAHOO.util.Connect.asyncRequest('POST', '/movePageElement', moveCallbacks, myHTML);
				}
			}
		}
		else {
			//this is not the node we're moving so just
			//assign this div's node an up to date pageOrder
			myNode = tree.getNodeByIndex(domIdToNodeIndexMap[pageEl.id]);
			myNode.value.pageOrder = i;
			console.log("   the node of this div: " + myNode + ", pageOrder: " + myNode.value.pageOrder);
			if (myNode.value.key) {
				var myHTML = "myElKey=" + myNode.value.key + "&myNewOrder=" + myNode.value.pageOrder;
				console.log(myHTML);
				setLoading();
				YAHOO.util.Connect.asyncRequest('POST', '/movePageElement', moveCallbacks, myHTML);
			}
		}
	}
	tree.draw();
}

var pageElDisable = function(e) {
	if (loadingCounter > 0) { return }
	var obj = YAHOO.util.Event.getTarget(e);
	var myKey = domIdToKeyMap[obj.id];
	if (myKey) {
		var myHTML = "myElKey=" + myKey;
		pageElDisableCallbacks.argument.key = myKey
		pageElDisableCallbacks.argument.nodeIndex = keyToNodeMap[myKey].index;
		setLoading();
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
		var m = [];
		try { m = YAHOO.lang.JSON.parse(o.responseText); }
		catch (x) {
			alert("JSON Parse failed! " + x);
			return;
		}
		markPageElAsDisabled(o.argument.nodeIndex);
		setLoaded();
	},
	failure : function (o) {
		alert("disablePageElement was not successful.");
	},
	argument : {
		"nodeIndex": null,
		"key": null
	},
	timeout : 30000
}
var removePageElementNodeFromTree = function(nodeIndex) {
	var myNode = tree.getNodeByIndex(nodeIndex);

	if (myNode) {
		/*
		var oldPageOrder = myNode.value.pageOrder;
		console.log("deleting page node with pageOrder: " + oldPageOrder);
		//now we need to loop through all the other nodes and reduce their page orders by 1 if they were above this deleted nodes page order
		for (var i = 0; i < myNode.parent.children.length; i++ ) {
			var newNode = myNode.parent.children[i];
			console.log("newnode page order: " + newNode.value.pageOrder);
			if (newNode.value.pageOrder >= oldPageOrder) {
				console.log("reducing newnode pageOrder by 1");
				newNode.value.pageOrder--;
			}
		}*/
		//done, not remove the node from the tree
		tree.removeNode(myNode, true);
	}

	tree.draw();
	var pageElementsWorkArea = YAHOO.util.Dom.get('pageElementsWorkArea');
	var myDiv = YAHOO.util.Dom.get('DIV' + nodeIndex);
	pageElementsWorkArea.removeChild(myDiv);
}
var pageElDelete = function(e) {
	if (loadingCounter > 0) { return }
	var obj = YAHOO.util.Event.getTarget(e);
	var myKey = domIdToKeyMap[obj.id];
	if (myKey) {
		var myHTML = "myElKey=" + myKey;
		pageElDeleteCallbacks.argument.key = myKey
		pageElDeleteCallbacks.argument.nodeIndex = keyToNodeMap[myKey].index;
		setLoading();
		YAHOO.util.Connect.asyncRequest('POST', '/deletePageElement', pageElDeleteCallbacks, myHTML);
	}
	else {
		var nodeIndex = domIdToNodeIndexMap[obj.id];
		removePageElementNodeFromTree(nodeIndex);
	}
}
var pageElDeleteCallbacks = {
	success : function (o) {
		// Process the JSON data returned from the server
		var m = [];
		try {
			m = YAHOO.lang.JSON.parse(o.responseText);
		}
		catch (x) {
			alert("JSON Parse failed! " + x);
			return;
		}
		removePageElementNodeFromTree(o.argument.nodeIndex);
		setLoaded();
	},
	failure : function (o) {
		alert("deletePageElement was not successful.");
	},
	argument : {
		"nodeIndex": null,
		"key": null
	},
	timeout : 30000
}
var pageElSave = function(e, newPageKey) {
	if (loadingCounter > 0) { return }
	var obj = YAHOO.util.Event.getTarget(e);
	if (!obj) {
		obj = YUD.get(e);
	}
	var myPageElKey = domIdToKeyMap[obj.id];
	var myPageKey = nodeToKeyMap[currentNodeIndex];
	var myPageElNodeIndex = domIdToNodeIndexMap[obj.id];
	var myNode = tree.getNodeByIndex(myPageElNodeIndex);
	//console.log("saving page element: obj.id(" + obj.id + ") key(" + myPageElKey + ") page(" + myPageKey + ") nodeIdx(" + currentNodeIndex + ") pageElIdx(" + myPageElNodeIndex + ") newPageKey(" + newPageKey + ")");

	var dataA = YAHOO.util.Dom.get('dataA' + myPageElNodeIndex);
	var dataB = YAHOO.util.Dom.get('dataB' + myPageElNodeIndex);
	var myDataB = null;
	if (dataB && dataB.value) {
		myDataB = dataB.value;
	}
	//are we saving a choice? is the value of the choice "new"? then we need to create a new page
	if (myNode.value.dataType == 3)
	{
		if (dataB.value == 'new') {
			if (!newPageKey) {
				//we need to create a new page
				waitingForPage = 1;
				var myPageName = '[new page]';
				if (dataA) { myPageName = dataA.value; }
				//console.log("adding a new choice, but first we're going to create a new page: " + myPageName);
				addPageSubmit(myPageName, obj);
				return;
				//now when addPageSubmit is done they will just call pageElSave again and pass in the obj we passed to them
			}
			if (newPageKey) {
				//addPageSubmit is done, so we just need to set dataB.value to the new page key
				//console.log("got newPageKey: " + newPageKey);
				myDataB = newPageKey;
				//add the new page to the select list and select it
				var newPageName = '[new page]';
				if (dataA) { newPageName = dataA.value; }
				var newOption = document.createElement('option');
				newOption.text = newPageName;
				newOption.value = newPageKey;
				//domID of select list is dataB + myPageElNodeIndex
				var selectList = YUD.get('dataB' + myPageElNodeIndex);
				selectList.options[selectList.length-1] = newOption;
				//selectList.appendChild(newOption);
				newOption.selected = true;
			}
		}
	}
	
	var myHTML = "myPageKey=" + myPageKey;
	//console.log('pageElSave: ' + obj.id + ', ' + myPageElKey);
	if (myPageElKey) {
		//existing node
		myHTML += "&myPageElKey=" + myPageElKey;
		pageElSaveCallbacks.argument.key = myPageElKey;
	}
	else {
		//new node
		myHTML += "&elementType=" + myNode.value.dataType;
	}
	pageElSaveCallbacks.argument.nodeIndex = myPageElNodeIndex;
	pageElSaveCallbacks.argument.pageKey = myPageKey;
	pageElSaveCallbacks.argument.pageNodeIndex = currentNodeIndex;
	var pageOrder = myNode.value.pageOrder;
	if (pageOrder) {
		myHTML += "&pageOrder=" + escape(pageOrder);
	}	
	if (dataA) {
		myHTML += "&dataA=" + escape(dataA.value);
	}
	if (myDataB) {
		myHTML += "&dataB=" + escape(myDataB);
	}
	var imageRef = YAHOO.util.Dom.get('imageRef' + myPageElNodeIndex);
	if (imageRef) {
		myHTML += "&imageRef=" + escape(imageRef.value);
	}
	var imageName = YAHOO.util.Dom.get('imageName' + myPageElNodeIndex);
	if (imageName) {
		myHTML += "&imageName=" + escape(imageName.value);
		imgCache[imageRef.value] = imageName.value;
		imgCache['length'] = (imgCache['length']||0) + 1
	}
	setLoading();
	console.log("saving page el: " + myHTML);
	YAHOO.util.Connect.asyncRequest('POST', '/savePageElement', pageElSaveCallbacks, myHTML);
}
var pageElSaveCallbacks = {
	success : function (o) {
		// Process the JSON data returned from the server
		var pageElement = [];
		try {
			pageElement = YAHOO.lang.JSON.parse(o.responseText);
		}
		catch (x) {
			alert("JSON Parse failed! " + x);
			return;
		}
		{
			var belowWorkArea = YAHOO.util.Dom.get('belowElWorkArea' + o.argument.nodeIndex);
			belowWorkArea.innerHTML = 'Saved.';
			var myTreeNode = tree.getNodeByIndex(o.argument.nodeIndex);
			addOrUpdateChildNode(pageElement.dataA, pageElement.dataType, null, pageElement, myTreeNode);
		}
		setLoaded();
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
	timeout : 30000
}

//ADD PAGE ELEMENTS TO THE ADVENTURE PAGE
var setupWorkArea = function() {
	//look at the current node index and see if there are any child elements
	//if there are, that means we already have page elements
	//if not, we should display the getting started text
	var workArea = YAHOO.util.Dom.get('workArea');
	workArea.innerHTML = '<div id="pageElementsWorkArea"></div>';
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
	//figure out what the new pageOrder should be
	var pageOrder = 0;
	for (var i = 0; i < myNode.children.length; i++) {
		if (myNode.children[i].value.pageOrder >= pageOrder) {
			pageOrder = (myNode.children[i].value.pageOrder + 1);
			console.log('node: ' + myNode.children[i] + ', new pageOrder set to ' + pageOrder);
		}
	}
	//done
	var pageElement = {
		"dataType": dataType,
		"pageOrder": pageOrder
	}
	var newNodeIndex = addOrUpdateChildNode("New " + pageElementTypeToNameMap[dataType], dataType, myNode, pageElement);
	var newNode = tree.getNodeByIndex(newNodeIndex);
	addPageElementToWorkArea(pageElement, newNodeIndex);
}

var addPageElementCallbacks = {
	success : function (o) {
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
		setLoaded();
	},
	failure : function (o) {
		alert("addPageElement was not successful.");
	},
	argument : { "nodeIndex": null },
	timeout : 30000
}
var getDescForChildNode = function(description, datatype) {
	var nodeDesc = null;
	if (description) {
		var prefix = 't: ';
		if (datatype == 2) { prefix = 'i: '; }
		else if (datatype == 3) { prefix = 'c: '; }
		nodeDesc = description.substr(0, 21);
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
		var idx = currentNode.index;
		domIdToKeyMap['up' + idx] = pageElement.key;
		domIdToKeyMap['disable' + idx] = pageElement.key;
		domIdToKeyMap['delete' + idx] = pageElement.key;
		domIdToKeyMap['down' + idx] = pageElement.key;
		domIdToKeyMap['save' + idx] = pageElement.key;
		nodeToKeyMap[idx] = pageElement.key;
		keyToNodeMap[pageElement.key] = currentNode;
		currentNode.value = pageElement;
	}
	//this next line adds the node page order to the label for debugging purposes
	currentNode.label = currentNode.value.pageOrder + ' ' + currentNode.label;
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
		//console.log("no page selected");
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
	obj.innerHTML = '<form id="addPageForm" method="post" action="javascript:addPageSubmitFunction()"><table class="table1"><tr><td>Name of page:<br><br><input type="text" id="newPageName"' + pageNameHTML + '></td><td class="myButton">' + divButtonFunction('addPageSubmit', 'icon-save') + 'Save</td></tr></table></form>';
	YAHOO.util.Event.addListener("addPageSubmit", "click", addPageSubmit);
	YAHOO.util.Event.on('addPageForm', 'submit', function(e) {
		YAHOO.util.Event.stopEvent(e);
		addPageSubmit();
	});
	YAHOO.util.Dom.get('newPageName').focus();
	//new YAHOO.widget.Tooltip("tooltipAddPageSubmit", { showdelay: 500, context:"addPageSubmit", text:"Save"} );
}
		
var addPageSubmit = function(e, pageElForm) {
	//myAdventureKey myPageKey pageName
	//this is used for the normal new and edit page buttons, but also for adding a choice + page at the same time
	//if the new or edit page buttons are used, we will have the 'newPageName' object
	//if we're adding a choice + page, we pass in the page name
	//pageElForm will only be set if we're adding a choice + page
	addPageCallbacks.argument.nodeIndex = currentNodeIndex;
	var pageKeyHTML = '';
	var newPageName = YAHOO.util.Dom.get('newPageName');
	if (newPageName) {
		newPageName = newPageName.value
		if (currentPage.key) {
			pageKeyHTML = "&myPageKey=" + currentPage.key;
		}
	}
	//else we use the passed in object, for the choice+page path
	else { 
		newPageName = e;
		addPageCallbacks.argument.pageElForm = pageElForm;
		//also reset the nodeIndex so it knows we're adding a new page
		addPageCallbacks.argument.nodeIndex = null;
		}
	console.log("newPageName: " + newPageName + ", " + pageKeyHTML);
	setLoading();
	YAHOO.util.Connect.asyncRequest('POST', '/addPage', addPageCallbacks,
		"myAdventureKey=" + adventureKey
		+ pageKeyHTML
		+ "&pageName=" + newPageName
	);
}
var addPageCallbacks = {
	success : function (o) {
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
		{
			//console.log(m.key + ' ' + m.name);
			//console.log(currentNodeIndex + '|' + o.argument.nodeIndex);
			var myNode = tree.getNodeByIndex(o.argument.nodeIndex);
			if (myNode) {
				console.log("updating existing page");
				myNode.label = m.name;
			}
			else {
				console.log("adding new page to tree");
				myNode = new YAHOO.widget.TextNode(m.name, tree.getRoot(), false);
				myNode.insertBefore(tree.getRoot().children[0]);
				myNode.value = m.key;
			}
			if (waitingForPage) {
				//this means that we tried to add a choice + new page and we need to add the choice now
				setLoaded();
				tree.draw();
				waitingForPage = 0;
				console.log("just added new page, got key back: " + m.key + ", and form data: " + o.argument.pageElForm);
				pageElSave(o.argument.pageElForm, m.key);
			}
			else {
				//normal operation of add page
				setLoaded();
				currentPage.name = myNode.label;
				nodeClick(myNode);
			}
		}
	},
	failure : function (o) {
		alert("addPage was not successful.");
	},
	argument : {
		"nodeIndex": null,
		"pageElForm": null
	},
	timeout : 30000
}

var deletePageSubmit = function(e) {
	//console.log("addPageSubmit");
	//myAdventureKey myPageKey pageName
	var pageKeyHTML = "myPageKey=" + currentPage.key;
	deletePageCallbacks.argument.nodeIndex = currentNodeIndex;
	setLoading();
	YAHOO.util.Connect.asyncRequest('POST', '/deletePage', deletePageCallbacks, pageKeyHTML);
}
var deletePageCallbacks = {
	success : function (o) {
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
		setLoaded();
	},
	failure : function (o) {
		alert("removePage was not successful.");
	},
	argument : { "nodeIndex": null },
	timeout : 30000
}

// Define the callbacks for the asyncRequest
var callbacks = {
	success : function (o) {
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
		tree = new YAHOO.widget.TreeView("treeDiv1");
		// The returned data was parsed into an array of objects.
		// Add a P element for each received message
		for (var i = 0, len = messages.length; i < len; ++i) {
			var m = messages[i];
			//m.name m.key
			var tmpNode = new YAHOO.widget.TextNode(m.name, tree.getRoot(), true);
			tmpNode.insertBefore(tree.getRoot().children[0]);
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
				labelClick = false;
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
		setLoaded();
       },
	failure : function (o) {
		if (!YAHOO.util.Connect.isCallInProgress(o)) {
			alert("Async call failed!");
		}
	},		
	timeout : 30000
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
	//console.log(node.index + " label was clicked");
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

var imagesByUserCallbacks = {
	success : function (o) {
		// Process the JSON data returned from the server
		var images = [];
		try {
			images = YAHOO.lang.JSON.parse(o.responseText);
		}
		catch (x) {
			alert("imagesByUserCallbacks JSON Parse failed! " + x);
			return;
		}
		for (var i = 0, len = images.length; i < len; ++i) {
			var image = images[i];
			imgCache[image.key] = image.imageName;
			imgCache.length = i+1;
		}
		setLoaded();
	},
	failure : function (o) {
		alert("imagesByUserCallbacks was not successful.");
	},
	argument : {
	},
	timeout : 30000
}

var setLoading = function() {
	loadingCounter++;
	disableIcons(true);
	YUD.get('loadTop').style.display = 'block';
	{
		//for all the loading gifs on each page element
		var loadElements = YUD.getElementsByClassName('loadElement', 'div', 'pageElementsWorkArea');
		for (var i = 0; i < loadElements.length; i++) {
			loadElements[i].style.display = 'block';
		}
	}
	{
		//for all the page element menu buttons
		var loadElements = YUD.getElementsBy(isPageElMenuTitle, 'td', 'pageElementsWorkArea');
		for (var i = 0; i < loadElements.length; i++) {
			disableDivPageEl(loadElements[i]);
		}
	}
}
var setLoaded = function() {
	loadingCounter--;
	if (loadingCounter <= 0) {
		enableIcons();
		YUD.get('loadTop').style.display = 'none';
		{
			//for all the loading gifs on each page element
			var loadElements = YUD.getElementsByClassName('loadElement', 'div', 'pageElementsWorkArea');
			for (var i = 0; i < loadElements.length; i++) {
				loadElements[i].style.display = 'none';
			}
		}
		{
			//for all the page element menu buttons
			var loadElements = YUD.getElementsBy(isPageElMenuTitle, 'td', 'pageElementsWorkArea');
			for (var i = 0; i < loadElements.length; i++) {
				enableDivPageEl(loadElements[i]);
			}
		}
	}
}

var isPageElMenuTitle = function(td) {
	if (td && td.title == 'pageElMenu') { return true; }
	return false;
}

//function to initialize the tree:
function treeInit() {
	//first see if we got an error from the python
	if (myError) {
		resetWorkArea(myError, true);
		return;
	}
	// Make the call to the server for JSON data
	setLoading();
	YAHOO.util.Connect.asyncRequest('POST',"/getPages?myAdventureKey=" + adventureKey, callbacks);
	setLoading();
	YAHOO.util.Connect.asyncRequest('POST',"/imagesByUser", imagesByUserCallbacks);

	//events for the button icons
	YAHOO.util.Event.addListener("addPageElementText", "click", addPageElement);
	YAHOO.util.Event.addListener("addPageElementText", "mouseover", eventIconMO);
	YAHOO.util.Event.addListener("addPageElementText", "mouseout", eventIconMOreset);

	YAHOO.util.Event.addListener("addPageElementImage", "click", addPageElement);
	YAHOO.util.Event.addListener("addPageElementImage", "mouseover", eventIconMO);
	YAHOO.util.Event.addListener("addPageElementImage", "mouseout", eventIconMOreset);

	YAHOO.util.Event.addListener("addPageElementChoice", "click", addPageElement);
	YAHOO.util.Event.addListener("addPageElementChoice", "mouseover", eventIconMO);
	YAHOO.util.Event.addListener("addPageElementChoice", "mouseout", eventIconMOreset);

	YAHOO.util.Event.addListener("addPage", "click", addPage);
	YAHOO.util.Event.addListener("addPage", "mouseover", eventIconMO);
	YAHOO.util.Event.addListener("addPage", "mouseout", eventIconMOreset);

	YAHOO.util.Event.addListener("editPage", "click", editPage);
	YAHOO.util.Event.addListener("editPage", "mouseover", eventIconMO);
	YAHOO.util.Event.addListener("editPage", "mouseout", eventIconMOreset);

	YAHOO.util.Event.addListener("deletePage", "click", deletePage);
	YAHOO.util.Event.addListener("deletePage", "mouseover", eventIconMO);
	YAHOO.util.Event.addListener("deletePage", "mouseout", eventIconMOreset);

	YAHOO.util.Event.addListener("playStory", "click", playStory);
	YAHOO.util.Event.addListener("playStory", "mouseover", eventIconMO);
	YAHOO.util.Event.addListener("playStory", "mouseout", eventIconMOreset);

	resetWorkArea();
	//new YAHOO.widget.Tooltip("tooltipDeletePage", { showdelay: 500, context:"deletePage", text:"Delete This Page"} );
	//new YAHOO.widget.Tooltip("tooltipAddPage", { showdelay: 500, context:"addPage", text:"Add A New Page"} );
	//new YAHOO.widget.Tooltip("tooltipEditPage", { showdelay: 500, context:"editPage", text:"Edit This Page's Name"} );
	//new YAHOO.widget.Tooltip("tooltipAddText", { showdelay: 500, context:"addPageElementText", text:"Add A Text Page Element"} );
	//new YAHOO.widget.Tooltip("tooltipAddImage", { showdelay: 500, context:"addPageElementImage", text:"Add An Image Page Element"} );
	new YAHOO.widget.Tooltip("tooltipAddChoice", { autodismissdelay:10000, showdelay:1000, context:"addPageElementChoice", text:"<div class=\"tt\">A choice is a course of action for the reader. Choices are like paths, they take the reader to another page in your story.</div>"} );
}