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

def users_key(group = 'default'):
      return db.Key.from_path('users', group)

class Handler(webapp2.RequestHandler):
      def write(self, *a, **kw):
          self.response.out.write(*a, **kw)
        
      def render_str(self, template, **params):
          t = jinja_environment.get_template(template)
          return t.render(params)

      def render(self, template, **kw):
          self.write(self.render_str(template, **kw))

        

class MainHandler(Handler):
    def get(self):
          self.render('base.html')
          
    def post(self):           
          teamname = self.request.get('teamname')
          password = self.request.get('password')
          u = Register.login(teamname, password)
          
          if u:
              self.redirect('/instructions')
          else:
              msg = 'Invalid login'
              self.render('base.html', error = msg) 

class Register(db.Model):
     teamname = db.StringProperty(required = False)
     password = db.StringProperty(required = True)
     email = db.StringProperty(required = True)
    
     @classmethod
     def by_name(cls, teamname):
         u = Register.all().filter('teamname =', teamname).get()
         return u
         
                         
     @classmethod
     def login(cls, teamname, pw):
         u = cls.by_name(teamname)
         if u and valid_pw(pw, u.password):
              return u       
   
def valid_pw(pw, pwc):
    return pw == pwc    
   
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

class Question(db.Model):
    question = db.TextProperty(required = True)
    choice_1 = db.TextProperty(required = True)
    choice_2 = db.TextProperty(required = True)
    choice_3 = db.TextProperty(required = True)
    choice_4 = db.TextProperty(required = True)
    answer = db.TextProperty(required = True)

class QuesHandler(Handler):
    def get(self):
        self.render('ques.html')
    def post(self):
        ques = self.request.get('ques')
        ch1 = self.request.get('ch1')
        ch2 = self.request.get('ch2')
        ch3 = self.request.get('ch3')
        ch4 = self.request.get('ch4')
        ans = self.request.get('ans')
        Q = Question(question = ques,choice_1 =ch1,choice_2 = ch2,choice_3 = ch3,choice_4 = ch4,answer = ans)
        Q.put()
        self.redirect('/admin/question')

class Instruction(Handler):
      def get(self):
          self.render('instruction.html')
      
      def post(self):
          
          self.redirect('/codered')    

class Codered(Handler):              
      def get(self):
          self.render('start.html')
      
      def post(self):
          choice = self.request.get('ch')# choice will contain the option selected (one OR two OR three OR FOUR--REFER start.html)
          questionNo = self.request.get('questionNo')
          self.render('start.html', question = questionNo)

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/admin/register', RegisterHandler),
    ('/admin/question', QuesHandler),
    ('/instructions', Instruction),
    ('/codered', Codered),
], debug=True)
