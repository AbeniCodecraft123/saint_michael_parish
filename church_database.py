# database for prayer request
# database for sermon
# database for announcement
# database for tithe
# database for offering
# database for other fees
# database for member registration
# database for youth department
# database for gallery

from datetime import datetime
from database_running import db
from wtforms import (StringField, PasswordField, SubmitField, FileField, TextAreaField,
                     TimeField, SelectField, DateField,
                     BooleanField, IntegerField,HiddenField, DecimalField)
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange


class Prayer_Request(db.Model):
    __tablename__ = 'prayer_request'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    email = db.Column(db.String)
    prayer = db.Column(db.String)

    def __init__(self, name, email, prayer):
        self.name = name
        self.email = email
        self.prayer = prayer

    def __repr__(self):
        return '<Prayer %r>' % self.name

    def __obj_to_dict(self):
        return {'id': self.id, 'name': self.name, 'email': self.email, 'prayer': self.prayer}


class PrayerForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    prayer = TextAreaField('Prayer', validators=[DataRequired()])
    submit = SubmitField('Submit')

class Sermon(db.Model):
    __tablename__ = 'sermon'
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String)
    video = db.Column(db.String)
    day = db.Column(db.String)
    duration = db.Column(db.String)
    date = db.Column(
        db.DateTime,
        default=datetime.utcnow)

    def __init__(self, topic, video, day, duration):
        self.topic = topic
        self.video = video
        self.day = day
        self.duration = duration

    def __obj_to_dict(self):
        return{
            'id': self.id,
            'topic': self.topic,
            'video': self.video,
            'day': self.day,
            'duration': self.duration
        }


class SermonForm(FlaskForm):
    topic = StringField(
        "Topic",
        validators=[DataRequired()]
    )

    video = FileField(
        "Sermon Video",
        validators=[
            DataRequired(),
            FileAllowed(
                ["mp4", "mov", "avi", "mkv"],
                "Only video files are allowed."
            )
        ]
    )

    day = StringField(
        "Day",
        validators=[DataRequired()]
    )

    duration = StringField(
        "Duration",
        validators=[DataRequired()]
    )

    post = SubmitField("Upload Sermon")


class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)
    announcement = db.Column(db.String)

    def __init__(self, timestamp, announcement):
        self.timestamp = timestamp
        self.announcement = announcement


    def __obj_to_dict(self):
        return{
            'id': self.id,
            'timestamp': self.timestamp,
            'announcement': self.announcement
        }

class AnnouncementForm(FlaskForm):
    timestamp = TimeField('Timestamp', validators=[DataRequired()])
    announcement = TextAreaField('Announcement', validators=[DataRequired()])
    post = SubmitField('Post')





class NewMember(db.Model):
    __tablename__ = "new_members"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    other_name = db.Column(db.String(50))
    gender = db.Column(db.String(10), nullable=False)
    date_of_birth = db.Column(db.Date)
    marital_status = db.Column(db.String(20))
    phone = db.Column(db.String(15), unique=False, nullable=False)
    alternate_phone = db.Column(db.String(15))
    email = db.Column(db.String(100), unique=False)
    address = db.Column(db.String(250), nullable=False)
    occupation = db.Column(db.String(100))
    place_of_work = db.Column(db.String(150))
    invited_by = db.Column(db.String(100))
    first_time_visit = db.Column(db.Boolean, default=True)
    born_again = db.Column(db.Boolean, default=False)
    baptized = db.Column(db.Boolean, default=False)
    prayer_request = db.Column(db.Text)
    department_of_interest = db.Column(db.String(100))
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(15))
    registration_date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __init__(
        self,
        first_name,
        last_name,
        other_name,
        gender,
        date_of_birth,
        marital_status,
        phone,
        alternate_phone,
        email,
        address,
        occupation,
        place_of_work,
        invited_by,
        first_time_visit,
        born_again,
        baptized,
        prayer_request,
        department_of_interest,
        emergency_contact_name,
        emergency_contact_phone
    ):
        self.first_name = first_name
        self.last_name = last_name
        self.other_name = other_name
        self.gender = gender
        self.date_of_birth = date_of_birth
        self.marital_status = marital_status
        self.phone = phone
        self.alternate_phone = alternate_phone
        self.email = email
        self.address = address
        self.occupation = occupation
        self.place_of_work = place_of_work
        self.invited_by = invited_by
        self.first_time_visit = first_time_visit
        self.born_again = born_again
        self.baptized = baptized
        self.prayer_request = prayer_request
        self.department_of_interest = department_of_interest
        self.emergency_contact_name = emergency_contact_name
        self.emergency_contact_phone = emergency_contact_phone

    def __repr__(self):
        return f"<NewMember {self.first_name} {self.last_name}>"

    def obj_to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "other_name": self.other_name,
            "gender": self.gender,
            "date_of_birth": self.date_of_birth.strftime("%Y-%m-%d") if self.date_of_birth else None,
            "marital_status": self.marital_status,
            "phone": self.phone,
            "alternate_phone": self.alternate_phone,
            "email": self.email,
            "address": self.address,
            "occupation": self.occupation,
            "place_of_work": self.place_of_work,
            "invited_by": self.invited_by,
            "first_time_visit": self.first_time_visit,
            "born_again": self.born_again,
            "baptized": self.baptized,
            "prayer_request": self.prayer_request,
            "department_of_interest": self.department_of_interest,
            "emergency_contact_name": self.emergency_contact_name,
            "emergency_contact_phone": self.emergency_contact_phone,
            "registration_date": self.registration_date.strftime("%Y-%m-%d %H:%M:%S")
            if self.registration_date else None
        }



