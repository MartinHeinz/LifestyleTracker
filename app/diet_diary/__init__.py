from flask import Blueprint

diet_diary = Blueprint('diet_diary', __name__)

from . import views  # noqa