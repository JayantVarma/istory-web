import os
from google.appengine.ext.webapp import template
import cgi
import re
import logging
import StringIO
import struct
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import datastore
from google.appengine.api import memcache
from google.appengine.api import images
from django.utils import simplejson
import adventureModel
import main

class ImageCropper(webapp.RequestHandler):
  def getImageInfo(self, data):
	data = str(data)
	size = len(data)
	height = -1
	width = -1
	content_type = ''
	# handle GIFs
	if (size >= 10) and data[:6] in ('GIF87a', 'GIF89a'):
		# Check to see if content_type is correct
		content_type = 'image/gif'
		w, h = struct.unpack("<HH", data[6:10])
		width = int(w)
		height = int(h)
	# See PNG 2. Edition spec (http://www.w3.org/TR/PNG/)
	# Bytes 0-7 are below, 4-byte chunk length, then 'IHDR'
	# and finally the 4-byte width, height
	elif ((size >= 24) and data.startswith('\211PNG\r\n\032\n')
		  and (data[12:16] == 'IHDR')):
		content_type = 'image/png'
		w, h = struct.unpack(">LL", data[16:24])
		width = int(w)
		height = int(h)
	# Maybe this is for an older PNG version.
	elif (size >= 16) and data.startswith('\211PNG\r\n\032\n'):
		# Check to see if we have the right content type
		content_type = 'image/png'
		w, h = struct.unpack(">LL", data[8:16])
		width = int(w)
		height = int(h)
	# handle JPEGs
	elif (size >= 2) and data.startswith('\377\330'):
		content_type = 'image/jpeg'
		jpeg = StringIO.StringIO(data)
		jpeg.read(2)
		b = jpeg.read(1)
		try:
			while (b and ord(b) != 0xDA):
				while (ord(b) != 0xFF): b = jpeg.read
				while (ord(b) == 0xFF): b = jpeg.read(1)
				if (ord(b) >= 0xC0 and ord(b) <= 0xC3):
					jpeg.read(3)
					h, w = struct.unpack(">HH", jpeg.read(4))
					break
				else:
					jpeg.read(int(struct.unpack(">H", jpeg.read(2))[0])-2)
				b = jpeg.read(1)
			width = int(w)
			height = int(h)
		except struct.error:
			pass
		except ValueError:
			pass
	return content_type, width, height


  def post(self):
	image = None
	imageOBJ = None
	adventure = None
	left = None
	top = None
	right = None
	bottom = None
	newWidth = 0
	newHeight = 0
	imageKey = self.request.get('imageKey')
	try:
		left = float(self.request.get('left'))
		top = float(self.request.get('top'))
		newWidth = float(self.request.get('width'))
		newHeight = float(self.request.get('height'))
		right = newWidth + left
		bottom = newHeight + top
	except Exception, e:
		logging.error('%s: %s' % (e.__class__.__name__, e))
		self.error(404)
		return

	if imageKey:
		logging.error("attempting to resize image with key " + imageKey)
		try:
			image = db.get(imageKey)
		except Exception, e:
			logging.error('%s: %s' % (e.__class__.__name__, e))
	if image.imageData:
		logging.info("got image data.")
		adventure = image.adventure
		imageOBJ = images.Image(image.imageData)
	else:
		self.error(404)
		return

	#make sure the user is logged in and owns this adventure and page
	if users.get_current_user():
		if adventure and adventure.realAuthor and adventure.realAuthor != users.get_current_user():
			self.error(404)
			return
	else:
		self.error(404)
		return

	#get the image dimensions
	contentType, width, height = self.getImageInfo(image.imageData)
	logging.info("left(" + str(left) + ") right(" + str(right) + ") top(" + str(top) + ") bottom(" + str(bottom) + ") width(" + str(width) + ") height(" + str(height) + ")")
	
	#get the borders of the bounding box, as a proportion
	left_x = left / width;
	top_y = top / height;
	right_x = right / width;
	bottom_y = bottom / height;
	logging.info("left_x(" + str(left_x) + ") right_x(" + str(right_x) + ") top_y(" + str(top_y) + ") bottom_y(" + str(bottom_y) + ")")
	
	#now do the crop
	imageOBJ.crop(left_x, top_y, right_x, bottom_y)
	
	#if new width is over 300, resize it down to 300
	#if new height is over 500, resize it down to 500
	#we first have to try to do both and then we will see which results in a bigger ratio, then we do that one
	widthRatio = 0.0
	heightRatio = 0.0
	if newWidth > 300:
		widthRatio = newWidth / 300
	if newHeight > 500:
		#get the ratio of the change and apply the same to the height
		heightRatio = newHeight / 500
	if widthRatio > heightRatio:
		logging.info("resizing to: 300, " + str(int(heightRatio*newHeight)))
		imageOBJ.resize(300, int(heightRatio*newHeight))
	elif heightRatio > widthRatio:
		logging.info("resizing to: " + str(int(widthRatio*newWidth)) + ", 500")
		imageOBJ.resize(int(widthRatio*newWidth), 500)
	
	#now execute the transforms
	image.imageData = imageOBJ.execute_transforms()
	image.put()
		
	self.response.out.write(simplejson.dumps('success'))
	logging.error(simplejson.dumps('success'))

