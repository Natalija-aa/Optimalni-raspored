from datetime import datetime, time, date, timedelta
from models import Obligation, Exam, Meal, Sleep

DANI_MAP = {
    "pon": 0, "uto": 1, "sri": 2, "čet": 3, "cet": 3,
    "pet": 4, "sub": 5, "ned": 6
}
DANI_REVERSE = {v: k for k, v in DANI_MAP.items()}


def unos_vremena(poruka):
    while True:
        try:
            vrijeme = input(poruka + " (HH.MM): ").strip()
            return datetime.strptime(vrijeme, "%H.%M").time()
        except ValueError:
            print("Pogrešan format vremena. Molimo unesite u formatu HH.MM.")


def unos_datuma(poruka):
    while True:
        try:
            datum = input(poruka + " (DD.MM.YYYY): ").strip()
            return datetime.strptime(datum, "%d.%m.%Y")
        except ValueError:
            print("Pogrešan format datuma. Molimo unesite u formatu DD.MM.YYYY.")


def get_time_range():
    start_date = unos_datuma("Unesi početni datum")
    end_date = unos_datuma("Unesi krajnji datum")
    return start_date, end_date


def get_sleep_schedule():
    spavanje_po_danu = {}

    isti_trajanje_sna = input("Da li želiš da svaki dan spavaš isti broj sati? (da/ne): ").strip().lower()

    if isti_trajanje_sna == "da":
        while True:
            try:
                trajanje_sna_str = input("Koliko sati obično spavaš? (npr. 7.5): ").replace(',', '.').strip()
                trajanje_sna = float(trajanje_sna_str)
                break
            except ValueError:
                print("Pogrešan format. Molimo unesite broj (npr. 7.5).")

        isti_spavanje_vrijeme = input("Da li ideš na spavanje u isto vrijeme svaki dan? (da/ne): ").strip().lower()

        if isti_spavanje_vrijeme == "da":
            vrijeme_spavanja = unos_vremena("Kada obično ideš na spavanje")
            # spavanje_do je ovde izvedeno iz trajanja sna
            spavanje_do = (datetime.combine(date.today(), vrijeme_spavanja) + timedelta(minutes=int(trajanje_sna * 60))).time()
            for i in range(7):
                spavanje_po_danu[i] = Sleep(vrijeme_spavanja, spavanje_do)
        else: # Ovde se dešavala greška
            print("Unesi vrijeme spavanja po danima:")
            for i in range(7):
                dan_label = DANI_REVERSE[i].capitalize()
                vrijeme_spavanja = unos_vremena(f"  Vrijeme spavanja za {dan_label}")
                # Sada eksplicitno definišemo spavanje_do
                spavanje_do = (datetime.combine(date.today(), vrijeme_spavanja) + timedelta(minutes=int(trajanje_sna * 60))).time()
                spavanje_po_danu[i] = Sleep(vrijeme_spavanja, spavanje_do)
    else: # ako ne želiš isti broj sati spavanja svaki dan
        ima_patern = input(
            "Da li postoji patern po danima (npr. par dana jedno vrijeme, par drugo)? (da/ne): ").strip().lower()
        preostali_dani = set(range(7))
        global_budjenje_time = None

        if ima_patern == "da":
            while preostali_dani:
                print("Preostali dani za unos:",
                      ", ".join([DANI_REVERSE[d].capitalize() for d in sorted(list(preostali_dani))]))
                dani_input_str = input("Unesi dane koji imaju isti ritam (npr. pon, cet, pet): ").lower()
                dani_unos = [d.strip() for d in dani_input_str.split(',')]
                dani_brojevi = [DANI_MAP[d] for d in dani_unos if d in DANI_MAP and DANI_MAP[d] in preostali_dani]

                if not dani_brojevi:
                    print("Nisu prepoznati dani ili su već uneti. Pokušaj ponovo.")
                    continue

                spavanje_od = unos_vremena("Vrijeme početka spavanja za ove dane")

                # Uvek pitaj za vreme buđenja za ovaj patern, ili ponudi korišćenje globalnog
                if global_budjenje_time is None:
                    spavanje_do_ovaj_patern = unos_vremena("Vrijeme buđenja (isto za sve odabrane dane u paternu)")
                    global_budjenje_time = spavanje_do_ovaj_patern # Postavi globalno vreme buđenja
                else:
                    # global_budjenje_time je već postavljeno, pitaj da li ga želi iskoristiti
                    reuse_global_wake = input(
                        f"Koristiti isto vrijeme buđenja ({global_budjenje_time.strftime('%H.%M')}) za ove dane? (da/ne): ").strip().lower()
                    if reuse_global_wake == "da":
                        spavanje_do_ovaj_patern = global_budjenje_time
                    else:
                        spavanje_do_ovaj_patern = unos_vremena("Vrijeme buđenja za ove dane (pojedinačno za patern)")

                # Dodeli vreme spavanja i buđenja svim danima u paternu
                for d in dani_brojevi:
                    spavanje_po_danu[d] = Sleep(spavanje_od, spavanje_do_ovaj_patern)
                    if d in preostali_dani:
                        preostali_dani.remove(d)
        else: # Ako nema paterna, unosi se za svaki dan posebno
            print("Unesi vrijeme spavanja i buđenja za svaki dan posebno:")
            for d in range(7):
                print(f"{DANI_REVERSE[d].capitalize()}:")
                spavanje_od = unos_vremena("  Vrijeme početka spavanja")
                # spavanje_do se unosi direktno
                spavanje_do = unos_vremena("  Vrijeme buđenja")
                spavanje_po_danu[d] = Sleep(spavanje_od, spavanje_do)

    return spavanje_po_danu