class NewMemberForm(FlaskForm):

    first_name = StringField(
        "First Name",
        validators=[DataRequired(), Length(max=50)]
    )

    last_name = StringField(
        "Last Name",
        validators=[DataRequired(), Length(max=50)]
    )

    other_name = StringField(
        "Other Name",
        validators=[Optional(), Length(max=50)]
    )

    gender = SelectField(
        "Gender",
        choices=[
            ("Male", "Male"),
            ("Female", "Female")
        ],
        validators=[DataRequired()]
    )

    date_of_birth = DateField(
        "Date of Birth",
        format="%Y-%m-%d",
        validators=[Optional()]
    )

    marital_status = SelectField(
        "Marital Status",
        choices=[
            ("Single", "Single"),
            ("Married", "Married"),
            ("Divorced", "Divorced"),
            ("Widowed", "Widowed")
        ],
        validators=[Optional()]
    )

    phone = StringField(
        "Phone Number",
        validators=[DataRequired(), Length(min=11, max=15)]
    )

    alternate_phone = StringField(
        "Alternate Phone",
        validators=[Optional(), Length(max=15)]
    )

    email = StringField(
        "Email Address",
        validators=[Optional(), Email()]
    )

    address = TextAreaField(
        "Residential Address",
        validators=[DataRequired()]
    )

    occupation = StringField(
        "Occupation",
        validators=[Optional()]
    )

    place_of_work = StringField(
        "Place of Work",
        validators=[Optional()]
    )

    invited_by = StringField(
        "Invited By",
        validators=[Optional()]
    )

    first_time_visit = BooleanField(
        "Is this your first time worshipping with us?"
    )

    born_again = BooleanField(
        "Are you Born Again?"
    )

    baptized = BooleanField(
        "Have you been Baptized?"
    )

    prayer_request = TextAreaField(
        "Prayer Request",
        validators=[Optional()]
    )

    department_of_interest = SelectField(
        "Department Interested In",
        choices=[
            ("", "-- Select Department --"),
            ("Choir", "Choir"),
            ("Ushering", "Ushering"),
            ("Media", "Media"),
            ("Drama", "Drama"),
            ("Protocol", "Protocol"),
            ("Children", "Children"),
            ("Evangelism", "Evangelism"),
            ("Prayer", "Prayer"),
            ("Sanctuary", "Sanctuary")
        ],
        validators=[Optional()]
    )

    emergency_contact_name = StringField(
        "Emergency Contact Name",
        validators=[Optional()]
    )

    emergency_contact_phone = StringField(
        "Emergency Contact Phone",
        validators=[Optional()]
    )

    submit = SubmitField("Register New Member")


class Youth(db.Model):
    __tablename__ = "youths"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    other_name = db.Column(db.String(50), nullable=True)
    gender = db.Column(db.String(10), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    address = db.Column(db.String(200), nullable=False)
    occupation = db.Column(db.String(100), nullable=True)
    school = db.Column(db.String(150), nullable=True)
    marital_status = db.Column(db.String(20), nullable=False)
    department = db.Column(db.String(100), nullable=True)
    emergency_contact_name = db.Column(db.String(100), nullable=True)
    emergency_contact_phone = db.Column(db.String(15), nullable=True)
    date_registered = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(
        self,
        first_name,
        last_name,
        other_name,
        gender,
        date_of_birth,
        age,
        phone,
        email,
        address,
        occupation,
        school,
        marital_status,
        department,
        emergency_contact_name,
        emergency_contact_phone
    ):
        self.first_name = first_name
        self.last_name = last_name
        self.other_name = other_name
        self.gender = gender
        self.date_of_birth = date_of_birth
        self.age = age
        self.phone = phone
        self.email = email
        self.address = address
        self.occupation = occupation
        self.school = school
        self.marital_status = marital_status
        self.department = department
        self.emergency_contact_name = emergency_contact_name
        self.emergency_contact_phone = emergency_contact_phone

    def __repr__(self):
        return f"<Youth {self.first_name} {self.last_name}>"

    def obj_to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "other_name": self.other_name,
            "gender": self.gender,
            "date_of_birth": self.date_of_birth.strftime("%Y-%m-%d") if self.date_of_birth else None,
            "age": self.age,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "occupation": self.occupation,
            "school": self.school,
            "marital_status": self.marital_status,
            "department": self.department,
            "emergency_contact_name": self.emergency_contact_name,
            "emergency_contact_phone": self.emergency_contact_phone,
            "date_registered": self.date_registered.strftime("%Y-%m-%d %H:%M:%S")
            if self.date_registered else None
        }


