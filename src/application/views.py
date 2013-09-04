"""
views.py

URL route handlers

Note that any handler params must match the URL route params.
For example the *say_hello* handler, handling the URL route '/hello/<username>',
  must be passed *username* as the argument.

"""
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.runtime.apiproxy_errors import CapabilityDisabledError

from flask import request, render_template, flash, url_for, redirect, abort
import logging

from flask_cache import Cache

from application import app
from decorators import login_required, admin_required
from models import Merchant, Customer, Payment, MerchLink, Account, Item, \
    RewardProperties, Reward, Order
from os import urandom

import urllib
import urlparse

from clover_api import CloverAPI
from forms import CustomerForm

from flask import jsonify, json
import uuid
from datetime import datetime, timedelta

# Flask-Cache (configured to use App Engine Memcache API)
cache = Cache(app)

# TODO change these to prod app secret and id when making prod

APP_SECRET = "4d69f86c-0758-6951-3f46-f08baa98e758"
APP_ID = "7JQ49Q1NGNFZ6"

TENDER_KEY = "com.clover.cloverexample"
TENDER_NAME = "Example Tender"

def home():
    return redirect(url_for('customer_home'))

def say_hello(username):
    """Contrived example to demonstrate Flask's url routing capabilities"""
    return 'Hello %s' % username

@login_required
def merchant_home():
    """List all payments"""
    base_url = CloverAPI.base_url
    account = Account.get_account()
    merchant = account.get_merchant()
    login_url = CloverAPI.build_auth_url(request.url_root + "clover_callback",
                                         APP_ID)
    if merchant:
        qry = Payment.query(Payment.merchant == merchant.key)
        payments = qry.order(Payment.time_made)
    if not (merchant and merchant.inventory):
        flash("You currently don't have any inventory loaded. Add items from the Clover dashboard and reload your inventory here.", "warning")
    return render_template('merchant_home.html',
                           format_price=format_price,
                           merchant_section="true",
                           **locals())

@login_required
def unlink_merchant():
    """Unlink the merchant from the user's account"""
    account = Account.get_account()
    merchant = account.get_merchant()
    if merchant:
        name = merchant.name
        account.merchant = None
        account.put()
        flash("Successfully unlinked merchant: " + name, "success")
    else:
        flash("No merchant to unlink", "error")
    return redirect(url_for("merchant_home"))

def list_merchants():
    all_merchants = Merchant.query().fetch()
    return render_template('list_merchants.html', **locals())

@login_required
def load_inventory(redirect_to_home=True):
    """Loads/Reloads the inventory of the merchant"""
    try:
        Account.get_account().get_merchant().get_inventory()
        flash("Merchant's inventory successfully loaded", "success")
    except Exception as e:
        print e
        flash("Could not get inventory of merchant", "error")
    if redirect_to_home:
        return redirect(url_for("merchant_home"))

@login_required
def clover_callback():
    account = Account.get_account()
    code = request.args.get('code')
    merchant_id = request.args.get('merchant_id')
    resp = CloverAPI().get('/cos/v1/oauth/token',
                           client_id=APP_ID,
                           client_secret=APP_SECRET,
                           code=code)
    access_token = resp.get("access_token")
    if merchant_id and access_token:
        merchant = Merchant.get_or_insert(merchant_id)
        account.set_merchant(merchant_id)

        try:
            c = CloverAPI(access_token, merchant_id)
            name = c.get("/v2/merchant/{mId}/name").name
        except:
            name = None
            flash("Could not update merchant's properties, there may "
                  "be an error with the access token", "error")

        #Create system tender if we haven't seen it before
        #If it's already made, it won't do anything
        if not hasattr(clover_callback, "system_tender_created"):
            try:
                c.post("/v2/tenders", 
                    { "tender" : {
                        "label" : TENDER_NAME,
                        "labelKey" : TENDER_KEY 
                    }})
                clover_callback.system_tender_created = True
            except:
                #Ignore if it's already taken since this might be called
                #again if server restarts
                pass
        
        if not merchant.created_tender:
            # Create merchant tender
            try:
                c.post("/v2/merchant/{mId}/tenders",
                       {"tender": {"opensCashDrawer": False,
                                   "enabled": True,
                                   "label": TENDER_NAME,
                                   "labelKey": TENDER_KEY}})
                merchant.created_tender = True
                flash("Created custom merchant tender", "success")
            except:
                flash("Could not create merchant tender", "error")

        merchant.populate(
            id = merchant_id,
            access_token = access_token,
            name = name
        )
        merchant.put()
        merchant.update_keys()
        load_inventory(redirect_to_home=False)
        flash("Merchant successfully linked", "success")
    else:
        flash("Error linking merchant, incorrect callback", "error")
    return redirect(url_for('merchant_home'))

