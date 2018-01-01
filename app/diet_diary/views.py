import datetime
from flask import render_template, request, jsonify
from flask_login import login_required

from ..models import Food, db, Day
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
        elif request.json['id'] == "meal_tree":
            return jsonify(meals=None)  # TODO
        elif request.json['id'] == "add_meal":  # TODO create meal, return success/fail
            return jsonify(success=True)
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
        most_recent = Day.get_most_recent_passed(session)
        if date > most_recent.date:
            dates = [most_recent.date + datetime.timedelta(days=x) for x in range((date - most_recent.date).days + 1)][1:]
            days = [Day(date=d) for d in dates]
            session.add_all(days)
            session.commit()
    return Day.get_by_date(session, date)
