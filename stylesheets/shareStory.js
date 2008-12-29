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

//setup some globals
var myDialog;


function treeInit() {
	myDialog = new YAHOO.widget.Dialog("dialogAddNewShare",
	{
		width: "30em",
		fixedcenter: true,
		visible: false,
		constraintoviewport: true,
		buttons: [
			{ text:"Submit", handler:ShareFormSubmit, isDefault:true },
			{ text:"Cancel", handler:ShareFormCancel }
		]
	} );
	myDialog.callback.success = ShareFormSuccess;
	myDialog.callback.failure = ShareFormFailure;
	
	myRemoveDialog = new YAHOO.widget.Dialog("dialogRemoveShare",
	{
		width: "30em",
		fixedcenter: true,
		visible: false,
		constraintoviewport: true,
		buttons: [
			{ text:"Remove Share", handler:RemoveShareFormSubmit, isDefault:true },
			{ text:"Cancel", handler:RemoveShareFormCancel }
		]
	} );
	myRemoveDialog.callback.success = RemoveShareFormSuccess;
	myRemoveDialog.callback.failure = RemoveShareFormFailure;
}

//############ ADD NEW SHARE
var ShareFormCancel = function() {
	console.log("cancelling form");
	this.cancel();
}
var ShareFormSubmit = function() {
	console.log("submitting form");
	this.submit();
}
var ShareFormSuccess = function(o) {
	var m = [];
	try {
		m = YAHOO.lang.JSON.parse(o.responseText);
	}
	catch (x) {
		alert(o.responseText);
		return;
	}
	console.log(o.responseText);
	console.log("shareStory: success");
	YUD.get("infoBar").innerHTML = 'An invite has been sent to ' + m.childEmail;
	YUD.get("infoBar").style.display = "block";
}
var ShareFormFailure = function(o) {
	console.log("shareStory: fail");
}
//#######

//####### REMOVE SHARE
var RemoveShareFormCancel = function() {
	console.log("cancelling form");
	this.cancel();
}
var RemoveShareFormSubmit = function() {
	console.log("submitting form");
	this.submit();
}
var RemoveShareFormSuccess = function(o) {
	var m = [];
	try {
		m = YAHOO.lang.JSON.parse(o.responseText);
	}
	catch (x) {
		alert(o.responseText);
		return;
	}
	console.log(o.responseText);
	console.log("shareStory: remove success");
	YUD.get("infoBar").innerHTML = 'This story is no longer shared with ' + m.childEmail;
	YUD.get("infoBar").style.display = "block";
}
var RemoveShareFormFailure = function(o) {
	console.log("shareStory: fail");
}
//#############

var shareForm = function(adventureKey) {
	YUD.get("dialogHeader").innerHTML = YUD.get("storyName").innerHTML;
	YUD.get("shareFormAdventureKey").value = adventureKey;
	console.log("showing add share form for key: " + adventureKey);
	myDialog.render();
	myDialog.show();
}

var removeShare = function(shareKey) {
	YUD.get("dialogRemoveHeader").innerHTML = YUD.get("sharePerson").innerHTML;
	YUD.get("shareKey").value = shareKey;
	console.log("showing remove share form for key: " + shareKey);
	myRemoveDialog.render();
	myRemoveDialog.show();
}


