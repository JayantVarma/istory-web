// Custom URL for the uploader swf file (same folder).
YAHOO.widget.Uploader.SWFURL = "uploader.swf";

   // Instantiate the uploader and write it to its placeholder div.
var uploader = new YAHOO.widget.Uploader( "uploaderOverlay" );

// Add event listeners to various events on the uploader.
// Methods on the uploader should only be called once the 
// contentReady event has fired.

uploader.addListener('contentReady', handleContentReady);
uploader.addListener('fileSelect', onFileSelect)
uploader.addListener('uploadStart', onUploadStart);
uploader.addListener('uploadProgress', onUploadProgress);
uploader.addListener('uploadCancel', onUploadCancel);
uploader.addListener('uploadComplete', onUploadComplete);
uploader.addListener('uploadCompleteData', onUploadResponse);
uploader.addListener('uploadError', onUploadError);
uploader.addListener('rollOver', handleRollOver);
uploader.addListener('rollOut', handleRollOut);
uploader.addListener('click', handleClick);
   	
   // Variable for holding the selected file id.
var fileID;

// When the mouse rolls over the uploader, this function
// is called in response to the rollOver event.
// It changes the appearance of the UI element below the Flash overlay.
function handleRollOver () {
	YAHOO.util.Dom.setStyle(YAHOO.util.Dom.get('selectLink'), 'color', "#FFFFFF");
	YAHOO.util.Dom.setStyle(YAHOO.util.Dom.get('selectLink'), 'background-color', "#000000");
}

// On rollOut event, this function is called, which changes the appearance of the
// UI element below the Flash layer back to its original state.
function handleRollOut () {
	YAHOO.util.Dom.setStyle(YAHOO.util.Dom.get('selectLink'), 'color', "#0000CC");
	YAHOO.util.Dom.setStyle(YAHOO.util.Dom.get('selectLink'), 'background-color', "#FFFFFF");
}

// When the Flash layer is clicked, the "Browse" dialog is invoked.
// The click event handler allows you to do something else if you need to.
function handleClick () {
}

// When contentReady event is fired, you can call methods on the uploader.
function handleContentReady () {
    // Allows the uploader to send log messages to trace, as well as to YAHOO.log
	uploader.setAllowLogging(true);
	
	// Disallows multiple file selection in "Browse" dialog.
	uploader.setAllowMultipleFiles(false);
	
	// New set of file filters.
	var ff = new Array({description:"Images", extensions:"*.jpg;*.png;*.gif"},
	                   {description:"Videos", extensions:"*.avi;*.mov;*.mpg"});
	                   
	// Apply new set of file filters to the uploader.
	uploader.setFileFilters(ff);
}

// Actually uploads the files. Since we are only allowing one file
// to be selected, we use the upload function, in conjunction with the id 
// of the selected file (returned by the fileSelect event). We are also including
// the text of the variables specified by the user in the input UI.

function upload() {
if (fileID != null) {
	uploader.upload(fileID, "http://www.yswfblog.com/upload/upload.php", 
	                "POST", 
	                {var1:document.getElementById("var1Value").value,
					 var2:document.getElementById("var2Value").value});
}	
}

// Fired when the user selects files in the "Browse" dialog
// and clicks "Ok". Here, we set the value of the progress
// report textfield to reflect the fact that a file has been
// selected.

function onFileSelect(event) {
	for (var file in event.fileList) {
	    if(YAHOO.lang.hasOwnProperty(event.fileList, file)) {
			fileID = event.fileList[file].id;
		}
	}
	
	this.progressReport = document.getElementById("progressReport");
	this.progressReport.value = "Selected " + event.fileList[fileID].name;
}


   // When the upload starts, we inform the user about it via
// the progress report textfield. 
function onUploadStart(event) {
	this.progressReport.value = "Starting upload...";
}

// As upload progresses, we report back to the user via the
// progress report textfield.
function onUploadProgress(event) {
	prog = Math.round(100*(event["bytesLoaded"]/event["bytesTotal"]));
	this.progressReport.value = prog + "% uploaded...";
}

// Report back to the user that the upload has completed.
function onUploadComplete(event) {
	this.progressReport.value = "Upload complete.";
}

// Report back to the user if there has been an error.
function onUploadError(event) {
	this.progressReport.value = "Upload error.";
}

// Do something if an upload is canceled.
function onUploadCancel(event) {

}

// When the data is received back from the server, display it to the user
// in the server data text area.
function onUploadResponse(event) {
	this.serverData = document.getElementById("serverData");
	this.serverData.value = event.data;
}