class ImageManager(webapp.RequestHandler):
  def get(self):
	adventure = None
	error = None
	if users.get_current_user():
		pass
	else:
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Please login to use the StoryForge'
		template_values = {
			'url': url,
			'url_linktext': url_linktext,
		}
		main.printHeader(self)
		path = os.path.join(os.path.dirname(__file__), 'pleaseLogin.html')
		self.response.out.write(template.render(path, template_values))
		main.printFooter(self, None)
		return
	
	myAdventureKey = self.request.get('myAdventureKey')
	if myAdventureKey:
		adventure = db.Model.get(myAdventureKey)
	else:
		error = 'error: no adventure key passed in'
	if adventure == None:
		error = 'error: could not find Adventure ' + myAdventureKey + ' in the database'
	elif users.get_current_user() != adventure.realAuthor:
		error = 'error: you do not own this story'
		adventure = None

	template_values = {
		'adventure': adventure,
		'error': error
	}

	main.printHeader(self, 'Image Manager')
	path = os.path.join(os.path.dirname(__file__), 'upload.html')
	self.response.out.write(template.render(path, template_values))
	main.printFooter(self, template_values)

class ImageServer(webapp.RequestHandler):
 def get(self):
	image = None
	imageKey = self.request.get('imageKey')
	if imageKey:
		logging.error("serving image with key " + imageKey)
		try:
			image = db.get(imageKey)
		except Exception, e:
			logging.error('%s: %s' % (e.__class__.__name__, e))
			#need to put an image in here that we can use for missing shit
			imageQuery = adventureModel.Image.all()
			images = imageQuery.fetch(1);
			for singleImage in images:
				image = singleImage
	if image.imageData:
		self.response.headers['Content-Type'] = 'image/png'
		self.response.out.write(image.imageData)
	else:
		self.error(404)
		return

class ImagesByUser(webapp.RequestHandler):
  def get(self):
	if users.get_current_user():
		pass
	else:
		self.error(404)
		return
	#get all the images that they own
	imgQuery = adventureModel.Image.all()
	imgQuery.filter('realAuthor = ', users.get_current_user())
	imgQuery.order('imageName')
	images = imgQuery.fetch(9999)
	jsonArray = []
	for image in images:
		jsonArray.append(image.toDict())
	self.response.out.write(simplejson.dumps(jsonArray))
	logging.error(simplejson.dumps(jsonArray))


class Uploader(webapp.RequestHandler):
  def post(self):
	logging.error("Uploader post start")
	pageElement = None
	adventure = None
	page = None
	newImage = None
	myImageKey = self.request.get('imageRef')
	myImageData = self.request.get('imageData')
	myImageName = self.request.get('imageName') or 'No Name'
	myPageElKey = self.request.get('myPageElKey')
	myPageKey = self.request.get('myPageKey')
	myPageOrder = int(self.request.get('myPageOrder') or -1)
	logging.error("Uploader: myImageKey(" + myImageKey + ") myPageElKey(" + myPageElKey + ") myPageKey(" + myPageKey + ") order(" + str(myPageOrder) + ")")
	if myImageData:
		logging.error("GOT IMAGE DATA!! " + str(len(myImageData)) + ' bytes.')
	if not myImageData and not myPageElKey and not myImageKey:
		self.error(404)
		return

	#try to get the existing page element, it might not exist
	if myPageElKey:
		pageElement = db.Model.get(myPageElKey)
		if pageElement:
			adventure = pageElement.adventure
			page = pageElement.page
		else:
			self.error(404)
			return		
	else:
		#we create the page element that will reference the new image
		logging.error('Uploader: creating new pageElement')
		pageElement = adventureModel.PageElement()
		pageElement.dataType = 2
		pageElement.enabled = 1
		pageElement.pageOrder = myPageOrder
		if (not myPageKey):
			logging.error("Uploader: expected myPageKey but it is null")
			if myImageData:
				self.response.out.write(simplejson.dumps(len(myImageData)))
			#self.error(404)
			return
		page = db.Model.get(myPageKey)
		adventure = page.adventure
		if not page or not adventure:
			self.error(404)
			return
		pageElement.adventure = adventure.key()
		pageElement.page = page.key()
		pageElement.put()

	#figure out which image to use
	#we might have a new page element and be trying to create it with an existing image (case 1)
	#we might have an existing page element with an image already there (case 2)
	#we need a new image (case 3)
	#in cases 1 and 2, we're also renaming the image (if a new name was given)
	if myImageKey:
		newImage = db.Model.get(myImageKey)
	elif pageElement.imageRef:
		newImage = pageElement.imageRef
	else:
		newImage = adventureModel.Image()

	if newImage.imageData and len(myImageData) > 100:
		#if the existing image data is different from the new image data, we need to create a new image
		#then set the image data, we dont need to set the image data if the old and new images are the same
		if newImage.imageData != myImageData:
			logging.error("the existing image data is different(" + str(len(myImageData)) + ").. lets create a new image")
			newImage = adventureModel.Image()
			newImage.imageData = db.Blob(myImageData)
	elif len(myImageData) > 100:
		#else its a new image, so save the image data from the form
		newImage.imageData = db.Blob(myImageData)

	if not page or not adventure:
		self.error(404)
		return

	#make sure the user is logged in and owns this adventure and page
	if users.get_current_user():
		if adventure.realAuthor and adventure.realAuthor != users.get_current_user():
			self.error(404)
			return
	else:
		self.error(404)
		return

	#now we read the image data from the form and save the image into the DB
	newImage.adventure = adventure.key()
	newImage.realAuthor = users.get_current_user()
	newImage.imageName = myImageName
	newImage.pageElement = str(pageElement.key())
	logging.error("imageName(" + newImage.imageName + ") pageElementRef(" + newImage.pageElement + ")")
	newImage.put()

	#now link the image to the new page element
	pageElement.imageRef = newImage.key()
	pageElement.dataA = newImage.imageName
	pageElement.put()

	#send the json response, it includes the page element key
	self.response.out.write(simplejson.dumps(newImage.toDict()))
	logging.error(simplejson.dumps(newImage.toDict()))