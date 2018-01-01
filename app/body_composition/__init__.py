from flask import Blueprint

body_comp = Blueprint('body_comp', __name__)

from . import views  # noqa
