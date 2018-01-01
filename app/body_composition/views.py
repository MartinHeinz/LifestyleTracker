from flask import request, render_template, flash
from flask_login import login_required, current_user
from werkzeug.exceptions import abort

from ..models import BodyComposition, Day
from .. import db
from .forms import BodyCompForm
from . import body_comp


@body_comp.route('/')
@login_required
def index():
    """Body composition base page."""
    return render_template('body_comp/index.html')


@body_comp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = BodyCompForm()
    if request.method == "GET":
        return render_template('body_comp/add.html', form=form)
    if form.validate_on_submit():
        day = Day.get_by_date(db.session, form.date.data)
        if day is None:
            day = Day(date=form.date.data, user=current_user)
        bc = BodyComposition(
            body_fat=form.body_fat.data,
            chest=form.chest.data,
            arm=form.arm.data,
            waist=form.waist.data,
            belly=form.belly.data,
            thigh=form.thigh.data,
            calf=form.calf.data,
            forearm=form.forearm.data,
            weight=form.weight.data,
            day=day
        )
        db.session.add(bc)
        db.session.commit()
        flash("Record added.", 'success')
        return render_template('body_comp/index.html')
    return render_template('body_comp/add.html', form=form)


@body_comp.route('/list_all')
@login_required
def list_all():
    """View all body composition records."""
    body_comps = BodyComposition.get_by_user(db.session, current_user)
    return render_template('body_comp/list_all.html', body_comps=body_comps)


@body_comp.route('/edit/<int:body_comp_id>', methods=['GET', 'POST'])
@login_required
def edit(body_comp_id):
    bc = BodyComposition.query.filter_by(id=body_comp_id).first()
    if bc is None:
        abort(404)
    form = BodyCompForm(obj=bc)
    if request.method == "GET":
        form.date.data = bc.day.date
        return render_template('body_comp/add.html', form=form)
    if form.validate_on_submit():
        day = Day.get_by_date(db.session, form.date.data)
        BodyComposition.query.filter(BodyComposition.id == body_comp_id).delete()
        if day is None:
            day = Day(date=form.date.data, user=current_user)
        # TODO check ci na dany den uz neukazuje nieco ine (musi to byt one to one)
        bc = BodyComposition(
            body_fat=form.body_fat.data,
            chest=form.chest.data,
            arm=form.arm.data,
            waist=form.waist.data,
            belly=form.belly.data,
            thigh=form.thigh.data,
            calf=form.calf.data,
            forearm=form.forearm.data,
            weight=form.weight.data,
            day=day
        )
        db.session.add(bc)
        db.session.commit()
        flash("Record updated.", 'success')
        return render_template('body_comp/index.html')
    else:
        return render_template('body_comp/add.html', form=form)