format_price = lambda price: "${}.{:02}".format(price / 100, price % 100)

@login_required
def order(merchant_id):
    merchant = Merchant.get_by_id(merchant_id)

    if not merchant:
        abort(404)

    customer = Customer.get_current()
    merch_link = MerchLink.get_merchlink(merchant_id)
    if merch_link==None:
        merch_link = MerchLink(merchant=merchant.key, customer=customer.key,
                pay_token=None)
        merch_link_key = merch_link.put()
        customer.linked_merchants.append(merch_link_key)
        customer.put()
    if customer:
        order_template = render_order_merchlink(merch_link)

    items = merchant.inventory
    categories = merchant.categories
    if (items is None) or (categories is None):
        flash("Sorry, this merchant doesn't have any items to order.", "error")
        return redirect(url_for('customer_home'))

    def format_item(item):
        return format_price(item.price) + \
            (" per " + item.unitName if item.priceType == "PER_UNIT" else "")

    return render_template("inventory.html", **locals())

@login_required
def show_inventory(merchant_id):
    merchant = Merchant.get_by_id(merchant_id)

    if not merchant:
        abort(404)

    customer = Customer.get_current()
    merch_link = MerchLink.get_merchlink(merchant_id)
    if merch_link==None:
        merch_link = MerchLink(merchant=merchant.key, customer=customer.key,
                pay_token=None)
        merch_link_key = merch_link.put()
        customer.linked_merchants.append(merch_link_key)
        customer.put()

    items = merchant.inventory
    categories = merchant.categories
    if (items is None) or (categories is None):
        flash("Sorry, you don't have any items to view. Try reloading your inventory.", "error")
        return redirect(url_for('merchant_home'))

    def format_item(item):
        return format_price(item.price) + \
            (" per " + item.unitName if item.priceType == "PER_UNIT" else "")

    return render_template("inventory.html", merchant_section="true", **locals())

def warmup():
    """App Engine warmup handler
    See http://code.google.com/appengine/docs/python/config/appconfig.html#Warming_Requests

    """
    return ''

def render_order_merchlink(merch_link, disable_order_button=False):
    if (merch_link and merch_link.curr_order != None and
        len(merch_link.curr_order.items) > 0):
        #Find total cost
        total_cost = 0
        for item in merch_link.curr_order.items:
            total_cost += item.quantity * item.price

        rewards = find_rewards_customer(merch_link.customer,
                Merchant.query(Merchant.key == merch_link.merchant).get().id, 
                total_cost)

        #Set to none if there are none
        if rewards == []:
            rewards = None

        return render_order(merch_link.curr_order,
                            disable_order_button,
                            merch_link.merchant.get(), rewards=rewards)
    return ""

def render_order(order, disable_order_button=False, merchant=None, 
        rewards=None):
    return render_template('order.html', format_price=format_price,
                           **locals())

@login_required
def add_item(merchant_id):
    merch_link = MerchLink.get_merchlink(merchant_id)
    item_id = request.args["id"]
    try:
        quantity = int(request.args['quantity'])
        merch_link.add_item(item_id, quantity)
    except ValueError as e:
        flash("Please enter a valid quantity", "error")
    return render_order_merchlink(merch_link)

@login_required
def remove_item(merchant_id):
    merch_link = MerchLink.get_merchlink(merchant_id)
    item_id = request.args["id"]
    merch_link.remove_item(item_id)
    return render_order_merchlink(merch_link)

