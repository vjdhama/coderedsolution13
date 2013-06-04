'''
CodeRed application is designed as a platform to test a user's C language aptitude
Languages used:
                python                -> to render dynamic webpages
                html, css, javascript -> to design web pages
                google appengine      -> for deployment and backend
'''

import webapp2, os, string, random, hmac, hashlib, operator 
import jinja2
from google.appengine.ext import db
from google.appengine.api import users

jinja_environment = jinja2.Environment(autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

def teams_key(group = 'default'):
      return db.Key.from_path('teams', group)

SECRET = 'rkuhoi$kjb&JKn%,kn&*@#'

top_scores = {}# store top scores
loggedUsers = [] # list of logged users
usersDi = {}#for  storing user data
qdir = {}#for storing all questions
tot_ques = 0 # for total number of questions in database


def check_secure_val(h):
      '''
      check if the submitted hash matches the objects original hash 
      '''
      val= h.strip().split('|')[0]
      if h == make_secure_val(val):
            return val 

def hash_str(s):
      '''
      create hash of the string passed  
      '''
      return hmac.new(SECRET,s).hexdigest()


def make_secure_val(s):
      '''
      append string and its hash
      '''
      return "%s|%s" % (s,hash_str(s))  
          


class user_data():
    '''
    Base Handler for the application
    All other handler classes are derived from this          
    '''

    def __init__(self):
        self.questionNo = 1    #stores the current question no
        self.questionSet = {}  #cache to store the questions

        #dictionary to store the scorecard
        self.solution = dict(solved = [], correct = 0, wrong = 0, totalAttempted = 0, score = 0)

        '''
        dictionary to pass data to the html page
                                :timer value
                                :question no
                                :class(tag identifier) for question grid submit buttons in start.html
        '''
        self.classMap = dict(timer1= '30',timer2 = '00', qno = self.questionNo, class29= 'q', class28= 'q', class21= 'q', class20= 'q', class23= 'q', class22= 'q', class25= 'q', class24= 'q', class27= 'q', class26= 'q', class8= 'q', class9= 'q', class6= 'q', class7= 'q', class4= 'q', class5= 'q', class2= 'q', class3= 'q', class1= 'current', class30= 'q', class18= 'q', class19= 'q', class14= 'q', class15= 'q', class16= 'q', class17= 'q', class10= 'q', class11= 'q', class12= 'q', class13= 'q')
        
        #flag to keep track of whether the current question is already submitted
        self.quesAlreadySubmitted = False        

    def getQuestion(self, cache = False):
        '''
        read question from cache   
        '''
        global qdir,tot_ques
        if cache == False:    
            a = random.randint(1,tot_ques - 29)# choose random question to start from
            newkey = 0
            for x in xrange(a,a+30):
                  newkey = newkey + 1
                  self.questionSet[newkey] = qdir[x]
        else:
            pass         
        self.classMap['question'] = self.questionSet[int(self.questionNo)][0]
        self.classMap['choice1'] =  self.questionSet[int(self.questionNo)][1]
        self.classMap['choice2'] =  self.questionSet[int(self.questionNo)][2]
        self.classMap['choice3'] =  self.questionSet[int(self.questionNo)][3]
        self.classMap['choice4'] =  self.questionSet[int(self.questionNo)][4]

    def setScore(self, choice):
        '''
        function checks if current option submitted is correct
        and changes the values of correct , wrong and attempted questions
        '''
        #if question response is not already submitted
        if int(self.questionNo) not in self.solution['solved']:
              
              #insert submitted question to list of solved question
              self.solution['solved'].append(int(self.questionNo))
              
              #check if solution is correct
              if int(self.questionSet[int(self.questionNo)][5]) == int(choice):
                  self.solution['correct'] += 1
              
              else:
                  self.solution['wrong'] += 1

              self.solution['totalAttempted'] += 1              


class Handler(webapp2.RequestHandler):
      def write(self, *a, **kw):
          self.response.out.write(*a, **kw)
        
      def render_str(self, template, **params):
          t = jinja_environment.get_template(template)
          return t.render(params)

      def render(self, template, **kw):
          self.write(self.render_str(template, **kw))
   
      def set_secure_cookie(self,name,val):
          '''
          create a cookie:
                     name -> string that is used to refer to value stored in cookie
                     val -> value to stored in cookie
          '''
          cookie_val = make_secure_val(val)
          self.response.headers.add_header('Set-Cookie','%s=%s; Path=/' % (name, cookie_val))
      
      def read_secure_cookie(self, name):
          '''
          read cookie header  
          '''
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
      

class MainHandler(Handler):
    '''
    login handler
    '''

    def get(self):

        #if (str(self.request.remote_addr) in ['127.0.0.1','203.199.146.114','192.168.55.111']): # add the list of allowed ip's
        curUser = users.get_current_user()

        if curUser:
            self.render('base.html')

        else:
            self.redirect(users.create_login_url(self.request.uri))

              
    def post(self):
          curUser = users.get_current_user()
          teamname = self.request.get('teamname')
          
          u = Register.login(teamname) #read this user's details from database
          
          global usersDi, loggedUsers
          
          #if user exists
          if u and (u.teamname not in loggedUsers):
              loggedUsers.append(u.teamname)
              self.login(u)
              x = user_data()
              usersDi[str(u.teamname)] = x
              x.getQuestion()
              self.redirect('/instructions')
          
          #if user doesn't exist    
          else:
            if u: 
              msg = 'Invalid login'
              self.render('base.html', error = msg) 
            
            else:
              Regstr = Register(teamname = teamname,email = curUser.email())
              Regstr.put()#write to database
              
              u = Register.login(teamname)
              loggedUsers.append(teamname)
              
              self.login(u)
              x = user_data()
              usersDi[str(u.teamname)] = x
              x.getQuestion()
              self.redirect('/instructions')


class Register(db.Model):
     '''
     Register table definition 
     '''
     teamname = db.StringProperty(required = True)
     email = db.StringProperty(required = True)
    
     @classmethod
     def by_name(cls, teamname):
         '''
         get user by name 
         '''
         u = Register.all().filter('teamname =', teamname).get()
         return u
     
     @classmethod
     def by_id(cls, teamid):
         '''
         get user by id    
         '''
         return Register.get_by_id(teamid, parent = teams_key()) 
                    
     @classmethod
     def login(cls, teamname):
         '''
         return user info from database if it exists and is valid                    
         '''
         u = cls.by_name(teamname)
         if u:
            return u       


class RegisterHandler(Handler):
    '''
    admin handler for registering users    
    '''
    def read_pasw(self):
        f = open('printopen.txt','rb')
        logins = f.read()
        log = logins.split('\n')
        
        for l in log :
             temp = l.split('      ')
             team = temp[0]
             mail = temp[1] 
             Regstr = Register(teamname = team,email = mail)
             Regstr.put()#write to database

    def get(self):
        user = users.get_current_user()
        if user:
            if users.is_current_user_admin(): 
               self.read_pasw()
               self.render('reg.html')
            
            else:
               self.render('403.html') 

        else:
           self.redirect('/')        

    def post(self):
        team = self.request.get('team')
        mail = self.request.get('email')
        Regstr = Register(teamname = team,email = mail)
        Regstr.put()#write to database
        self.redirect('/admin/register')


class Question(db.Model):
    '''
    Question table definition
    '''
    question = db.TextProperty(required = True)
    choice_1 = db.TextProperty(required = True)
    choice_2 = db.TextProperty(required = True)
    choice_3 = db.TextProperty(required = True)
    choice_4 = db.TextProperty(required = True)
    answer = db.TextProperty(required = True)

    
class Scorecard(db.Model):
    '''
    scorecard table definition
    '''
    teamname = db.TextProperty(required = True)    
    attempted = db.TextProperty(required = True)
    correct = db.TextProperty(required = True)
    score = db.TextProperty(required = True)


class QuesHandler(Handler):
    '''
    admin handler to enter questions in database
    '''
    def get(self):
        user = users.get_current_user()
        if user:
            if users.is_current_user_admin():
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

        else:
           self.redirect('/')        

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


class ReadQuestion(Handler):
    '''
    read questions from database
    '''
    def get(self):
        global qdir, tot_ques
        user = users.get_current_user()
        
        if user:
            if users.is_current_user_admin():
                query = Question.all()
                key = 0#for key in qdir
                
                for ques in query:
                    key = key + 1
                    qdir[key] = [ques.question,ques.choice_1,ques.choice_2,ques.choice_3,ques.choice_4,ques.answer]#qdir = {key : list}
                tot_ques = key
            
            else:
                self.render('403.html')     
        
        self.redirect('/')


class Instruction(Handler):
      '''
      Instruction page handler
      '''
      def get(self):
          check = self.read_secure_cookie('team_id')
          
          #render if user is logged in
          if check:
             self.render('instruction.html')
          
          else:
             self.redirect('/') 
          
      def post(self):
          self.redirect('/codered')    


class Codered(Handler):              
      '''
      handler for questions page
      '''
      def get(self):
          global usersDi
          team_name = self.read_secure_cookie('team_id')
          
          #render only if user is logged in
      
          if team_name:
              read_user = usersDi[str(team_name)]
              #read_user.getQuestion()          
              self.render('start.html', **read_user.classMap)
          
          else:
             self.redirect('/') 
          
      def post(self):
          global usersDi
          team_name = self.read_secure_cookie('team_id')
          read_user = usersDi[str(team_name)]
          
          #read timer value
          read_user.classMap['timer1'] = self.request.get('timer1')  
          read_user.classMap['timer2'] = self.request.get('timer2')
          
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
          if qNo != read_user.questionNo:
                  
                  #if user wants to goto new question 
                  if qNo or prev or next:
                      
                      #if prev question was not already submitted
                      if read_user.quesAlreadySubmitted == False:
                          #set prev questions (HTML identifier)class to 'q' 
                          read_user.classMap['class'+str(read_user.questionNo)] ='q'
                      
                      else:
                          #set prev questions (HTML identifier)class to 'submitted' 
                          read_user.classMap['class'+str(read_user.questionNo)] ='submitted'  
                      
                      if prev:
                          qNo = int(read_user.questionNo) - 1
                          if qNo < 1:
                              qNo = 30
                      
                      if next:
                          qNo = int(read_user.questionNo) + 1         
                          if qNo > 30:
                              qNo = 1

                      if read_user.classMap['class'+str(qNo)] == 'submitted' :
                          read_user.quesAlreadySubmitted = True  
                      
                      else:
                          read_user.quesAlreadySubmitted = False       
                      
                      #set new questions (HTML identifier)class to 'current'
                      read_user.classMap['class'+str(qNo)] ='current'    
                      
                      #store the current question no
                      read_user.questionNo = qNo 
                      read_user.classMap['qno'] = read_user.questionNo       
                      
                  #if user presses submit button    
                  else:
                      submit = self.request.get('submit')
                      #if submit button is clicked and answer is provided   
                      if submit and choice:
                          #call score manipulation function
                          read_user.setScore(choice)
                          
                          #set questions (HTML identifier)class to 'submitted'
                          read_user.classMap['class'+str(read_user.questionNo)] ='submitted'
                          temp = int(read_user.questionNo)
                          
                          #find the next question that is not alredy submitted
                          while read_user.classMap['class'+str(temp)] =='submitted':
                              temp += 1
                              if temp > 30:
                                   temp = 1
                              if temp == int(read_user.questionNo):
                                   break
                           
                          if temp == int(read_user.questionNo):
                                    read_user.quesAlreadySubmitted = True 
                                    read_user.classMap['class'+str(temp)] ='submitted'             
                          
                          else:          
                                    read_user.classMap['class'+str(temp)] ='current'   
                          
                          #make that question the current question          
                          read_user.questionNo = temp           
                          read_user.classMap['qno'] = read_user.questionNo 
                  
                  #get question from database OR cache        
                  read_user.getQuestion(True)                                                                      
          
          self.render('start.html', **read_user.classMap)


class Score(MainHandler):
      '''
      handler for scorecard page
      '''
      def get(self):
          #check = self.read_secure_cookie('team_id')
          global usersDi,top_scores
          team_name = self.read_secure_cookie('team_id')
          
          #if user is logged in
          if team_name:
              read_user = usersDi[str(team_name)]
              score = {}
              score['name'] = team_name
              score['correct'] = read_user.solution['correct']
              score['wrong'] = read_user.solution['wrong']
              score['attempted'] = read_user.solution['totalAttempted'] 
              score['score'] = (int(read_user.solution['correct']) * 3) - int(read_user.solution['wrong']) 
              
              scoreRecord = Scorecard(teamname = team_name, attempted = str(read_user.solution['totalAttempted']), correct = str(read_user.solution['correct']), score = str(score['score']))
              scoreRecord.put()#write score to database 
              
              top_scores[team_name] = score['score']
              self.render('score.html', **score) 
          
          else:
              self.redirect('/')   
      
      def post(self):
          self.redirect('/logout') 


class Logout(MainHandler):
      '''
      logout handler
      '''
      def get(self):
          global usersDi
          team_name = self.read_secure_cookie('team_id')
          
          if team_name:
              read_user = usersDi[str(team_name)]
              del usersDi[str(team_name)]
              self.logout()
              
              if not users.is_current_user_admin():
                  self.redirect(users.create_logout_url('/'))
              
              else:
                  self.redirect('/')    
          
          else:    
              self.redirect('/')

class TopScore(Handler):
    def sortdic(self,x):
        sorted_x = sorted(x.iteritems(), key=operator.itemgetter(1))
        sorted_x.reverse()
        return sorted_x

    def get(self):
        global top_scores
        l = self.sortdic(top_scores)
        self.render('topscore.html',topscore=l)
     
class test(Handler):
        def get(self):
            global usersDi, loggedUsers
            user = users.get_current_user()

            if user:
                if users.is_current_user_admin():
                   self.response.out.write(usersDi)
                   self.response.out.write(loggedUsers)
                
                else:
                   self.render('403.html')

            else:
                self.redirect('/')          

#declaration of handlers
app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/admin/register', RegisterHandler),
    ('/admin/question', QuesHandler),
    ('/admin/readquestion', ReadQuestion),
    ('/instructions', Instruction),
    ('/codered', Codered),
    ('/score', Score),
    ('/logout', Logout),
    ('/admin/topscore', TopScore),
    ('/admin/debug', test),
], debug=True)
