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

class TransactionForm(FlaskForm):
    description = TextAreaField("Description", validators=[DataRequired()])
    amount = DecimalField("Amount", validators=[DataRequired(), NumberRange(min=0)], places=2, rounding=None)
    type = SelectField("Transaction Type", validators=[DataRequired()], choices=[("deposit","Deposit"),("transfer","Transfer")])
    submit = SubmitField("Make Transaction")

class DepositForm(FlaskForm):
    amount = DecimalField("Amount", validators=[DataRequired(), NumberRange(min=0.01, message="Amount must be at least 0.01")], places=2, rounding=None)
    description = TextAreaField("Description", validators=[DataRequired()])
    submit = SubmitField("Deposit")

class PaymentForm(FlaskForm):
    recipient_type = SelectField("Recipient Type", choices=[("internal", "Internal User"), ("external", "External User")], validators=[DataRequired()])
    internal_account = SelectField("Select Internal Account", coerce=int, validators=[])
    external_account = StringField("External Account Number / Reference", validators=[])
    amount = DecimalField("Amount", validators=[DataRequired(), NumberRange(min=0.01, message="Amount must be at least 0.01")], places=2, rounding=None)
    description = TextAreaField("Description", validators=[DataRequired()])
    submit = SubmitField("Send Payment")