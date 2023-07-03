from flask import render_template
from flask_login import login_required

from util.misc import meta_data


@login_required
def tests_page():
    return render_template('tests.html', meta=meta_data())