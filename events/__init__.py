from flask.blueprints import Blueprint

from .models import *

app = Blueprint('blueprint', __name__, template_folder='templates')
