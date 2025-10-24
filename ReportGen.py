
import matplotlib.pyplot as plt
import numpy as np
import math
from flask import Flask, current_app
from models import User, Report, db
from datetime import datetime as _dt
from typing import Optional
from datetime import datetime, timedelta, time


class ReportGen:
    def __init__(self, db_path: Optional[str] = None, app: Optional[Flask] = None):
        self.db_path = db_path
        self.app = app

    def generate_report(self, login: str):
        """
        If self.app is provided, use its app_context(). Otherwise require the caller
        to have an active Flask app context. Returns matplotlib.figure.Figure.
        """
        if self.app is not None:
            with self.app.app_context():
                return self._generate_report(login)
        else:
            # verify we have an active app context
            try:
                _ = current_app.name
            except RuntimeError:
                raise RuntimeError(
                    "No Flask application context. Either:\n"
                    "1) pass a Flask app instance to ReportGen(..., app=app), or\n"
                    "2) call generate_report() inside `with app.app_context():`."
                )
            return self._generate_report(login)

    def _generate_report(self, login: str):
        # Retrieve user via model (requires Flask app context)
        user = User.query.get(login)
        response_text = f"Imię: {user.Name}\nStanowisko: {user.Stanowisko}\nlogin: f{user.Login}"

        if not user:
            raise ValueError(f"No user found for login: {login}")

        today = datetime.now().date()
        since_date = today - timedelta(days=31)

        reports = (
            Report.query
            .filter(Report.Login == login, Report.Data >= since_date)
            .order_by(Report.Data)
            .all()
        )

        if not reports:
            raise ValueError(f"No report data for login {login} in the last 31 days")

        project_data = {}
        for rpt in reports:
            rpt_date = rpt.Data
            project = rpt.Projekt

            start_time = rpt.GodzinaStart
            end_time = rpt.GodzinaKoniec or _dt.now().time()

            try:
                start_dt = datetime.combine(rpt_date, start_time)
                end_dt = datetime.combine(rpt_date, end_time)
                delta = end_dt - start_dt
                hours_spent = max(0.0, delta.total_seconds() / 3600.0)
            except Exception:
                continue

            date_str = rpt_date.isoformat()
            project_data.setdefault(project, {})
            project_data[project][date_str] = project_data[project].get(date_str, 0.0) + hours_spent

        if not project_data:
            raise ValueError(f"No valid time entries for login {login} in the last 31 days")

        # Prepare stacked bar plot per date
        fig, ax = plt.subplots(figsize=(15, 8))

        projects = list(project_data.keys())

        # sorted unique dates across all projects
        all_dates = sorted({d for pd in project_data.values() for d in pd.keys()})
        x = np.arange(len(all_dates))
        width = 0.6

        # stack bars: keep running bottom
        bottom = np.zeros(len(all_dates))
        for project in projects:
            heights = np.array([project_data[project].get(d, 0.0) for d in all_dates])
            ax.bar(x, heights, width, bottom=bottom, label=project, alpha=0.9)
            bottom = bottom + heights
        
        totals_per_day = bottom  # bottom now contains stacked totals per date
        max_total = float(totals_per_day.max()) if len(totals_per_day) > 0 else 0.0
        if max_total <= 0:
            y_max = 1.0
        else:
            y_max = math.ceil(max_total * 1.1)  # 10% headroom, rounded up to whole hour
        
        ax.set_ylim(0, y_max)

        ax.set_xlabel('Date')
        ax.set_ylabel('Hours Spent')
        ax.set_title(f'Daily Time Spent per Project (Last 31 Days) - {login} ({user.Name} {user.Stanowisko})')
        ax.set_xticks(x)
        ax.set_xticklabels([d for d in all_dates], rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()

        return response_text, fig
    
if __name__ == "__main__":
    # Example: create minimal Flask app and initialize db, then call generate_report
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():

        u1 = User(
            Login       ='test@gmail.com',
            Password    ='haslo',
            Name        ='Imie',
            Stanowisko  ='Wozny'
        )

        existing = User.query.filter_by(
            Login       =u1.Login,
            Password    =u1.Password,
            Name        =u1.Name,
            Stanowisko  =u1.Stanowisko
        ).first()

        if not existing:
            db.session.add(u1)
        sample_entries = [
            Report(
            login           ='test@gmail.com',
            data            =_dt.strptime('2025-10-24', '%Y-%m-%d').date(),
            godzina_start   =time(9,15),
            godzina_koniec  =time(12,3),
            projekt         ='Projekt A'
            ),
            Report(
            login           ='test@gmail.com',
            data            =_dt.strptime('2025-10-24', '%Y-%m-%d').date(),
            godzina_start   =time(12,15),
            godzina_koniec  =time(16,50),
            projekt         ='Projekt B'
            ),
            Report(
            login           ='test@gmail.com',
            data            =_dt.strptime('2025-10-24', '%Y-%m-%d').date(),
            godzina_start   =time(17,9),
            godzina_koniec  =time(20,17),
            projekt         ='Projekt C'
            ),
            Report(
            login           ='test@gmail.com',
            data            =_dt.strptime('2025-10-1', '%Y-%m-%d').date(),
            godzina_start   =time(17,9),
            godzina_koniec  =time(20,17),
            projekt         ='Projekt C'
            ),
            Report(
            login           ='test@gmail.com',
            data            =_dt.strptime('2025-9-24', '%Y-%m-%d').date(),
            godzina_start   =time(17,9),
            godzina_koniec  =time(20,17),
            projekt         ='Projekt C'
            ),
            Report(
            login           ='test@gmail.com',
            data            =_dt.strptime('2025-9-24', '%Y-%m-%d').date(),
            godzina_start   =time(10,9),
            godzina_koniec  =time(15,10),
            projekt         ='Projekt A'
            ),
            Report(
            login           ='test@gmail.com',
            data            =_dt.strptime('2025-9-24', '%Y-%m-%d').date(),
            godzina_start   =time(6,9),
            godzina_koniec  =time(9,50),
            projekt         ='Projekt C'
            ),
        ]
        for report in sample_entries:
            existing = Report.query.filter_by(
                Login=report.Login,
                Data=report.Data,
                GodzinaStart=report.GodzinaStart,
                Projekt=report.Projekt
            ).first()

            if not existing:
                db.session.add(report)
        db.session.commit()

        rg = ReportGen(app=app)
        text,fig = rg.generate_report('test@gmail.com')
        print(text)
        fig.savefig('jdoe_report.png')