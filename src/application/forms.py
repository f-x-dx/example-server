"""
forms.py

Web forms based on Flask-WTForms

See: http://flask.pocoo.org/docs/patterns/wtforms/
     http://wtforms.simplecodes.com/

"""

from flaskext import wtf
from flaskext.wtf import validators
from wtforms.ext.appengine.ndb import model_form


#from .models import ExampleModel
from .models import Customer
from .models import *

class CustomerForm(wtf.Form):
    name = wtf.TextField('Name', validators=[validators.Required()])
    credit_card = wtf.TextField('Credit Card', validators=[validators.Required()])
    merchant = wtf.SelectField('Merchants', coerce=int, default=0, validators=[validators.Required()])
    

#class ClassicExampleForm(wtf.Form):
#    example_name = wtf.TextField('Name', validators=[validators.Required()])
#    example_description = wtf.TextAreaField('Description', validators=[validators.Required()])
#
## App Engine ndb model form example
#ExampleForm = model_form(ExampleModel, wtf.Form, field_args={
#    'example_name': dict(validators=[validators.Required()]),
#    'example_description': dict(validators=[validators.Required()]),
#})
