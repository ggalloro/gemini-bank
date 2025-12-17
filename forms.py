from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, SelectField, TextAreaField, DecimalField
from wtforms.validators import DataRequired, Email, EqualTo, NumberRange, Optional


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
    amount = DecimalField("Amount", validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    description = TextAreaField("Description", validators=[DataRequired()])
    submit = SubmitField("Deposit")

class PaymentForm(FlaskForm):
    amount = DecimalField("Amount", validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    description = TextAreaField("Description", validators=[DataRequired()])
    payment_type = SelectField("Payment Type", choices=[('internal', 'Internal'), ('external', 'External')], default='internal')
    internal_account = SelectField("Recipient Account", coerce=int, validators=[Optional()], validate_choice=False)
    external_account = StringField("External Account Number")
    submit = SubmitField("Make Payment")