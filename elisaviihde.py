# Elisa Viihde API Python implementation
# License: GPLv3
# Author: Juho Tykkala

import requests, json, re

class elisaviihde:
  # Init args
  verbose = False
  baseurl = "https://beta.elisaviihde.fi"
  ssobaseurl = "https://id.elisa.fi"
  session = None
  authcode = None
  userinfo = None
  
  def __init__(self, verbose=False):
    # Init session to store cookies
    self.verbose = verbose
    self.session = requests.Session()
    self.session.headers.update({"Referer": self.baseurl + "/"})
    
    # Make initial request to get session cookie
    if self.verbose: print "Initing session..."
    
    init = self.session.get(self.baseurl + "/")
    self.checkrequest(init.status_code)
  
  def login(self, username, password):
    # Get sso auth token
    if self.verbose: print "Getting single-sign-on token..."
    token = self.session.post(self.baseurl + "/api/sso/authcode",
                              data={"username": username},
                              headers={"Content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                                       "X-Requested-With": "XMLHttpRequest"})
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
                                       "Origin": self.baseurl})
    self.checkrequest(login.status_code)
    
    # Login with username and password
    if self.verbose: print "Logging in with username and password..."
    user = self.session.post(self.baseurl + "/api/user",
                             data={"username": username,
                                   "password": password},
                             headers={"Content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                                      "X-Requested-With": "XMLHttpRequest"})
    try:
      self.userinfo = user.json()
    except ValueError as err:
      raise Exception("Could not fetch user information", err)
  
  def islogged(self):
    return True if self.userinfo else False
    
  def checklogged(self):
    if not self.islogged():
      raise Exception("Not logged in")
  
  def checkrequest(self, statuscode):
    if not statuscode == requests.codes.ok:
      raise Exception("API request failed")
  
  def close(self):
    if self.verbose: print "Logging out and closing session..."
    logout = self.session.post(self.baseurl + "/api/user/logout",
                               headers={"X-Requested-With": "XMLHttpRequest"})
    self.session.close()
    self.userinfo = None
    self.authcode = None
    self.checkrequest(logout.status_code)
  
  def gettoken(self):
    return self.authcode
  
  def getuser(self):
    return self.userinfo
  
  def getfolders(self):
    # Get recording folders
    if self.verbose: print "Getting folder info..."
    self.checklogged()
    folders = self.session.get(self.baseurl + "/tallenteet/api/folders",
                               headers={"X-Requested-With": "XMLHttpRequest"})
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
                                  headers={"X-Requested-With": "XMLHttpRequest"})
    self.checkrequest(recordings.status_code)
    return recordings.json()
  
  def getstreamuri(self, programid=0):
    # Parse recording stream uri from first recording
    self.checklogged()
    if self.verbose: print "Getting stream uri info..."
    uridata = self.session.get(self.baseurl + "/tallenteet/katso/" + str(programid))
    self.checkrequest(uridata.status_code)
    for line in uridata.text.split("\n"):
      if "new Player" in line:
        return re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', line)[0]

