import os
import uuid

from dotenv import load_dotenv
from werkzeug.utils import secure_filename

load_dotenv()
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from church_database import (db, PrayerForm, Prayer_Request, NewMember, NewMemberForm, Announcement, Gallery,
                             Sermon, SermonForm, DonationForm, Donation, AnnouncementForm, GalleryForm )
from decimal import Decimal
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config["SECRET_KEY"] = os.getenv('APP_SECRET_KEY')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECURITY_PASSWORD_SALT'] = os.environ.get('SECURITY_PASSWORD_SALT')
app.config["UPLOAD_FOLDER"] = os.path.join(
    app.root_path,
    "static",
    "uploads"
)

app.config["GALLERY_FOLDER"] = os.path.join(
    app.root_path,
    "static",
    "uploads",
    "gallery"
)

app.config["SERMON_FOLDER"] = os.path.join(
    app.root_path,
    "static",
    "uploads",
    "sermons"
)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024   # 500MB

os.makedirs(app.config["GALLERY_FOLDER"], exist_ok=True)
os.makedirs(app.config["SERMON_FOLDER"], exist_ok=True)

db.init_app(app)
CSRFProtect(app)



@app.route('/', methods=['GET', 'POST'])
def index():
    form = NewMemberForm()
    if form.validate_on_submit():
        church_member = NewMember(
            first_name= form.first_name.data,
            last_name= form.last_name.data,
            other_name= form.other_name.data,
            gender= form.gender.data,
            date_of_birth= form.date_of_birth.data,
            marital_status= form.marital_status.data,
            phone= form.phone.data,
            alternate_phone= form.alternate_phone.data,
            email= form.email.data,
            address= form.address.data,
            occupation= form.occupation.data,
            place_of_work= form.place_of_work.data,
            invited_by= form.invited_by.data,
            first_time_visit=form.first_time_visit.data,
            born_again=form.born_again.data,
            baptized = form.baptized.data,
            prayer_request=form.prayer_request.data,
            department_of_interest=form.department_of_interest.data,
            emergency_contact_name=form.emergency_contact_name.data,
            emergency_contact_phone=form.emergency_contact_phone.data,
        )
        db.session.add(church_member)
        db.session.commit()
        flash(
            "Registration successful! Welcome to the Saint Michael Parish family. We are delighted to have you worship with us.",
            "success"
        )
        return redirect(url_for("index"))
    return render_template('index.html', form=form)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = PrayerForm()
    if form.validate_on_submit():
        prayers = Prayer_Request(
            name=form.name.data,
            email=form.email.data,
            prayer=form.prayer.data
        )
        db.session.add(prayers)
        db.session.commit()
        flash(
            'Your prayer request has been forwarded to the shepherd, we pray that the Lord Almighty will accept all your prayer')
    return render_template('contact.html', form=form)

@app.route('/gallery')
def gallery():
    galleries = Gallery.query.all()
    return render_template('gallery.html', galleries=galleries )

@app.route('/announcements')
def announcements():
    announce = Announcement.query.all()
    return render_template('announcements.html', announce=announce)

@app.route('/sermons')
def sermons():
    sermon= Sermon.query.all()
    return render_template('sermons.html', sermon=sermon)

@app.route('/worship')
def worship():
    return render_template('worship.html')


@app.route('/give_offering')
def give_offering():
    return render_template('give-offering.html')

@app.route('/give_other')
def give_other():
    return render_template('give-other.html')

@app.route('/give_tithe')
def give_tithe():
    return render_template('give-tithe.html')

@app.route('/prayer_request', methods=['GET', 'POST'])
def prayer_request():
    form = PrayerForm()
    if form.validate_on_submit():
        prayers = Prayer_Request(
            name= form.name.data,
            email= form.email.data,
            prayer= form.prayer.data
        )
        db.session.add(prayers)
        db.session.commit()
        flash('Your prayer request has been forwarded to the shepherd, we pray that the Lord Almighty will accept all your prayer')
    return render_template('prayer_request_form.html', form=form)



@app.route("/give", methods=["GET", "POST"])
def give():
    form = DonationForm()

    if form.validate_on_submit():

        donation = Donation(
            full_name=form.full_name.data,
            email=form.email.data,
            phone=form.phone.data,
            donation_type=form.donation_type.data,
            amount=Decimal(form.amount.data),
            status="pending"
        )

        db.session.add(donation)
        db.session.commit()
        db.session.add(donation)
        db.session.commit()

        flash(
            "Thank you for your generosity. OPay checkout is currently unavailable for testing. Please check back later.",
            "info")

        return redirect(url_for("give"))
    return render_template(
        "give.html",
        title="Give",
        form=form
    )

@app.route("/donation/<reference>")
def donation_summary(reference):

    donation = Donation.query.filter_by(
        reference=reference
    ).first_or_404()

    return render_template(
        "donation_summary.html",
        donation=donation
    )

@app.route("/donation/success")
def donation_success():
    return render_template("donation_success.html")

@app.route('/admin_dashboard', methods=["GET", "POST"])
def admin_dashboard():
    return render_template("admin_dashboard.html")

@app.route('/announcements_form', methods=["GET", "POST"])
def announcements_form():
    form= AnnouncementForm()
    if form.validate_on_submit():
        announcement = Announcement(
            timestamp=form.timestamp.data,
            announcement=form.announcement.data,
        )
        db.session.add(announcement)
        db.session.commit()
    return render_template("admin/announcements_form.html", form=form)


@app.route('/gallery_form', methods=["GET", "POST"])
def gallery_form():
    form = GalleryForm()
    if form.validate_on_submit():
        image = form.image.data
        filename = secure_filename(image.filename)
        filename = f"{uuid.uuid4().hex}_{filename}"
        image.save(
            os.path.join(app.config["UPLOAD_FOLDER"], filename)
        )
        gallery = Gallery(
            title=form.title.data,
            image=filename
        )
        db.session.add(gallery)
        db.session.commit()
        flash("Gallery image uploaded successfully.", "success")
        return redirect(url_for("gallery_form"))
    return render_template(
        "admin/gallery_form.html", form=form)



@app.route("/sermon_form", methods=["GET", "POST"])
def sermon_form():
    form = SermonForm()

    if form.validate_on_submit():

        video = form.video.data

        filename = secure_filename(video.filename)
        filename = f"{uuid.uuid4().hex}_{filename}"

        video.save(
            os.path.join(
                app.config["SERMON_FOLDER"],
                filename
            )
        )

        sermon = Sermon(
            topic=form.topic.data,
            video=filename,
            day=form.day.data,
            duration=form.duration.data
        )

        db.session.add(sermon)
        db.session.commit()

        flash("Sermon uploaded successfully.", "success")

        return redirect(url_for("sermon_form"))

    return render_template(
        "sermon_form.html",
        form=form
    )


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')