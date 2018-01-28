import datetime

from dateutil import parser
from flask import render_template, request, jsonify, json
from flask_login import login_required, current_user

from app.utils import is_time, is_date
from ..models import Food, db, Day, Meal
from .forms import AddMealForm, CopyMealForm, SelectDayForm
from . import diet_diary


SEARCH_BY = ["name", "cal", "protein", "fat", "carbs",  "fibre", "brand"]
TABLE_COLS = ["Name", "Calories", 'Protein', "Fats", "Carbs"]
SELECTED_DAY = None


@diet_diary.route('/', methods=['GET', 'POST'])
@login_required
def index():
    """Diet diary base page."""
    add_meal_form = AddMealForm()
    copy_meal_form = CopyMealForm()
    if request.method == "GET":
        global SELECTED_DAY
        if SELECTED_DAY is None:
            SELECTED_DAY = get_day(db.session, datetime.date.today())
            db.session.expunge(SELECTED_DAY)  # TODO maybe not good thing to do?
        select_day_form = SelectDayForm()
        select_day_form.date.data = SELECTED_DAY.date
        return render_template('diet_diary/index.html',
                               select_day_form=select_day_form,
                               add_meal_form=add_meal_form,
                               copy_meal_form=copy_meal_form,
                               search_by=SEARCH_BY,
                               table_cols=TABLE_COLS)
    else:
        if request.json['id'] == "search":
            return jsonify(search_result=search(request.json['search_input'], request.json['search_by_value']))
        elif request.json['id'] == "select_day":
            if is_date(request.json['date']):
                input_date = parser.parse(request.json['date'])
                day = Day.get_by_date(db.session, input_date.date(), current_user)
                if day is not None:
                    temp = jsonify(meals=[item.serialize for item in day.meals])

                    return temp
            return jsonify(success=False)
        elif request.json['id'] == "add_meal":  # TODO test
            if is_time(request.json["time"]):
                new_meal = Meal(day=SELECTED_DAY, time=request.json["time"], name=request.json["name"])
                db.session.add(new_meal)
                db.session.commit()
                return jsonify(success=True)  # TODO add meal to meal_tree
            return jsonify(success=False)  # TODO display Warning message
        return ""


def search(search_input, search_by_value):
    if search_by_value in ["food", "name"]:
        rows = Food.search_by_attribute(db.session, search_input, "name")
    elif search_by_value in ["cal", "protein", "carbs", "fat", "fibre"] and search_input.replace('.', '', 1).isdigit():
        rows = Food.get_closest_matches(db.session, float(search_input), search_by_value, 10)
    else:
        rows = Food.search_by_attribute(db.session, search_input, search_by_value)

    result = []
    for row in rows:
        result.append([row.name, float(row.cal), float(row.protein), float(row.fat), float(row.carbs)])
    return result


def get_day(session, date, generate_missing=True):
    if generate_missing:
        most_recent = Day.get_most_recent_passed(session, current_user)
        if most_recent is None:
            most_recent = Day(date=datetime.date.today() - datetime.timedelta(1), user=current_user)
        if date > most_recent.date:
            dates = [most_recent.date + datetime.timedelta(days=x) for x in range((date - most_recent.date).days + 1)][1:]
            days = [Day(date=d, user=current_user) for d in dates]
            session.add_all(days)
            session.commit()
    return Day.get_by_date(session, date, current_user)
