import os
import uuid
import hmac
import json
import hashlib
import requests
from functools import wraps
from flask import session, jsonify
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from datetime import datetime
load_dotenv()
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from church_database import (db, PrayerForm, Prayer_Request, NewMember, NewMemberForm, Announcement, Gallery,
                             Sermon, SermonForm, DonationForm, Donation, AnnouncementForm,
                             GalleryForm, Youth, YouthForm , ActivityLog,ResourceForm, Resource)
from decimal import Decimal
from flask_dance.contrib.google import make_google_blueprint, google
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
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
db.init_app(app)
csrf = CSRFProtect(app)
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logging.getLogger().addHandler(console_handler)

def try_parse_date(value):
    for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%B %d, %Y', '%b %d, %Y', '%B %Y', '%b %Y'):
        try:
            return datetime.strptime(value.strip(), fmt)
        except (ValueError, AttributeError):
            continue
    return None





if app.debug:
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

google_bp = make_google_blueprint(
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ],
    redirect_to="admin_google_callback",
)
app.register_blueprint(google_bp, url_prefix="/login")

ADMIN_EMAILS = [e.strip().lower() for e in os.getenv('ADMIN_EMAILS', '').split(',') if e.strip()]

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin_email'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return wrapper

@app.route('/admin/login')
def admin_login():
    if session.get('admin_email'):
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/admin_login.html')


@app.route('/admin/google/callback')
def admin_google_callback():

    if not google.authorized:
        flash("Google authentication failed.", "danger")
        return redirect(url_for('admin_login'))

    response = google.get("/oauth2/v2/userinfo")

    if not response.ok:
        flash("Could not retrieve your Google account information.", "danger")
        return redirect(url_for('admin_login'))

    userinfo = response.json()

    email = (userinfo.get("email") or "").lower()

    if email not in ADMIN_EMAILS:
        flash(
            "This Google account isn't authorized for admin access.",
            "danger"
        )
        return redirect(url_for('admin_login'))

    session["admin_email"] = email
    session["admin_name"] = userinfo.get("name")
    session["admin_picture"] = userinfo.get("picture")

    ActivityLog.log(
        f'Admin login: {userinfo.get("name")}'
    )

    return redirect(url_for("admin_dashboard"))


@app.route('/admin/logout')
def admin_logout():
    if session.get('admin_name'):
        ActivityLog.log(f'Admin logout: {session.get("admin_name")}')
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/', methods=['GET', 'POST'])
def index():
    form = NewMemberForm()
    if form.validate_on_submit():
        church_member = NewMember(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            other_name=form.other_name.data,
            gender=form.gender.data,
            date_of_birth=form.date_of_birth.data,
            marital_status=form.marital_status.data,
            phone=form.phone.data,
            alternate_phone=form.alternate_phone.data,
            email=form.email.data,
            address=form.address.data,
            occupation=form.occupation.data,
            place_of_work=form.place_of_work.data,
            invited_by=form.invited_by.data,
            first_time_visit=form.first_time_visit.data,
            born_again=form.born_again.data,
            baptized=form.baptized.data,
            prayer_request=form.prayer_request.data,
            department_of_interest=form.department_of_interest.data,
            emergency_contact_name=form.emergency_contact_name.data,
            emergency_contact_phone=form.emergency_contact_phone.data,
        )
        db.session.add(church_member)
        db.session.commit()
        ActivityLog.log(f'New member registered: {form.first_name.data} {form.last_name.data}')
        flash(
            "Registration successful! Welcome to the Saint Michael Parish family. We are delighted to have you worship with us.",
            "success"
        )
        return redirect(url_for("index"))

    gallery_items = Gallery.query.order_by(Gallery.upload_date.desc()).limit(6).all()
    gallery_total = Gallery.query.count()
    recent_sermons = Sermon.query.order_by(Sermon.date.desc()).limit(4).all()
    sermon_total = Sermon.query.count()
    recent_announcements = Announcement.query.order_by(Announcement.timestamp.desc()).limit(3).all()
    announcement_total = Announcement.query.count()
    return render_template(
        'index.html', form=form,
        gallery_items=gallery_items, gallery_total=gallery_total,
        recent_sermons=recent_sermons, sermon_total=sermon_total,
        recent_announcements=recent_announcements, announcement_total=announcement_total
    )

