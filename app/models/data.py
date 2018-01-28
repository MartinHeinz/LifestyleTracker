import textwrap
from datetime import date
from itertools import chain

import decimal
from sqlalchemy import Table, Column, Integer, ForeignKey, Date, Numeric, String, Text, Boolean, Time, and_, or_, cast, \
    func, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects import postgresql

from .mixins import MixinGetByName, MixinSearch
from .utils import sort_to_match

from .user import User
from .. import db

User.days = relationship("Day", back_populates="user")

# RAW SQLALCHEMY, TO CHANGE WHOLE FOLE TO RAW SQLALCHEMY CHANGE db.Model TO Base, WHERE BASE IS DECLARATIVE BASE E.G.
# Base = declarative_base(cls=RepresentableBase)

# recipe_tag_table = Table('recipe_tag', Base.metadata,
#                          Column("recipe_id", Integer, ForeignKey('recipe.id')),
#                          Column('tag_id', Integer, ForeignKey('tag.id')),
#                          extend_existing=True
#                          )
#
# exercise_equipment_table = Table('exercise_equipment', Base.metadata,
#                                  Column('equipment_id', Integer, ForeignKey('equipment.id')),
#                                  Column('exercise_id', Integer, ForeignKey('exercise.id')),
#                                  extend_existing=True
#                                  )
#
# exercise_tag_table = Table('exercise_tag', Base.metadata,
#                            Column('tag_id', Integer, ForeignKey('tag.id')),
#                            Column('exercise_id', Integer, ForeignKey('exercise.id')),
#                            extend_existing=True
#                            )
#
# food_tag_table = Table('food_tag', Base.metadata,
#                        Column("food_id", Integer, ForeignKey('food.id')),
#                        Column('tag_id', Integer, ForeignKey('tag.id')),
#                        extend_existing=True
#                        )


recipe_tag_table = db.Table('recipe_tag',
                            db.Column("recipe_id", db.Integer, db.ForeignKey('recipe.id')),
                            db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
                            extend_existing=True
                            )

exercise_equipment_table = db.Table('exercise_equipment',
                                    db.Column('equipment_id', db.Integer, db.ForeignKey('equipment.id')),
                                    db.Column('exercise_id', db.Integer, db.ForeignKey('exercise.id')),
                                    extend_existing=True
                                    )

exercise_tag_table = db.Table('exercise_tag',
                              db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
                              db.Column('exercise_id', db.Integer, db.ForeignKey('exercise.id')),
                              extend_existing=True
                              )

food_tag_table = db.Table('food_tag',
                          db.Column("food_id", db.Integer, db.ForeignKey('food.id')),
                          db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
                          extend_existing=True
                         )


class Day(db.Model):
    __tablename__ = 'day'
    __table_args__ = (UniqueConstraint("date", "user_id", name="date_user_constraint"),
                      {'extend_existing': True},
                      )

    id = Column(Integer, primary_key=True)
    body_composition = relationship("BodyComposition", uselist=False, back_populates="day")
    date = Column(Date)
    target_cal = Column(postgresql.INT4RANGE)
    target_carbs = Column(postgresql.INT4RANGE)
    target_protein = Column(postgresql.INT4RANGE)
    target_fat = Column(postgresql.INT4RANGE)
    target_fibre = Column(postgresql.INT4RANGE)
    training_id = Column(Integer, ForeignKey('training.id'))
    training = relationship("Training", uselist=False, back_populates="day")
    meals = relationship("Meal", cascade="all, delete-orphan", back_populates="day")
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship("User", back_populates="days")

    @classmethod
    def get_by_date(cls, session, date, user):
        return session.query(cls).join(User).filter(and_(cls.date == date,
                                                         user.id == User.id)).scalar()

    @classmethod
    def get_most_recent(cls, session, user):
        return session.query(cls).join(User)\
            .filter(user.id == User.id)\
            .order_by(cls.date.desc()).first()  # user.id == User.id? alebo user.id == cls.user_id

    @classmethod
    def get_most_recent_passed(cls, session, user):
        """ Returns day in interval <first - today> that is closest to today and is
        contained in database."""
        return session.query(cls).filter(and_(cls.date <= date.today(),
                                              user.id == cls.user_id)).order_by(cls.date.desc()).first()


