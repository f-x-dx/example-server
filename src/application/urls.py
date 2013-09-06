"""
urls.py

URL dispatch route mappings and error handlers

"""
from flask import render_template

from application import app
from application import views

## URL dispatch rules
# App Engine warm up handler
# See http://code.google.com/appengine/docs/python/config/appconfig.html#Warming_Requests
app.add_url_rule('/_ah/warmup', 'warmup', view_func=views.warmup)

# Home page
app.add_url_rule('/', 'home', view_func=views.home)

# Examples list page
app.add_url_rule('/merchant/home', 'merchant_home',
                 view_func=views.merchant_home, methods=['GET'])

# Callback after clover login
app.add_url_rule('/merchant/unlink', 'unlink_merchant',
                 view_func=views.unlink_merchant)

# Loads inventory of merchant
app.add_url_rule('/merchant/load_inventory', 'load_inventory',
                 view_func=views.load_inventory)

# Callback after clover login
app.add_url_rule('/clover_callback', 'clover_callback',
                 view_func=views.clover_callback)

# Customer home page
app.add_url_rule('/customer_home', 'customer_home',
                 view_func=views.customer_home)

# Posts a new merchlink with a credit card and merchant
app.add_url_rule('/post_cc', 'post_cc',
                 view_func=views.post_cc, methods=['POST'])

# Go to merchant's inventory page
app.add_url_rule('/merchant/<merchant_id>/order', 'order',
                 view_func=views.order, methods=['GET'])

# Go to merchant's inventory page (read only)
app.add_url_rule('/merchant/<merchant_id>/inventory', 'inventory',
                 view_func=views.show_inventory, methods=['GET'])

# List all merchants for new merchant order ahead
app.add_url_rule('/merchants', 'list_merchants',
                 view_func=views.list_merchants, methods=['GET'])

# Adds an Item to an order
app.add_url_rule('/merchant/<merchant_id>/add_item', 'add_item',
                 view_func=views.add_item, methods=['POST'])

# Removes an Item from an order
app.add_url_rule('/merchant/<merchant_id>/remove_item', 'remove_item',
                 view_func=views.remove_item,  methods=['POST'])

# Gets Details of an order and places it.
app.add_url_rule('/merchant/<merchant_id>/place_order', 'place_order',
                 view_func=views.place_order, methods=['POST', 'GET'])

# Makes and pays for order.
app.add_url_rule('/pay/<merchant_id>', 'finish_order',
                 view_func=views.finish_order)

# Page to show past orders
app.add_url_rule('/orders/<order_id>', 'order_page',
                 view_func=views.order_page)

# Marks an Order Completed.
app.add_url_rule('/complete/<order_id>', 'compelete_order',
        view_func=views.complete_order, methods = ['POST'])

# Removes a merchant link
app.add_url_rule('/remove_cc/<merchant_id>', 'remove_cc',
                 view_func=views.remove_cc, methods=['POST', 'GET'])

# Shows QR Code
app.add_url_rule("/show_qr_code", "show_qr_code",
                 view_func=views.show_qr_code, methods=["GET"])

# Show pebble access_token
app.add_url_rule("/get_pebble_token", "get_pebble_token",
                 view_func=views.get_pebble_token, methods=['GET'])

# Gets qr code and refreshes token
app.add_url_rule("/get_qr_from_token", "get_qr_from_token",
                view_func=views.get_qr_from_token, methods=['POST'])

#Charge customer
app.add_url_rule("/charge", "charge",
                 view_func=views.charge, methods=["POST"])

#Record a payment made on the device
app.add_url_rule("/record_payment", "record_payment",
        view_func=views.record_payment, methods=['POST'])

# Gets a merchants orders
app.add_url_rule("/get_orders/<merchant_id>", "get_orders",
        view_func=views.get_orders, methods=['GET'])

#Show reward points 
app.add_url_rule("/show_reward_points", "show_reward_points",
                 view_func=views.show_reward_points, methods=["GET"])

#Show current reward properties
app.add_url_rule("/show_reward_props/<merchant_id>", "show_reward_props",
                 view_func=views.show_reward_props, methods=["GET"])

#Changes reward properties for a merchant
app.add_url_rule("/set_reward_props", "set_reward_props",
                 view_func=views.set_reward_props, methods=["POST"])

#Adds a reward for a merchant
app.add_url_rule("/add_reward_merchant", "add_reward_merchant",
        view_func=views.add_reward_merchant, methods=["POST"])

#Resets the reward points for all customers of this merchant
app.add_url_rule("/reset_rewards_merchant", "reset_rewards_merchant",
        view_func=views.reset_rewards_merchant, methods=["POST"])

#Removes a reward for a merchant
app.add_url_rule("/remove_reward_merchant", "remove_reward_merchant", 
        view_func=views.remove_reward_merchant, methods=["POST"])

#Returns the rewards a customer qualifies for
app.add_url_rule("/get_rewards_customer", "get_rewards_customer", 
        view_func=views.get_rewards_customer, methods=["GET"])

#applies the rewards to a customer's order
app.add_url_rule("/apply_rewards_customer", "apply_rewards_customer",
        view_func=views.apply_rewards_customer, methods=["POST"])


## Error handlers
# Handle 404 errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Handle 500 errors
@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500
