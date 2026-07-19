from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, SelectField, TextAreaField, DecimalField
from wtforms.validators import DataRequired, Email, EqualTo, NumberRange


class RegisterForm(FlaskForm):
    firstname = StringField("First Name", validators=[DataRequired()])
    lastname = StringField("Last Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(),Email()])
    password1 = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField("Retype password", validators=[DataRequired(),EqualTo("password1")])
    submit = SubmitField("Register user")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(),Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Log in")

class CreateAccountForm(FlaskForm):
    submit = SubmitField("Create Account")

class DepositForm(FlaskForm):
    description = TextAreaField("Description", validators=[DataRequired()])
    amount = DecimalField("Amount", validators=[DataRequired(), NumberRange(min=0.01)], places=2, rounding=None)
    submit = SubmitField("Deposit Funds")

class PaymentForm(FlaskForm):
    description = TextAreaField("Description", validators=[DataRequired()])
    amount = DecimalField("Amount", validators=[DataRequired(), NumberRange(min=0.01)], places=2, rounding=None)
    recipient_type = SelectField("Recipient Type", validators=[DataRequired()], choices=[("internal", "Internal User"), ("external", "External User")])
    internal_recipient = SelectField("Internal Recipient", coerce=int)
    external_recipient = StringField("External Recipient (Name/Details)")
    submit = SubmitField("Make Payment")