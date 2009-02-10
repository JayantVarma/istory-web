//Add an onDOMReady handler to build the tree when the document is ready
YAHOO.util.Event.onDOMReady(treeInit);
//set shortcuts for common yahoo stuff
var YUD = YAHOO.util.Dom, YUE = YAHOO.util.Event, YUC = YAHOO.util.Connect;

//if there is no console, set it to null
try { console.log('init console... done'); } catch(e) { console = { log: function() {} } }

//we also expect the variable MY_ADVENTURE_KEY to be set from the footer
var adventureKey = '';
var myError = '';
if (MY_ADVENTURE_KEY) {
	adventureKey = MY_ADVENTURE_KEY;
}
if (MY_ERROR) {
	myError = MY_ERROR;
}

//get existing vote data from python
var myVote = null;
var myVoteComment = null;
if (MY_VOTE) {
	myVote = MY_VOTE;
	myVoteComment = MY_VOTE_COMMENT;
}

//setup some globals
var loadingCounter = 0;
var numPages = 0;
var keyToPageIdMap = {};
var pageHistory = [];
var alreadySelectedStars = false;
var page;
var SS = {};
var ifBlocked = false;
var ifBlockResult = [];
var backDisabled = false;

function treeInit() {
	// Make the call to the server for JSON data
	setLoading();
	if (myError) {
		YUD.get('player').innerHTML = myError;
		return;
	}
	YUC.asyncRequest('POST',"/getPages?myAdventureKey=" + adventureKey, getPagesCallbacks);
	YAHOO.util.Event.addListener("restartStory", "mouseover", eventIconMO);
	YAHOO.util.Event.addListener("restartStory", "mouseout", eventIconMOreset);
	YAHOO.util.Event.addListener("restartStory", "click", restartStory);
	if (IS_USER_AUTHOR) {
		YAHOO.util.Event.addListener("storyForge", "mouseover", eventIconMO);
		YAHOO.util.Event.addListener("storyForge", "mouseout", eventIconMOreset);
		YAHOO.util.Event.addListener("storyForge", "click", loadStoryForge);
	}
	if (IS_USER_ADMIN) {
		YAHOO.util.Event.addListener("shareStory", "mouseover", eventIconMO);
		YAHOO.util.Event.addListener("shareStory", "mouseout", eventIconMOreset);
		YAHOO.util.Event.addListener("shareStory", "click", loadShareStory);
		YAHOO.util.Event.addListener("submitStory", "mouseover", eventIconMO);
		YAHOO.util.Event.addListener("submitStory", "mouseout", eventIconMOreset);
		YAHOO.util.Event.addListener("submitStory", "click", loadSubmitStory);
	}
	//for voting stars
	for (var i = 1; i <= 5; i++) {
		YAHOO.util.Event.addListener("star" + i, "mouseover", starMO, i);
		YAHOO.util.Event.addListener("star" + i, "mouseout", starMOreset, i);
		YAHOO.util.Event.addListener("star" + i, "click", starClick, i);
	}
	YAHOO.util.Event.on('voteForm', 'submit', function(e) {
		YAHOO.util.Event.stopEvent(e);
		sendVote();
	});
	
	//see if the user has already voted
	if (myVote) {
		starClick(null, myVote);
		if (myVoteComment) {
			YUD.get("voteComment").innerHTML = myVoteComment;
		}
	}
}

var starMO = function(e, starNumber) {
	if (alreadySelectedStars) { return; }
	for (var i = 1; i <= starNumber; i++) {
		var td = YUD.get("star" + i);
		var icon = td.firstChild;
		icon.className = "icon-starFull";
	}
}
var starMOreset = function(e, starNumber) {
	if (alreadySelectedStars) { return; }
	for (var i = 1; i <= starNumber; i++) {
		var td = YUD.get("star" + i);
		var icon = td.firstChild;
		icon.className = "icon-starEmpty";
	}
}
var starClick = function(e, starNumber) {
	//console.log(starNumber);
	alreadySelectedStars = false;
	starMOreset(null, 5);
	starMO(null, starNumber);
	alreadySelectedStars = true;
	YUD.get("voteValue").value = starNumber;
}

var sendVote = function() {
	if (loadingCounter > 0) { return; }
	setLoading();
	YAHOO.util.Connect.setForm('voteForm', false);
	YAHOO.util.Connect.asyncRequest('POST', '/vote', voteCallbacks);
}

// Define the callbacks for getPages
var voteCallbacks = {
	success : function (o) {
		setLoaded();
		alreadyVoted = true;
		YUD.get("voteBottom").innerHTML = o.responseText;
	},
	failure : function (o) {
		if (!YUC.isCallInProgress(o)) {
			alert("voting failed!");
		}
	},
	timeout : 30000
}