class YouthForm(FlaskForm):

    first_name = StringField(
        "First Name",
        validators=[DataRequired(), Length(max=50)]
    )

    last_name = StringField(
        "Last Name",
        validators=[DataRequired(), Length(max=50)]
    )

    other_name = StringField(
        "Other Name",
        validators=[Optional(), Length(max=50)]
    )

    gender = SelectField(
        "Gender",
        choices=[
            ("Male", "Male"),
            ("Female", "Female")
        ],
        validators=[DataRequired()]
    )

    date_of_birth = DateField(
        "Date of Birth",
        format="%Y-%m-%d",
        validators=[DataRequired()]
    )

    age = IntegerField(
        "Age",
        validators=[
            DataRequired(),
            NumberRange(min=12, max=40)
        ]
    )

    phone = StringField(
        "Phone Number",
        validators=[
            DataRequired(),
            Length(min=11, max=15)
        ]
    )

    email = StringField(
        "Email Address",
        validators=[
            Optional(),
            Email()
        ]
    )

    address = TextAreaField(
        "Residential Address",
        validators=[DataRequired()]
    )

    occupation = StringField(
        "Occupation",
        validators=[Optional()]
    )

    school = StringField(
        "School / Institution",
        validators=[Optional()]
    )

    marital_status = SelectField(
        "Marital Status",
        choices=[
            ("Single", "Single"),
            ("Married", "Married")
        ],
        validators=[DataRequired()]
    )

    department = SelectField(
        "Church Department",
        choices=[
            ("", "-- Select Department --"),
            ("Choir", "Choir"),
            ("Drama", "Drama"),
            ("Ushering", "Ushering"),
            ("Media", "Media"),
            ("Protocol", "Protocol"),
            ("Prayer", "Prayer Unit"),
            ("Evangelism", "Evangelism"),
            ("Sanctuary", "Sanctuary"),
            ("Technical", "Technical"),
            ("None", "Not Yet")
        ],
        validators=[Optional()]
    )

    emergency_contact_name = StringField(
        "Emergency Contact Name",
        validators=[Optional()]
    )

    emergency_contact_phone = StringField(
        "Emergency Contact Phone",
        validators=[
            Optional(),
            Length(max=15)
        ]
    )

    submit = SubmitField("Register Youth")


class Gallery(db.Model):
    __tablename__ = "gallery"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    image = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime,default=datetime.utcnow)

    def __init__(self, title, image):
        self.title = title
        self.image = image

    def __repr__(self):
        return f"<Gallery {self.title}>"

    def obj_to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "image": self.image,
            "upload_date": self.upload_date.strftime("%Y-%m-%d %H:%M:%S")
            if self.upload_date else None
        }

class GalleryForm(FlaskForm):
    title = StringField(
        "Title",
        validators=[
            DataRequired(),
            Length(max=150)
        ]
    )

    image = FileField(
        "Image",
        validators=[
            FileRequired(),
            FileAllowed(
                ["jpg", "jpeg", "png", "webp"],
                "Images only!"
            )
        ]
    )

    submit = SubmitField("Upload Image")



import uuid

class Donation(db.Model):
    __tablename__ = "donations"

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(64), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)

    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20), nullable=True)

    donation_type = db.Column(db.String(30), nullable=False)  # 'tithe', 'offering', 'harvest', 'building_fund', etc.
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(3), default="NGN")

    status = db.Column(db.String(20), default="pending")  # pending, successful, failed, cancelled
    opay_order_no = db.Column(db.String(100), nullable=True)   # OPay's orderNo from their response
    opay_transaction_id = db.Column(db.String(100), nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)
    payment_response = db.Column( db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return (f"<Donation {self.reference} "
                f"{self.amount} "
                f"{self.status}>")



class DonationForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=150)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Phone", validators=[Length(max=20)])
    donation_type = SelectField(
        "Donation Type",
        choices=[
            ("offering", "Offering"),
            ("tithe", "Tithe"),
            ("harvest", "Harvest"),
            ("building_fund", "Building Fund"),
            ("other", "Other"),
        ],
        validators=[DataRequired()],
    )
    amount = DecimalField("Amount", validators=[DataRequired(), NumberRange(min=100, message="Minimum amount is ₦100")])



class ContactMessage(db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date_sent = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, full_name, phone_number, email, message):
        self.full_name = full_name
        self.phone_number = phone_number
        self.email = email
        self.message = message

    def __repr__(self):
        return f"<ContactMessage {self.full_name}>"

    def obj_to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "phone_number": self.phone_number,
            "email": self.email,
            "message": self.message,
            "date_sent": self.date_sent.strftime("%Y-%m-%d %H:%M:%S")
        }
