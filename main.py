#CodeRedSolution application is designed as a platform to test a user's C language aptitude
#Languages used:
#                python                -> to render dynamic webpages
#                html, css, javascript -> to design web pages
#                google appengine      -> for deployment and backend


import webapp2, os, string, random, hmac, hashlib 
import jinja2
from google.appengine.ext import db

jinja_environment = jinja2.Environment(autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

def teams_key(group = 'default'):
      return db.Key.from_path('teams', group)

SECRET = 'rkuhoi$kjb&JKn%,kn&*@#'

questionNo = 1    #stores the current question no
questionSet = {}  #cache to store the questions

#dictionary to store the scorecard
solution = dict(solved = [], correct = 0, wrong = 0, totalAttempted = 0, score = 0)

#dictionary to pass data to the html page
#                        :timer value
#                        :question no
#                        :class(tag identifier) for question grid submit buttons in start.html
classMap = dict(timer1= '30',timer2 = '00', qno = questionNo, class29= 'q', class28= 'q', class21= 'q', class20= 'q', class23= 'q', class22= 'q', class25= 'q', class24= 'q', class27= 'q', class26= 'q', class8= 'q', class9= 'q', class6= 'q', class7= 'q', class4= 'q', class5= 'q', class2= 'q', class3= 'q', class1= 'current', class30= 'q', class18= 'q', class19= 'q', class14= 'q', class15= 'q', class16= 'q', class17= 'q', class10= 'q', class11= 'q', class12= 'q', class13= 'q')
adminname = ''   
pword = ''

#check if the submitted hash matches the objects original hash  
def check_secure_val(h):
      val= h.strip().split('|')[0]
      if h == make_secure_val(val):
            return val 

#create hash
def hash_str(s):
      return hmac.new(SECRET,s).hexdigest()

#create hash
def make_secure_val(s):
      return "%s|%s" % (s,hash_str(s))  
          
# Base Handler for the application
#All other handler classes are derived from this          
class Handler(webapp2.RequestHandler):
      def write(self, *a, **kw):
          self.response.out.write(*a, **kw)
        
      def render_str(self, template, **params):
          t = jinja_environment.get_template(template)
          return t.render(params)

      def render(self, template, **kw):
          self.write(self.render_str(template, **kw))
   
      #create a cookie:
      #               name -> string that is used to refer to value stored in cookie
      #               val -> value to stored in cookie
      def set_secure_cookie(self,name,val):
          cookie_val = make_secure_val(val)
          self.response.headers.add_header('Set-Cookie','%s=%s; Path=/' % (name, cookie_val))
      
      #read cookie header    
      def read_secure_cookie(self, name):
          cookie_val = self.request.cookies.get(name)
          return cookie_val and check_secure_val(cookie_val)
      

      def login(self, team):
          self.set_secure_cookie('team_id', str(team.teamname))
      
      def logout(self):
          self.response.headers.add_header('Set-Cookie','team_id=; Path=/')
          
      #first function that is called
      def initialize(self, *a, **kw):
          webapp2.RequestHandler.initialize(self, *a, **kw)
          teamid = self.read_secure_cookie('team_id')
          self.team = teamid and Register.by_name(teamid)  
      
      #read question from database   
      def getQuestion(self, cacheFlag = False):
          global questionNo, questionSet, solution, classMap
          #if reading for first time
          if cacheFlag == False:  
                query = Question.all()
                qdir = {}#for storing all questions
                key = 0#for key in qdir
                for ques in query:
                    key = key + 1
                    qdir[key] = [ques.question,ques.choice_1,ques.choice_2,ques.choice_3,ques.choice_4,ques.answer]#qdir = {key : list}
                    
                a = random.randint(1,key-29)# choose random question to statr from
                newkey = 0
                for x in xrange(a,a+30):
                    newkey = newkey + 1
                    questionSet[newkey] = qdir[x]
          #else use the cache          
          else:           
               pass        
          classMap['question'] = questionSet[int(questionNo)][0]
          classMap['choice1'] =  questionSet[int(questionNo)][1]
          classMap['choice2'] =  questionSet[int(questionNo)][2]
          classMap['choice3'] =  questionSet[int(questionNo)][3]
          classMap['choice4'] =  questionSet[int(questionNo)][4]      
      
      #reset all global values to default
      def reset(self):
          global questionNo, classMap, solution, quesAlreadySubmitted
          questionNo = 1
          quesAlreadySubmitted = False
          for x in range(1, 31):
              classMap['class' + str(x)] = 'q'
              solution[x] = None
          solution['correct'] = 0
          solution['wrong'] = 0
          solution['totalAttempted'] = 0
          solution['score'] = 0   
          classMap['timer1'] = '30'
          classMap['timer2'] = '00'
          classMap['class1'] = 'current' 
          classMap['qno'] = questionNo
          del solution['solved']
          solution['solved'] = []

#login handler
class MainHandler(Handler):
    def get(self):
        if (str(self.request.remote_addr) in ['127.0.0.1','203.199.146.114']): # add the list of allowed ip's
            self.render('base.html')
        else:
            self.render('403.html') #Access denied. maybe use a HTML PAGE
          
    def post(self):           
          teamname = self.request.get('teamname')
          password = self.request.get('password')
          u = Register.login(teamname, password) #read this user's details from database
          
          #if user exists
          if u:
              self.login(u)
              self.reset()
              self.redirect('/instructions')
          #if user doesn't exist    
          else:
              msg = 'Invalid login'
              self.render('base.html', error = msg) 

#Register table definition 
class Register(db.Model):
     teamname = db.StringProperty(required = False)
     password = db.StringProperty(required = True)
     email = db.StringProperty(required = True)
    
     #get user by name    
     @classmethod
     def by_name(cls, teamname):
         u = Register.all().filter('teamname =', teamname).get()
         return u
     
     #gwt user by id    
     @classmethod
     def by_id(cls, teamid):
         return Register.get_by_id(teamid, parent = teams_key()) 
                    
     #return user info from database if it exists and is valid                    
     @classmethod
     def login(cls, teamname, pw):
         u = cls.by_name(teamname)
         if u and valid_pw(pw, u.password):
              return u       

#validate password   
def valid_pw(pw, pwc):
    return pw == pwc    

#create a salt
def make_salt(length = 5):
    return ''.join(random.choice(string.letters) for x in xrange(length)) 

#admin handler for registering users    
class RegisterHandler(Handler):
    def make_pass(self):
        return ''.join(random.choice(string.letters) for x in xrange(5))
    def get(self):
        #if user is admin
        if adminname and pword:
            self.render('reg.html')
        #if user is not admin    
        else:
            self.render('403.html')

    def post(self):
        team = self.request.get('team')
        mail = self.request.get('email')
        pasw = self.make_pass()
        Regstr = Register(teamname = team,password = pasw,email = mail)
        Regstr.put()#write to database
        self.redirect('/')

#Question table definition
class Question(db.Model):
    question = db.TextProperty(required = True)
    choice_1 = db.TextProperty(required = True)
    choice_2 = db.TextProperty(required = True)
    choice_3 = db.TextProperty(required = True)
    choice_4 = db.TextProperty(required = True)
    answer = db.TextProperty(required = True)

#scorecard table definition    
class Scorecard(db.Model):
    teamname = db.TextProperty(required = True)    
    attempted = db.TextProperty(required = True)
    correct = db.TextProperty(required = True)
    score = db.TextProperty(required = True)

#admin handler to enter questions in database
class QuesHandler(Handler):
    def get(self):
        if adminname and pword:
            data = open('1.txt', 'rb')
            k = data.read()
            tt = k.split('!!!')
            #pp = tt[0].split('!!')
            for t in tt:
                p = t.split('!!')
                ques = p[0]
                ch1 = p[1]
                ch2 = p[2] 
                ch3 = p[3]
                ch4 = p[4]
                ans = p[5]
                Q = Question(question = ques,choice_1 =ch1,choice_2 = ch2,choice_3 = ch3,choice_4 = ch4,answer = ans)
                Q.put()   

            data.close()
            #self.write(pp)
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

#Instruction page handler
class Instruction(Handler):
      def get(self):
          check = self.read_secure_cookie('team_id')
          #render if user is logged in
          if check:
             self.render('instruction.html')
          else:
             self.redirect('/') 
          
          
      def post(self):
          self.redirect('/codered')    

#flag to keep track of whether the current question is already submitted
quesAlreadySubmitted = False 

#function checks if current option submitted is correct
#and changes the values of correct , wrong and attempted questions
def setScore(choice):
      global questionNo, solution
      #if question response is not already submitted
      if int(questionNo) not in solution['solved']:
          #insert submitted question to list of solved question
          solution['solved'].append(int(questionNo))
          #check if solution is correct
          if int(questionSet[int(questionNo)][5]) == int(choice):
                 solution['correct'] += 1
          else:
                 solution['wrong'] += 1
          solution['totalAttempted'] += 1              


#handler for questions page
class Codered(Handler):              
      def get(self):
          check = self.read_secure_cookie('team_id')
          #render only if user is logged in
          if check:
              self.getQuestion()          
              self.render('start.html', **classMap)
          else:
             self.redirect('/') 
          
      def post(self):
          global questionNo, quesAlreadySubmitted , questionSet, classMap, solution 
          #read timer value
          classMap['timer1'] = self.request.get('timer1')  
          classMap['timer2'] = self.request.get('timer2')
          #read if user wants to finish the test  
          completed = self.request.get('viewscore')
          #if user wants to finish
          #render scorecard
          if completed:
              self.redirect('/score')
          #else continue    
          choice = self.request.get('ch')# choice will contain the choice selected (one OR two OR three OR FOUR--REFER start.html)
          qNo = self.request.get('questionNo') # get which question button on questiongrid did the user pressed
          prev = self.request.get('previous')
          next = self.request.get('next')
          #if current question is NOT what user wants to go to 
          if qNo != questionNo:
                  #if user wants to goto new question 
                  if qNo or prev or next:
                      #if prev question was not already submitted
                      if quesAlreadySubmitted == False:
                          #set prev questions (HTML identifier)class to 'q' 
                          classMap['class'+str(questionNo)] ='q'
                      else:
                          #set prev questions (HTML identifier)class to 'submitted' 
                          classMap['class'+str(questionNo)] ='submitted'  
                      if prev:
                          qNo = int(questionNo) - 1
                          if qNo < 1:
                              qNo = 30
                      if next:
                          qNo = int(questionNo) + 1         
                          if qNo > 30:
                              qNo = 1

                      if classMap['class'+str(qNo)] == 'submitted' :
                          quesAlreadySubmitted = True  
                      else:
                          quesAlreadySubmitted = False       
                      
                      #set new questions (HTML identifier)class to 'current'
                      classMap['class'+str(qNo)] ='current'    
                      #store the current question no
                      questionNo = qNo 
                      classMap['qno'] = questionNo       
                      
                  #if user presses submit button    
                  else:
                      submit = self.request.get('submit')
                      #if submit button is clicked and answer is provided   
                      if submit and choice:
                          #call score manipulation function
                          setScore(choice)
                          #set questions (HTML identifier)class to 'submitted'
                          classMap['class'+str(questionNo)] ='submitted'
                          temp = int(questionNo)
                          
                          #find the next question that is not alredy submitted
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
                          #make that question the current question          
                          questionNo = temp           
                          classMap['qno'] = questionNo 
                  #get question from database OR cache        
                  self.getQuestion(True)                                                                      
          self.render('start.html', **classMap)

#handler for scorecard page
class Score(MainHandler):
      def get(self):
          check = self.read_secure_cookie('team_id')
          #if user is logged in
          if check:
              score = {}
              score['name'] = check
              score['correct'] = solution['correct']
              score['wrong'] = solution['wrong']
              score['attempted'] = solution['totalAttempted'] 
              score['score'] = (int(solution['correct']) * 3) - int(solution['wrong']) 
              scoreRecord = Scorecard(teamname = check, attempted = str(solution['totalAttempted']), correct = str(solution['correct']), score = str(score['score']))
              scoreRecord.put()#write score to database 
              self.render('score.html', **score) 
          else:
              self.redirect('/')   
      
      def post(self):
          self.logout()
          self.redirect('/') 

#logout handler
class Logout(MainHandler):
      def get(self):
          self.logout()
          self.redirect('/') 

#handler for admin login
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

#declaration of handlers
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