@login_required
def place_order(merchant_id):
    merch_link = MerchLink.get_merchlink(merchant_id)
    merchant = merch_link.get_merchant()
    if request.method == 'POST':
        merch_link.curr_order.customer_name = request.json['name']
        merch_link.curr_order.order_number = merchant.current_order_number%100
        merch_link.curr_order.pickup_time = \
          datetime.fromtimestamp(request.json['pickup_timestamp'])
        merch_link.put()
        return jsonify(status="OK");
    elif request.method == 'GET':
        order_number = merchant.current_order_number % 100;
        order_template = render_order_merchlink(merch_link, disable_order_button=True)
        return render_template('order_details.html', **locals())

def format_time(time):
    timedate = time.split(' ')
    time = timedate[1]
    date = timedate[0]
    formatted_time = time.split(':')[:2]
    hour = int(formatted_time[0])
    if hour > 12:
        td = ' PM'
        hour = hour % 12
    else:
        td = ' AM'
        if hour == 0:
            hour0 = 12
    time = str(hour) + ':' + formatted_time[1] + td
    date = '-'.join(date.split('-')[1:])
    return time + ' on ' + date

def get_orders(merchant_id):
    #within_last = request.args['time']
    merchant = Merchant.query(Merchant.id==merchant_id).get()
    py_orders = Order.query(ndb.AND(Order.merchant==merchant.key,
            #(Order.pickup_time < datetime.now() +
             #   timedelta(seconds=int(within_last))),
             )).order(-Order.pickup_time).order(-Order.order_number).fetch(15)
    json_orders = []
    for order in py_orders:
        json_order = {"order_id": order.id, "pickup_time":
                format_time(str(order.pickup_time)),
                "customer_name": order.customer_name,
                "order_number": order.order_number, 
                "completed":order.completed}
        json_orders.append(json_order)
    return jsonify(orders=json_orders)

@login_required
def order_page(order_id):
    try:
        # TODO: Check that the order_id belongs to the customer or merchant
        #       before rendering it
        order = Order.get_by_id(int(order_id))
        assert order is not None
    except:
        abort(404)
    order_html = render_order(order, disable_order_button=True)
    return render_template('order_page.html', **locals())

@login_required
def finish_order(merchant_id):
    try:
        merch_link = MerchLink.get_merchlink(merchant_id)
        if(merch_link.curr_order == None or len(merch_link.curr_order.items)==0):
            flash('No items in order.', 'error')
            return redirect(url_for('customer_home'))
        merchant = merch_link.get_merchant()
        merchant.current_order_number += 1
        merchant.put()
        c = CloverAPI(merchant.access_token, merchant.id)
        uuid = c.post("/v2/merchant/{mId}/orders", {}).uuid
        merch_link.curr_order.id = uuid;
        merch_link.put()
        c.post("/v2/merchant/{mId}/orders/{orderId}/state",
            {"state": "OPEN"},orderId=uuid)
        total = merch_link.curr_order.total
        for item in merch_link.curr_order.items:
            #TODO support adding for item unit quantity
            i = 0
            while i < item.quantity:
                c.post("/v2/merchant/{mId}/orders/{orderId}/line_items",
                        {"item": {"id": item.id} , "unitQty" : 1}, orderId=uuid)
                i += 1
        c.post("/v2/merchant/{mId}/orders/{orderId}/state",
            {"state": "CLOSED"}, orderId=uuid)
        c.post("/v2/merchant/{mId}/orders/{orderId}/total", 
                {"total":merch_link.curr_order.total},
                orderId=uuid)

        if merch_link.pay_token == None:
            return add_cc(merchant_id, uuid, total)
        resp = make_payment(uuid, total, merch_link)
        if (resp.result == "APPROVED"):
            #Give the customer reward points
            #Whether or not they are enabled is checked in the function
            new_points = calculate_reward_points(total, 
                    RewardProperties.query(
                        RewardProperties.key == merchant.reward_props).get())
            merch_link.rewards_points += new_points
            merch_link.put()

            flash("Order placed. Payment Successful.", 'success')
            return redirect(url_for('customer_home'))
        elif (resp.result == "DECLINED"):
            flash("Credit Card Declined", "error")
            logging.info(resp)
        else:
            flash("Something went wrong", "error")
        return redirect(url_for('order', merchant_id=merchant_id))
    except Exception as e:
        print(e)
        return redirect(url_for('customer_home'))


