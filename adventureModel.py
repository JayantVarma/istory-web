from google.appengine.ext import db

class Adventure(db.Model):
	title = db.StringProperty(multiline=False)
	realAuthor = db.UserProperty()
	author = db.StringProperty(multiline=False)
	version = db.StringProperty(multiline=False)
	date = db.DateTimeProperty(auto_now_add=True)
	desc = db.TextProperty()

class Page(db.Model):
	adventure = db.ReferenceProperty(Adventure)
	name = db.StringProperty()
	def toDict(self):
		return {
			#'adventure': str(self.adventure.key()),
			'key': str(self.key()),
			'name': self.name,
		}

class Image(db.Model):
	adventure = db.ReferenceProperty(Adventure)
	pageElement = db.StringProperty(multiline=False)
	imageName = db.StringProperty(multiline=False)
	imageData = db.BlobProperty()
	realAuthor = db.UserProperty()
	def toDict(self):
		return {
			'adventure': str(self.adventure.key()),
			'imageName': self.imageName,
			'realAuthor': str(self.realAuthor.nickname()),
			'key': str(self.key()),
			'pageElement': self.pageElement,
		}

class PageElement(db.Model):
	page = db.ReferenceProperty(Page)
	adventure = db.ReferenceProperty(Adventure)
	dataType = db.IntegerProperty()
	pageOrder = db.IntegerProperty()
	dataA = db.TextProperty()
	dataB = db.TextProperty()
	imageRef = db.ReferenceProperty(Image)
	enabled = db.IntegerProperty()
	def toDict(self):
		imageRef = None
		if self.imageRef:
			imageRef = str(self.imageRef.key())
		return {
			'page': str(self.page.key()),
			'adventure': str(self.adventure.key()),
			'key': str(self.key()),
			'dataType': self.dataType,
			'pageOrder': self.pageOrder,
			'dataA': self.dataA,
			'dataB': self.dataB,
			'enabled': self.enabled,
			'imageRef': imageRef,
		}