var loadStoryForge = function() {
	window.location = '/storyEditor?myAdventureKey=' + adventureKey;
}
var loadShareStory = function() {
	window.location = '/share?myAdventureKey=' + adventureKey;
}
var loadSubmitStory = function() {
	window.location = '/submit?myAdventureKey=' + adventureKey;
}
var restartStory = function() {
	resetSS();
	pageHistory = [];
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
	disableDiv('shareStory');
}
var enableIcons = function()
{
	if (loadingCounter > 0) { return; }
	enableDiv('restartStory');
	if (IS_USER_AUTHOR) { enableDiv('storyForge'); }
	if (IS_USER_ADMIN) {
		enableDiv('shareStory');
		enableDiv('submitStory');
	}
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
var iconDisable = function(td, lightFlag) {
	if (!lightFlag) { td.className = 'iconBG-disabled'; }
	var icon = td.firstChild;
	if (icon.className.substr((icon.className.length-2), 2) == 'MO') {
		icon.className = icon.className.substr(0, (icon.className.length-2) );
	}
	if (icon.className.substr((icon.className.length-1), 1) == 'D') {
		icon.className = icon.className.substr(0, (icon.className.length-1) );
	}
	icon.className = icon.id + 'D';
}

var disableDiv = function(name, lightFlag) {
	var td = YAHOO.util.Dom.get(name);
	iconDisable(td, lightFlag);
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
		if (pages[0]) {
			playPage(pages[0].key)
		}
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
	//console.log("playing page: " + e + ', ' + pageKey);
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
		//console.log("going back.. previous key: " + previousKey);
		playPage(previousKey);
	}
	else {
		//if we are here that means we emptied out the history, which is bad
		//we should re-add the discarded element
		//console.log("going back.. added discarded key: " + discarded);
		pageHistory.push(discarded);
	}
}

