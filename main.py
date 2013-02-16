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
questionSet = {}
solution = dict(solved = [], correct = 0, wrong = 0, totalAttempted = 0, score = 0)
classMap = dict(timer1= '00',timer2 = '31', qno = questionNo, class29= 'q', class28= 'q', class21= 'q', class20= 'q', class23= 'q', class22= 'q', class25= 'q', class24= 'q', class27= 'q', class26= 'q', class8= 'q', class9= 'q', class6= 'q', class7= 'q', class4= 'q', class5= 'q', class2= 'q', class3= 'q', class1= 'current', class30= 'q', class18= 'q', class19= 'q', class14= 'q', class15= 'q', class16= 'q', class17= 'q', class10= 'q', class11= 'q', class12= 'q', class13= 'q')
adminname = ''
pword = ''
 
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
          self.set_secure_cookie('team_id', str(team.teamname))
      
      def logout(self):
          self.response.headers.add_header('Set-Cookie','team_id=; Path=/')
          
      def initialize(self, *a, **kw):
          webapp2.RequestHandler.initialize(self, *a, **kw)
          teamid = self.read_secure_cookie('team_id')
          self.team = teamid and Register.by_name(teamid)  
         
      def getQuestion(self, cacheFlag = False):
          global questionNo, questionSet, solution, classMap
          if cacheFlag == False:
                query = Question.all()
                qdir = {}#for storing all questions
                key = 0#for key in qdir
                for ques in query:
                    key = key + 1
                    qdir[key] = [ques.question,ques.choice_1,ques.choice_2,ques.choice_3,ques.choice_4,ques.answer]#qdir = {key : list}
                    
                a = random.randint(1,key-3)
                newkey = 0
                for x in xrange(a,a+4):
                    newkey = newkey + 1
                    questionSet[newkey] = qdir[x]
          else:
               pass        
          classMap['question'] = questionSet[int(questionNo)][0]
          classMap['choice1'] =  questionSet[int(questionNo)][1]
          classMap['choice2'] =  questionSet[int(questionNo)][2]
          classMap['choice3'] =  questionSet[int(questionNo)][3]
          classMap['choice4'] =  questionSet[int(questionNo)][4]      
      
      def reset(self):
          global questionNo, classMap, solution
          questionNo = 1
          for x in range(1, 31):
              classMap['class' + str(x)] = 'q'
              solution[x] = None
          solution['correct'] = 0
          solution['wrong'] = 0
          solution['totalAttempted'] = 0
          solution['score'] = 0   
          classMap['timer1'] = '00'
          classMap['timer2'] = '31'
          classMap['class1'] = 'current' 
          classMap['qno'] = 1
          del solution['solved']
          solution['solved'] = []

class MainHandler(Handler):
    def get(self):
        if (str(self.request.remote_addr) in ['127.0.0.1','203.199.146.114']): # add the list of allowed ip's
            self.render('base.html')
        else:
            self.render('403.html') #Access denied. maybe use a HTML PAGE
          
    def post(self):           
          teamname = self.request.get('teamname')
          password = self.request.get('password')
          u = Register.login(teamname, password)
          
          if u:
              self.login(u)
              self.reset()
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
        if adminname and pword:
            self.render('reg.html')
        else:
            self.render('403.html')

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
    
class Scorecard(db.Model):
    teamname = db.TextProperty(required = True)    
    attempted = db.TextProperty(required = True)
    correct = db.TextProperty(required = True)
    score = db.TextProperty(required = True)

class QuesHandler(Handler):
    def get(self):
        if adminname and pword:
            self.render('ques.html')
        else:
            self.render('403.html')

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
          self.redirect('/codered')    

quesAlreadySubmitted = False
def setScore(choice):
      global questionNo, solution
      if int(questionNo) not in solution['solved']:
          solution['solved'].append(int(questionNo))
          if int(questionSet[int(questionNo)][5]) == int(choice):
                 solution['correct'] += 1
          else:
                 solution['wrong'] += 1
          solution['totalAttempted'] += 1              


class Codered(Handler):              
      def get(self):
          check = self.read_secure_cookie('team_id')
          if check:
              self.getQuestion()          
              self.render('start.html', **classMap)
          else:
             self.redirect('/') 
          
      def post(self):
          global questionNo, quesAlreadySubmitted , questionSet, classMap, solution 
          classMap['timer1'] = self.request.get('timer1')  
          classMap['timer2'] = self.request.get('timer2')  
          completed = self.request.get('viewscore')
          if completed:
              self.redirect('/score')
          choice = self.request.get('ch')# choice will contain the choice selected (one OR two OR three OR FOUR--REFER start.html)
          qNo = self.request.get('questionNo')
          if qNo != questionNo:
                  #if user goes to a different question
                  #quesAlreadySubmitted is used to check if the current question is alredy submitted
                  if qNo :
                      if quesAlreadySubmitted == False:
                             classMap['class'+str(questionNo)] ='q'
                      else:
                             classMap['class'+str(questionNo)] ='submitted'   
                      if classMap['class'+str(qNo)] == 'submitted' :
                             quesAlreadySubmitted = True  
                      else:
                             quesAlreadySubmitted = False       
                      
                      classMap['class'+str(qNo)] ='current'    
                      questionNo = qNo 
                      classMap['qno'] = questionNo       
                      
                    #if user presses submit button    
                  if not qNo:
                      submit = self.request.get('submit')   
                      if submit and choice:
                          setScore(choice)
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
                                    quesAlreadySubmitted = True 
                                    classMap['class'+str(temp)] ='submitted'             
                          else:          
                                    classMap['class'+str(temp)] ='current'   
                          questionNo = temp           
                          classMap['qno'] = questionNo 
                  self.getQuestion(True)                                                                      
          self.render('start.html', **classMap)

class Score(MainHandler):
      def get(self):
          check = self.read_secure_cookie('team_id')
          if check:
              score = {}
              score['name'] = check
              score['correct'] = solution['correct']
              score['wrong'] = solution['wrong']
              score['attempted'] = solution['totalAttempted'] 
              score['score'] = (int(solution['correct']) * 3) - int(solution['wrong']) 
              scoreRecord = Scorecard(teamname = check, attempted = str(solution['totalAttempted']), correct = str(solution['correct']), score = str(score['score']))
              scoreRecord.put() 
              self.render('score.html', **score) 
          else:
              self.redirect('/')   
      
      def post(self):
          self.logout()
          self.redirect('/') 

class Logout(MainHandler):
      def get(self):
          self.logout()
          self.redirect('/') 

class AdminHandler(Handler):
    def get(self):
        self.render('admin.html')
    def post(self):
        global adminname , pword
        adminname = self.request.get('username')
        pword = self.request.get('password')
        if adminname == 'harry' and pword == 'ron':
            self.redirect('/') 
        else:
            adminname = ''
            pword = ''
            msg = 'Invalid login'
            self.render('admin.html', error = msg)

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/admin/register', RegisterHandler),
    ('/admin/question', QuesHandler),
    ('/instructions', Instruction),
    ('/codered', Codered),
    ('/score', Score),
    ('/logout', Logout),
    ('/admin', AdminHandler)
], debug=True)
