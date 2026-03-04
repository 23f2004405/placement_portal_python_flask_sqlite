from flask import Blueprint,render_template,flash,redirect,url_for
from flask_login import current_user,logout_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def landing_page():
    return render_template('landing.html')

@main_bp.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash('You have been logged out')
        return redirect(url_for('main.landing_page'))
    return redirect(url_for('main.landing_page'))