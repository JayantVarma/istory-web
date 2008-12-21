//Add an onDOMReady handler to build the tree when the document is ready
YAHOO.util.Event.onDOMReady(treeInit);
//set shortcuts for common yahoo stuff
var YUD = YAHOO.util.Dom, YUE = YAHOO.util.Event, YUC = YAHOO.util.Connect;

//if there is no console, set it to null
try { console.log('init console... done'); } catch(e) { console = { log: function() {} } }

//we also expect the variable MY_ADVENTURE_KEY to be set from the footer
var adventureKey = '';
if (MY_ADVENTURE_KEY) {
	adventureKey = MY_ADVENTURE_KEY;
}

//setup some globals
var loadingCounter = 0;
var numPages = 0;
var keyToPageIdMap = {};
var pageHistory = [];

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

var eventIconMO = function(e, isLight) {
	if (this.id) {
		iconMO(this, isLight);
	}
}
var eventIconMOreset = function(e, isLight) {
	if (this.id) {
		iconMOreset(this, isLight);
	}
}
var iconMO = function(td, isLight) {
	if (!td.id) { return }
	if (loadingCounter > 0) { return }
	var icon = td.firstChild;
	if (!isLight) {
		//this is for the normal menu buttons
		td.className = 'iconBG-light';
		icon.className = icon.id + 'MO'
	}
	else {
		//this is for light background icons
		//if the pagehistory only has 1 element in it, dont do it
		if (pageHistory.length > 1) {
			td.className = 'iconBG-light2';
			icon.className = icon.id + 'MO'
		}
	}
}
var iconMOreset = function(td, isLight) {
	if (!td.id) { return }
	if (loadingCounter > 0) { return }
	var icon = td.firstChild;
	if (!isLight) {
		//this is for the normal menu buttons
		td.className = 'iconBG-dark';
		icon.className = icon.id;
	}
	else {
		//this is for light background icons
		//if the pagehistory only has 1 element in it, dont do it
		if (pageHistory.length > 1) {
			td.className = 'iconBG-dark2';
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

var playPageEvent = function(e, pageKey) {
	console.log("playing page: " + e + ', ' + pageKey);
	//this sets the focus to the #top href tag
	window.location.hash = 'top';
	playPage(pageKey);
}

var back = function() {
	//first discard the most recent item since it will be the current page
	var discarded = pageHistory.pop();
	//get the last item from the history and play it
	var previousKey = pageHistory.pop();
	if (previousKey) {
		console.log("going back.. previous key: " + previousKey);
		playPage(previousKey);
	}
	else {
		//if we are here that means we emptied out the history, which is bad
		//we should re-add the discarded element
		console.log("going back.. added discarded key: " + discarded);
		pageHistory.push(discarded);
	}
}

var playPage = function(pageKey) {
	//console.log('playPage: ' + pageKey);
	workArea = YUD.get('player');
	var page = pages[keyToPageIdMap[pageKey]];
	//add the last page to the history
	pageHistory.push(pageKey);
	console.log("adding key to history: " + pageKey);
	//create the back button and title, and tooltip for the back button
	workArea.innerHTML = '<div><table width="100%"><tr><td id="back" class="iconBG-disabled2" width="48px"><div id="icon-back" class="icon-back"></td><td><h1>' + page.name + '</h1></td><td width="48px"></td></tr></table></div>';
	//if the pagehistory only has 1 element in it, change the icon class to disabled
	if (pageHistory.length == 1) {
		YUD.get('icon-back').className = 'icon-backD';
	}
	else {
		//only setup the tooltip and listeners if the button is useable
		new YAHOO.widget.Tooltip("tooltipBack", { autodismissdelay:3000, showdelay:2000, context:"back", text:"Go back a page."});
		//add event listeners for the back button
		YAHOO.util.Event.addListener("back", "mouseover", eventIconMO, true);
		YAHOO.util.Event.addListener("back", "mouseout", eventIconMOreset, true);
		YAHOO.util.Event.addListener("back", "click", back);
	}
	//go through each page element for this page and add it to the HTML
	for (var i = 0; i < page.elements.length; i++) {
		var pageElement = page.elements[i];
		//create a new div that we can append to workArea
		var newDiv = document.createElement('div');
		newDiv.id = "pageElement" + i;
		workArea.appendChild(newDiv);

		//console.log("got page element of type: " + pageElement.dataType);
		if (pageElement.dataType == 1) {
			//text element
			//console.log("page element text: " + pageElement.dataA.substr(0, 20));
			if (pageElement.dataA) {
				pageElement.dataA = pageElement.dataA.replace(/\n/g, '<br>');
				newDiv.innerHTML = '<div class="playerSmall">' + pageElement.dataA + '</div>';
			}
		}
		if (pageElement.dataType == 2) {
			//image element
			//console.log("page element image: " + pageElement.dataA);
			if (pageElement.dataA) {
				newDiv.innerHTML = '<div class="playerSmall"><img src="/images?imageKey=' + pageElement.imageRef + '"></div>';
			}
		}
		if (pageElement.dataType == 3) {
			//choice element
			//console.log("page element choice: " + pageElement.dataA + ", " + pageElement.dataB + ', ' + i);
			if (pageElement.dataA) {
				newDiv.innerHTML = '<div class="playerSmallChoice" id="choiceClick' + i + '"><table width="100%"><tr><td align="left">' + pageElement.dataA + '</td><td align="right">--></td></tr></table></div>';
				YUE.addListener('pageElement' + i, "click", playPageEvent, pageElement.dataB);
			}
		}
	}
}