var playPage = function(pageKey) {
	//console.log('playPage: ' + pageKey);
	workArea = YUD.get('player');
	page = pages[keyToPageIdMap[pageKey]];
	//add the last page to the history
	pageHistory.push(pageKey);
	//console.log("adding key to history: " + pageKey);
	//create the back button and title, and tooltip for the back button
	workArea.innerHTML = '<div><table width="100%"><tr><td id="back" class="iconBG-disabled2" width="48px"><div id="icon-back" class="icon-back"></td><td><h1>' + page.name + '</h1></td><td width="48px"></td></tr></table></div>';
	//if the pagehistory only has 1 element in it, change the icon class to disabled
	if (pageHistory.length == 1 || backDisabled) {
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
	//go through each page element and reset the view status to shown for each page element
	for (var i = 0; i < page.elements.length; i++) {
		var pageElement = page.elements[i];
		pageElement.hidden = false;
	}
	//go through each page element for this page and add it to the HTML
	for (var i = 0; i < page.elements.length; i++) {
		var pageElement = page.elements[i];
		if (pageElement.hidden) { continue; }
		//create a new div that we can append to workArea
		var newDiv = document.createElement('div');
		newDiv.id = "pageElement" + i;
		workArea.appendChild(newDiv);

		//console.log("got page element of type: " + pageElement.dataType);
		if (pageElement.dataType == 1) {
			//text element
			//console.log("page element text: " + pageElement.dataA.substr(0, 20));
			if (pageElement.dataA) {
				//console.log(pageElement.dataA);
				var myPageText = storyScript(pageElement.dataA);
				myPageText = myPageText.replace(/\n/g, '<br>');
				newDiv.innerHTML = '<div class="playerSmall">' + myPageText + '</div>';
			}
		}
		if (pageElement.dataType == 2) {
			//image element
			//console.log("page element image: " + pageElement.dataA);
			if (pageElement.dataA) {
				newDiv.innerHTML = '<div class="playerSmall"><center><img src="/images?imageKey=' + pageElement.imageRef + '"></center></div>';
			}
		}
		if (pageElement.dataType == 3) {
			//choice element
			//console.log("page element choice: " + pageElement.dataA + ", " + pageElement.dataB + ', ' + i);
			if (pageElement.dataA) {
				newDiv.innerHTML = '<div class="playerSmallChoice" id="choiceClick' + i + '"><table width="100%"><tr><td align="left">' + pageElement.dataA + '</td><td align="right" width="25px">--></td></tr></table></div>';
				YUE.addListener('pageElement' + i, "click", playPageEvent, pageElement.dataB);
			}
		}
	}
	console.log(SS);
}

var storyScript = function(inputText) {
	var bracketMatcher = /{{.*?}}/g;
	var outputText = '';

	//go through line by line
	var lines = inputText.split(/\n/);
	for (var lineNumber = 0; lineNumber < lines.length; lineNumber++) {
		line = lines[lineNumber];
		//console.log("line: " + line);
		//console.log("ifBlocked(%s)", ifBlocked);
		//console.log(ifBlockResult);
		//first loop through and get everything inside of double curly brackets {{ }}
		var brackets = line.match(bracketMatcher);
		if (brackets == null) {
			if (ifBlocked == false) {
				outputText += line + "\n";
			}
			continue;
		}
		//disable going back, we can't really handle it when we have variables too
		backDisabled = true;
		//now loop through each curly bracket
		for (var n = 0; n < brackets.length; n++) {
			bracket = brackets[n];
			//get the new ifstatus
			var ifResult = parseScriptForIfs(bracket);
			//see if we got ifs back, if we did then we parsed an if statement, so we can go onto the next bracket
			if (ifResult == "GOT IFS") {
				line = line.replace(/{{.*?}}/, '');
				continue;
			}
			if (ifBlocked == true) {
				line = '';
			}
			else {
				//parse what is inside the brackets
				var result = parseScriptForData(bracket);
				if (result != null) {
					//replace the curly bracket expression with the result
					line = line.replace(/{{.*?}}/, result);
				}
			}
		}
		if (line.length > 0) { line += "\n"; }
		outputText += line;
	}
	return outputText;
}

var parseScript = function(bracket) {
	//this function just turns the script command that is in brackets into tokens for processing
	//first get rid of the brackets
	bracket = bracket.replace(/{|}/g, '');
	//remove leading and trailing spaces
	bracket = bracket.replace(/^\s+/, '');
	bracket = bracket.replace(/\s+$/, '');

	//split the string up based on spaces
	tokens = bracket.split(/\s+/);
	
	//console.log('ParseScript: ' + bracket);
	//console.log(tokens);
	return tokens;
}

var parseScriptForData = function(bracket) {
	var tokens = parseScript(bracket);
	if (tokens.length == 0) { return 'NO TOKEN'; }
	var primaryToken = tokens.shift();
	
	//just return the value of the variable
	if (tokens.length == 0) {
		return getValueForToken(primaryToken);
	}

	var primaryOperator = tokens.shift();
	
	//see if we're doing a simple variable set
	if (primaryOperator == '=') {
		//combine all the rest of the tokens and set it equal to the primaryToken
		SS[primaryToken] = combineArrayOfTokens(tokens);
		return '';
	}
	else {
		//add the primary token and primary operator back on, we need to add everything up
		tokens.unshift(primaryOperator);
		tokens.unshift(primaryToken);
		return(combineArrayOfTokens(tokens));
	}
	
	return null;
}

var parseScriptForIfs = function(tokens) {
	var tokens = parseScript(bracket);
	if (tokens.length == 0) { return 'NO TOKEN'; }
	var primaryToken = tokens.shift();
	if (primaryToken == 'ifequal' || primaryToken == 'ifgt' || primaryToken == 'iflt' || primaryToken == 'ifge' || primaryToken == 'ifle') {
		if (ifBlocked) {
			ifBlockResult.unshift(-1);
			return "GOT IFS";
		}
		if (processIf(primaryToken, tokens)) {
			ifBlockResult.unshift(1);
			ifBlocked = false;
		}
		else {
			ifBlockResult.unshift(0);
			ifBlocked = true;
		}
	}
	else if (primaryToken == 'else') {
		if (ifBlockResult.length == 0) {
			alert("ERROR: else block with no matching if");
			return null;
		}
		if (ifBlocked && ifBlockResult[0] == -1) {
			return "GOT IFS";
		}
		if (ifBlockResult[0] == 1) {
			ifBlocked = true;
			ifBlockResult[0] = 0;
		}
		else {
			ifBlocked = false;
			ifBlockResult[0] = 1;
		}
	}
	else if (primaryToken == 'endif') {
		ifBlockResult.shift();
		ifBlocked = true;
		if (ifBlockResult.length == 0 || ifBlockResult[0] == 1) {
			ifBlocked = false;
		}
	}
	else {
		return "NO IFS";
	}
	tokens.shift();
	return "GOT IFS";
}

var processIf = function(ifType, tokens) {
	//make sure we have 2 more tokens
	if (tokens.length != 2) {
		alert("ERROR: if statements take 2 arguments");
		return null;
	}
	var retval = false;
	var firstToken = getValueForToken(tokens.shift());
	var secondToken = getValueForToken(tokens.shift());
	if (ifType == 'ifequal') {
		if (firstToken == secondToken) { retval = true; }
	}
	else if (ifType == 'ifgt') {
		if (firstToken > secondToken) { retval = true; }
	}
	else if (ifType == 'ifge') {
		if (firstToken >= secondToken) { retval = true; }
	}
	else if (ifType == 'iflt') {
		if (firstToken < secondToken) { retval = true; }
	}
	else if (ifType == 'ifle') {
		if (firstToken <= secondToken) { retval = true; }
	}
	else {
		alert("ERROR: unknown if operator: " + primaryToken);
		return null;
	}
	//console.log("IFRESULT: %s %s %s : %s", ifType, firstToken, secondToken, retval);
	return retval;
}

var combineArrayOfTokens = function(tokens) {
	//keep looping until we run out of tokens
	//this is kind of a reverse polish notation processor
	var iterations = 0;
	
	while (tokens.length > 0 && iterations < 50) {
		iterations++;
		//console.log("TOKENS: ");
		//console.log(tokens);
		//shift off the first token, we will add to this if there are any more
		var firstToken = tokens.shift();

		//we need to have at least 1 tokens left
		if (tokens.length < 1) {
			return getValueForToken(firstToken);
		}

		//process the simple hide / show stuff first
		if (firstToken == 'hide') {
			if (tokens.length < 1) {
				alert("ERROR: hide requires 1 argument, the page element to hide");
				return("ERROR: hide requires 1 argument, the page element to hide");
			}
			var secondToken = tokens.shift();
			page.elements[secondToken].hidden = true;
			return '';
		}
		else if (firstToken == 'show') {
			if (tokens.length < 1) {
				alert("ERROR: show requires 1 argument, the page element to hide");
				return("ERROR: show requires 1 argument, the page element to hide");
			}
			var secondToken = tokens.shift();
			page.elements[secondToken].hidden = false;
			return '';
		}

		//we need to have at least 2 tokens left
		if (tokens.length < 2) {
			return getValueForToken(firstToken);
		}

		//this means we have atleast 2 tokens left, so we must be trying to do something like 3 + 4 or random 3 4
		var secondToken = tokens.shift();
		var thirdToken = tokens.shift();
		//check primary token for reserved keywords
		if (firstToken == 'random') {
			var runningValue = randomTokens(secondToken, thirdToken);
			tokens.unshift(runningValue);
		}
		else if (secondToken == 'random') {
			if (tokens.length >= 1) {
				var fourthToken = tokens.shift();
				var runningValue = randomTokens(thirdToken, fourthToken);
				tokens.unshift(runningValue);
				tokens.unshift(firstToken);
			}
			else {
				alert("ERROR: invalid number of tokens with random");
				return "ERROR: invalid number of tokens with random";
			}
		}
		else if (thirdToken == 'random') {
			if (tokens.length >= 2) {
				var fourthToken = tokens.shift();
				var fifthToken = tokens.shift();
				var runningValue = randomTokens(fourthToken, fifthToken);
				tokens.unshift(runningValue);
				tokens.unshift(secondToken);
				tokens.unshift(firstToken);
			}
			else {
				alert("ERROR: invalid number of tokens with random");
				return "ERROR: invalid number of tokens with random";
			}
		}
		else {
			//this must be a basic math operation
			var runningValue = combineTokens(firstToken, secondToken, thirdToken);
			tokens.unshift(runningValue);
		}
	}
	return null;
}

var randomTokens = function(low, high) {
	low = getValueForToken(low);
	high = getValueForToken(high);
	var diff = high - low;
	var randomValue = Math.floor(Math.random() * (diff+1)) + low;
	//console.log("randomTokens: " + randomValue);
	return randomValue;
}

var combineTokens = function(_numA, myOperator, _numB) {
	//console.log("combineTokens: " + _numA + "," + _numB);
	var numA = getValueForToken(_numA);
	var numB = getValueForToken(_numB);
	if      (myOperator == '+') { numA = numA + numB; }
	else if (myOperator == '-') { numA = numA - numB; }
	else if (myOperator == '*') { numA = numA * numB; }
	else if (myOperator == '/') { numA = numA / numB; }
	else {
		alert("Invalid operator: " + bracket);
		return "(ERROR invalid operator)";
	}
	//console.log("combineTokens: " + numA);
	return numA;
}

var getValueForToken = function(token) {
	//first see if its a number
	numberResult = parseInt(token);
	if (numberResult || numberResult == 0) {
		return numberResult;
	}
	//else return its stored value
	if (SS[token]) {
		return SS[token];
	}
	else { return 0; }
}

var resetSS = function() {
	for (var key in SS) {
		//console.log("reset %s,%s", key, SS[key]);
		SS[key] = null;
	}
}