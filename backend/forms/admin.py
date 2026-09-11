from flask_wtf import FlaskForm
from wtforms import (FloatField, IntegerField, SelectField, StringField, SubmitField, TextAreaField)
from wtforms.validators import DataRequired, Length, Optional

class ProductForm(FlaskForm):
    """Form for adding/editing products"""
    name = StringField('Product Name', validators=[DataRequired(), Length(max=100)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    cost_price = FloatField('Cost Price', validators=[DataRequired()])
    selling_price = FloatField('Selling Price', validators=[DataRequired()])
    stock_quantity = IntegerField('Stock Quantity', validators=[DataRequired()])
    minimum_stock_alert = IntegerField('Minimum Stock Alert', default=10, validators=[DataRequired()])
    supplier_name = StringField('Supplier Name', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Save Product')

class SupplierForm(FlaskForm):
    """Form for adding/editing suppliers"""
    name = StringField('Supplier Name', validators=[DataRequired(), Length(max=100)])
    contact_person = StringField('Contact Person', validators=[Optional(), Length(max=100)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    email = StringField('Email', validators=[Optional(), Length(max=120)])
    address = TextAreaField('Address', validators=[Optional()])
    submit = SubmitField('Save Supplier')

class PurchaseForm(FlaskForm):
    """Form for adding new stock purchases"""
    supplier_id = SelectField('Supplier', coerce=int, validators=[DataRequired()])
    product_id = SelectField('Product', coerce=int, validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    purchase_price = FloatField('Purchase Price (per unit)', validators=[DataRequired()])
    submit = SubmitField('Record Purchase')

class CategoryForm(FlaskForm):
    """Form for adding/editing categories"""
    name = StringField('Category Name', validators=[DataRequired(), Length(max=50)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Save Category')
