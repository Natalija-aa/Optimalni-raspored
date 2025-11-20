from datetime import time, date

class Obligation:
    def __init__(self, name, start_time, end_time, importance, repetition_type, date=None, start_date=None, days=None):
        self.name = name
        self.start_time = start_time
        self.end_time = end_time
        self.importance = importance
        self.repetition_type = repetition_type
        self.date = date #za ne
        self.start_date = start_date # za svaki
        self.days = days # za dani

    def __repr__(self):
        return f"Obligation({self.name}, {self.start_time}-{self.end_time}, Importance: {self.importance})"

class Exam:
    def __init__(self, subject_name, exam_date, start_time, duration_minutes, study_hours, color=None):
        self.subject_name = subject_name
        self.exam_date = exam_date
        self.start_time = start_time
        self.duration_minutes = duration_minutes
        self.study_hours = study_hours
        self.color = color
        self.plan = {} # blokovi za svaki dan

    def __repr__(self):
        return f"Exam({self.subject_name} on {self.exam_date} at {self.start_time})"

class Meal:
    def __init__(self, name, start_time, end_time):
        self.name = name
        self.start_time = start_time
        self.end_time = end_time

    def __repr__(self):
        return f"Meal({self.name}, {self.start_time}-{self.end_time})"

class Sleep:
    def __init__(self, start_time, end_time):
        self.start_time = start_time
        self.end_time = end_time

    def __repr__(self):
        return f"Sleep({self.start_time}-{self.end_time})"