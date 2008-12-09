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

class PageElement(db.Model):
	page = db.ReferenceProperty(Page)
	adventure = db.ReferenceProperty(Adventure)
	dataType = db.IntegerProperty()
	pageOrder = db.IntegerProperty()
	dataA = db.TextProperty()
	dataB = db.TextProperty()
	enabled = db.IntegerProperty()
	def toDict(self):
		return {
			'page': str(self.page.key()),
			'adventure': str(self.adventure.key()),
			'key': str(self.key()),
			'dataType': self.dataType,
			'pageOrder': self.pageOrder,
			'dataA': self.dataA,
			'dataB': self.dataB,
			'enabled': self.enabled,
		}
