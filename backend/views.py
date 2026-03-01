"""View routes for rendering HTML templates."""

from flask import Blueprint, render_template

views_bp = Blueprint('views', __name__)


@views_bp.route('/')
def index():
    return render_template('marketing.html')

@views_bp.route('/login')
def login_page():
    return render_template('login.html')


@views_bp.route('/register')
def register_page():
    return render_template('register.html')


@views_bp.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')


@views_bp.route('/modules')
def modules_page():
    return render_template('modules.html')


@views_bp.route('/module1')
def module1_page():
    return render_template('module1.html')


@views_bp.route('/module2')
def module2_page():
    return render_template('module2.html')


@views_bp.route('/module3')
def module3_page():
    return render_template('module3.html')


@views_bp.route('/module4')
def module4_page():
    return render_template('module4.html')


@views_bp.route('/module5')
def module5_page():
    return render_template('module5.html')


@views_bp.route('/module6')
def module6_page():
    return render_template('module6.html')


@views_bp.route('/module7')
def module7_page():
    return render_template('module7.html')


@views_bp.route('/module8')
def module8_page():
    return render_template('module8.html')


@views_bp.route('/matching')
def matching_page():
    return render_template('matching.html')


@views_bp.route('/chat')
def chat_page():
    return render_template('chat.html')