@login_required
def customer_home():
    user = users.get_current_user()
    customer = Customer.get_or_insert(user.user_id(), user=user,
            access_token=str(uuid.uuid4()))
    qry = Payment.query(Payment.customer == customer.key)
    payments = qry.order(Payment.time_made).fetch(20)
    name = customer.name
    linked_merchants = customer.get_merchant_links()
    customer.put()
    return render_template('customer_home.html', format_price=format_price,
            **locals())

@login_required
def get_pebble_token():
    user = users.get_current_user()
    customer = Customer.query(Customer.user == user).get()
    return render_template('display_pebble.html', token=customer.access_token)

def refresh_access_token():
    old_token = request.json['token']
    customer = Customer.query(Customer.access_token==old_token).get()
    customer.access_token = str(uuid.uuid4());
    customer.put();
    return jsonify(token=customer.access_token)

def get_qr_from_token():
    old_token = request.json['token']
    customer = Customer.query(Customer.access_token==old_token).get()
    customer.access_token = str(uuid.uuid4());
    customer.qr_code = str(uuid.uuid4())
    customer.put();
    return jsonify(token=customer.access_token, qr_code=customer.qr_code)

# Goes to template that adds credit card. The card is encrypted in javascript
# client-side before it is ever sent anywhere
@login_required
def add_cc(merchant_id, orderId, amount):
    user = users.get_current_user()
    base_url = CloverAPI.base_url
    customer = Customer.query(Customer.user == user).get()
    merchant = Merchant.query(Merchant.id==merchant_id).get()
    merchant.update_keys()
    return render_template('add_cc.html', **locals())

# Posts the cc to clover and gets back and stores the cc token
@login_required
def post_cc():
    if request.json['result'] == "APPROVED":
        pay_token = request.json['paytoken']
        merchant_id = request.json['merchant']
        last_four = request.json['last_four']
        amount = request.json['amount']
        merchant = Merchant.query(Merchant.id==merchant_id).get()
        auth_token = merchant.access_token
        merch_link = MerchLink.query(ndb.AND(MerchLink.merchant==merchant.key,
            MerchLink.customer==Customer.get_current().key)).get()
        if merch_link.pay_token == None:
            user = users.get_current_user()
            merch_link.pay_token = pay_token
            merch_link.last_four = last_four
            order = merch_link.curr_order
            order_key = order.put()
            merch_link.prev_orders.append(order_key)
            merch_link.curr_order = None
            merch_link_key = merch_link.put()
            payment = Payment(amount=amount, merchant=merchant.key,
                    customer=Customer.get_current().key, order=order_key)
            payment.put()
        return redirect(url_for('customer_home'))
    else:
        flash("We are sorry, Something went wrong. Please try again.", "error")
    return jsonify(error="error")

# Removes the specified merchlink
@login_required
def remove_cc(merchant_id):
    customer = Customer.get_current()
    merch_link = MerchLink.get_merchlink(merchant_id)
    customer.linked_merchants.remove(merch_link.key)
    customer.put()
    merch_link.key.delete()
    return render_template('customer_home.html')

def record_payment():
    merchant_id = request.json['merchant']
    last_four = request.json['last_four']
    amount = request.json['amount']
    qr_code = request.json['qr_code']
    pay_token = request.json['pay_token']
    customer =  Customer.query(Customer.qr_code == qr_code).get()
    merchant = Merchant.query(Merchant.id==merchant_id).get()
    auth_token = merchant.access_token
    merch_link = MerchLink.query(ndb.AND(MerchLink.merchant==merchant.key,
            MerchLink.customer==customer.key)).get()
    if merch_link.pay_token == None:
        merch_link.pay_token = pay_token
        merch_link.last_four = last_four
        order = Order(merchant=merchant.key, total=amount, completed=True)
        order_key = order.put()
        merch_link.prev_orders.append(order_key)
        merch_link.curr_order = None
        merch_link_key = merch_link.put()
        customer.linked_merchants.append(merch_link_key)
        customer.put()
        payment = Payment(amount=amount, merchant=merchant.key,
                customer=customer.key, order=order_key)
        payment.put()
    return jsonify(status="OK")

