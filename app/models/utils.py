def sort_to_match(ids, objects, attr="id"):
    """ Sorts objects by one of their attributes to match order of ids. Used when order of objects is
    needed to be retained and DB returns objects in "random" order.
    """
    object_map = {getattr(o, attr): o for o in objects}
    objects = [object_map[id] for id in ids]
    return objects

# RAW SQLALCHEMY, REQUIRES DECLARATIVE BASE
# def get_model_by_tablename(tablename):
#     """Return class reference mapped to table.
#     :param tablename: String with name of table.
#     :return: Class reference or None.
#     """
#
#     for c in Base._decl_class_registry.values():
#         if hasattr(c, '__tablename__') and c.__tablename__ == tablename:
#             return c
#
#
# def get_model(name):
#     return Base._decl_class_registry.get(name, None)
