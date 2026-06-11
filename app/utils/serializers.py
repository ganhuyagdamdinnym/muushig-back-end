def serialize_room(room):
    if room and "_id" in room:
        room["_id"] = str(room["_id"])
    return room