#!/usr/bin/env python
# coding=utf8
# Kyle Fitzsimmons 2013

import os
import logging
import unicodedata
from flask import Flask, render_template, request, url_for, redirect, session, flash
from flask.ext.wtf import Form, TextField, Required
from werkzeug.exceptions import BadRequestKeyError, BadGateway
# Custom imports
import Browser
import RollScraper
from InputFormatter import format_streetname

app = Flask(__name__)
app.secret_key = os.urandom(24) # set salt for CRSF

# Debugs any errors to "debug.log"
file_handler = logging.FileHandler("debug.log","a")                                                                                             
file_handler.setLevel(logging.WARNING)
app.logger.addHandler(file_handler)

# classes to populate forms
class StreetForm(Form):
    street_name = TextField('Street name', validators=[Required()])
class AddressRange(Form):
    start_address = TextField('Street address (without subdivision; 4556 instead of 4556B)', validators=[Required()])
    end_address = TextField('End address')
        
# Mechanize browser as its own class to manage cookies between requests
BrowserInstance = Browser.Browser()

def init_session():
    print "Initial run, setting init state variables."
    session['street_name'] = None
    session['nbhood_form_fields'] = []
    session['nbhood_full_list'] = None
    session['selection_index'] = None
    session['csv_files'] = None    

@app.route('/', methods=['GET', 'POST'])
def index():
    '''This method is initially a little wonky because it contains two different forms
        within the same view. The ideal way may be just to present two different pages
        but this provides a more consistent user experience and is how it was originally
        written. It operates as follows:
            1.  checks to see if street name/address were set in the sessions dict on a
                previous run. Otherwise makes sure the variable used for this info later
                is set to None for checks.
            2.  Checks if first run (loop of view with data entered); sets up default variables
            3.  Checks if second run; gets entered street name and crawls for arrondissment choices
            4.  Checks if third (final) run; gets input arrondissment choice, scrapes assessment roll 
                and direct to success page
            5.  Success page - display .csv to download and return link; reinitialize form
    '''

    street_form = StreetForm() #enter street name
    address_form = AddressRange() #enter street address range

    if request.method == 'POST':
        if session.get('street_name') and not street_form.street_name.data:
            street_form.street_name.data = session.get('street_name')
        if session.get('start_address'):
            street_form.street_name.data = session.get('start_address')

    # clear blank field input for logic tests
    if street_form.street_name.data == '':
        street_form.street_name.data = None
    if address_form.start_address.data == '':
        address_form.start_address.data = None

    # if first run
    if not street_form.street_name.data:
        init_session()
    # elif street name has been entered but no data is in other fields
    elif street_form.street_name.data and not address_form.start_address.data:
        street_string = format_streetname(str(street_form.street_name.data))
        if session.get('street_name') != street_string:
            session['street_name'] = street_string
        print session['street_name']
        street_form.validate_on_submit()
        try:
            session['nbhood_form_fields'], session['nbhood_full_list'] = RollScraper.get_nbhoods_list(
                BrowserInstance, session['street_name'])
        except AttributeError:
            flash('Street name not found, please check and try again.')
            init_session()
        except Exception, e:
            flash(e)
            init_session()
        return render_template('forms.html', 
                        title="Montreal Assessment Roll Scraper",
                        street_form=street_form,
                        address_form=address_form,
                        neighborhood_list=session['nbhood_form_fields'])

    # else if second form is filled out (neighborhood and address range)
    else:
        # Custom dropdown form element (bit of a hack from normal WTF-flask forms)
        selected_neighborhood = str(request.form['selected-street'].encode('utf-8'))
        selection_index, garbage = selected_neighborhood.split(".", 1)
        selection_index = int(selection_index) - 1
        session['selection_index'] = selection_index
        # make sure that the input numbers are integers
        try:
            start_address = int(address_form.start_address.data.strip())
            '''disable ability to crawl address range'''
            # if address_form.end_address.data.strip() == '':
            end_address = None
            # else:
            #     end_address = int(address_form.end_address.data.strip())
        except:
            flash('Invalid address entered, please enter an integer only.')
            init_session()
            return render_template('forms.html', 
                            title="Montreal Assessment Roll Scraper", 
                            street_form=street_form,
                            address_form=AddressRange(),
                            neighborhood_list=session['nbhood_form_fields'])
        # execute the query to the assessment role webui
        try:
            scraped_data = RollScraper.enter_street_address(
                BrowserInstance, session['nbhood_full_list'], selection_index,
                start_address, end_address)
        except Exception, e:
            flash(e)
            init_session()
            return render_template('forms.html', 
                            title="Montreal Assessment Roll Scraper", 
                            street_form=street_form,
                            address_form=AddressRange(),
                            neighborhood_list=session['nbhood_form_fields'])
        # construct the .csv filenames 
        csv_files = {}
        for address, data_tuples_list in scraped_data.items():
            csv_list = []
            unit_in_building_index = 1
            for unit_id, scraped_json in data_tuples_list:
                if len(data_tuples_list) > 1:
                    csv = str(address).replace(" ", "_") + "__" + str(unit_in_building_index) + '.csv'
                    unit_in_building_index += 1
                else:
                    csv = str(address).replace(" ", "_") + '.csv'
                # Remove accents from filestring so our URL doesnt break
                nkfd_form = unicodedata.normalize('NFKD', unicode(csv.decode('utf-8')))
                csv = u"".join([c for c in nkfd_form if not unicodedata.combining(c)])
                csv_list.append(csv)
                # .csv output filepath
                csv_filepath = app.static_folder + '/csvs/' + csv
                RollScraper.csv_writer(csv_filepath, scraped_json)
            csv_files[address] = csv_list
            session['csv_files'] = csv_files
        return redirect(url_for('success'))

    return render_template('forms.html', 
                            title="Montreal Assessment Roll Scraper", 
                            street_form=street_form,
                            address_form=AddressRange(),
                            neighborhood_list=session['nbhood_form_fields'])

@app.route('/crawl_success', methods=['GET'])
def success():
    csv_url_dict = {}
    # print session['csv_files']
    for address, csv_list in session['csv_files'].items():
        csv_urls = []
        for csv_file in csv_list:
            csv_filename = 'csvs/' + csv_file
            csv_url = url_for('static', filename=csv_filename)
            csv_file = csv_file.replace("_", " ")
            csv_file = csv_file.replace(" ", "_", 1) # Juggle the string so it winds up like "3_453 James St.csv" (3 is the 3rd property)
            csv_urls.append((csv_url, csv_file))
        address = unicode(address, "utf8")
        csv_url_dict[address] = csv_urls
    session['selection_index'] = None #reset for next run
    # Clear session cookies
    BrowserInstance.cj.clear
    init_session()
    return render_template('success.html',
                            title="Crawl success!",
                            csv_url_dict=csv_url_dict)

# http://flask.pocoo.org/snippets/35/
class ReverseProxied(object):
    '''Wrap the application in this middleware and configure the 
    front-end server to add these headers, to let you quietly bind 
    this to a URL other than / and to an HTTP scheme that is 
    different than what is used locally.

    In nginx:
    location /myprefix {
        proxy_pass http://192.168.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Scheme $scheme;
        proxy_set_header X-Script-Name /myprefix;
        }

    :param app: the WSGI application
    '''
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]

        scheme = environ.get('HTTP_X_SCHEME', '')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        return self.app(environ, start_response)

app.wsgi_app = ReverseProxied(app.wsgi_app)

if __name__ == '__main__':
    # app.debug = True
    app.run(host='0.0.0.0')
    # app.run()

