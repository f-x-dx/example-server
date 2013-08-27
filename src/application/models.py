"""
models.py

App Engine datastore models

"""

from google.appengine.api import users
from google.appengine.ext import ndb
from flask import flash
from clover_api import CloverAPI
from collections import defaultdict
from datetime import datetime
import base64

class RSAPubKey(ndb.Model):
    n = ndb.TextProperty()
    e = ndb.TextProperty()

#Class that describes a reward for a particular merchant
class Reward(ndb.Model):
    item_id = ndb.StringProperty() #id of the item they get as a reward
    cyclic = ndb.BooleanProperty() #Whether the cost is cyclic(ie 10 20 30..)
    cost = ndb.IntegerProperty() #required number of points
    name = ndb.StringProperty() #Name of item

#Class that describes a merchant's reward settings
class RewardProperties(ndb.Model):
    #constants for reward type
    TYPE_NONE = 0 #no rewards for this merchant
    TYPE_AMOUNT = 1 #rewards based off amount spent
    TYPE_ORDER = 2 #rewards based on order

    #Specify reward type
    reward_type = ndb.IntegerProperty()
    #minimum to qualify for rewards(for TYPE_ORDER)
    minimum_price = ndb.IntegerProperty()

class Merchant(ndb.Model):
    id = ndb.StringProperty()
    access_token = ndb.StringProperty()
    name = ndb.StringProperty()
    money = ndb.IntegerProperty(default=0)
    last_updated = ndb.DateTimeProperty()
    inventory = ndb.PickleProperty()
    categories = ndb.PickleProperty()
    prefix = ndb.StringProperty()
    cc_key = ndb.StructuredProperty(RSAPubKey)
    reward_props = ndb.KeyProperty(kind=RewardProperties)
    rewards = ndb.KeyProperty(kind=Reward, repeated=True)
    created_tender = ndb.BooleanProperty(default=False)
    current_order_number = ndb.IntegerProperty(default=0)

    def get_inventory(self):
        if self.access_token and self.id:
            c = CloverAPI(self.access_token, self.id)
            items = c.get("/v2/merchant/{mId}/inventory/items_with_categories").items

            # category => {category_name : [item_id]}
            categories = defaultdict(list)
            # inventory => {item_id : item}
            inventory = {}

            for item in items:
                if item.priceType != "VARIABLE":
                    # Do not add variable price items
                    inventory[item.id] = item
                    for category in item.get("categories", []):
                        categories[category.name].append(item.id)

            self.inventory = inventory
            self.categories = categories
            self.put()
            self.update_keys()
        else:
            raise ValueError("Merchant does not have access token or id")

    def update_keys(self):
        if(self.last_updated == None
                or (datetime.now() - self.last_updated).days >= 7):
            c = CloverAPI(self.access_token, self.id)
            resp = c.get("/v2/merchant/{mId}/pay/key")
            key = RSAPubKey(n = resp.modulus, e = resp.exponent)
            self.cc_key = key
            self.prefix = resp.prefix[len(resp.prefix)-8:]

            self.last_updated = datetime.now()
            self.put()

    #gets rewards of this merchant
    def get_rewards(self):
        return ndb.get_multi(self.rewards)

    #Gets reward properties of merchant, initializing if it doesn't exist
    def get_reward_props(self):
        if not self.reward_props:
            self.reward_props = \
                RewardProperties(reward_type=RewardProperties.TYPE_NONE,
                minimum_price=0).put()
            self.put()
        return self.reward_props.get()


class Account(ndb.Model):
    """Google user account, and its properties"""
    user = ndb.UserProperty(required=True)
    merchant = ndb.KeyProperty(kind=Merchant)

    @classmethod
    def get_account(cls):
        """Gets account of current user or create a new one if none exists"""
        user = users.get_current_user()
        return cls.get_or_insert(user.user_id(), user=user)

    def get_merchant(self):
        if self.merchant:
            return self.merchant.get()
        return None

    def set_merchant(self, merchant_id):
        self.merchant = ndb.Key("Merchant", merchant_id)
        self.put()

class Item(ndb.Model):
    id = ndb.StringProperty()
    quantity = ndb.IntegerProperty()
    price = ndb.IntegerProperty()
    name = ndb.StringProperty()

class Order(ndb.Model):
    items = ndb.StructuredProperty(Item, repeated=True)
    pickup_time = ndb.DateTimeProperty()
    id = ndb.StringProperty()
    order_number = ndb.IntegerProperty()
    created_time = ndb.DateTimeProperty(auto_now_add=True)
    merchant = ndb.KeyProperty(kind="Merchant")
    customer_name = ndb.StringProperty()
    completed = ndb.BooleanProperty(default=False)
    total = ndb.IntegerProperty(default=0)

class MerchLink(ndb.Model):
    merchant = ndb.KeyProperty(kind="Merchant")
    customer = ndb.KeyProperty(kind="Customer")
    pay_token = ndb.StringProperty()
    last_four = ndb.StringProperty()
    prev_orders = ndb.KeyProperty(kind="Order", repeated=True, default=None)
    curr_order = ndb.StructuredProperty(Order)
    rewards_points = ndb.IntegerProperty(default=0)

    def get_merchant(self):
        if self.merchant:
            return self.merchant.get()
        return None

    def set_merchant(self, merchant_id):
        self.merchant = ndb.Key("Merchant", merchant_id)
        self.put()

    def add_item(self, item_id, quantity):
        price = self.get_merchant().inventory[item_id].price
        name = self.get_merchant().inventory[item_id].name.encode('utf-8')
        if(self.curr_order == None):
            self.curr_order = Order(items = [], merchant=self.merchant)
        self.remove_item(item_id)
        self.curr_order.items.append(Item(id=item_id,
                                name=name,
                                quantity=quantity,
                                price=price))
        self.curr_order.total += price * quantity
        flash("Added {} {} to cart".format(quantity, name), "success")
        self.put()

    def remove_item(self, item_id):
        for item in self.curr_order.items:
            if item.id == item_id and self.curr_order != None:
                self.curr_order.items.remove(item)
                self.curr_order.total -= item.price * item.quantity
                flash("Removed {} from cart".format(item.name), "success")
        self.put()

    @classmethod
    def get_merchlink(cls, merchant_id):
        merchant = Merchant.get_by_id(merchant_id)
        customer = Customer.get_current()
        return cls.query(cls.merchant==merchant.key,
                         cls.customer==customer.key).get()

class Customer(ndb.Model):
    user = ndb.UserProperty(required=True)
    name = ndb.StringProperty()
    access_token = ndb.StringProperty()
    linked_merchants = ndb.KeyProperty(kind="MerchLink", repeated=True)
    qr_code = ndb.StringProperty()

    def get_merchant_links(self):
        if len(self.linked_merchants) > 0:
            link = []
            for key in self.linked_merchants:
                merchant = key.get()
                link.append(merchant)
            return link
        return None

    def add_merchant_link(self, merchant_link_id):
        self.linked_merchants += [ndb.Key("MerchLink", merchant_link_id)]
        self.put()

    @classmethod
    def get_current(cls):
        return cls.get_by_id(users.get_current_user().user_id())

class Payment(ndb.Model):
    amount = ndb.IntegerProperty()
    merchant = ndb.KeyProperty(kind="Merchant")
    customer = ndb.KeyProperty(kind="Customer")
    time_made = ndb.TimeProperty(auto_now_add=True)
    order = ndb.KeyProperty(kind="Order")