def get_meals():
    obroci_po_danu = {} #kljuc su dani
    podrazumevano_trajanje_obroka_min = 40 # 40min obrok

    isti_obroci_svaki_dan = input("Da li imate isti broj i vremena obroka svaki dan? (da/ne): ").strip().lower()

    if isti_obroci_svaki_dan == "da":
        while True:
            try:
                broj_obroka = int(input("Koliko obroka dnevno imaš? "))
                if broj_obroka < 0:
                    raise ValueError
                break
            except ValueError:
                print("Molimo unesite validan broj obroka (cijeli broj, npr. 3).")

        temp_obroci = []
        for i in range(broj_obroka):
            ime_obroka = input(f"Unesi naziv obroka {i + 1} (npr. Doručak, Ručak, Večera): ").strip()
            pocetak = unos_vremena(f"Unesi početak '{ime_obroka}'")
            end_dt = datetime.combine(date.today(), pocetak) + timedelta(minutes=podrazumevano_trajanje_obroka_min)
            kraj = end_dt.time()
            temp_obroci.append(Meal(ime_obroka, pocetak, kraj))

        for i in range(7): # Kopiraj iste obroke za svaki dan
            obroci_po_danu[i] = [Meal(m.name, m.start_time, m.end_time) for m in temp_obroci]

    else:
        ima_patern = input("Da li postoji patern u rasporedu obroka po danima? (da/ne): ").strip().lower()
        preostali_dani = set(range(7))

        if ima_patern == "da":
            while preostali_dani:
                print("\nPreostali dani za unos obroka:",
                      ", ".join([DANI_REVERSE[d].capitalize() for d in sorted(list(preostali_dani))]))
                dani_input_str = input("Unesi dane koji imaju isti patern obroka (npr. pon, sri, pet): ").lower()
                dani_unos = [d.strip() for d in dani_input_str.split(',')]
                dani_brojevi = [DANI_MAP[d] for d in dani_unos if d in DANI_MAP and DANI_MAP[d] in preostali_dani]

                if not dani_brojevi:
                    print("Nisu prepoznati dani ili su već uneti. Pokušaj ponovo.")
                    continue

                while True:
                    try:
                        broj_obroka_za_patern = int(input(f"Koliko obroka imaš za ove dane ({', '.join([DANI_REVERSE[d].capitalize() for d in dani_brojevi])})? "))
                        if broj_obroka_za_patern < 0:
                            raise ValueError
                        break
                    except ValueError:
                        print("Molimo unesite validan broj obroka.")

                temp_obroci_za_patern = []
                for i in range(broj_obroka_za_patern):
                    ime_obroka = input(f"  Unesi naziv obroka {i + 1} za ovaj patern: ").strip()
                    pocetak = unos_vremena(f"  Unesi početak '{ime_obroka}' za ovaj patern")
                    end_dt = datetime.combine(date.today(), pocetak) + timedelta(minutes=podrazumevano_trajanje_obroka_min)
                    kraj = end_dt.time()
                    temp_obroci_za_patern.append(Meal(ime_obroka, pocetak, kraj))

                for d in dani_brojevi:
                    obroci_po_danu[d] = [Meal(m.name, m.start_time, m.end_time) for m in temp_obroci_za_patern]
                    if d in preostali_dani: 
                        preostali_dani.remove(d)
        else:
            print("\nUnesi raspored obroka za svaki dan posebno:")
            for d_idx in range(7):
                dan_label = DANI_REVERSE[d_idx].capitalize()
                print(f"\n--- {dan_label} ---")
                while True:
                    try:
                        broj_obroka_za_dan = int(input(f"Koliko obroka imaš za {dan_label}? "))
                        if broj_obroka_za_dan < 0:
                            raise ValueError
                        break
                    except ValueError:
                        print("Molimo unesite validan broj obroka.")

                dnevni_obroci = []
                for i in range(broj_obroka_za_dan):
                    ime_obroka = input(f"  Unesi naziv obroka {i + 1} za {dan_label}: ").strip()
                    pocetak = unos_vremena(f"  Unesi početak '{ime_obroka}' za {dan_label}")
                    end_dt = datetime.combine(date.today(), pocetak) + timedelta(minutes=podrazumevano_trajanje_obroka_min)
                    kraj = end_dt.time()
                    dnevni_obroci.append(Meal(ime_obroka, pocetak, kraj))
                obroci_po_danu[d_idx] = dnevni_obroci
                preostali_dani.discard(d_idx) 

    return obroci_po_danu