#Make a payment and record it.
def make_payment(orderId, amount, merch_link):
    merchant = merch_link.get_merchant()
    c = CloverAPI(merchant.access_token, merchant.id)
    resp = c.post("/v2/merchant/{mId}/pay", {"orderId": orderId,
        "currency": "usd", "token": merch_link.pay_token, "amount": amount})
    if(resp.result == "APPROVED"):
        merch_link.pay_token = resp.token
        if merch_link.curr_order == None:
            order = Order(merchant=merchant.key, total=amount)
        else:
            order = merch_link.curr_order
        order_key = order.put()
        merch_link.curr_order = None
        merch_link.prev_orders.append(order_key)
        payment = Payment(amount=amount, merchant=merch_link.merchant,
                customer=merch_link.customer, order=order_key)
        payment.put()
        merch_link.put()

        #Change qr code
        customer = merch_link.customer.get()
        customer.qr_code = str(uuid.uuid4())
        customer.put()

    return resp

def complete_order(order_id):
    order = Order.query(Order.id == order_id).get()
    order.completed = True
    order.put()
    return jsonify(status="OK")

@login_required
def show_qr_code():
    current_user = users.get_current_user()

    query = Customer.query(Customer.user == current_user)
    #If nothing matched this query(shouldn't ever happen)
    if not query:
        return render_template("500.html"), 500
    customer = query.get()
    #If it doesn't already have one, assign a new qr code
    if not customer.qr_code:
        customer.qr_code = str(uuid.uuid4())
        customer.put()
    qr_code = customer.qr_code

    return render_template("qr_code.html", qr_code=qr_code)

#Charge a customer using QR code and merchant id
def charge():
    try:
        json_in = request.get_json(silent = True)
        #check to make sure json is ok
        if not (json_in and ("qr_code" in json_in) and ("merchant_id" in json_in)):
            return jsonify(status="invalid request")

        merch_id = json_in["merchant_id"]
        qr_code = json_in["qr_code"]
        order_id = json_in["order_id"]
        amount = json_in["amount"]

        #get customer
        customer =  Customer.query(Customer.qr_code == qr_code).get()
        #If qr_code didn't match anything in ndb
        if not customer:
            return jsonify(status="customer not found")

        #get the Merchant associated with this merch_id
        merchant = Merchant.query(Merchant.id == merch_id).get()
        if not merchant:
            return jsonify(status="merchant not found")

        #Find MerchLink from customer and merchant
        merch_link = MerchLink.query(MerchLink.merchant == merchant.key,
                MerchLink.customer == customer.key).get()
        if (merch_link == None):
            merch_link = MerchLink(merchant=merchant.key, customer=customer.key,
                    pay_token=None)
            merch_link.put()
        if merch_link.pay_token == None:
            return jsonify(status="no pay token",
                    access_token=merchant.access_token, qr_code=qr_code)

        resp = make_payment(order_id, amount, merch_link)
        if(resp.result == "APPROVED"):
            #Give the customer reward points
            #Whether or not they are enabled is checked in the function
            new_points = calculate_reward_points(amount, 
                    RewardProperties.query(
                        RewardProperties.key == merchant.reward_props).get())
            merch_link.rewards_points += new_points
            merch_link.put()

            return jsonify(status="payed")
        elif (resp.result == "DECLIND"):
            return jsonify(status="declined")
        else:
            return jsonify(status="error")
    except Exception as e:
        print(e)

#Displays rewards points that a customer has accumulated
@login_required
def show_reward_points():
    customer = Customer.query(Customer.user == users.get_current_user()).get()
    merch_links = customer.get_merchant_links()
    ret = []
    if merch_links:
        for merch_link in merch_links:
            #If there were no rewards before, set to 0
            try:
                merch_link.reward_points
            except AttributeError:
                merch_link.reward_points = 0
                merch_link.put()

            merchant = Merchant.query(Merchant.key == merch_link.merchant).get()
            ret.append({ "name" : merchant.name,
                "reward_points" : merch_link.reward_points })

    #get rewards
    if not merch_link:
        return render_template("500.html"), 500

    return render_template("show_reward_points.html",
            merchants=ret)

