from google.appengine.api import images

from google.appengine.ext import db
from google.appengine.ext import webapp

class Photo(db.Model):
  title = db.StringProperty()
  full_size_image = db.BlobProperty()

class Thumbnailer(webapp.RequestHandler):
  def get(self):
    if self.request.get("id"):
      photo = Photo.get_by_id(self.request.get("id")) 

      if photo:
        img = images.Image(photo.full_size_image)
        img.resize(width=80, height=100)
        img.im_feeling_lucky()
        thumbnail = img.execute_transforms(output_encoding=images.JPEG)

        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(thumbnail)
        return

    # Either "id" wasn't provided, or there was no image with that ID
    # in the datastore.
    self.error(404)