from sqlalchemy import Column, String, func, and_


class MixinGetByName(object):
    name = Column(String)

    @classmethod
    def get_by_name(cls, session, name):
        return session.query(cls).filter(cls.name == name).all()


class MixinSearch(object):

    @classmethod
    def search_by_attribute(cls, session, search_string, field):
        words = " & ".join(search_string.split())
        return session.query(cls). \
            filter(func.to_tsvector('english', getattr(cls, field)).match(words, postgresql_regconfig='english')).all()

    @classmethod
    def get_closest_matches(cls, session, search_value, field, delta):
        col = getattr(cls, field)
        return session.query(cls). \
            filter(and_(col >= search_value-delta, col <= search_value+delta))

