# -*- coding: iso-8859-1 -*-                    
import urllib
import urllib2
import re
import xbmc
import xbmcplugin
import xbmcgui  
import xbmcaddon
import cookielib
import os
import simplejson
import sys
import time
import datetime

# Enable Eclipse debugger
REMOTE_DBG = False

# append pydev remote debugger
if REMOTE_DBG:
    # Make pydev debugger works for auto reload.
    # Note pydevd module need to be copied in XBMC\system\python\Lib\pysrc
    try:
        import pysrc.pydevd as pydevd
        # stdoutToServer and stderrToServer redirect stdout and stderr to eclipse console
        pydevd.settrace('localhost', stdoutToServer=True, stderrToServer=True)
    except ImportError:
        sys.stderr.write("Error: " + 
        "You must add org.python.pydev.debug.pysrc to your PYTHONPATH.")
        sys.exit(1)

#Elisa Viihde
__settings__ = xbmcaddon.Addon(id='plugin.video.elisa.viihde')
__language__ = __settings__.getLocalizedString

BASE_RESOURCE_PATH = xbmc.translatePath(os.path.join(__settings__.getAddonInfo('path'), "resources"))
sys.path.append(os.path.join(BASE_RESOURCE_PATH, "lib"))

username = __settings__.getSetting("username") 
password = __settings__.getSetting("password") 

login_url = "http://elisaviihde.fi/etvrecorder/login.sl?username=" + username + "&password=" + password + "&savelogin=true&ajax=true"

vkopaivat = {0:__language__(30006), 1:__language__(30007), 2:__language__(30008), 3:__language__(30009), 4:__language__(30010), 5:__language__(30011), 6:__language__(30012)}
 
#logging in
def login():
    COOKIEFILE = xbmc.translatePath('special://profile/addon_data/plugin.video.elisa.viihde/cookies.lwp')
    
    urlopen = urllib2.urlopen
    cj = cookielib.LWPCookieJar()             # This is a subclass of FileCookieJar that has useful load and save methods
    Request = urllib2.Request

    if os.path.isfile(COOKIEFILE):
        cj.load(COOKIEFILE)

    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    urllib2.install_opener(opener)

    txdata = None                                                                                                                                                     
    txheaders = {'User-agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}    

    req = Request(login_url, txdata, txheaders)
    handle = urlopen(req)

    cj.save(COOKIEFILE) 
                         
def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
                                                    
    return param

def addLink(name, progid, length):
    u = sys.argv[0] + "?progid=" + str(progid)
    ok = True
    liz = xbmcgui.ListItem(label=name)
    liz.setInfo('video', { "Title": name, "duration":length})        
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok    

def addDir(name, id, iconimage):
    u = sys.argv[0] + "?id=" + str(id)
    ok = True
    liz = xbmcgui.ListItem(label=name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo('video', { "Title": name })
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


def addWatchLink(name, id):    
    u = sys.argv[0] + "?watch=true&progid=" + str(id)
    ok = True
    liz = xbmcgui.ListItem(name)
    liz.setInfo('video', { "Title": name })
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok
    
def addTextItem(text):            
    liz = xbmcgui.ListItem(" - " + text)    
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url="", listitem=liz)
    return True

def addTextItem2(text):            
    liz = xbmcgui.ListItem(text)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url="", listitem=liz)
    return True

def addTextPlot(text):
    word_list = text.split()
    temp = ''
    rows = []
    for word in word_list:
        temp += ' ' 
        temp += word
        if len(temp) < 50:
            continue
        rows.append(temp)
        temp = ''
    rows.append(temp)
    
    for row in rows:
        line = "     " + row
        addTextItem2(line)

def watch_program(prog_id):
    prog_url = "http://elisaviihde.fi/etvrecorder/program.sl?programid=" + str(prog_id) + "&ajax"
    req = urllib2.Request(prog_url)
    response = urllib2.urlopen(req)
    link = response.read()
    link = fix_chars(link)         
    prog_data = simplejson.loads(link)
    url = prog_data['url']
    name = prog_data['name']
    desc = prog_data['short_text']
    tn = prog_data['tn']
    length = prog_data['length']
    
    listitem = xbmcgui.ListItem(name)    
    xbmc.Player().play(url, listitem)
    
    
    #mark program watched
    view_url = "http://elisaviihde.fi/etvrecorder/program.sl?programid=" + str(prog_id) + "&view=true"
    urllib2.urlopen(view_url)
    
    return True
     
