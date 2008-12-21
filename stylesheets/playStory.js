//Add an onDOMReady handler to build the tree when the document is ready
YAHOO.util.Event.onDOMReady(treeInit);
//set shortcuts for common yahoo stuff
var YUD = YAHOO.util.Dom, YUE = YAHOO.util.Event, YUC = YAHOO.util.Connect;

//if there is no console, set it to null
if (!console) {
	
}

//we also expect the variable MY_ADVENTURE_KEY to be set from the footer
var adventureKey = '';
if (MY_ADVENTURE_KEY) {
	adventureKey = MY_ADVENTURE_KEY;
}

//setup some globals
var loadingCounter = 0;
var numPages = 0;
var pages = {};
var keyToPageIdMap = {};

function treeInit() {
	// Make the call to the server for JSON data
	setLoading();
	YUC.asyncRequest('GET',"/getPages?myAdventureKey=" + adventureKey, getPagesCallbacks);
	YAHOO.util.Event.addListener("restartStory", "mouseover", eventIconMO);
	YAHOO.util.Event.addListener("restartStory", "mouseout", eventIconMOreset);
	YAHOO.util.Event.addListener("restartStory", "click", restartStory);
	YAHOO.util.Event.addListener("storyForge", "mouseover", eventIconMO);
	YAHOO.util.Event.addListener("storyForge", "mouseout", eventIconMOreset);
	YAHOO.util.Event.addListener("storyForge", "click", loadStoryForge);
}

var loadStoryForge = function() {
	window.location.replace('/storyEditor?myAdventureKey=' + adventureKey);
}
var restartStory = function() {
	playPage(pages[0].key);
}

var setLoading = function() {
	loadingCounter++;
	disableIcons(true);
	YUD.get('loadTop').style.display = 'block';
}
var setLoaded = function() {
	loadingCounter--;
	if (loadingCounter <= 0) {
		enableIcons();
		YUD.get('loadTop').style.display = 'none';
	}
}
var disableIcons = function()
{
	disableDiv('restartStory');
	disableDiv('storyForge');
}
var enableIcons = function()
{
	if (loadingCounter > 0) { return; }
	enableDiv('restartStory');
	enableDiv('storyForge');
}

var eventIconMO = function(e) {
	if (this.id) {
		//console.log(this.id);
		iconMO(this);
	}
}
var eventIconMOreset = function(e) {
	if (this.id) {
		iconMOreset(this);
	}
}
var iconMO = function(td) {
	if (!td.id) { return }
	if (loadingCounter > 0) { return }
	var icon = td.firstChild;
	//this is for the normal menu buttons
	td.className = 'iconBG-light';
	icon.className = icon.id + 'MO';
}
var iconMOreset = function(td, useValue) {
	if (!td.id) { return }
	if (loadingCounter > 0) { return }
	var icon = td.firstChild;
	//this is for the normal menu buttons
	td.className = 'iconBG-dark';
	icon.className = icon.id;
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
var disableDiv = function(name) {
	var td = YAHOO.util.Dom.get(name);
	iconDisable(td);
}
var enableDiv = function(name) {
	var td = YAHOO.util.Dom.get(name);
	iconMOreset(td);
}


// Define the callbacks for getPages
var getPagesCallbacks = {
	success : function (o) {
		setLoaded();
		enableIcons();
		// Process the JSON data returned from the server
		var m = [];
		try {
			m = YAHOO.lang.JSON.parse(o.responseText);
		}
		catch (x) {
			alert("Get Pages json parse failed!");
			alert(x);
			return;
		}
		pages = m;
		for (var i = 0; i < m.length; i++) {
			//console.log("adding " + m[i].key + " to map as page " + i);
			keyToPageIdMap[m[i].key] = i;
			numPages++;
		}
		//console.log("got " + numPages + " pages.");
		playPage(pages[0].key)
			/*//m.name m.key
			var page = {
				'key': m.key,
				'name': m.name,
				'pageElements': {}
			};
			var myPageElements = {};
				var pageElement = {
					'dataA': mm.dataA,
					'dataB': mm.dataB,
					'dataType': mm.dataType,
					'imageRef': mm.imageRef
				};*/
	},
	failure : function (o) {
		if (!YUC.isCallInProgress(o)) {
			alert("Get Pages failed!");
		}
	},		
	timeout : 30000
}

var playPageEvent = function(e) {
	//this sets the focus to the #top href tag
	//console.log("playing page: " + e);
	window.location.hash = 'top';
	playPage(this.id);
}

var playPage = function(pageKey) {
	//console.log('playPage: ' + pageKey);
	workArea = YUD.get('player');
	var page = pages[keyToPageIdMap[pageKey]];
	workArea.innerHTML = '<div><h1>' + page.name + '</h1></div>';
	for (var i = 0; i < page.elements.length; i++) {
		var pageElement = page.elements[i];
		//console.log("got page element of type: " + pageElement.dataType);
		if (pageElement.dataType == 1) {
			//text element
			//console.log("page element text: " + pageElement.dataA.substr(0, 20));
			if (pageElement.dataA) {
				workArea.innerHTML += '<div class="playerSmall">' + pageElement.dataA + '</div>';
			}
		}
		if (pageElement.dataType == 2) {
			//image element
			//console.log("page element image: " + pageElement.dataA);
			if (pageElement.dataA) {
				workArea.innerHTML += '<div class="playerSmall"><img src="/images?imageKey=' + pageElement.imageRef + '"></div>';
			}
		}
		if (pageElement.dataType == 3) {
			//choice element
			//console.log("page element choice: " + pageElement.dataA);
			if (pageElement.dataA) {
				workArea.innerHTML += '<div class="playerSmallChoice" id="' + pageElement.dataB + '"><table width="100%"><tr><td align="left">' + pageElement.dataA + '</td><td align="right">--></td></tr></table></div>';
				YAHOO.util.Event.addListener(pageElement.dataB, "click", playPageEvent);
			}
		}
	}
}




