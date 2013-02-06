#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2, os, string, random 
import jinja2
from google.appengine.ext import db

jinja_environment = jinja2.Environment(autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
        
    def render_str(self, template, **params):
        t = jinja_environment.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class Register(db.Model):
    teamname = db.StringProperty(required = False)
    password = db.StringProperty(required = True)
    email = db.StringProperty(required = True)

class MainHandler(Handler):
    def get(self):
        self.render("base.html")
    def post(self):
        self.render("base.html")

class RegisterHandler(Handler):
    def make_pass(self):
        return ''.join(random.choice(string.letters) for x in xrange(5))
    def get(self):
        self.render('reg.html')
    def post(self):
        team = self.request.get('team')
        mail = self.request.get('email')
        pasw = self.make_pass()
        Regstr = Register(teamname = team,password = pasw,email = mail)
        Regstr.put()
        self.redirect('/')


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/admin/register', RegisterHandler)
], debug=True)