# Returns list of rewards that should be applied given current customer id,
# merchant id, and items in the order
def find_rewards_customer(customer_key, merchant_id, total_amount):
    #Find merchant
    merchant = Merchant.query(Merchant.id == merchant_id).get()
    if not merchant:
        return []

    #Now get the customer
    customer = Customer.query(Customer.key == customer_key).get()
    if not customer:
        return []

    #Get current points
    merch_link = MerchLink.query(MerchLink.merchant == merchant.key,
            MerchLink.customer == customer.key).get()
    if not merch_link:
        return []

    points = merch_link.rewards_points

    #Get reward properties
    reward_props = merchant.get_reward_props()
    #get number of points that would be added by this order
    added_points = calculate_reward_points(total_amount, reward_props)

    #return list of rewards as dictionaries of name and item_id 
    ret = []
    #get rewards
    rewards = merchant.get_rewards()
    for reward in rewards:
        if reward.cyclic:
            #If cyclic, we have to pass another "cycle"
            if points % reward.cost + added_points >= reward.cost:
                ret.append({ "name" : reward.name, "item_id" : reward.item_id})

        else:
            #See if we should add this reward
            if points < reward.cost and points + added_points >= reward.cost:
                ret.append({ "name" : reward.name, "item_id" : reward.item_id})

    return ret

#Finds the amount of points earned by the items
def calculate_reward_points(total_amount, reward_props):
    #If no rewards
    if reward_props.reward_type == RewardProperties.TYPE_NONE:
        return 0

    #If we get points based on price of item
    if reward_props.reward_type == RewardProperties.TYPE_AMOUNT:
        return total_amount

    #otherwise we get points based on number of orders

    #If the total cost is more than minimum, give them a point
    if total_amount >= reward_props.minimum_price:
        return 1

    return 0

""" 
Returns json representation of rewards that customer will get if he/she 
goes through with the order
"""
def get_rewards_customer():
    qr_code = request.args.get("qr_code")
    merchant_id = request.args.get("merchant_id")
    total_amount = int(request.args.get("total_amount"))
    
    customer = Customer.query(Customer.qr_code == qr_code).get()
    if not customer:
        return jsonify(status="error", 
            message="No customer found with that qr_code")

    merchant = Merchant.query(Merchant.id == merchant_id).get()
    if not merchant:
        return jsonify(status="error", 
            message = "No merchant found with that id")
    
    rewards = find_rewards_customer(customer.key, merchant_id, total_amount)

    return jsonify(status="success", rewards=rewards)

#Gives rewards to customer
def apply_rewards_customer():
    #TODO ensure this is sent from someone who's actually authorized to do so
    merchant_id = request.get_json()["merchant_id"]
    order_id = request.get_json()["order_id"]
    #rewards should be json array of "item_id"
    rewards = request.get_json()["rewards"]

    merchant = Merchant.query(Merchant.id == merchant_id).get()
    if not merchant:
        return jsonify(status="error", message="No merchant found with that id")

    clover = CloverAPI(access_token=merchant.access_token, 
            merchant_id=merchant_id)

    #try to add every reward to order
    for reward in rewards:
        #Add the line item
        response = clover.post("/v2/merchant/{mId}/orders/{orderId}/line_items",
            { "item" : { "id" : reward["itemId"], 
                "unitQty" : reward["unitQty"] } }, orderId=order_id)

        #Make the line item free
        clover.post("/v2/merchant/{mId}/orders/{orderId}"
            "/line_items/{lineItemId}/adjustments", 
            { "adjustment" : { "type" : "DISCOUNT", "percentage" : 100} }, 
            orderId = order_id, 
            lineItemId=response["uuid"])

    #return success/fail and new pricing
    return jsonify(status="success")
    
