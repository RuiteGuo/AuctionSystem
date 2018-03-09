#!/usr/bin/env python

import sys; sys.path.insert(0, 'lib') # this line is necessary for the rest
import os                             # of the imports to work!

import web
import sqlitedb
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

###########################################################################################
##########################DO NOT CHANGE ANYTHING ABOVE THIS LINE!##########################
###########################################################################################

######################BEGIN HELPER METHODS######################

# helper method to convert times from database (which will return a string)
# into datetime objects. This will allow you to compare times correctly (using
# ==, !=, <, >, etc.) instead of lexicographically as strings.

# Sample use:
# current_time = string_to_time(sqlitedb.getTime())

def string_to_time(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

# helper method to render a template in the templates/ directory
#
# `template_name': name of template file to render
#
# `**context': a dictionary of variable names mapped to values
# that is passed to Jinja2's templating engine
#
# See curr_time's `GET' method for sample usage
#
# WARNING: DO NOT CHANGE THIS METHOD
def render_template(template_name, **context):
    extensions = context.pop('extensions', [])
    globals = context.pop('globals', {})

    jinja_env = Environment(autoescape=True,
            loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
            extensions=extensions,
            )
    jinja_env.globals.update(globals)

    web.header('Content-Type','text/html; charset=utf-8', unique=True)

    return jinja_env.get_template(template_name).render(context)

#####################END HELPER METHODS#####################

urls = ('/currtime', 'curr_time',
        '/selecttime', 'select_time',
        '/search', 'search',
        '/add_bid', 'add_bid',
        '/item', 'item',
        '/', 'search'
        # first parameter => URL, second parameter => class name
        )

class item:
    def GET(self):
        get_params = web.input()
        itemID = get_params["itemID"]
        item = sqlitedb.item(itemID)
        message = str(item)
        return render_template('item.html', item = sqlitedb.getItemById(itemID), status = item[0], winner = item[1], bids = item[2], categories = item[3])

class curr_time:
    def GET(self):
        current_time = sqlitedb.getTime()
        return render_template('curr_time.html', time = current_time)
    # A simple GET request, to '/currtime'
    #
    # Notice that we pass in `current_time' to our `render_template' call
    # in order to have its value displayed on the web page
class add_bid:

    def GET(self):
        return render_template('add_bid.html',message = "Enter Your Bid!")


    def POST(self):
        post_params = web.input()
        InputArray = {}
        InputArray[0]=post_params["itemID"]
        InputArray[1]=post_params["userID"]
        InputArray[2]=post_params["price"]


        #print(InputArray)
        result = sqlitedb.addBid(InputArray)
        if(result[1]):
            return render_template('add_bid.html', message=result[0], add_result=result[1])
        return render_template('add_bid.html', message=result[0])


class search:

    def GET(self):
        message = "Search for an auction!"
        return render_template('search.html', message = message, search_result = None)
    def POST(self):
        post_params=web.input()
        searchKeys = [post_params['itemID'],post_params["userID"],post_params["minPrice"],post_params["maxPrice"], post_params["itemDescription"], post_params["status"]]
        result = sqlitedb.search(searchKeys)
        return render_template('search.html',message="Type in fields to search by", search_result = result)

class select_time:
    # Aanother GET request, this time to the URL '/selecttime'
    def GET(self):
        return render_template('select_time.html')

    # A POST request
    #
    # You can fetch the parameters passed to the URL
    # by calling `web.input()' for **both** POST requests
    # and GET requests
    def POST(self):
        post_params = web.input()
        MM = post_params['MM']
        dd = post_params['dd']
        yyyy = post_params['yyyy']
        HH = post_params['HH']
        mm = post_params['mm']
        ss = post_params['ss'];
        enter_name = post_params['entername']


        selected_time = '%s-%s-%s %s:%s:%s' % (yyyy, MM, dd, HH, mm, ss)
        update_message = '(Hello, %s. Previously selected time was: %s.)' % (enter_name, selected_time)
        # TODO: save the selected time as the current time in the database
        result = sqlitedb.setTime(selected_time)
        # Here, we assign `update_message' to `message', which means
        # we'll refer to it in our template as `message'
        if result:
            return render_template('select_time.html', message = update_message)
        return render_template('select_time.html', message = "Failed to update time: must set time forward, Dr. Who!")

###########################################################################################
##########################DO NOT CHANGE ANYTHING BELOW THIS LINE!##########################
###########################################################################################

if __name__ == '__main__':
    web.internalerror = web.debugerror
    app = web.application(urls, globals())
    app.add_processor(web.loadhook(sqlitedb.enforceForeignKey))
    app.run()
