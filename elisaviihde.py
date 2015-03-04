# Elisa Viihde API Python implementation
# License: GPLv3
# Author: Juho Tykkala
# Version: 1.1b

import requests, json, re, time, datetime

class elisaviihde:
  # Init args
  verbose = False
  baseurl = "https://beta.elisaviihde.fi"
  ssobaseurl = "https://id.elisa.fi"
  session = None
  authcode = None
  userinfo = None
  inited = False
  verifycerts = False
  
  def __init__(self, verbose=False):
    # Init session to store cookies
    self.verbose = verbose
    self.session = requests.Session()
    self.session.headers.update({"Referer": self.baseurl + "/"})
    
    # Make initial request to get session cookie
    if self.verbose: print "Initing session..."
    
    init = self.session.get(self.baseurl + "/", verify=self.verifycerts)
    self.checkrequest(init.status_code)
  
  def login(self, username, password):
    # Get sso auth token
    if self.verbose: print "Getting single-sign-on token..."
    token = self.session.post(self.baseurl + "/api/sso/authcode",
                              data={"username": username},
                              headers={"Content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                                       "X-Requested-With": "XMLHttpRequest"},
                              verify=self.verifycerts)
    self.checkrequest(token.status_code)
    try:
      self.authcode = token.json()["code"]
    except ValueError as err:
      raise Exception("Could not fetch sso token", err)
    
    # Login with token
    if self.verbose: print "Logging in with single-sign-on token..."
    login = self.session.post(self.ssobaseurl + "/sso/login",
                              data=json.dumps({"accountId": username,
                                               "password": password,
                                               "authCode": self.authcode,
                                               "suppressErrors": True}),
                              headers={"Content-type": "application/json; charset=UTF-8",
                                       "Origin": self.baseurl},
                              verify=self.verifycerts)
    self.checkrequest(login.status_code)
    
    # Login with username and password
    if self.verbose: print "Logging in with username and password..."
    user = self.session.post(self.baseurl + "/api/user",
                             data={"username": username,
                                   "password": password},
                             headers={"Content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                                      "X-Requested-With": "XMLHttpRequest"},
                             verify=self.verifycerts)
    self.checkrequest(user.status_code)
    try:
      self.userinfo = user.json()
    except ValueError as err:
      raise Exception("Could not fetch user information", err)
    self.inited = True
  
  def islogged(self):
    if self.inited:
      return True
    try:
      logincheck = self.session.get(self.baseurl + "/tallenteet/api/folders",
                                    headers={"X-Requested-With": "XMLHttpRequest"},
                                    verify=self.verifycerts)
      self.checkrequest(logincheck.status_code)
      self.inited = True
      return True
    except Exception as err:
      return False
    
  def checklogged(self):
    if not self.islogged():
      raise Exception("Not logged in")
  
  def checkrequest(self, statuscode):
    if not statuscode == requests.codes.ok:
      raise Exception("API request failed")
  
  def close(self):
    if self.verbose: print "Logging out and closing session..."
    logout = self.session.post(self.baseurl + "/api/user/logout",
                               headers={"X-Requested-With": "XMLHttpRequest"},
                               verify=self.verifycerts)
    self.session.close()
    self.userinfo = None
    self.authcode = None
    self.inited = False
    self.checkrequest(logout.status_code)
  
  def gettoken(self):
    return self.authcode
  
  def getuser(self):
    return self.userinfo
  
  def getsession(self):
    return requests.utils.dict_from_cookiejar(self.session.cookies)
    
  def setsession(self, cookies):  
    self.session.cookies=requests.utils.cookiejar_from_dict(cookies)
  
  def getfolders(self, folderid=0):
    # Get recording folders
    if self.verbose: print "Getting folder info..."
    self.checklogged()
    # TODO: Implement recursive folder walk
    if folderid != 0:
      return []
    folders = self.session.get(self.baseurl + "/tallenteet/api/folders",
                               headers={"X-Requested-With": "XMLHttpRequest"},
                               verify=self.verifycerts)
    self.checkrequest(folders.status_code)
    return folders.json()["folders"][0]["folders"]
  
  def getrecordings(self, folderid=0, page=0, sortby="startTime", sortorder="desc", status="all"):
    # Get recordings from first folder
    self.checklogged()
    if self.verbose: print "Getting recording info..."
    recordings = self.session.get(self.baseurl + "/tallenteet/api/recordings/" + str(folderid)
                                    + "?page=" + str(page)
                                    + "&sortBy=" + str(sortby)
                                    + "&sortOrder=" + str(sortorder)
                                    + "&watchedStatus=" + str(status),
                                  headers={"X-Requested-With": "XMLHttpRequest"},
                                  verify=self.verifycerts)
    self.checkrequest(recordings.status_code)
    return recordings.json()
  
  def getprogram(self, programid=0):
    # Parse program information
    self.checklogged()
    if self.verbose: print "Getting program info..."
    uridata = self.session.get(self.baseurl + "/ohjelmaopas/ohjelma/" + str(programid), verify=self.verifycerts)
    self.checkrequest(uridata.status_code)
    programname = ""
    programdesc = ""
    programsrvc = ""
    programtime = 0
    try:
      for line in uridata.text.split("\n"):
        if "itemprop=\"name\"" in line and "data-programid" in line:
          programname = re.findall('<h3.*?>(.*?)</h3>', line)[0]
        elif "itemprop=\"description\"" in line:
          programdesc = re.findall('<p.*?>(.*?)</p>', line)[0]
        elif "itemprop=\"name\"" in line:
          programsrvc = re.findall('<p.*?>(.*?)</p>', line)[0]
        elif "itemprop=\"startDate\"" in line:
          programtimestr = re.findall('<span.*?>(.*?)</span>', line)[0]
          programtime = int(datetime.datetime.fromtimestamp(
                              time.mktime(time.strptime(programtimestr,
                                                        "%d.%m.%Y %H:%M"))).strftime("%s"))
          programtime = programtime * 1000
    except Exception as exp:
      print "ERROR:", str(exp)
    except Error as exp:
      print "ERROR:", str(exp)
    
    return {"name": programname, "description": programdesc, "serviceName": programsrvc, "startTimeUTC": programtime}
  
  def getstreamuri(self, programid=0):
    # Parse recording stream uri for program
    self.checklogged()
    if self.verbose: print "Getting stream uri info..."
    uridata = self.session.get(self.baseurl + "/tallenteet/katso/" + str(programid), verify=self.verifycerts)
    self.checkrequest(uridata.status_code)
    for line in uridata.text.split("\n"):
      if "new Player" in line:
        return re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', line)[0]