class BodyComposition(db.Model):
    __tablename__ = 'body_composition'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    day_id = Column(Integer, ForeignKey('day.id'))
    day = relationship("Day", back_populates="body_composition")
    body_fat = Column(Numeric(precision=5, scale=2))
    chest = Column(Numeric(precision=5, scale=2))
    arm = Column(Numeric(precision=5, scale=2))
    waist = Column(Numeric(precision=5, scale=2))
    belly = Column(Numeric(precision=5, scale=2))
    thigh = Column(Numeric(precision=5, scale=2))
    calf = Column(Numeric(precision=5, scale=2))
    forearm = Column(Numeric(precision=5, scale=2))
    weight = Column(Numeric(precision=5, scale=2))

    @classmethod
    def get_by_user(cls, session, user):
        return session.query(cls).join(cls.day).join(User).filter(User.id == user.id).all()


class Ingredient(db.Model):
    __tablename__ = 'ingredient'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    amount = Column(Numeric(precision=5, scale=2))
    measurement_id = Column(Integer, ForeignKey('measurement.id'))
    measurement = relationship("Measurement", back_populates="ingredients")
    food_id = Column(Integer, ForeignKey('food.id'))
    food = relationship("Food", back_populates="ingredients")
    recipe_id = Column(Integer, ForeignKey('recipe.id'))
    recipe = relationship("Recipe", back_populates="ingredients")

    def get_calories(self):
        # return self.food.round(self.food.cal * (self.measurement/100), 2)
        if not self.measurement:
            return round(self.food.cal * (self.amount / 100))
        return round(self.food.cal * ((self.amount * self.measurement.grams) / 100))

    def get_attr_amount(self, attr_name):
        if not self.measurement:
            return getattr(self.food, attr_name, 0) * (self.amount / 100)
        return getattr(self.food, attr_name, 0) * ((self.amount * self.measurement.grams) / 100)

    def get_amount_by_cal(self, cal):
        cal = decimal.Decimal(cal)
        if not self.measurement:
            return round((100 * cal) / self.food.cal, 2)
        amount = (100 * cal) / self.food.cal
        return round(amount / self.measurement.grams, 2)


class FoodUsage(db.Model):
    __tablename__ = 'food_usage'
    __table_args__ = {'extend_existing': True}
    meal_id = Column(Integer, ForeignKey('meal.id'))
    food_id = Column(Integer, ForeignKey('food.id'))
    recipe_id = Column(Integer, ForeignKey('recipe.id'))
    amount = Column(Numeric(precision=5, scale=2))
    meal = relationship("Meal", back_populates="foods")
    food = relationship("Food", back_populates="meals")
    id = Column(Integer, primary_key=True)
    measurement_id = Column(Integer, ForeignKey('measurement.id'))
    measurement = relationship("Measurement", back_populates="food_usages")

    def get_calories(self):
        # return self.food.round(self.food.cal * (self.measurement/100), 2)
        if not self.measurement:
            return round(self.food.cal * (self.amount / 100))
        return round(self.food.cal * ((self.amount * self.measurement.grams) / 100))

    def get_attr_amount(self, attr_name):
        if not self.measurement:
            return getattr(self.food, attr_name, 0) * (self.amount / 100)
        return getattr(self.food, attr_name, 0) * ((self.amount * self.measurement.grams) / 100)

    def get_amount_by_cal(self, cal):
        cal = decimal.Decimal(cal)
        if not self.measurement:
            return round((100 * cal) / self.food.cal, 2)
        amount = (100 * cal) / self.food.cal
        return round(amount / self.measurement.grams, 2)


