# -*- coding: iso-8859-1 -*-

import re
import os
import sys
import time
import datetime
import threading
import json
import elisaviihde

# Elisa session
elisa = None

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
try:
    import xbmc
    import xbmcplugin
    import xbmcgui
    import xbmcaddon
    __settings__ = xbmcaddon.Addon(id='plugin.video.elisa.viihde')
    __language__ = __settings__.getLocalizedString
    BASE_RESOURCE_PATH = xbmc.translatePath(os.path.join(__settings__.getAddonInfo('path'), "resources"))
    sys.path.append(os.path.join(BASE_RESOURCE_PATH, "lib"))
    vkopaivat = {0: __language__(30006), 1: __language__(30007), 2: __language__(30008), 3: __language__(
        30009), 4: __language__(30010), 5: __language__(30011), 6: __language__(30012)}
        
except ImportError:
    pass

# Init Elisa
elisa = elisaviihde.elisaviihde(False)
time_format = "%d.%m.%Y %H:%M:%S"

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

def add_dir(name, id, iconimage):
    u = sys.argv[0] + "?id=" + str(id)
    liz = xbmcgui.ListItem(label=name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo('video', {"Title": name})
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return liz

def add_watch_link(name, progid, totalItems=None, **kwargs):
    u = sys.argv[0] + "?watch=true&progid=" + str(progid)
    liz = xbmcgui.ListItem(name)
    kwargs['Title'] = name
    liz.setInfo('video', kwargs)
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, totalItems=totalItems)
    return liz

def create_name(prog_data):
    time_raw = prog_data["startTimeUTC"]/1000
    parsed_time = datetime.datetime.fromtimestamp(time_raw).strftime(time_format)
    weekday_numb = int(datetime.datetime.fromtimestamp(time_raw).strftime("%w"))
    prog_date = datetime.date.fromtimestamp(time_raw)
    today = datetime.date.today()
    diff = today - prog_date
    if diff.days == 0:
        date_name = __language__(30013) + " " + datetime.datetime.fromtimestamp(time_raw).strftime("%H:%M")
    elif diff.days == 1:
        date_name = __language__(30014) + " " + datetime.datetime.fromtimestamp(time_raw).strftime("%H:%M")
    else:
        date_name = str(vkopaivat[weekday_numb]) + " " + datetime.datetime.fromtimestamp(time_raw).strftime("%d.%m.%Y %H:%M")
    return prog_data['name'] + " (" + prog_data['serviceName'] + ", " + date_name + ")"

def watch_program(prog_id):
    url = elisa.getstreamuri(int(prog_id))
    prog_data = elisa.getprogram(prog_id)
    name = create_name(prog_data)
    listitem = xbmcgui.ListItem(name)
    listitem.setInfo('video', {'Title': name})
    xbmc.Player().play(url, listitem)
    return True

def show_dir(id):
    if str(id) == "0":
        # Show root directory
        folder_id = 0
    else:
        # Show directory by id
        folder_id = int(id)
    
    # List folders
    for row in elisa.getfolders(folder_id):
        name = row['name']
        id = row['id']
        add_dir(name, id, "")
    
    data = elisa.getrecordings(folder_id)
    totalItems = len(data)
    
    # List recordings
    for row in data:
        str_time = datetime.datetime.fromtimestamp(row["startTimeUTC"]/1000).strftime('%Y-%m-%dT%H:%M:%S')
        parsed_time = time.strptime(str_time, "%Y-%m-%dT%H:%M:%S")
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

        date_string = time.strftime("%d.%m.%Y", parsed_time)

        name = row['name'] + " (" + row['channel'] + ", " + date_name + ")"
        
        link = add_watch_link(name,
                              row['programId'],
                              playcount=1 if row['isWatched'] else 0,
                              totalItems=totalItems,
                              duration=((row["endTimeUTC"]/1000/60) - (row["startTimeUTC"]/1000/60)),
                              date=date_string,
                              plotoutline=(row['description'] if "description" in row else "XX"),
                              plot=(row['description'] if "description" in row else "XX")
                              )
        if "thumbnail" in row:
          link.setThumbnailImage(row['thumbnail'])

def mainloop():
    try:
        elisa.setsession(json.loads(__settings__.getSetting("session")))
    except ValueError as ve:
        __settings__.setSetting("session", "{}")
    
    if not elisa.islogged():
        dialog = xbmcgui.Dialog()
        ok = dialog.ok('XBMC', __language__(30003), __language__(30004))
        if ok == True:
            __settings__.openSettings(url=sys.argv[0])
            
        username = __settings__.getSetting("username")
        password = __settings__.getSetting("password")
        elisa.login(username, password)
        __settings__.setSetting("session", json.dumps(elisa.getsession()))
    
    params = get_params()
    
    folder_id = None
    prog_id = None
    watch = None
    search = None
    
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

    try:
        search = str(params["search"])
    except:
        pass

    if search != None:
        keyboard = xbmc.Keyboard()
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            show_search_items(str(keyboard.getText()))

    elif folder_id == None and prog_id == None:
        show_dir("0")
    elif prog_id == None and folder_id != None:
        show_dir(str(folder_id))
    elif watch == "true" and prog_id != None:
        watch_program(str(prog_id))
    else:
        show_dir("0")

    xbmcplugin.endOfDirectory(int(sys.argv[1]))

if __name__ == '__main__':
    mainloop()