# Maps search keywords to (endpoint, anchor) — the actual page + section
# where that content lives. Add entries as you add content to new pages.
SITE_SEARCH_INDEX = [
    # --- About page sections ---
    {"endpoint": "about", "anchor": "founder", "keywords": [
        "shepherd", "michael olusegun olufowora", "olufowora",
        "most superior evangelist", "founder of the parish",
    ]},
    {"endpoint": "about", "anchor": "wife", "keywords": [
        "shepherd's wife", "monsurat", "abolanle", "prophetess monsurat",
    ]},
    {"endpoint": "about", "anchor": "patriarchs", "keywords": [
        "patriarch", "oshoffa", "bada", "ajose", "ajanlekoko",
        "jesse", "maforikan", "omoge", "heroes of the past",
    ]},
    {"endpoint": "about", "anchor": "current-heroes", "keywords": [
        "rev lawal", "victor lawal", "david abiodun olufowora", "current heroes",
    ]},
    {"endpoint": "about", "anchor": "church", "keywords": [
        "the church", "ccc saint michael parish", "vision statement",
        "mission statement", "tosho village",
    ]},
    {"endpoint": "about", "anchor": "core-values", "keywords": [
        "core values", "holiness", "faith in jesus christ",
        "evangelism", "discipline and orderliness", "love and unity",
    ]},
    {"endpoint": "about", "anchor": "church-tenets", "keywords": [
        "tenets", "sutana", "dietary restrictions", "intoxicants",
        "smoking", "dress and appearance", "purity",
    ]},
    {"endpoint": "about", "anchor": "departments", "keywords": [
        "organogram", "departments", "board", "elders", "clergies",
        "choir", "finance", "youth department", "women affairs",
    ]},
    {"endpoint": "about", "anchor": "sacraments", "keywords": [
        "sacraments", "baptism", "marriage", "child christening",
        "mode of worship", "rank and promotion", "funeral", "burial",
    ]},
    {"endpoint": "about", "anchor": "governance", "keywords": [
        "governance", "constitution", "foundational blueprint",
        "financial governance", "financial control", "classification of expenses",
    ]},
    {"endpoint": "about", "anchor": "disciplinary", "keywords": [
        "disciplinary", "discipline", "acts of indiscipline",
        "disciplinary measures", "disciplinary procedures",
    ]},
    {"endpoint": "about", "anchor": "church-use-requirements", "keywords": [
        "sanctuary", "requirements for the use of the church", "dress code", "ikilo",
    ]},

    {"endpoint": "worship", "anchor": None, "keywords": [
        "worship", "service times", "sunday service", "when do you meet",
    ]},
    {"endpoint": "contact", "anchor": None, "keywords": [
        "contact", "phone number", "whatsapp", "email", "parish address", "location",
    ]},
    {"endpoint": "give", "anchor": None, "keywords": [
        "give", "giving", "donate", "tithe", "offering", "harvest",
    ]},
]


def find_page_match(query):
    q = query.lower().strip()
    if not q:
        return None
    for entry in SITE_SEARCH_INDEX:
        for kw in entry["keywords"]:
            if kw in q or q in kw:
                return entry["endpoint"], entry["anchor"]
    return None