class Food(MixinGetByName, MixinSearch, db.Model):
    __tablename__ = 'food'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    cal = Column(Numeric(precision=5, scale=2))
    protein = Column(Numeric(precision=5, scale=2))
    carbs = Column(Numeric(precision=5, scale=2))
    fat = Column(Numeric(precision=5, scale=2))
    fibre = Column(Numeric(precision=5, scale=2))
    brand = Column(String)
    description = Column(Text)  # TODO test
    measurements = relationship("Measurement", back_populates="food")
    meals = relationship("FoodUsage", back_populates="food")
    ingredients = relationship("Ingredient", back_populates="food")
    tags = relationship(
        "Tag",
        secondary=food_tag_table,
        back_populates="foods")
    supplements = relationship("FoodSupplement", back_populates="food")

    @classmethod  # TODO check if it works when rows with type other than "food" are added
    def search_by_tag(cls, session, search_string):
        words = " & ".join(search_string.split())
        return session.query(Food). \
            join(Food.tags). \
            filter(and_(or_(func.to_tsvector('english', Tag.name).match(words, postgresql_regconfig='english'),
                            func.to_tsvector('english', Tag.description).match(words, postgresql_regconfig='english')),
                        Tag.type == "food")).all()

    def get_field_secondary_text(self):
        text = "Brand: {brand: <10} {cal: >10} cal {protein: >10} protein {fat: >10} fat {carbs: >10} carbs {fibre: >10} fibre" \
            .format(brand="Undefined" if self.brand is None else self.brand,
                    cal=self.cal,
                    protein=self.protein,
                    fat=self.fat,
                    carbs=self.carbs,
                    fibre=self.fibre)

        return text


class FoodSupplement(db.Model):
    __tablename__ = 'food_supplement'
    food_id = Column(Integer, ForeignKey('food.id'), primary_key=True)
    supplement_id = Column(Integer, ForeignKey('supplement.id'), primary_key=True)
    amount = Column(Numeric(precision=5, scale=2))
    food = relationship("Food", back_populates="supplements")
    supplement = relationship("Supplement", back_populates="foods")


class Supplement(MixinGetByName, db.Model):
    __tablename__ = 'supplement'
    __table_args__ = (CheckConstraint("type ~* '^(vitamin|micronutrient|stimulant){1}$'", name="type_check"),
                      {'extend_existing': True},
                      )

    id = Column(Integer, primary_key=True)
    type = Column(String)  # vitamin/micronutrient/stimulant
    foods = relationship("FoodSupplement", back_populates="supplement")


class Measurement(MixinGetByName, db.Model):
    __tablename__ = 'measurement'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    food_id = Column(Integer, ForeignKey('food.id'))
    food = relationship("Food", back_populates="measurements")
    grams = Column(Numeric(precision=5, scale=2))
    food_usages = relationship("FoodUsage", back_populates="measurement")
    ingredients = relationship("Ingredient", back_populates="measurement")


class Meal(MixinGetByName, db.Model):
    __tablename__ = 'meal'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    foods = relationship("FoodUsage", cascade="all, delete-orphan", back_populates="meal")
    # description = Column(Text)  # TODO test
    day_id = Column(Integer, ForeignKey('day.id'))
    day = relationship("Day", back_populates="meals")
    time = Column(Time)
    recipes = relationship("Recipe", cascade="all, delete-orphan", back_populates="meal")

    @property
    def serialize(self):
        return {
            'name': self.name,
            'id': self.id,
            #'foods': [item.serialize() for item in self.foods],  # TODO
            'day_id': self.day_id,
            #'day': self.day.serialize(),   # TODO
            'time': self.time,  # TODO is this correct (strftime?)
            #'recipes': [item.serialize() for item in self.recipes]   # TODO
        }

    def add_food(self, food, amount, measurement=None):
        food_usage = FoodUsage(amount=amount)
        food_usage.food = food
        food_usage.measurement = measurement
        if self.foods is None:
            self.foods = [food_usage]
        else:
            self.foods.append(food_usage)

    def add_recipe(self, recipe):
        if self.recipes is not None:
            self.recipes.append(recipe)
        else:
            self.recipes = [recipe]

    def get_calories(self):
        return sum(i.get_calories() for i in chain(self.foods, self.recipes))

    def get_attr_amount(self, attr_name):
        return sum(f.get_attr_amount(attr_name) for f in chain(self.foods, self.recipes))


