from flask.blueprints import Blueprint

from .models import *
from .views import *

app = Blueprint('blueprint', __name__, template_folder='templates')
