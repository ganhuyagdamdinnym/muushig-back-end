def serialize_user(user):
    if user and "_id" in user:
        user["_id"] = str(user["_id"])
    return user