class Recipe(MixinGetByName, MixinSearch, db.Model):
    __tablename__ = 'recipe'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    serving_size = Column(Numeric(precision=5, scale=2))
    notes = Column(Text)
    tags = relationship(
        "Tag",
        secondary=recipe_tag_table,
        back_populates="recipes")
    ingredients = relationship("Ingredient", cascade="all, delete-orphan", back_populates="recipe")
    is_template = Column(Boolean, default=False)
    recipe_executions = relationship("Recipe",
                                     uselist=True,
                                     foreign_keys='Recipe.template_id',
                                     backref=backref("template", uselist=False, remote_side=[id]))
    template_id = Column(Integer, ForeignKey('recipe.id'))
    meal_id = Column(Integer, ForeignKey('meal.id'))
    meal = relationship("Meal", back_populates="recipes")

    @classmethod  # TODO check if it works when rows with type other than "recipe" are added
    def search_by_tag(cls, session, search_string):
        words = " & ".join(search_string.split())
        return session.query(Recipe). \
            join(Recipe.tags). \
            filter(and_(or_(func.to_tsvector('english', Tag.name).match(words, postgresql_regconfig='english'),
                            func.to_tsvector('english', Tag.description).match(words, postgresql_regconfig='english')),
                        Tag.type == "recipe")).all()

    def add_food(self, food, amount, measurement=None):
        ingredient = Ingredient(amount=amount)
        ingredient.food = food
        ingredient.measurement = measurement
        if self.ingredients is None:
            self.ingredients = [ingredient]
        else:
            self.ingredients.append(ingredient)

    def get_calories(self):
        return sum(i.get_calories() for i in self.ingredients)

    def get_attr_amount(self, attr_name):
        return sum(f.get_attr_amount(attr_name) for f in self.ingredients)

    def get_field_secondary_text(self):
        text = "Calories per serving: {cal: <4} Ingredients: {ing}"\
            .format(cal=self.get_calories()/self.serving_size,
                    ing=textwrap.shorten(', '.join([getattr(n.food, "name") for n in self.ingredients]),
                                         width=50, placeholder="..."))
        return text

    @classmethod
    def search_by_attribute(cls, session, search_string, field, only_template=False):
        if only_template:
            return session.query(cls). \
                filter(and_(
                       cls.is_template == True,
                       func.to_tsvector('english', getattr(cls, field)).match(search_string,
                                                                              postgresql_regconfig='english'))).all()
        return session.query(cls). \
            filter(
            func.to_tsvector('english', getattr(cls, field)).match(search_string, postgresql_regconfig='english')).all()