#show program info
def show_program(id):     
    #get program data
    prog_url = "http://elisaviihde.fi/etvrecorder/program.sl?programid=" + str(prog_id) + "&ajax"
    req = urllib2.Request(prog_url)
    response = urllib2.urlopen(req)
    link = response.read()
    link = fix_chars(link)         
    prog_data = simplejson.loads(link)
    url = prog_data['url']
    
    addWatchLink(__language__(30015), id)
    addTextItem(prog_data['name'])    
    
    parsed_time = time.strptime(prog_data['start_time'], "%d.%m.%Y %H:%M:%S")
    weekday_numb = int(time.strftime("%w", parsed_time))    
    
    prog_date = datetime.date.fromtimestamp(time.mktime(parsed_time))
    today = datetime.date.today()
    diff = today - prog_date
    if diff.days == 0:
        date_name = __language__(30013) + " " + time.strftime("%H:%M", parsed_time)
    elif diff.days == 1:
        date_name = __language__(30014) + " " + time.strftime("%H:%M", parsed_time)
    else:
        date_name = str(vkopaivat[weekday_numb]) + " " + time.strftime("%d.%m.%Y %H:%M", parsed_time)
    
    addTextItem(prog_data['channel'] + ", " + date_name)
    addTextItem(__language__(30016) + ": " + prog_data['flength'])
    addTextPlot(prog_data['short_text'])

def fix_chars(string):
    string = string.replace("%20", " ")
    string = re.sub('%C3%A4', '\u00E4', string) #ä
    string = re.sub('%C3%B6', '\u00F6', string) #ö
    string = re.sub('%C3%A5', '\u00E5', string) #å
    string = re.sub('%C3%84', '\u00C4', string) #Ä
    string = re.sub('%C3%96', '\u00D6', string) #Ö
    string = re.sub('%C3%85', '\u00C5', string) #Å
    string = re.sub('%2C', ',', string) #pilkku
    string = re.sub('%26', '&', string) #&
    string = re.sub('%3F', '?', string) #?
    string = re.sub('%3A', ':', string) #:
    string = re.sub('%2F', '/', string) #/
    return string
                
def show_dir(id):
    if str(id) == "0":
            #show root directory         
            folder_id = ""
    else:
            #show directory by id
            folder_id = str(id) 
            
    folder_url = "http://elisaviihde.fi/etvrecorder/ready.sl?folderid=" + folder_id + "&ajax"
    response = urllib2.urlopen(folder_url)
    link = response.read()    
    link = fix_chars(link)
    
    response.close()

    data = simplejson.loads(link)
    data = data['ready_data']
    data = data.pop()                 
    #list folders            
    for row in data['folders']:
    	name = row['name'] 
    	id = row['id']                             
        addDir(name, id, "")
    
    #list recordings
    for row in data['recordings']:
                     
    	if row['viewcount'] == "0":
        	print_star = "* "
        else:
        	print_star = ""
            
        parsed_time = time.strptime(row['timestamp'][:-5], "%Y-%m-%dT%H:%M:%S")
        weekday_numb = int(time.strftime("%w", parsed_time))
            
        starttime = time.strftime("%d.%m %H:%M", parsed_time)
            
        prog_date = datetime.date.fromtimestamp(time.mktime(parsed_time))
        today = datetime.date.today()
        diff = today - prog_date
        if diff.days == 0:
            date_name = __language__(30013) + " " + time.strftime("%H:%M", parsed_time)
        elif diff.days == 1:
            date_name = __language__(30014) + " " + time.strftime("%H:%M", parsed_time)
        else:
            date_name = str(vkopaivat[weekday_numb]) + " " + time.strftime("%d.%m.%Y %H:%M", parsed_time)
            
        name = print_star + row['name'] + " (" + row['channel'] + ", " + date_name + ")"
            
        addLink(name, row['program_id'], row['length'])            



#check login
response = urllib2.urlopen(login_url)
link = response.read()

if not str(link) == "TRUE":
    dialog = xbmcgui.Dialog()
    ok = dialog.ok('XBMC', __language__(30003), __language__(30004))
    if ok == True:
        __settings__.openSettings(url=sys.argv[0])        
        
else:
    login()     
    params = get_params()

    #dialog = xbmcgui.Dialog()
    #ok = dialog.ok('XBMC', str(params))
    
    folder_id = None
    prog_id = None
    watch = None
    try:
        folder_id = int(params["id"])
    except:
        pass
        
    try:
        prog_id = int(params["progid"])
    except:
        pass
    
    try:
        watch = str(params["watch"])
    except:
        pass

        
    if folder_id == None and prog_id == None:
        show_dir("0")
    elif prog_id == None and folder_id <> None:
        show_dir(str(folder_id))
    elif prog_id <> None and watch == None:
        show_program(str(prog_id))        
    elif watch == "true" and prog_id <> None:
        watch_program(str(prog_id))
    else:
        show_dir("0")



xbmcplugin.endOfDirectory(int(sys.argv[1]))