@app.route('/search')
def search():
    q = request.args.get('q', '').strip()
    if not q:
        return redirect(url_for('index'))

    parsed = try_parse_date(q)
    like = f'%{q}%'

    page_match = None

    if parsed:
        sermon_match = Sermon.query.filter(db.func.date(Sermon.date) == parsed.date()).first()
        gallery_match = Gallery.query.filter(db.func.date(Gallery.event_date) == parsed.date()).first()
        announcement_match = Announcement.query.filter(db.func.date(Announcement.timestamp) == parsed.date()).first()
    else:
        sermon_match = Sermon.query.filter(db.or_(Sermon.topic.ilike(like), Sermon.day.ilike(like))).first()
        gallery_match = Gallery.query.filter(db.or_(Gallery.title.ilike(like), Gallery.category.ilike(like))).first()
        announcement_match = Announcement.query.filter(Announcement.announcement.ilike(like)).first()
        page_match = find_page_match(q)

    # Priority: sermons, then gallery, then announcements, then static pages
    if sermon_match:
        return redirect(url_for('sermons', q=q))
    if gallery_match:
        return redirect(url_for('gallery', q=q))
    if announcement_match:
        return redirect(url_for('announcements', q=q))
    if page_match:
        endpoint, anchor = page_match
        target = url_for(endpoint)
        return redirect(f"{target}#{anchor}" if anchor else target)

    return redirect(url_for('sermons', q=q))


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
    q = request.args.get('q', '').strip()
    query = Gallery.query
    if q:
        parsed = try_parse_date(q)
        if parsed:
            query = query.filter(db.func.date(Gallery.event_date) == parsed.date())
        else:
            like = f'%{q}%'
            query = query.filter(db.or_(Gallery.title.ilike(like), Gallery.category.ilike(like)))
    galleries = query.order_by(Gallery.upload_date.desc()).all()
    return render_template('gallery.html', galleries=galleries, search_query=q)


@app.route('/sermons')
def sermons():
    q = request.args.get('q', '').strip()
    query = Sermon.query
    if q:
        parsed = try_parse_date(q)
        if parsed:
            query = query.filter(db.func.date(Sermon.date) == parsed.date())
        else:
            like = f'%{q}%'
            query = query.filter(db.or_(Sermon.topic.ilike(like), Sermon.day.ilike(like)))
    sermon = query.order_by(Sermon.date.desc()).all()
    return render_template('sermons.html', sermon=sermon, search_query=q)


@app.route('/announcements')
def announcements():
    q = request.args.get('q', '').strip()
    query = Announcement.query
    if q:
        parsed = try_parse_date(q)
        if parsed:
            query = query.filter(db.func.date(Announcement.timestamp) == parsed.date())
        else:
            query = query.filter(Announcement.announcement.ilike(f'%{q}%'))
    announce = query.order_by(Announcement.timestamp.desc()).all()
    return render_template('announcements.html', announce=announce, search_query=q)

@app.route('/worship')
def worship():
    return render_template('worship.html')




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
        ActivityLog.log(f'New prayer request submitted by {form.name.data}')
        flash(
            'Your prayer request has been forwarded to the shepherd, we pray that the Lord Almighty will accept all your prayer')
    return render_template('prayer_request_form.html', form=form)



OPAY_CASHIER_URL = "https://testapi.opaycheckout.com/api/v1/international/cashier/create"