class Exercise(MixinGetByName, MixinSearch, db.Model):
    __tablename__ = 'exercise'
    __table_args__ = (CheckConstraint("tempo ~ '^((\d|X){4}|((\d{1,2}|X)-){3}(\d{1,2}|X))$'", name="tempo_check"),
                      {'extend_existing': True},
                      )

    id = Column(Integer, primary_key=True)
    weight_id = Column(Integer, ForeignKey('weight.id'))
    weight = relationship("Weight", back_populates="exercise")
    tempo = Column(String)
    pause = Column(postgresql.INT4RANGE)  # TODO test
    set_range = Column(postgresql.INT4RANGE)
    rep_range = Column(postgresql.INT4RANGE)
    notes = Column(Text)
    equipment = relationship(
        "Equipment",
        secondary=exercise_equipment_table,
        back_populates="exercises")
    tags = relationship(
        "Tag",
        secondary=exercise_tag_table,
        back_populates="exercises")
    training_exercises = relationship("TrainingExercise", back_populates="exercise")

    def get_field_secondary_text(self):
        if self.set_range.lower is None:
            sets = "None"
        elif self.set_range.upper is None:
            sets = str(self.set_range.lower) + "+"
        else:
            sets = str(self.set_range.lower) + "-"
            sets += str(self.set_range.upper) if self.set_range.upper_inc else str(self.set_range.upper-1)
        if self.rep_range.lower is None:
            reps = "None"
        elif self.rep_range.upper is None:
            reps = str(self.rep_range.lower) + "+"
        else:
            reps = str(self.rep_range.lower) + "-"
            reps += str(self.rep_range.upper) if self.rep_range.upper_inc else str(self.rep_range.upper-1)
        if getattr(self.pause, "lower", None) is None:
            pause = "None"
        elif self.pause.upper is None:
            pause = str(self.pause.lower) + "+"
        else:
            if self.pause.lower == self.pause.upper_inc:  # TODO test
                pause = str(self.pause.lower)
            else:
                pause = str(self.pause.lower) + "-"
                pause += str(self.pause.upper) if self.pause.upper_inc else str(self.pause.upper)
        if self.weight is not None:
            if self.weight.kilogram is not None:
                weight = str(self.weight.kilogram.lower) + "-" + str(self.weight.kilogram.upper)
            elif self.weight.BW:
                weight = "BW"
            else:
                weight = ""
            if self.weight.RM is not None:
                weight = str(self.weight.RM) + "RM = " + weight
            elif self.weight.percentage_range is not None:
                weight = str(self.weight.percentage_range.lower) + "-" + str(self.weight.percentage_range.upper) \
                         + "% of " + str(self.weight.RM) + " RM = " + weight
            if self.weight.band is not None:
                weight += " + " + self.weight.band
        else:
            weight = "None"
        weight = weight.strip("= ")
        weight = weight if weight != "" else "None"
        return "Sets: {sets: <8} Reps: {reps: <8} Tempo: {tempo: <8} Pause: {pause: <8} Weight: {weight} ".format(sets=sets, reps=reps, weight=weight, tempo=str(self.tempo), pause=pause)

    @classmethod
    def get_by_tag(cls, session, tags):
        return session.query(cls).join(cls.tags).filter(Tag.name.in_(tags)).all()

    @classmethod  # TODO check if it works when rows with type other than "exercise" are added
    def search_by_tag(cls, session, search_string):
        words = " & ".join(search_string.split())
        return session.query(Exercise). \
            join(Exercise.tags). \
            filter(and_(or_(func.to_tsvector('english', Tag.name).match(words, postgresql_regconfig='english'),
                            func.to_tsvector('english', Tag.description).match(words, postgresql_regconfig='english')),
                        Tag.type == "exercise")).all()

    @classmethod
    def search_by_equipment(cls, session, search_string):
        return session.query(Exercise). \
            join(Exercise.equipment). \
            filter(or_(func.to_tsvector('english', Equipment.name).match(search_string, postgresql_regconfig='english'),
                       func.to_tsvector('english', Equipment.description).match(search_string, postgresql_regconfig='english'))).all()

    @classmethod
    def search_by_weight(cls, session, search_string, field):
        return session.query(Exercise). \
            join(Exercise.weight). \
            filter(
            func.to_tsvector('english', getattr(Weight, field)).match(search_string, postgresql_regconfig='english')).all()


class Weight(db.Model):
    __tablename__ = 'weight'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    exercise = relationship("Exercise", back_populates="weight", uselist=False)
    RM = Column(Integer)
    percentage_range = Column(postgresql.NUMRANGE)
    kilogram = Column(postgresql.NUMRANGE)
    BW = Column(Boolean)
    band = Column(String)


class Equipment(db.Model, MixinGetByName):
    __tablename__ = 'equipment'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(Text)
    exercises = relationship(
        "Exercise",
        secondary=exercise_equipment_table,
        back_populates="equipment")


class Tag(db.Model, MixinGetByName):
    __tablename__ = 'tag'
    __table_args__ = (CheckConstraint("type ~* '^(exercise|recipe|food){1}$'", name="type_check"),
                      {'extend_existing': True},
                      )

    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(String)  # exercise/recipe/food
    description = Column(Text)
    exercises = relationship(
        "Exercise",
        secondary=exercise_tag_table,
        back_populates="tags")
    recipes = relationship(
        "Recipe",
        secondary=recipe_tag_table,
        back_populates="tags")
    foods = relationship(
        "Food",
        secondary=food_tag_table,
        back_populates="tags")


