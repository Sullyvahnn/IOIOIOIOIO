from datetime import datetime, time, timedelta

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    Login = db.Column(db.String, primary_key=True)
    Password = db.Column(db.String(128), nullable=False)
    Name = db.Column(db.String(50))
    Stanowisko = db.Column(db.String(50))

    def to_dict(self):
        return {
            "login": self.Login,
            "password": self.Password,
            "name": self.Name,
            "stanowisko": self.Stanowisko
        }

def auth(login, password):
    user = User.query.filter_by(Login=login).first()
    if user is not None and user.Password == password:
        return True
    return False


def addUser(login, password, name, stanowisko):
    try:
        new_user = User(
            Login=login,
            Password=password,
            Name=name,
            Stanowisko=stanowisko
        )
        db.session.add(new_user)
        db.session.commit()
        return {"message": "User added successfully"}
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}



class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Login = db.Column(db.String, db.ForeignKey('user.Login'), nullable=False)
    Data = db.Column(db.Date, nullable=False)
    GodzinaStart = db.Column(db.Time, nullable=False)
    GodzinaKoniec = db.Column(db.Time, nullable=True)
    Projekt = db.Column(db.String(100), nullable=False)

    def __init__(self, login, data, godzina_start, godzina_koniec, projekt):
        self.Login = login
        self.Data = data
        self.GodzinaStart = godzina_start
        self.GodzinaKoniec = godzina_koniec
        self.Projekt = projekt


    def to_dict(self):
        return {
            "Login": self.Login,
            "Data": self.Data,
            "GodzinaStart": self.GodzinaStart,
            "GodzinaKoniec": self.GodzinaKoniec,
            "Projekt": self.Projekt,
        }

    def startWorking(self, login, projekt):
        try:
            new_report = Report(
                login=login,
                data=datetime.now().date(),
                godzina_start=datetime.now().time(),
                godzina_koniec=None,
                projekt=projekt
            )
            db.session.add(new_report)
            db.session.commit()
            return {"message": "Work started successfully"}
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}

    def stopWorking(login):
        try:
            reports = Report.query.filter_by(Login=login, GodzinaKoniec=None).all()

            for report in reports:
                report.GodzinaKoniec = time.now().time()

            db.session.commit()
            return {"message": "Zakończono pracę"}
        except Exception as e:
            # Rollback in case of an error
            db.session.rollback()
            return {"error": str(e)}

    def closeAllAndReopen(self):
        try:
            reports = Report.query.filter_by(GodzinaKoniec=None).all()
            for report in reports:
                report.GodzinaKoniec = time.combine( time(23, 59, 59))

                # Open a new report for today
                new_report = Report(report.Login, report.Data + timedelta(days=1), time(0, 0, 0), None, report.Projekt)
                db.session.add(new_report)

            db.session.commit()
            return {"message": "Poprawnie zamknięto wszystkie raporty i otwarto nowe na dzisiaj"}
        except Exception as e:
            # Rollback in case of an error
            db.session.rollback()
            return {"error": str(e)}

    def get_reports_with_user_data(login):
        try:
            # Pobierz raporty, gdzie Login == login
            reports = Report.query.filter_by(Login=login).all()
            result = []
            for report in reports:
                user = User.query.get(report.Login)
                report_data = report.to_dict()
                user_data = user.to_dict() if user else {}
                result.append({**report_data, **user_data})
            return result
        except Exception as e:
            return {"error": str(e)}