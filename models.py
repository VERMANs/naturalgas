from app import db


# Area
class Area(db.Model):
    __tablename__ = "area"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255))
    gasprice = db.Column(db.Float)
    is_used = db.Column(db.CHAR(255))


# Manager
class Management(db.Model):
    __tablename__ = "manager"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.VARCHAR(30))
    password = db.Column(db.VARCHAR(30))
    type = db.Column(db.Integer)
    area_id = db.Column(db.Integer)


# User
class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.VARCHAR(255))
    name = db.Column(db.VARCHAR(12))
    area_id = db.Column(db.Integer)


# Dosage
class Dosage(db.Model):
    __tablename__ = "dosage"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer)
    used = db.Column(db.Float)
    paid = db.Column(db.Float)


# Accout
class Accout(db.Model):
    __tablename__ = "account"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer)
    balance = db.Column(db.Float)