class Set(db.Model):
    __tablename__ = 'set'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    reps = Column(Integer)
    weight = Column(Numeric(precision=5, scale=2))
    is_PR = Column(Boolean, default=False)
    is_AMRAP = Column(Boolean, default=False)
    training_exercise_id = Column(Integer, ForeignKey('training_exercise.id'))


class Training(db.Model, MixinGetByName):
    __tablename__ = 'training'
    __table_args__ = (CheckConstraint("start < \"end\"", name="time_check"),
                      {'extend_existing': True},
                      )

    id = Column(Integer, primary_key=True)
    name = Column(String)
    start = Column(Time)
    end = Column(Time)
    day = relationship("Day", back_populates="training", uselist=False)
    training_exercises = relationship("TrainingExercise", cascade="save-update, merge, delete", back_populates="training")
    description = Column(Text)
    next = relationship("Training",
                        uselist=False,
                        foreign_keys='Training.next_id',
                        remote_side=[id],
                        backref=backref("prev", uselist=False))
    next_id = Column(Integer, ForeignKey('training.id'))
    is_first = Column(Boolean, default=False)
    is_template = Column(Boolean, default=False)
    training_schedule_id = Column(Integer, ForeignKey('training_schedule.id'))
    training_schedule = relationship("TrainingSchedule", back_populates="trainings")
    template_executions = relationship("Training",
                                       uselist=True,
                                       foreign_keys='Training.template_id',

                                       backref=backref("template", uselist=False, remote_side=[id]))
    template_id = Column(Integer, ForeignKey('training.id'))
    training_plan_history_id = Column(Integer, ForeignKey('training_plan_history.id'))
    training_plan_history = relationship("TrainingPlanHistory", back_populates="trainings")

    def get_exercises(self):
        exercises = []
        for exercise in self.training_exercises:
            exercises.append(exercise.get_superset())
        return exercises

    @classmethod
    def create_training_sessions(cls, s, templates):  # TREBA NAKONCI COMMITNUT PO POUZITI FUNKCIE
        training_sessions = []
        for i, template in enumerate(templates):
            training_session = Training(template=template)
            if i == 0:
                training_session.is_first = True
            else:
                training_sessions[i-1].next = training_session
            training_sessions.append(training_session)
            training_exercises = []
            s.add(training_session)
            s.flush()
            supersets = template.get_exercises()
            for superset in supersets:
                ex_ids = []
                for ex in superset:
                    ex_ids.append(ex.exercise_id)
                training_exercises.append(
                    TrainingExercise.create_superset(s, ex_ids, training_session.id))
        return training_sessions

    @classmethod
    def get_schedules_by_template(cls, session, template):
        schedules = session.query(Training).filter(and_(Training.template_id == template.id,
                                                        Training.is_first == True)).all()
        return schedules


