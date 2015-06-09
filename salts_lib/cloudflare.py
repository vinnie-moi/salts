
#
#      Copyright (C) 2015 tknorris (Derived from Mikey1234's)
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
#  This code is a derivative of the YouTube plugin for XBMC and associated works
#  released under the terms of the GNU General Public License as published by
#  the Free Software Foundation; version 3


import re
import urllib2
import urlparse
from types import *
import log_utils
import xbmc
from salts_lib.constants import USER_AGENT

indent = -1

def getNested(s, delim=("(", ")")):
        level = 0
        pos = 0
        for c in s:
                pos += 1
                if c == delim[0]:
                        level += 1
                elif c == delim[1]:
                        level -= 1
                if level == -1:
                        return pos - 1
        log_utils.log("Couldn't find matching - level: %s" % (level), xbmc.LOGWARNING)
        return s

def solveEquation(q):
        global indent
        indent += 1
        pos = 0
        res = 0
        stringify = False
        if q[0] == "!":
                stringify = True
        while pos < len(q):
                if q[pos] == "(":
                        nested = getNested(q[pos + 1: len(q)])
                        nres = solveEquation(q[pos + 1:pos + 1 + nested])
                        if type(nres) is StringType and type(res) is not StringType:
                                res = str(res) + nres
                        elif type(res) == StringType and type(nres) is IntType:
                                res = res + str(nres)
                        else:
                                res += nres
                        pos += nested + 1
                elif q[pos] == ")":
                        pass
                        pos += 1
                elif q[pos:pos + 4] == "!+[]":
                        res += 1
                        pos += 4
                elif q[pos:pos + 5] == "+!![]":
                        res += 1
                        pos += 5
                elif q[pos:pos + 3] == "+[]":
                        pos += 3
                elif q[pos:pos + 2] == "+(":
                        pos += 1
                # we dont care about whitespaces
                elif q[pos] == " ":
                        pos += 1
                elif q[pos] == "\t":
                        pos += 1
                else:
                        log_utils.log('%s Unknown: %s' % ('\t' * indent, q[pos:pos + 6]), xbmc.LOGDEBUG)
                        break
        
        indent -= 1
        if stringify:
                return str(res)
        return res

def solve(url, cj, wait=True):
        headers = {'User-Agent': USER_AGENT, 'Referer': url}
        if cj:
            try: cj.load(ignore_discard=True)
            except: pass
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
            urllib2.install_opener(opener)

        request = urllib2.Request(url)
        for key in headers: request.add_header(key, headers[key])
        try:
            response = urllib2.urlopen(request)
            html = response.read()
        except urllib2.HTTPError as e:
            html = e.read()
        
        solver_pattern = 'var t,r,a,f,\s*([^=]+)={"([^"]+)":([^}]+)};.+challenge-form\'\);.*?\n.*?;(.*?);a\.value'
        match = re.search(solver_pattern, html, re.DOTALL)
        if not match:
            log_utils.log("Couldn't find answer script - No cloudflare check?", xbmc.LOGWARNING)
            return False
        res = match.groups()

        vc_pattern = 'input type="hidden" name="jschl_vc" value="([^"]+)'
        match = re.search(vc_pattern, html)
        if not match:
            log_utils.log("Couldn't find vc input - No cloudflare check?", xbmc.LOGWARNING)
            return False
        vc = match.group(1)

        pass_pattern = 'input type="hidden" name="pass" value="([^"]+)'
        match = re.search(pass_pattern, html)
        if not match:
            log_utils.log("Couldn't find pass input - No cloudflare check?", xbmc.LOGWARNING)
            return False
        password = match.group(1)

        #log_utils.log("VC is: %s" % (vc), xbmc.LOGDEBUG)
        varname = (res[0], res[1])
        solved = int(solveEquation(res[2].rstrip()))
        log_utils.log("Initial value: %s Solved: %s" % (res[2], solved), xbmc.LOGDEBUG)
        
        for extra in res[3].split(";"):
                extra = extra.rstrip()
                if extra[:len('.'.join(varname))] != '.'.join(varname):
                        log_utils.log("Extra does not start with varname (%s)" % (extra), xbmc.LOGDEBUG)
                else:
                        extra = extra[len('.'.join(varname)):]

                if extra[:2] == "+=":
                        solved += int(solveEquation(extra[2:]))
                elif extra[:2] == "-=":
                        solved -= int(solveEquation(extra[2:]))
                elif extra[:2] == "*=":
                        solved *= int(solveEquation(extra[2:]))
                elif extra[:2] == "/=":
                        solved /= int(solveEquation(extra[2:]))
                else:
                        log_utils.log("Unknown modifier: %s" % (extra), xbmc.LOGWARNING)

                log_utils.log('intermediate: %s = %s' % (extra, solved), xbmc.LOGDEBUG)
        
        scheme = urlparse.urlparse(url).scheme
        domain = urlparse.urlparse(url).hostname
        solved += len(domain)
        log_utils.log("Solved value: %s" % (solved), xbmc.LOGDEBUG)

        if wait:
                log_utils.log('Sleeping for 5 Seconds', xbmc.LOGDEBUG)
                xbmc.sleep(5000)
                
        url = scheme + "://" + domain + "/cdn-cgi/l/chk_jschl?jschl_vc={0}&jschl_answer={1}&pass={2}".format(vc, solved, password)
        log_utils.log('url: %s' % (url), xbmc.LOGDEBUG)
        request = urllib2.Request(url)
        for key in headers: request.add_header(key, headers[key])
        try:
            response = urllib2.urlopen(request)
            final = response.read()
        except urllib2.HTTPError as e:
            log_utils.log('CloudFlare Error: %s on url: %s' % (e.code, url), xbmc.LOGWARNING)
            return False

        if cj:
            cj.save()
            
        return final
