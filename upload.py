import os
from google.appengine.ext.webapp import template
import cgi
import re
import logging
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import datastore
from google.appengine.api import memcache
from django.utils import simplejson
import adventureModel
import main

class ImageManager(webapp.RequestHandler):
  def get(self):
	adventure = None
	error = None
	if users.get_current_user():
		pass
	else:
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Please login to use the Story Editor'
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
		image = db.get(imageKey)
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
		logging.error("GOT IMAGE DATA!!")
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
		pageElement = adventureModel.PageElement()
		pageElement.dataType = 2
		pageElement.enabled = 1
		pageElement.pageOrder = myPageOrder
		if (not myPageKey):
			logging.error("Uploader: expected myPageKey but it is null")
			self.error(404)
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
	if myImageData:
		newImage.imageData = db.Blob(myImageData)
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
