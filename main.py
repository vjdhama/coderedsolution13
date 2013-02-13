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
import webapp2, os, string, random, hmac, hashlib 
import jinja2
from google.appengine.ext import db

jinja_environment = jinja2.Environment(autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

def teams_key(group = 'default'):
      return db.Key.from_path('teams', group)

SECRET = 'rkuhoi$kjb&JKn%,kn&*@#'

questionNo = 1
questionSet = []

classMap = dict(qno = questionNo,class29= 'q', class28= 'q', class21= 'q', class20= 'q', class23= 'q', class22= 'q', class25= 'q', class24= 'q', class27= 'q', class26= 'q', class8= 'q', class9= 'q', class6= 'q', class7= 'q', class4= 'q', class5= 'q', class2= 'q', class3= 'q', class1= 'current', class30= 'q', class18= 'q', class19= 'q', class14= 'q', class15= 'q', class16= 'q', class17= 'q', class10= 'q', class11= 'q', class12= 'q', class13= 'q')

 
def check_secure_val(h):
      val= h.strip().split('|')[0]
      if h == make_secure_val(val):
            return val 

def hash_str(s):
      return hmac.new(SECRET,s).hexdigest()

def make_secure_val(s):
      return "%s|%s" % (s,hash_str(s))  
          
class Handler(webapp2.RequestHandler):
      def write(self, *a, **kw):
          self.response.out.write(*a, **kw)
        
      def render_str(self, template, **params):
          t = jinja_environment.get_template(template)
          return t.render(params)

      def render(self, template, **kw):
          self.write(self.render_str(template, **kw))
   
      def set_secure_cookie(self,name,val):
          cookie_val = make_secure_val(val)
          self.response.headers.add_header('Set-Cookie','%s=%s; Path=/' % (name, cookie_val))
          
      def read_secure_cookie(self, name):
          cookie_val = self.request.cookies.get(name)
          return cookie_val and check_secure_val(cookie_val)
          
      def login(self, team):
          self.set_secure_cookie('team_id', str(team.key().id()))
      
      def logout(self):
          self.response.headers.add_header('Set-Cookie','team_id=; Path=/')
          
      def initialize(self, *a, **kw):
          webapp2.RequestHandler.initialize(self, *a, **kw)
          teamid = self.read_secure_cookie('team_id')
          self.team = teamid and Register.by_id(int(teamid))  
         
      def getQuestion(self, cacheFlag = False):
          global questionNo, questionSet, classMap
          if cacheFlag == False:
               questionSet = db.GqlQuery("SELECT * FROM Question")
          else:
               self.write('cache')         
          classMap['question'] = questionSet[int(questionNo)-1].question
          classMap['choice1'] =  questionSet[int(questionNo)-1].choice_1
          classMap['choice2'] =  questionSet[int(questionNo)-1].choice_2
          classMap['choice3'] =  questionSet[int(questionNo)-1].choice_3
          classMap['choice4'] =  questionSet[int(questionNo)-1].choice_4      
          
                 
class MainHandler(Handler):
    def get(self):
          self.render('base.html')
          
    def post(self):           
          teamname = self.request.get('teamname')
          password = self.request.get('password')
          u = Register.login(teamname, password)
          
          if u:
              self.login(u)
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
     def by_id(cls, teamid):
         return Register.get_by_id(teamid, parent = teams_key()) 
                         
     @classmethod
     def login(cls, teamname, pw):
         u = cls.by_name(teamname)
         if u and valid_pw(pw, u.password):
              return u       
   
def valid_pw(pw, pwc):
    return pw == pwc    

def make_salt(length = 5):
    return ''.join(random.choice(string.letters) for x in xrange(length)) 
   
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
          check = self.read_secure_cookie('team_id')
          if check:
             self.render('instruction.html')
          else:
             self.redirect('/') 
          
          
      def post(self):
          global questionNo
          questionNo = 1
          self.redirect('/codered')    

kflag = False

class Codered(Handler):              
      def get(self):
          check = self.read_secure_cookie('team_id')
          if check:
              global questionNo
              self.getQuestion()                   
              self.render('start.html', **classMap)
          else:
             self.redirect('/') 
          
      def post(self):
          global questionNo, kflag , questionSet         
          choice = self.request.get('ch')# choice will contain the choice selected (one OR two OR three OR FOUR--REFER start.html)
          qNo = self.request.get('questionNo')
          if qNo != questionNo:
                  #if user goes to a different question
                  #kflag is used to check if the current question is alredy submitted
                  if qNo :
                      if kflag == False:
                             classMap['class'+str(questionNo)] ='q'
                      else:
                             classMap['class'+str(questionNo)] ='submitted'   
                      if classMap['class'+str(qNo)] == 'submitted' :
                             kflag = True  
                      else:
                             kflag = False       
                      
                      classMap['class'+str(qNo)] ='current'    
                      questionNo = qNo 
                      classMap['qno'] = questionNo       
                      
                    #if user presses submit button    
                  if not qNo:
                      submit = self.request.get('submit')   
                      if submit and choice:
                          classMap['class'+str(questionNo)] ='submitted'
                          temp = int(questionNo)
                          
                          while classMap['class'+str(temp)] =='submitted':
                              temp += 1
                              if temp > 30:
                                   temp = 1
                              if temp == int(questionNo):
                                   break
                          # 
                          if temp == int(questionNo):
                                    kflag = True 
                                    classMap['class'+str(temp)] ='submitted'             
                          else:          
                                    classMap['class'+str(temp)] ='current'   
                          questionNo = temp           
                          classMap['qno'] = questionNo 
                  self.getQuestion(True)                                                        
          self.render('start.html', **classMap)

class Logout(MainHandler):
      def get(self):
          self.logout()
          self.redirect('/') 

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/admin/register', RegisterHandler),
    ('/admin/question', QuesHandler),
    ('/instructions', Instruction),
    ('/codered', Codered),
    ('/logout', Logout),
], debug=True)