def verify_opay_callback_signature(payload_dict, received_sha512):
    """Verify an incoming OPay callback really came from OPay."""
    secret_key = os.getenv("OPAY_SECRET_KEY")  # your Secret/Private key
    payload_string = json.dumps(payload_dict, separators=(",", ":"), ensure_ascii=False)
    expected = hmac.new(
        secret_key.encode("utf-8"),
        payload_string.encode("utf-8"),
        hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(expected, received_sha512 or "")


"""@app.route("/give", methods=["GET", "POST"])
def give():
    form = DonationForm()

    if form.validate_on_submit():
        amount = Decimal(form.amount.data)
        reference = f"DON-{uuid.uuid4().hex[:20].upper()}"

        donation = Donation(
            full_name=form.full_name.data,
            email=form.email.data,
            phone=form.phone.data,
            donation_type=form.donation_type.data,
            amount=amount,
            status="pending",
            reference=reference,
        )
        db.session.add(donation)
        db.session.commit()

        payload = {
            "country": "NG",
            "reference": reference,
            "amount": {
                "total": int(amount * 100),   # naira -> kobo
                "currency": "NGN"
            },
            "returnUrl": url_for("donation_summary", reference=reference, _external=True),
            "callbackUrl": url_for("opay_callback", _external=True),
            "cancelUrl": url_for("give", _external=True),
            "expireAt": 30,
            "userInfo": {
                "userEmail": form.email.data,
                "userMobile": form.phone.data,
                "userName": form.full_name.data,
            },
            "product": {
                "name": "Church Donation",
                "description": f"Church donation - {form.donation_type.data}",
            },
        }

        try:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {os.getenv('OPAY_PUBLIC_KEY')}",
                "MerchantId": os.getenv("OPAY_MERCHANT_ID"),
            }

            response = requests.post(OPAY_CASHIER_URL, headers=headers, json=payload, timeout=30)
            result = response.json()
            print("OPAY RESPONSE:", json.dumps(result, ensure_ascii=True))

            if response.status_code != 200 or result.get("code") != "00000":
                flash(result.get("message", "Unable to initialize OPay payment."), "error")
                return redirect(url_for("give"))

            data = result.get("data", {})
            checkout_url = data.get("cashierUrl")
            if not checkout_url:
                flash("OPay did not return a checkout URL.", "error")
                return redirect(url_for("give"))

            donation.opay_order_no = data.get("orderNo")
            db.session.commit()

            ActivityLog.log(f"Giving initiated — ₦{amount} ({form.donation_type.data})")
            return redirect(checkout_url)

        except requests.RequestException as e:
            print("OPay request error:", e)
            flash("Unable to connect to OPay. Please try again.", "error")
            return redirect(url_for("give"))

    return render_template("give.html", title="Give", form=form)

@csrf.exempt
@app.route("/opay/callback", methods=["POST"])
def opay_callback():
    data = request.get_json()
    payload = data.get("payload", {})
    received_sig = data.get("sha512")

    if not verify_opay_callback_signature(payload, received_sig):
        print("OPay callback: signature mismatch — rejecting")
        return jsonify({"status": "invalid signature"}), 400

    reference = payload.get("reference")
    donation = Donation.query.filter_by(reference=reference).first()

    if not donation:
        return jsonify({"status": "error"}), 404

    if payload.get("status") == "SUCCESS":
        donation.status = "successful"
        donation.opay_transaction_id = payload.get("transactionId")
        donation.payment_method = payload.get("instrumentType")
        donation.payment_response = data
        db.session.commit()

    return jsonify({"status": "success"}), 200
"""

import base64

MONNIFY_BASE_URL = os.getenv("MONNIFY_BASE_URL", "https://sandbox.monnify.com")
MONNIFY_API_KEY = os.getenv("MONNIFY_API_KEY")
MONNIFY_SECRET_KEY = os.getenv("MONNIFY_SECRET_KEY")
MONNIFY_CONTRACT_CODE = os.getenv("MONNIFY_CONTRACT_CODE")


def get_monnify_token():
    """Authenticate with Monnify and return a Bearer access token (valid 1 hour)."""
    credentials = f"{MONNIFY_API_KEY}:{MONNIFY_SECRET_KEY}"
    encoded = base64.b64encode(credentials.encode()).decode()
    resp = requests.post(
        f"{MONNIFY_BASE_URL}/api/v1/auth/login",
        headers={"Authorization": f"Basic {encoded}"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["responseBody"]["accessToken"]


def verify_monnify_webhook_signature(raw_body, received_signature):
    """Verify an incoming Monnify webhook really came from Monnify."""
    expected = hmac.new(
        MONNIFY_SECRET_KEY.encode("utf-8"),
        raw_body,
        hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(expected, received_signature or "")


@app.route("/give", methods=["GET", "POST"])
def give():
    form = DonationForm()

    if form.validate_on_submit():
        amount = Decimal(form.amount.data)
        reference = f"DON-{uuid.uuid4().hex[:20].upper()}"

        donation = Donation(
            full_name=form.full_name.data,
            email=form.email.data,
            phone=form.phone.data,
            donation_type=form.donation_type.data,
            amount=amount,
            status="pending",
            reference=reference,
        )
        db.session.add(donation)
        db.session.commit()

        payload = {
            "amount": float(amount),               # NOTE: Monnify wants plain Naira, NOT kobo like OPay was
            "customerName": form.full_name.data,
            "customerEmail": form.email.data,
            "paymentReference": reference,
            "paymentDescription": f"Church donation - {form.donation_type.data}",
            "currencyCode": "NGN",
            "contractCode": MONNIFY_CONTRACT_CODE,
            "redirectUrl": url_for("donation_summary", reference=reference, _external=True),
            "paymentMethods": ["ACCOUNT_TRANSFER", "CARD"],
        }

        try:
            token = get_monnify_token()
            response = requests.post(
                f"{MONNIFY_BASE_URL}/api/v1/merchant/transactions/init-transaction",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                },
                json=payload,
                timeout=30,
            )
            result = response.json()
            logger.info("MONNIFY RESPONSE: %s", json.dumps(result, ensure_ascii=True)[:2000])

            if not result.get("requestSuccessful"):
                flash(result.get("responseMessage", "Unable to initialize payment."), "error")
                return redirect(url_for("give"))

            data = result.get("responseBody", {})
            checkout_url = data.get("checkoutUrl")
            if not checkout_url:
                flash("Monnify did not return a checkout URL.", "error")
                return redirect(url_for("give"))

            donation.opay_order_no = data.get("transactionReference")   # reused field — see note below
            db.session.commit()

            ActivityLog.log(f"Giving initiated — ₦{amount} ({form.donation_type.data})")
            return redirect(checkout_url)

        except requests.RequestException as e:
            print("Monnify request error:", e)
            flash("Unable to connect to Monnify. Please try again.", "error")
            return redirect(url_for("give"))

    return render_template("give.html", title="Give", form=form)


@csrf.exempt
@app.route("/monnify/callback", methods=["POST"])
def monnify_callback():
    raw_body = request.get_data()
    received_sig = request.headers.get("monnify-signature")

    if not verify_monnify_webhook_signature(raw_body, received_sig):
        print("Monnify webhook: signature mismatch — rejecting")
        return jsonify({"status": "invalid signature"}), 400

    data = request.get_json()
    event_data = data.get("eventData", {})
    reference = event_data.get("paymentReference")

    donation = Donation.query.filter_by(reference=reference).first()
    if not donation:
        return jsonify({"status": "error"}), 404

    if event_data.get("paymentStatus") == "PAID":
        donation.status = "successful"
        donation.opay_transaction_id = event_data.get("transactionReference")  # reused field
        donation.payment_method = event_data.get("paymentMethod")
        donation.payment_response = data
        db.session.commit()

    return jsonify({"status": "success"}), 200

@app.route("/donation/<reference>")
def donation_summary(reference):
    donation = Donation.query.filter_by(reference=reference).first_or_404()
    return render_template("donation_summary.html", donation=donation)


@app.route("/donation/success")
def donation_success():
    return render_template("donation_success.html")

from datetime import timedelta

@app.route('/admin_dashboard', methods=["GET"])
def admin_dashboard():
    week_ago = datetime.utcnow() - timedelta(days=7)
    stats = {
        'prayer_requests': Prayer_Request.query.count(),
        'prayer_requests_week': Prayer_Request.query.filter(Prayer_Request.date_submitted >= week_ago).count(),
        'sermons': Sermon.query.count(),
        'sermons_week': Sermon.query.filter(Sermon.date >= week_ago).count(),
        'gallery_items': Gallery.query.count(),
        'gallery_week': Gallery.query.filter(Gallery.upload_date >= week_ago).count(),
        'announcements': Announcement.query.count(),
        'announcements_week': Announcement.query.filter(Announcement.timestamp >= week_ago).count(),
    }

    recent = []
    for s in Sermon.query.order_by(Sermon.date.desc()).limit(9):
        recent.append({'title': s.topic, 'type': 'Sermon', 'date': s.date})
    for a in Announcement.query.order_by(Announcement.timestamp.desc()).limit(9):
        recent.append({'title': (a.announcement or '')[:60], 'type': 'Announcement', 'date': a.timestamp})
    for g in Gallery.query.order_by(Gallery.upload_date.desc()).limit(9):
        recent.append({'title': g.title, 'type': 'Gallery', 'date': g.upload_date})
    recent.sort(key=lambda x: x['date'] or datetime.min, reverse=True)
    total_content = Sermon.query.count() + Announcement.query.count() + Gallery.query.count()
    recent = recent[:9]

    today = datetime.utcnow().date()
    days_ahead = (6 - today.weekday()) % 7 or 7
    next_sunday = today + timedelta(days=days_ahead)

    open_modal = request.args.get('open')

    return render_template(
        "admin/admin_dashboard.html",
        stats=stats, recent_content=recent, total_content=total_content,
        next_sunday=next_sunday, open_modal=open_modal,
        activities=ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(10).all(),
        prayer_requests=Prayer_Request.query.order_by(Prayer_Request.date_submitted.desc()).all(),
        sermons=Sermon.query.order_by(Sermon.date.desc()).all(),
        announcements=Announcement.query.order_by(Announcement.timestamp.desc()).all(),
        gallery_items=Gallery.query.order_by(Gallery.upload_date.desc()).all(),
        resources=Resource.query.order_by(Resource.upload_date.desc()).all(),
        members=NewMember.query.order_by(NewMember.registration_date.desc()).all(),
        donations=Donation.query.order_by(Donation.created_at.desc()).all(),
        youths=Youth.query.order_by(Youth.date_registered.desc()).all(),
        sermon_form=SermonForm(), announcement_form=AnnouncementForm(),
        gallery_form_obj=GalleryForm(), resource_form=ResourceForm(),
    )

@app.route('/admin/recent-activity')
def admin_recent_activity():
    combined = []
    for s in Sermon.query.all():
        combined.append({'title': s.topic, 'type': 'Sermon', 'date': s.date})
    for a in Announcement.query.all():
        combined.append({'title': (a.announcement or '')[:100], 'type': 'Announcement', 'date': a.timestamp})
    for g in Gallery.query.all():
        combined.append({'title': g.title, 'type': 'Gallery', 'date': g.upload_date})
    combined.sort(key=lambda x: x['date'] or datetime.min, reverse=True)
    return render_template('admin/admin_recent_activity.html', items=combined)


@app.route('/announcements_form', methods=["GET", "POST"])
#@admin_required
def announcements_form():
    if request.method == "GET":
        return redirect(url_for("admin_dashboard"))

    form = AnnouncementForm()
    if form.validate_on_submit():
        announcement = Announcement(
            timestamp=datetime.utcnow(),
            announcement=form.announcement.data,
        )
        db.session.add(announcement)
        db.session.commit()
        ActivityLog.log('New announcement posted')
        flash("Announcement posted.", "success")
        return redirect(url_for("admin_dashboard"))

    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{field}: {error}", "error")
    return redirect(url_for("admin_dashboard", open="announcementModal"))


@app.route('/gallery_form', methods=["GET", "POST"])
#@admin_required
def gallery_form():
    form = GalleryForm()
    if form.validate_on_submit():
        files = [f for f in request.files.getlist('image') if f and f.filename]
        if not files:
            flash("Please choose at least one image.", "error")
            return redirect(url_for("admin_dashboard", open="galleryModal"))

        allowed_ext = {'jpg', 'jpeg', 'png', 'webp'}
        uploaded = 0
        for image in files:
            ext = image.filename.rsplit('.', 1)[-1].lower()
            if ext not in allowed_ext:
                continue
            filename = secure_filename(image.filename)
            filename = f"{uuid.uuid4().hex}_{filename}"
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            db.session.add(Gallery(
                title=form.title.data, image=filename,
                category=form.category.data, event_date=form.event_date.data
            ))
            uploaded += 1

        db.session.commit()
        ActivityLog.log(f'Gallery updated — {uploaded} photo(s) uploaded ({form.category.data})')
        flash(f"{uploaded} image(s) uploaded successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{field}: {error}", "error")
    return redirect(url_for("admin_dashboard", open="galleryModal"))


@app.route("/sermon_form", methods=["GET", "POST"])
#@admin_required
def sermon_form():
    if request.method == "GET":
        return redirect(url_for("admin_dashboard"))

    form = SermonForm()
    if form.validate_on_submit():
        video = form.video.data
        filename = secure_filename(video.filename)
        filename = f"{uuid.uuid4().hex}_{filename}"
        video.save(os.path.join(app.config["SERMON_FOLDER"], filename))

        sermon = Sermon(
            topic=form.topic.data, video=filename,
            day=form.day.data, duration=form.duration.data
        )
        db.session.add(sermon)
        db.session.commit()
        ActivityLog.log(f'New sermon published: "{sermon.topic}"')
        flash("Sermon uploaded successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{field}: {error}", "error")
    return redirect(url_for("admin_dashboard", open="sermonModal"))


@app.route("/youth-registration", methods=["GET", "POST"])
def youth_registration():

    form = YouthForm()

    if form.validate_on_submit():

        # Check if phone already exists
        existing_phone = Youth.query.filter_by(
            phone=form.phone.data
        ).first()

        if existing_phone:
            flash(
                "A youth with this phone number is already registered.",
                "danger"
            )
            return render_template(
                "youth_registration.html",
                form=form
            )

        # Check email only if one was provided
        if form.email.data:
            existing_email = Youth.query.filter_by(
                email=form.email.data
            ).first()

            if existing_email:
                flash(
                    "A youth with this email address is already registered.",
                    "danger"
                )
                return render_template(
                    "youth_registration.html",
                    form=form
                )

        youth = Youth(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            other_name=form.other_name.data,
            gender=form.gender.data,
            date_of_birth=form.date_of_birth.data,
            age=form.age.data,
            phone=form.phone.data,
            email=form.email.data or None,
            address=form.address.data,
            occupation=form.occupation.data,
            school=form.school.data,
            marital_status=form.marital_status.data,
            department=form.department.data,
            emergency_contact_name=form.emergency_contact_name.data,
            emergency_contact_phone=form.emergency_contact_phone.data
        )

        db.session.add(youth)
        db.session.commit()

        flash(
            "Youth registration completed successfully!",
            "success"
        )

        return redirect(url_for("youth_registration"))

    return render_template(
        "youth_registration.html",
        form=form
    )


@app.route('/admin/prayer-requests/<int:id>/delete', methods=["POST"])
def delete_prayer_request(id):
    item = Prayer_Request.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    ActivityLog.log(f'Prayer request from "{item.name}" deleted')
    flash('Prayer request deleted.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/sermons/<int:id>/delete', methods=["POST"])
def delete_sermon(id):
    item = Sermon.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    ActivityLog.log(f'Sermon deleted: "{item.topic}"')
    flash('Sermon deleted.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/announcements/<int:id>/delete', methods=["POST"])
def delete_announcement(id):
    item = Announcement.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    ActivityLog.log('Announcement deleted')
    flash('Announcement deleted.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/gallery/<int:id>/delete', methods=["POST"])
def delete_gallery(id):
    item = Gallery.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    ActivityLog.log(f'Gallery item removed: "{item.title}"')
    flash('Gallery item removed.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/resources/<int:id>/delete', methods=["POST"])
def delete_resource(id):
    item = Resource.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    ActivityLog.log(f'Resource removed: "{item.title}"')
    flash('Resource removed.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/resource_form', methods=["GET", "POST"])
def resource_form():
    form = ResourceForm()
    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)
        filename = f"{uuid.uuid4().hex}_{filename}"
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        resource = Resource(title=form.title.data, category=form.category.data, file=filename)
        db.session.add(resource)
        db.session.commit()
        ActivityLog.log(f'New resource uploaded: "{resource.title}"')
        flash("Resource uploaded successfully.", "success")
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", "error")
        return redirect(url_for("admin_dashboard", open="resourceModal"))


@app.route('/admin/members/<int:id>/delete', methods=["POST"])
def delete_member(id):
    item = NewMember.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    ActivityLog.log(f'Member registration deleted: {item.first_name} {item.last_name}')
    flash('Member registration deleted.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/youths/<int:id>/delete', methods=["POST"])
def delete_youth(id):
    item = Youth.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    ActivityLog.log(f'Youth registration deleted: {item.first_name} {item.last_name}')
    flash('Youth registration deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

def timesince(dt):
    if dt is None:
        return '—'
    seconds = (datetime.utcnow() - dt).total_seconds()
    if seconds < 60: return 'just now'
    minutes = seconds // 60
    if minutes < 60: return f'{int(minutes)} minute{"s" if minutes != 1 else ""} ago'
    hours = minutes // 60
    if hours < 24: return f'{int(hours)} hour{"s" if hours != 1 else ""} ago'
    days = hours // 24
    return f'{int(days)} day{"s" if days != 1 else ""} ago'

app.jinja_env.filters['timesince'] = timesince

import csv
import io
from flask import Response

@app.route('/admin/members/<int:id>/download')
def download_member(id):
    item = NewMember.query.get_or_404(id)
    lines = [
        f"Name: {item.first_name} {item.last_name} {item.other_name or ''}".strip(),
        f"Gender: {item.gender or ''}",
        f"Date of Birth: {item.date_of_birth or ''}",
        f"Marital Status: {item.marital_status or ''}",
        f"Phone: {item.phone or ''}",
        f"Alternate Phone: {item.alternate_phone or ''}",
        f"Email: {item.email or ''}",
        f"Address: {item.address or ''}",
        f"Occupation: {item.occupation or ''}",
        f"Place of Work: {item.place_of_work or ''}",
        f"Invited By: {item.invited_by or ''}",
        f"First Time Visit: {'Yes' if item.first_time_visit else 'No'}",
        f"Born Again: {'Yes' if item.born_again else 'No'}",
        f"Baptized: {'Yes' if item.baptized else 'No'}",
        f"Department of Interest: {item.department_of_interest or ''}",
        f"Prayer Request: {item.prayer_request or ''}",
        f"Emergency Contact: {item.emergency_contact_name or ''} ({item.emergency_contact_phone or ''})",
        f"Registration Date: {item.registration_date or ''}",
    ]
    filename = f"member_{item.last_name}_{item.first_name}.txt".replace(" ", "_")
    return Response("\n".join(lines), mimetype="text/plain",
                     headers={"Content-Disposition": f"attachment; filename={filename}"})


@app.route('/admin/members/download-all')
def download_all_members():
    members = NewMember.query.order_by(NewMember.registration_date.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "First Name", "Last Name", "Other Name", "Gender", "Date of Birth", "Marital Status",
        "Phone", "Alternate Phone", "Email", "Address", "Occupation", "Place of Work",
        "Invited By", "First Time Visit", "Born Again", "Baptized",
        "Department of Interest", "Prayer Request",
        "Emergency Contact Name", "Emergency Contact Phone", "Registration Date"
    ])
    for m in members:
        writer.writerow([
            m.first_name, m.last_name, m.other_name, m.gender, m.date_of_birth, m.marital_status,
            m.phone, m.alternate_phone, m.email, m.address, m.occupation, m.place_of_work,
            m.invited_by, m.first_time_visit, m.born_again, m.baptized,
            m.department_of_interest, m.prayer_request,
            m.emergency_contact_name, m.emergency_contact_phone, m.registration_date
        ])
    return Response(output.getvalue(), mimetype="text/csv",
                     headers={"Content-Disposition": "attachment; filename=members.csv"})


@app.route('/admin/youths/<int:id>/download')
def download_youth(id):
    item = Youth.query.get_or_404(id)
    lines = [
        f"Name: {item.first_name} {item.last_name} {item.other_name or ''}".strip(),
        f"Gender: {item.gender}",
        f"Age: {item.age}",
        f"Date of Birth: {item.date_of_birth or ''}",
        f"Marital Status: {item.marital_status}",
        f"Phone: {item.phone}",
        f"Email: {item.email or ''}",
        f"Address: {item.address}",
        f"Occupation: {item.occupation or ''}",
        f"School: {item.school or ''}",
        f"Department: {item.department or ''}",
        f"Emergency Contact: {item.emergency_contact_name or ''} ({item.emergency_contact_phone or ''})",
        f"Registration Date: {item.date_registered or ''}",
    ]
    filename = f"youth_{item.last_name}_{item.first_name}.txt".replace(" ", "_")
    return Response("\n".join(lines), mimetype="text/plain",
                     headers={"Content-Disposition": f"attachment; filename={filename}"})


@app.route('/admin/youths/download-all')
def download_all_youths():
    youths = Youth.query.order_by(Youth.date_registered.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "First Name", "Last Name", "Other Name", "Gender", "Age", "Date of Birth",
        "Marital Status", "Phone", "Email", "Address", "Occupation", "School", "Department",
        "Emergency Contact Name", "Emergency Contact Phone", "Registration Date"
    ])
    for y in youths:
        writer.writerow([
            y.first_name, y.last_name, y.other_name, y.gender, y.age, y.date_of_birth,
            y.marital_status, y.phone, y.email, y.address, y.occupation, y.school, y.department,
            y.emergency_contact_name, y.emergency_contact_phone, y.date_registered
        ])
    return Response(output.getvalue(), mimetype="text/csv",
                     headers={"Content-Disposition": "attachment; filename=youths.csv"})

@app.route('/board')
def board():
    return render_template('board_page.html')

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')