def get_obligations(start_date, end_date):
    while True:
        try:
            broj_obaveza = int(input("Koliko obaveza imaš (npr. kafa, trening)? "))
            if broj_obaveza < 0:
                raise ValueError
            break
        except ValueError:
            print("Molimo unesite validan broj obaveza (cijeli broj).")

    all_obligations = []
    for i in range(broj_obaveza):
        naziv = input(f"Unesi naziv obaveze {i + 1}: ")
        while True:
            try:
                vaznost = int(input(f"Koliko je važna obaveza '{naziv}'? (1 = niska, 5 = kritična): "))
                if not (1 <= vaznost <= 5):
                    raise ValueError
                break
            except ValueError:
                print("Molimo unesite važnost između 1 i 5.")

        ponavljanje = input(f"Da li se '{naziv}' ponavlja? (ne, svaki, svaki2, svaki3, dani): ").strip().lower()

        if ponavljanje == "ne":
            datum = unos_datuma(f"Unesi datum za '{naziv}'").date()
            pocetak = unos_vremena(f"Početak obaveze '{naziv}'")
            kraj = unos_vremena(f"Kraj obaveze '{naziv}'")
            all_obligations.append(Obligation(naziv, pocetak, kraj, vaznost, ponavljanje, date=datum))
        elif ponavljanje in ["svaki", "svaki2", "svaki3"]:
            datum_pocetka_dt = unos_datuma(f"Od kog datuma se '{naziv}' ponavlja?")
            datum_pocetka = datum_pocetka_dt.date()
            pocetak = unos_vremena(f"Početak obaveze '{naziv}'")
            kraj = unos_vremena(f"Kraj obaveze '{naziv}'")
            interval = int(ponavljanje[-1]) if ponavljanje != "svaki" else 1

            current_day = start_date.date()  
            end_date_obj = end_date.date() 

            while current_day <= end_date_obj:
                # da li je u intervalu
                if current_day >= datum_pocetka and (current_day - datum_pocetka).days % interval == 0:
                    all_obligations.append(Obligation(naziv, pocetak, kraj, vaznost, ponavljanje, date=current_day,
                                                      start_date=datum_pocetka))
                current_day += timedelta(days=1)
        elif ponavljanje == "dani":
            print("Dani u sedmici: pon, uto, sri, čet, pet, sub, ned")
            dani_input_str = input(f"Koje dane u sedmici se '{naziv}' dešava? (razdvojene zarezom): ").lower()
            dani_unos = [d.strip() for d in dani_input_str.split(',')]
            dani_brojevi = [DANI_MAP[d] for d in dani_unos if d in DANI_MAP]

            if not dani_brojevi:
                print("Nisu prepoznati dani. Obaveza neće biti dodana.")
                continue

            pocetak = unos_vremena(f"Početak obaveze '{naziv}'")
            kraj = unos_vremena(f"Kraj obaveze '{naziv}'")

            current_day = start_date.date()  
            end_date_obj = end_date.date()  

            while current_day <= end_date_obj:
                if current_day.weekday() in dani_brojevi:
                    all_obligations.append(
                        Obligation(naziv, pocetak, kraj, vaznost, ponavljanje, date=current_day, days=dani_brojevi))
                current_day += timedelta(days=1)
        else:
            print("Nepoznata opcija ponavljanja. Preskačem ovu obavezu.")
    return all_obligations


