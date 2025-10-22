from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.dialects.postgresql import JSON

db = SQLAlchemy()


def is_better_cabin_possible(group_size):
    available_cabins = db.session.query(Cabin).filter(
        Cabin.is_locked == False,
        (Cabin.capacity - Cabin.occupied_places) == group_size
    ).all()
    return available_cabins

def get_member_group(member_id):
    token = db.session.query(User).filter(User.id == member_id).first().groupCode
    return db.session.query(User).filter(User.groupCode == token).all()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(50))
    groupCode = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    cabin_id = db.Column(db.Integer, default=None)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "groupCode": self.groupCode,
            "is_admin": self.is_admin,
            "cabin_id": self.cabin_id
        }


class Cabin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    capacity = db.Column(db.Integer)
    occupied_places = db.Column(db.Integer, default=0)
    members = db.Column(MutableList.as_mutable(JSON), default=list)
    is_locked = db.Column(db.Boolean, default=True)
    unlock_time = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "capacity": self.capacity,
            "occupied_places": self.occupied_places,
            "members": self.members,
            "is_locked": self.is_locked,
            "unlock_time": self.unlock_time
        }

    def add_member(self, member_id):
        group_members = get_member_group(member_id)
        group_size = len(group_members)
        free_capacity = self.capacity - self.occupied_places

        if free_capacity < group_size:
            raise ValueError("Group size exceeds available cabin capacity.")

        if free_capacity != group_size:
            better_cabins = is_better_cabin_possible(group_size)
            if better_cabins:
                raise ValueError(f"Cabins: {better_cabins} are better option")

        for member in group_members:
            self.members.append(member.id)
            member.cabin_id = self.id
            self.occupied_places += 1
        return None

    def remove_member(self, user_id):
        group_members = get_member_group(user_id)

        for member in group_members:
            self.members.remove(member.id) # member not in group?
            member.cabin_id = None
            self.occupied_places -= 1
            #todo obsluzyc przypadki ze zmiana grupy
        return None

    def check_unlock_condition(self):
        if self.unlock_time and datetime.utcnow() >= self.unlock_time:
            self.is_locked = False


