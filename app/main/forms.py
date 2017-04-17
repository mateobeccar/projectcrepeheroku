from flask_wtf import Form
from wtforms import StringField, TextAreaField, BooleanField, SelectField,\
    SubmitField
from wtforms.validators import Required, Length, Email, Regexp
from wtforms import ValidationError
from flask_pagedown.fields import PageDownField
from ..models import Role, User


class NameForm(Form):
    name = StringField('What is your name?', validators=[Required()])
    submit = SubmitField('Submit')


class EditProfileForm(Form):
    name = StringField('Real name', validators=[Length(0, 64)])
    university = SelectField(
        'University',
        choices=[('',''), ('Yale University', 'Yale University'), ('Harvard University', 'Harvard University'),
        ('Princeton University', 'Princeton University')])
    year = SelectField(
        'Year',
        choices=[('',''), ('Freshman', 'Freshman'), ('Sophomore', 'Sophomore'), ('Junior', 'Junior'), ('Senior', 'Senior')])
    about_me = TextAreaField('Qualifications or link to resume')
    submit = SubmitField('Submit')

class EditCompanyProfileForm(Form):
    name = StringField('Company Name', validators=[Length(0, 64)])
    industry = StringField('Industry', validators=[Length(0, 64)])
    website = StringField('Website', validators=[Length(0, 64)])
    about_me = TextAreaField('Company Description')
    submit = SubmitField('Submit')


class EditProfileAdminForm(Form):
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    username = StringField('Username', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          'Usernames must have only letters, '
                                          'numbers, dots or underscores')])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class PostForm(Form):
    title = StringField("Title", validators=[Required()])
    body = PageDownField("Job", validators=[Required()])
    university = SelectField(
        'University',
        choices=[('',''), ('Yale University', 'Yale University'), ('Harvard University', 'Harvard University'),
        ('Princeton University', 'Princeton University')])
    submit = SubmitField('Publish')

class ApplicantForm(Form):
    why = TextAreaField("The company will receive your profile. Is there any further information about yourself you'd like them to know to be considered for this job?")
    submit = SubmitField('Apply')

class CommentForm(Form):
    body = StringField('Enter your message', validators=[Required()])
    submit = SubmitField('Send')
