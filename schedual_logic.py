from datetime import datetime, timedelta, time, date
from models import Obligation, Exam, Meal, Sleep
from data_input import DANI_REVERSE

def vrijeme_u_minute(v):
    return v.hour * 60 + v.minute

# dolazi do preklapanja, pomjeram vrijeme budjenja
def pomjeri_budjenje_unaprijed(day_index, max_start_time, sleep_schedule_for_day):
    original_sleep = sleep_schedule_for_day.start_time
    original_wake = sleep_schedule_for_day.end_time

    wake_dt = datetime.combine(date.today(), original_wake)
    max_start_dt = datetime.combine(date.today(), max_start_time)

    if wake_dt <= max_start_dt:
        return sleep_schedule_for_day

    # pomjeri
    for pomak in range(0, 180, 10):  # do 3 sata
        new_wake_dt = wake_dt - timedelta(minutes=pomak)
        if new_wake_dt <= max_start_dt:
            sleep_schedule_for_day.end_time = new_wake_dt.time()
            return sleep_schedule_for_day
    return sleep_schedule_for_day  # ako nema promjene

#pomjeram vrijeme odlaska na spavanje
def pomjeri_spavanje_unaprijed(day_index, min_end_dt, sleep_schedule_for_day):
    if isinstance(min_end_dt, time):
        min_end_dt = datetime.combine(date.today(), min_end_dt)

    original_sleep_time = sleep_schedule_for_day.start_time
    original_sleep_dt = datetime.combine(date.today(), original_sleep_time)

    if sleep_schedule_for_day.end_time < original_sleep_time:
        original_sleep_dt += timedelta(days=1)

    if min_end_dt >= original_sleep_dt: 
        return sleep_schedule_for_day

    # pomjeranje spavanja
    for pomak in range(0, 180, 10):  # do 3 sata
        new_sleep_dt = original_sleep_dt + timedelta(minutes=pomak)
        if new_sleep_dt >= min_end_dt:
            sleep_schedule_for_day.start_time = new_sleep_dt.time()
            return sleep_schedule_for_day
    return sleep_schedule_for_day  

