
#
#      Copyright (C) 2015 tknorris (Derived from Mikey1234's & Lambda's)
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
import log_utils
import xbmc
from salts_lib.constants import USER_AGENT

def solve_equation(equation):
    try:
        offset = 1 if equation[0] == '+' else 0
        return int(eval(equation.replace('!+[]', '1').replace('!![]', '1').replace('[]', '0').replace('(', 'str(')[offset:]))
    except:
        pass

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
        init_match = re.search(solver_pattern, html, re.DOTALL)
        vc_pattern = 'input type="hidden" name="jschl_vc" value="([^"]+)'
        vc_match = re.search(vc_pattern, html)
        pass_pattern = 'input type="hidden" name="pass" value="([^"]+)'
        pass_match = re.search(pass_pattern, html)

        if not init_match or not vc_match or not pass_match:
            log_utils.log("Couldn't find attribute: init: |%s| vc: |%s| pass: |%s| No cloudflare check?" % (init_match, vc_match, pass_match), xbmc.LOGWARNING)
            return False
            
        res = init_match.groups()
        vc = vc_match.group(1)
        password = pass_match.group(1)

        #log_utils.log("VC is: %s" % (vc), xbmc.LOGDEBUG)
        varname = (res[0], res[1])
        solved = int(solve_equation(res[2].rstrip()))
        log_utils.log("Initial value: %s Solved: %s" % (res[2], solved), xbmc.LOGDEBUG)
        
        for extra in res[3].split(";"):
                extra = extra.rstrip()
                if extra[:len('.'.join(varname))] != '.'.join(varname):
                        log_utils.log("Extra does not start with varname (%s)" % (extra), xbmc.LOGDEBUG)
                else:
                        extra = extra[len('.'.join(varname)):]

                equation = extra[2:]
                operator = extra[0]
                if operator not in ['+', '-', '*', '/']:
                    log_utils.log("Unknown modifier: %s" % (extra), xbmc.LOGWARNING)
                    continue
                    
                solved = int(str(eval(str(solved) + operator + str(solve_equation(equation)))))
                log_utils.log('intermediate: %s = %s' % (extra, solved), xbmc.LOGDEBUG)
        
        scheme = urlparse.urlparse(url).scheme
        domain = urlparse.urlparse(url).hostname
        solved += len(domain)
        log_utils.log("Final Solved value: %s" % (solved), xbmc.LOGDEBUG)

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
