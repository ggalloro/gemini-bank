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
    amount = DecimalField("Amount", validators=[DataRequired(), NumberRange(min=0.01, message="Amount must be greater than 0")], places=2, rounding=None)
    submit = SubmitField("Deposit Money")

class PaymentForm(FlaskForm):
    description = TextAreaField("Description", validators=[DataRequired()])
    amount = DecimalField("Amount", validators=[DataRequired(), NumberRange(min=0.01, message="Amount must be greater than 0")], places=2, rounding=None)
    recipient_type = SelectField("Recipient Type", validators=[DataRequired()], choices=[("internal","Internal User"),("external","External User")])
    internal_account = SelectField("Internal Account", coerce=int, validators=[])
    external_account = StringField("External Account Number", validators=[])
    submit = SubmitField("Send Payment")

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        if self.recipient_type.data == 'internal':
            if not self.internal_account.data or self.internal_account.data == 0:
                self.internal_account.errors.append("You must select an internal account.")
                return False
        elif self.recipient_type.data == 'external':
            if not self.external_account.data or not self.external_account.data.strip():
                self.external_account.errors.append("You must provide an external account number.")
                return False
        return True

class TransactionForm(FlaskForm):
    description = TextAreaField("Description", validators=[DataRequired()])
    amount = DecimalField("Amount", validators=[DataRequired(), NumberRange(min=0)], places=2, rounding=None)
    type = SelectField("Transaction Type", validators=[DataRequired()], choices=[("deposit","Deposit"),("transfer","Transfer")])
    submit = SubmitField("Make Transaction")