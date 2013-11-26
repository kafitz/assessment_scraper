#!/usr/bin/python
# coding=utf-8
# 2013 Kyle Fitzsimmons

import datetime
import time
import cookielib
import mechanize
from BeautifulSoup import MinimalSoup


class PrettifyHandler(mechanize.BaseHandler):
    '''Used to fix broken html tags for Mechanize parser'''
    def http_response(self, request, response):
        if not hasattr(response, "seek"):
            response = mechanize.response_seek_wrapper(response)
        # only use BeautifulSoup if response is html
        if 'content-type' in response.info().dict and ('html' in response.info().dict['content-type']):
            soup = MinimalSoup(response.get_data())
            response.set_data(soup.prettify())
        return response


class Browser(object):
    '''Create the browser emulator to allow the assessment role to be scraped'''
    def __init__(self):
        # LWPCookieJar will store in human readable format if we ever write to disk
        # to be debugged
        self.cj = cookielib.LWPCookieJar()
        self.br = mechanize.Browser()
        self.br.add_handler(PrettifyHandler())
        self.br.set_cookiejar(self.cj)

        # Browser options (blindly copied -- to be reviewed)
        self.br.set_handle_equiv(True)
        self.br.set_handle_gzip(False)
        self.br.set_handle_redirect(True)
        self.br.set_handle_referer(True)
        self.br.set_handle_robots(False)

        # Falsify the user-agent (No API offered, site requires falsified
        # browser user-agent)
        self.br.addheaders = [(
            'User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

    def mimic_cookie_js(self, street):
        '''Emulate page javascript cookie creation and set expiry date one year ahead'''
        # Should also do page the javascript string replacement found in the
        # page source
        future = datetime.datetime.now() + datetime.timedelta(days=365)
        expiration_date = time.mktime(future.timetuple())
        ck = cookielib.Cookie(
            version=0,
            name='nom_rue',
            value=street,
            port=None,
            port_specified=False,
            domain='evalweb.ville.montreal.qc.ca',
            domain_specified=False,
            domain_initial_dot=False,
            path='/Role2011actualise/',
            path_specified=True,
            secure=False,
            expires=expiration_date,
            discard=True,
            comment=None,
            comment_url=None,
            rest={'HttpOnly': None},
            rfc2109=False
        )
        self.cj.set_cookie(ck)