class TrainingExercise(db.Model):
    __tablename__ = 'training_exercise'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    training_id = Column(Integer, ForeignKey('training.id'))
    exercise_id = Column(Integer, ForeignKey('exercise.id'))
    exercise = relationship("Exercise", back_populates="training_exercises")
    training = relationship("Training", back_populates="training_exercises")
    is_optional = Column(Boolean, default=False)
    superset_with = relationship("TrainingExercise",
                                 cascade="save-update, merge, delete",
                                 uselist=False,
                                 backref=backref("prev", uselist=False, remote_side=[id]))
    prev_training_exercise_id = Column(Integer, ForeignKey('training_exercise.id'))
    pause = Column(postgresql.INT4RANGE)
    sets = relationship("Set", cascade="save-update, merge, delete",)

    #  TODO: TEST
    @classmethod
    def create_superset(cls, session, exercise_ids, training_id):
        training = session.query(Training).filter(Training.id == training_id).first()
        training_exercises = [TrainingExercise() for _ in range(len(exercise_ids))]
        exercises = session.query(Exercise).filter(Exercise.id.in_(exercise_ids)).all()
        exercises = sort_to_match(exercise_ids, exercises)
        for i, ex in enumerate(exercises):
            training_exercises[i].exercise = ex
            if ex.set_range.upper is not None:
                sets = [Set(reps=ex.rep_range.upper) for _ in range(ex.set_range.upper)]
            else:
                sets = [Set(reps=ex.rep_range.lower) for _ in range(ex.set_range.lower)]
            training_exercises[i].sets = sets
            if i == 0:
                training.training_exercises.append(training_exercises[i])
            if i != len(exercises)-1:
                training_exercises[i].superset_with = training_exercises[i+1]
        return training_exercises

    def get_superset(self):
        exercises = [self]
        ex = self
        while ex.superset_with is not None:
            exercises.append(ex.superset_with)
            ex = ex.superset_with
        return exercises


class TrainingSchedule(db.Model, MixinGetByName):
    __tablename__ = 'training_schedule'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    name = Column(String)
    phase_id = Column(Integer, ForeignKey('phase.id'))
    phase = relationship("Phase", back_populates="training_schedules")
    description = Column(Text)
    trainings = relationship("Training", back_populates="training_schedule")


class Phase(db.Model, MixinGetByName):
    __tablename__ = 'phase'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    training_schedules = relationship("TrainingSchedule", back_populates="phase")
    training_plan_id = Column(Integer, ForeignKey('training_plan.id'))
    training_plan = relationship("TrainingPlan", back_populates="phases")
    name = Column(String)
    length = Column(postgresql.INT4RANGE)
    description = Column(Text)


class TrainingPlan(MixinGetByName, db.Model):
    __tablename__ = 'training_plan'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    description = Column(Text)
    phases = relationship("Phase", back_populates="training_plan")
    training_plan_history = relationship("TrainingPlanHistory", back_populates="training_plan")

    @classmethod
    def get_current(cls, session):
        return session.query(cls).join(cls.training_plan_history).filter(
           TrainingPlanHistory.end == None
        ).scalar()

    @classmethod  # TODO test with more t_p, phases, t_t in tables
    def get_schedules(cls, session, plan):
        return session.query(TrainingSchedule).select_from(TrainingPlan).\
            join(TrainingPlan.phases).\
            join(TrainingSchedule).\
            filter(plan.id == TrainingPlan.id).all()


class TrainingPlanHistory(db.Model):
    __tablename__ = 'training_plan_history'
    __table_args__ = (CheckConstraint("start < \"end\"", name="date_check"),
                      {'extend_existing': True},
                      )

    id = Column(Integer, primary_key=True)
    training_plan_id = Column(Integer, ForeignKey('training_plan.id'))
    training_plan = relationship("TrainingPlan", back_populates="training_plan_history")
    goals = relationship("Goal", back_populates="training_plan_history")
    start = Column(Date)
    end = Column(Date)
    description = Column(Text)  # TODO test
    trainings = relationship("Training", back_populates="training_plan_history")

    @classmethod
    def get_all(cls, session):  # TODO test
        return session.query(TrainingPlanHistory)\
            .join(TrainingPlanHistory.training_plan)\
            .group_by(TrainingPlanHistory.id, TrainingPlan.name)\
            .order_by(TrainingPlanHistory.start).all()


class Goal(MixinGetByName, db.Model):
    __tablename__ = 'goal'
    __table_args__ = (CheckConstraint("start_date < end_date", name="date_check"),
                      {'extend_existing': True},
                      )

    id = Column(Integer, primary_key=True)
    achieved = Column(Boolean, default=False)
    notes = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)
    training_plan_history_id = Column(Integer, ForeignKey('training_plan_history.id'))
    training_plan_history = relationship("TrainingPlanHistory", back_populates="goals")

    @classmethod
    def create_goal(cls, session, size):
        # TODO
        return