# ima li konflikta 
def postoji_konflikt(activity_start_time, activity_duration_minutes, daily_dummy_schedule):
    start_min = vrijeme_u_minute(activity_start_time)   # novi pocetak
    end_min = start_min + activity_duration_minutes
    for blok in range(start_min // 10, (end_min - 1) // 10 + 1):  # po 10 min
        if 0 <= blok < 144 and daily_dummy_schedule[blok] != "Slobodno":
            return True
    return False

# pomjeranje obroka ako postoji konflikt
def pomjeri_obrok(meal_obj, daily_dummy_schedule, day_date):
    original_start = meal_obj.start_time
    original_end = meal_obj.end_time
    trajanje = (datetime.combine(day_date, original_end) - datetime.combine(day_date, original_start)).seconds // 60
    if trajanje < 0:  # ponoc
        trajanje = (datetime.combine(day_date + timedelta(days=1), original_end) - datetime.combine(day_date,
                                                                                                    original_start)).seconds // 60

    if not postoji_konflikt(original_start, trajanje, daily_dummy_schedule):
        return original_start, original_end

    for pomak in range(0, 240, 10):  # do 4 sata
        new_start_dt = datetime.combine(day_date, original_start) + timedelta(minutes=pomak)
        new_end_dt = new_start_dt + timedelta(minutes=trajanje)
        new_p = new_start_dt.time()
        new_k = new_end_dt.time()

        # da ne predjje u novi dan
        if original_start <= original_end and new_p > new_k:
            continue

        if not postoji_konflikt(new_p, trajanje, daily_dummy_schedule):
            return new_p, new_k

    # pomjeri unazad
    for pomak in range(10, 240, 10):  
        new_start_dt = datetime.combine(day_date, original_start) - timedelta(minutes=pomak)
        if new_start_dt.date() != day_date:  
            if original_start <= original_end:  
                break

        new_end_dt = new_start_dt + timedelta(minutes=trajanje)
        new_p = new_start_dt.time()
        new_k = new_end_dt.time()

        if original_start > original_end and new_p <= new_k:
            continue

        if not postoji_konflikt(new_p, trajanje, daily_dummy_schedule):
            return new_p, new_k

    return original_start, original_end  

# raspored
def generate_schedule(start_date, end_date, spavanje_po_danu, obroci_po_danu, obligations_input, exams_input):
    dani = []
    raspored = []
    current_day = start_date

    # sortiranje po vaznosti
    obligations_sorted = sorted(obligations_input, key=lambda x: -x.importance)
    # ispiti se sortiraju prvo datum pa vrijeme uceja
    exams_sorted = sorted(
        exams_input,
        key=lambda x: (
            x.exam_date,
            -sum(1 for blok_list in x.plan.values() for aktivnost in blok_list if aktivnost == "Učenje")
        )
    )

    all_meals_by_day = {} 

    while current_day <= end_date:
        # fiksni dogadjaji i inicijalni konflikti
        daily_dummy_schedule = ["Slobodno"] * 144  # 24 * 6(10 min) = 144
        day_of_week_index = current_day.weekday()  # 0=pon, ..., 6=ned

        # temp spavanje
        current_day_sleep_schedule = spavanje_po_danu[day_of_week_index]
        temp_sleep = Sleep(current_day_sleep_schedule.start_time, current_day_sleep_schedule.end_time)

        # ispiti sa spremanjem, putom i povratkom
        exams_today = [e for e in exams_sorted if e.exam_date == current_day.date()]
        for exam in exams_today:
            exam_start_dt = datetime.combine(current_day, exam.start_time)
            exam_end_dt = exam_start_dt + timedelta(minutes=exam.duration_minutes)

            # prije ispita - spremanje(60-30 min before)
            prep_start = exam_start_dt - timedelta(minutes=60)
            prep_end = exam_start_dt - timedelta(minutes=30)
            if prep_start.date() == current_day.date():  
                temp_sleep = pomjeri_budjenje_unaprijed(day_of_week_index, prep_start.time(), temp_sleep)
                for block in range(vrijeme_u_minute(prep_start.time()) // 10,
                                   vrijeme_u_minute(prep_end.time()) // 10):
                    if 0 <= block < 144:
                        daily_dummy_schedule[block] = "Spremanje"

            # put do (30-0 min)
            travel_start = prep_end
            travel_end = exam_start_dt
            if travel_start.date() == current_day.date():  
                for block in range(vrijeme_u_minute(travel_start.time()) // 10,
                                   vrijeme_u_minute(travel_end.time()) // 10):
                    if 0 <= block < 144:
                        daily_dummy_schedule[block] = "Put"

            # ispit
            for block in range(vrijeme_u_minute(exam_start_dt.time()) // 10,
                               vrijeme_u_minute(exam_end_dt.time()) // 10):
                if 0 <= block < 144:
                    daily_dummy_schedule[block] = f"{exam.subject_name} (Ispit)"

            # povratak (30 min)
            return_start = exam_end_dt
            return_end = exam_end_dt + timedelta(minutes=30)
            if return_end.date() == current_day.date():  
                for block in range(vrijeme_u_minute(return_start.time()) // 10,
                                   vrijeme_u_minute(return_end.time()) // 10):
                    if 0 <= block < 144:
                        daily_dummy_schedule[block] = "Povratak"
            temp_sleep = pomjeri_spavanje_unaprijed(day_of_week_index, return_end, temp_sleep)

        # obaveze sa putem i povratkom
        obligations_today = [o for o in obligations_sorted if o.date == current_day.date()]
        for ob in obligations_today:
            ob_start_dt = datetime.combine(current_day, ob.start_time)
            ob_end_dt = datetime.combine(current_day, ob.end_time)

            # spremanje prije (60-30 min)
            prep_start = ob_start_dt - timedelta(minutes=60)
            prep_end = ob_start_dt - timedelta(minutes=30)
            if prep_start.date() == current_day.date():
                temp_sleep = pomjeri_budjenje_unaprijed(day_of_week_index, prep_start.time(), temp_sleep)
                for block in range(vrijeme_u_minute(prep_start.time()) // 10,
                                   vrijeme_u_minute(prep_end.time()) // 10):
                    if 0 <= block < 144:
                        daily_dummy_schedule[block] = "Spremanje"

            # put do 30 min
            travel_start = prep_end
            travel_end = ob_start_dt
            if travel_start.date() == current_day.date():
                for block in range(vrijeme_u_minute(travel_start.time()) // 10,
                                   vrijeme_u_minute(travel_end.time()) // 10):
                    if 0 <= block < 144:
                        daily_dummy_schedule[block] = "Put"

            # obaveza
            for block in range(vrijeme_u_minute(ob_start_dt.time()) // 10,
                               vrijeme_u_minute(ob_end_dt.time()) // 10):
                if 0 <= block < 144:
                    daily_dummy_schedule[block] = ob.name

            #povratak
            return_start = ob_end_dt
            return_end = ob_end_dt + timedelta(minutes=30)
            if return_end.date() == current_day.date():
                for block in range(vrijeme_u_minute(return_start.time()) // 10,
                                   vrijeme_u_minute(return_end.time()) // 10):
                    if 0 <= block < 144:
                        daily_dummy_schedule[block] = "Povratak"
            temp_sleep = pomjeri_spavanje_unaprijed(day_of_week_index, return_end, temp_sleep)

        # obroci
        adjusted_meals_today = []
        day_of_week_index = current_day.weekday()  

        # obroci za dan
        current_day_meals = obroci_po_danu.get(day_of_week_index, [])

        for meal in current_day_meals: 
            adjusted_start, adjusted_end = pomjeri_obrok(meal, daily_dummy_schedule, current_day.date())
            adjusted_meals_today.append(Meal(meal.name, adjusted_start, adjusted_end))
            #ako ima pomjeranja
            meal_duration = (datetime.combine(current_day, adjusted_end) - datetime.combine(current_day,
                                                                                            adjusted_start)).seconds // 60
            if meal_duration < 0:  
                meal_duration = (datetime.combine(current_day + timedelta(days=1), adjusted_end) - datetime.combine(
                    current_day, adjusted_start)).seconds // 60

            for block in range(vrijeme_u_minute(adjusted_start) // 10,
                               (vrijeme_u_minute(adjusted_start) + meal_duration - 1) // 10 + 1):
                if 0 <= block < 144:
                    daily_dummy_schedule[block] = meal.name  #ime obroka
        all_meals_by_day[current_day.date()] = adjusted_meals_today

        # zavrsni raspored
        final_daily_schedule = []
        blok_indexi = {exam.subject_name: 0 for exam in exams_input}
        blokovi_dana = {
            exam.subject_name: exam.plan.get(current_day.date(), [])
            for exam in exams_input
        }

        # kraj ispita
        latest_exam_end = None
        for exam in exams_today:
            exam_end_dt = datetime.combine(current_day, exam.start_time) + timedelta(minutes=exam.duration_minutes)
            if latest_exam_end is None or exam_end_dt > latest_exam_end:
                latest_exam_end = exam_end_dt

        # 2 sata poslije ispita se ne uci
        study_block_until = latest_exam_end + timedelta(hours=2) if latest_exam_end else None

        for block_num in range(144):  
            current_block_start_dt = datetime.combine(current_day, datetime.min.time()) + timedelta(
                minutes=block_num * 10)
            current_block_end_dt = current_block_start_dt + timedelta(minutes=10)
            current_block_start_time = current_block_start_dt.time()
            activity_added = False

            # spavanje
            sleep_start_min = vrijeme_u_minute(temp_sleep.start_time)
            sleep_end_min = vrijeme_u_minute(temp_sleep.end_time)

            if temp_sleep.start_time <= temp_sleep.end_time:  
                if sleep_start_min <= current_block_start_dt.hour * 60 + current_block_start_dt.minute < sleep_end_min:
                    final_daily_schedule.append("Spavanje")
                    activity_added = True
            else:  
                if current_block_start_dt.hour * 60 + current_block_start_dt.minute >= sleep_start_min or \
                        current_block_start_dt.hour * 60 + current_block_start_dt.minute < sleep_end_min:
                    final_daily_schedule.append("Spavanje")
                    activity_added = True

            # velik prioritet i vec je u dummy scheduale
            if not activity_added and daily_dummy_schedule[block_num] != "Slobodno":
                final_daily_schedule.append(daily_dummy_schedule[block_num])
                activity_added = True

            # obroci, provjera, trebalo bi da je ok u dummy schedule
            if not activity_added:
                for meal_obj in all_meals_by_day.get(current_day.date(), []):  
                    meal_start_dt_curr_day = datetime.combine(current_day, meal_obj.start_time)
                    meal_end_dt_curr_day = datetime.combine(current_day, meal_obj.end_time)

                    if meal_obj.start_time > meal_obj.end_time:
                        meal_end_dt_curr_day += timedelta(days=1)

                    if meal_start_dt_curr_day <= current_block_start_dt < meal_end_dt_curr_day:
                        final_daily_schedule.append(meal_obj.name)  
                        activity_added = True
                        break

            # ucenje
            if not activity_added and 8 <= current_block_start_time.hour < 22:  #  moze se uciti samo od 8 do 22
                for exam in exams_sorted:
                    subject_name = exam.subject_name
                    learning_blocks_for_day = blokovi_dana.get(subject_name, [])

                    if blok_indexi[subject_name] < len(learning_blocks_for_day):
                        aktivnost = learning_blocks_for_day[blok_indexi[subject_name]]

                        if study_block_until and current_block_start_dt < study_block_until:
                            continue

                        if aktivnost == "Učenje":
                            dani_do_ispita = (exam.exam_date - current_day.date()).days
                            # ako je blizu dana ispita priorite ucenjaje velik
                            if dani_do_ispita >= 0 and dani_do_ispita <= 2:  
                                final_daily_schedule.append(subject_name + " (Optimizovano)")
                                blok_indexi[subject_name] += 1
                                activity_added = True
                                break  
                            elif daily_dummy_schedule[
                                block_num] == "Slobodno": 
                                final_daily_schedule.append(subject_name + " (Optimizovano)")
                                blok_indexi[subject_name] += 1
                                activity_added = True
                                break
                        elif aktivnost == "Pauza" and daily_dummy_schedule[block_num] == "Slobodno":
                            final_daily_schedule.append("Pauza")
                            blok_indexi[subject_name] += 1
                            activity_added = True
                            break  
                        
            # slobodno vrijeme, najmanji prioritet
            if not activity_added:
                final_daily_schedule.append("Slobodno")

        raspored.append(final_daily_schedule)
        dani.append(current_day.strftime("%a %d.%m"))
        current_day += timedelta(days=1)

    return dani, raspored, all_meals_by_day, temp_sleep 