#Adds a reward for a merchant
def add_reward_merchant():
    #Get form values
    merchant_id = request.form["merchant_id"]
    item_id = request.form["item_id"]
    cyclic = False
    if "cyclic" in request.form:
        cyclic = True
    cost = request.form["cost"]
    reward_name = request.form["name"]

    #Get merchant
    merchant = Merchant.query(Merchant.id == merchant_id).get()
    if not merchant:
        #Signal that operation failed
        return render_template("500.html"), 500

    #add new reward
    new_reward_key = \
            Reward(item_id=item_id, cyclic=bool(cyclic), cost=int(cost),
            name=reward_name).put()

    #Update merchant
    merchant.rewards.append(new_reward_key)
    merchant.put()

    #Get items
    inventory = merchant.inventory
    #Set to empty dict if there's no inventory
    if not inventory:
        inventory = {}
    inventory = json.dumps(inventory)

    #Get reward_props
    reward_props = merchant.get_reward_props()
    #get rewards
    rewards = merchant.get_rewards()

    return render_template("show_reward_props.html",
            reward_type=reward_props.reward_type,
            minimum_price=reward_props.minimum_price, rewards=rewards,
            merchant_id=merchant_id, changed=1,
            merchant_section="true", json_inventory=inventory)

#Removes a reward from merchant settings
def remove_reward_merchant():
    reward_key = ndb.Key(urlsafe=request.form["reward_key"])
    merchant_id = request.form["merchant_id"]

    #Get merchant
    merchant = Merchant.query(Merchant.id == merchant_id).get()

    #get reward

    #remove reward from rewards and from ndb
    merchant.rewards.remove(reward_key)
    reward_key.delete()

    #Add merchant back after removing rewards
    merchant.put()

    #Stuff for template
    rewards = merchant.get_rewards()
    reward_props = merchant.get_reward_props()
    inventory = json.dumps(merchant.inventory)

    return render_template("show_reward_props.html",
            reward_type=reward_props.reward_type,
            minimum_price=reward_props.minimum_price, rewards=rewards,
            merchant_id=merchant_id, changed=1,
            merchant_section="true", json_inventory=inventory)

#Sets reward properties for a merchant
def set_reward_props():#merchant_id, reward_type, minimum_price)
    merchant_id = request.form["merchant_id"]
    reward_type = int(request.form["reward_type"])
    minimum_price = int(request.form["minimum_price"])

    #get merchant
    merchant = Merchant.query(Merchant.id == merchant_id).get()

    if not merchant:
        return render_template("500.html"), 500

    #Check that reward_type is valid
    if not (reward_type == RewardProperties.TYPE_NONE or
            reward_type == RewardProperties.TYPE_AMOUNT or
            reward_type == RewardProperties.TYPE_ORDER):
        return render_template("500.html"), 500

    #min price can't be negative if it's going to be used
    if reward_type != RewardProperties.TYPE_ORDER:
        minimum_price = 0

    if minimum_price < 0:
        return render_template("500.html"), 500

    #get reward properties
    reward_props = merchant.get_reward_props()

    #set reward type and minimum price
    reward_props.reward_type = reward_type
    reward_props.minimum_price = minimum_price
    reward_props.put()

    rewards = merchant.get_rewards()

    #Get inventory
    inventory = merchant.inventory
    #Set to empty dict if there's no inventory
    if not inventory:
        inventory = {}
    inventory = json.dumps(inventory)

    return render_template("show_reward_props.html",
            reward_type=reward_props.reward_type,
            minimum_price=reward_props.minimum_price,
            merchant_id=merchant_id, changed=1, rewards=rewards,
            merchant_section="true", json_inventory=inventory)

#Show current reward properties
def show_reward_props(merchant_id):
    #get merchant
    merchant = Merchant.query(Merchant.id == merchant_id).get()
    if not merchant:
        return render_template("500.html"), 500

    #get reward_props
    reward_props = merchant.get_reward_props()

    #get rewards
    rewards = merchant.get_rewards()

    #Get items
    inventory = merchant.inventory
    #Set to empty dict if there's no inventory
    if not inventory:
        inventory = {}
    inventory = json.dumps(inventory)

    return render_template("show_reward_props.html",
            reward_type=reward_props.reward_type,
            minimum_price=reward_props.minimum_price, rewards=rewards,
            merchant_id=merchant_id, changed=0,
            merchant_section="true", json_inventory=inventory)