def get_exams(start_date, end_date):
    while True:
        try:
            broj_ispita = int(input("Koliko ispita/kolokvijuma imaš? "))
            if broj_ispita < 0:
                raise ValueError
            break
        except ValueError:
            print("Molimo unesite validan broj ispita (cijeli broj).")

    ispiti = []
    boje_predmeta = {}
    boje_dostupne = ["orange", "red", "cyan", "lime", "magenta", "brown", "teal", "gold"]

    for i in range(broj_ispita):
        naziv = input(f"Unesi naziv predmeta {i + 1}: ")
        datum_ispita_dt = unos_datuma(f"Unesi datum ispita za {naziv}")
        vrijeme_ispita = unos_vremena(f"Unesi vrijeme početka ispita za {naziv}")
        while True:
            try:
                trajanje_ispita = int(input(f"Koliko minuta traje ispit za {naziv}? "))
                if trajanje_ispita <= 0:
                    raise ValueError
                break
            except ValueError:
                print("Molimo unesite validno trajanje ispita u minutama (cijeli broj > 0).")
        while True:
            try:
                sati_ucenja_str = input(f"Koliko sati trebaš učiti za {naziv}? (npr. 10.5): ").replace(',', '.').strip()
                sati_ucenja = float(sati_ucenja_str)
                if sati_ucenja <= 0:
                    raise ValueError
                break
            except ValueError:
                print("Molimo unesite validan broj sati učenja (npr. 10.5).")

        boja = boje_dostupne[i % len(boje_dostupne)]
        boje_predmeta[naziv] = boja

        schedule_start_date_obj = start_date.date()
        datum_ispita_obj = datum_ispita_dt.date()

        broj_dana_do_ispita = (datum_ispita_obj - schedule_start_date_obj).days

        study_days_available = 0 

        if broj_dana_do_ispita < 0:
            print(
                f"Datum ispita za {naziv} je prije početnog datuma rasporeda ({schedule_start_date_obj.strftime('%d.%m.%Y')}). Preskačem planiranje učenja za ovaj ispit.")
            continue
        elif broj_dana_do_ispita == 0:
            print(f"Ispit za {naziv} je na početni datum rasporeda. Neće biti planiranih blokova učenja prije ispita.")
            study_days_available = 1  # ako je ispit taj dan onda mozes uciti
        else:
            study_days_available = broj_dana_do_ispita

        if sati_ucenja > 0 and study_days_available == 0:
            study_days_available = 1  # ako je dan ispita jedini dan za uciti moze se uciti

        exam_obj = Exam(naziv, datum_ispita_obj, vrijeme_ispita, trajanje_ispita, sati_ucenja, color=boja)

        if sati_ucenja > 0 and study_days_available > 0:
            ukupno_blokova = int(sati_ucenja * 60 // 50)  # 50min ucenje
            if ukupno_blokova == 0:
                ukupno_blokova = 1

            blokovi_po_danu = ukupno_blokova // study_days_available
            ostatak = ukupno_blokova % study_days_available

            for j in range(study_days_available):
                dan = schedule_start_date_obj + timedelta(days=j)
                broj_blokova = blokovi_po_danu + (1 if j < ostatak else 0)

                blokovi = []
                for _ in range(broj_blokova):
                    blokovi.extend(
                        ["Učenje"] * 5 + ["Pauza"])  # 50min 10min, ucenje pauza
                exam_obj.plan[dan] = blokovi

        ispiti.append(exam_obj)
    return ispiti, boje_predmeta