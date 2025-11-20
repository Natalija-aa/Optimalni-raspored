import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def visualize_schedule(dani, raspored, all_exams, all_obligations, all_meals_by_day, colors_by_subject):
    
    boje = {
        "Spavanje": "blue",
        "Spremanje (Jutro)": "salmon",
        "Spremanje (Veče)": "lightcoral",
        "Obrok": "yellow",
        "Slobodno": "purple",
        "Pauza": "lightgray",
        "Spremanje": "salmon", 
        "Put": "darkgray",
        "Povratak": "lightblue"
    }

    # boje ispita i ucenja
    for day_date, meals_list in all_meals_by_day.items():
        for meal in meals_list:
            if meal.name not in boje:
                boje[meal.name] = "yellow"  # svi zuti ali razlicita imena

    # ispit
    for exam in all_exams:
        boje[exam.subject_name + " (Ispit)"] = "black" 
        if exam.color: # ucenje
            boje[exam.subject_name + " (Optimizovano)"] = exam.color

    boje_obaveza_dostupne = [
        "pink", "lightgreen", "lightblue", "lightyellow", "plum", "khaki", "lavender", "peachpuff",
        "lightcyan", "thistle", "wheat", "powderblue", "moccasin", "honeydew", "azure"
    ]
    assigned_obligation_colors = {}
    color_index = 0
    for ob in sorted(all_obligations, key=lambda x: -x.importance): 
        if ob.name not in assigned_obligation_colors:
            if ob.importance >= 4:
                assigned_obligation_colors[ob.name] = "crimson" # velika vaznost
            elif ob.importance == 3:
                assigned_obligation_colors[ob.name] = "orange" # srednja vaznost
            else:
                assigned_obligation_colors[ob.name] = boje_obaveza_dostupne[color_index % len(boje_obaveza_dostupne)]
                color_index += 1
    boje.update(assigned_obligation_colors)


    fig, ax = plt.subplots(figsize=(14, len(dani) * 0.5))

    for i, day_label in enumerate(dani):
        for j, aktivnost in enumerate(raspored[i]):
            ax.barh(i, 1 / 6, left=j * (1 / 6), color=boje.get(aktivnost, "gray"))

    ax.set_yticks(range(len(dani)))
    ax.set_yticklabels(dani)
    ax.set_xlabel("Vrijeme (po 10 min)")
    ax.set_title("Raspored po danima (10-minutni intervali)")

    # X osa sati
    xticks = []
    xticklabels = []
    for i in range(144): 
        sat = i // 6
        minuta = (i % 6) * 10
        xticks.append(i * (1 / 6))
        if minuta == 0:
            xticklabels.append(f"{sat:02d}:00")
        else:
            xticklabels.append("") 

    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels, fontsize=7)
    ax.set_xlim(0, 24) #24h
    ax.set_ylim(-0.5, len(dani) - 0.5) 

    # legenda
    unique_activities = sorted(list(set(item for sublist in raspored for item in sublist)))
    legend_patches = []
    for activity_name in unique_activities:
        if activity_name in boje:
            legend_patches.append(mpatches.Patch(color=boje[activity_name], label=activity_name))
        elif "(Optimizovano)" in activity_name and activity_name.replace(" (Optimizovano)", "") in colors_by_subject:
             legend_patches.append(mpatches.Patch(color=colors_by_subject[activity_name.replace(" (Optimizovano)", "")], label=activity_name))
        elif "(Ispit)" in activity_name:
             legend_patches.append(mpatches.Patch(color="black", label=activity_name))


    # spremanja
    final_legend_patches = []
    seen_labels = set()
    for patch in legend_patches:
        if patch.get_label() == "Spremanje" and ("Spremanje (Jutro)" in seen_labels or "Spremanje (Veče)" in seen_labels):
            continue
        if patch.get_label() not in seen_labels:
            final_legend_patches.append(patch)
            seen_labels.add(patch.get_label())


    ax.legend(handles=final_legend_patches, bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)

    plt.tight_layout()
    plt.show()