import re
import hmac


SECRET = 'rkuhoi$kjb&JKn%,kn&*@#'

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
          
def checkTeamName(teamname):
      if re.match(r"team[0-9]+", teamname):
        return False
      else:
        return True
