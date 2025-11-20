from data_input import get_time_range, get_sleep_schedule, get_meals, get_obligations, get_exams
from schedual_logic import generate_schedule
from visualization import visualize_schedule

def main():
    print("Dobrodošli u planer rasporeda!")

    start_date, end_date = get_time_range()

    spavanje_po_danu = get_sleep_schedule()

    obroci_po_danu = get_meals() 

    obligations_input = get_obligations(start_date, end_date)

    exams_input, colors_by_subject = get_exams(start_date, end_date)

    print("\nGenerisanje rasporeda...")
    dani, raspored, all_meals_by_day, final_sleep_schedules = generate_schedule(
        start_date, end_date, spavanje_po_danu, obroci_po_danu, obligations_input, exams_input
    )

    print("Vizualizacija rasporeda...")
    visualize_schedule(dani, raspored, exams_input, obligations_input, all_meals_by_day, colors_by_subject)
    print("Raspored generisan i prikazan!")

if __name__ == "__main__":
    main()