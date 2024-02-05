import tkinter as tk
from tkinter import scrolledtext, Label, Entry, Button, messagebox
from tkcalendar import Calendar
import threading
import re
from tkinter import ttk
import winsound
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException

# Fonction pour effectuer la recherche de vols
def effectuer_recherche_vols_selenium(date_debut_str, date_fin_str, lieu_depart, duree_sejour, prix_max):
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    service = FirefoxService(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=options)
    
    date_debut = datetime.strptime(date_debut_str, "%d-%m-%Y")
    date_fin = datetime.strptime(date_fin_str, "%d-%m-%Y")
    delta_jour = timedelta(days=1)

    meilleures_offres = {}

    date_actuelle = date_debut
    while date_actuelle <= date_fin:
        date_out = date_actuelle.strftime("%Y-%m-%d")
        date_in = (date_actuelle + timedelta(days=duree_sejour)).strftime("%Y-%m-%d")

        # Inclusion du paramètre prix_max dans l'URL
        url = f"https://www.ryanair.com/fr/fr/cheap-flights-beta?originIata={lieu_depart}&destinationIata=ANY&isReturn=true&isMacDestination=false&promoCode=&adults=1&teens=0&children=0&infants=0&dateOut={date_out}&dateIn={date_in}&daysTrip={duree_sejour}&dayOfWeek=TUESDAY&isExactDate=true&outboundFromHour=00:00&outboundToHour=23:59&inboundFromHour=00:00&inboundToHour=23:59&priceValueTo={prix_max}&currency=EUR&isFlexibleDay=false"

        driver.get(url)
        try:
            WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.country-card__content")))
            content = driver.page_source
            soup = BeautifulSoup(content, 'html.parser')
            cards = soup.select("div.country-card__content")
            for card in cards:
                original_text = card.text.strip()
                cleaned_text = re.sub(r"\s+", " ", original_text).strip()

                match = re.search(r"(\w+)\s.*€(\d+[\.,]?\d*)", cleaned_text)
                if match:
                    pays = match.group(1)
                    prix = float(match.group(2).replace(',', '.'))
                    details_vol = f"{date_out} - {date_in} | Prix: €{prix}"

                    if pays == "Bas":
                        pays = "Pays-Bas"

                    if pays == "Uni":
                        pays = "Royaume-Uni"

                    if pays not in meilleures_offres or meilleures_offres[pays]["prix"] > prix:
                        meilleures_offres[pays] = {"prix": prix, "details": details_vol}

        except TimeoutException:
            pass
        date_actuelle += delta_jour

    driver.quit()

    # Bip-bip pour la fin du processus
    jouer_son_fin_processus()

    # Préparation des résultats pour l'affichage
    offres_triees = sorted(meilleures_offres.items(), key=lambda offre: offre[1]['prix'])
    resultats = [f"{pays}: {infos['details']}" for pays, infos in offres_triees]

    return resultats

# Fonction appelée lorsque l'utilisateur clique sur le bouton Rechercher
def lancer_recherche_vols():
    label_traitement.config(text='Recherche en cours...', fg='red')
    label_traitement.grid(row=7, column=0, padx=10, pady=10, sticky="e")
    btn_rechercher.config(state='disabled')
    threading.Thread(target=rechercher_vols).start()

# Fonction pour exécuter la recherche de vols et mettre à jour l'interface avec les résultats
def rechercher_vols():
    global resultats
    try:
        date_debut_str = entry_date_debut.get()
        date_fin_str = entry_date_fin.get()
        lieu_depart = entry_lieu_depart.get()
        duree_sejour = int(entry_duree_sejour.get())
        prix_max = float(entry_prix_max.get())  # Récupération du prix maximum

        # Mise à jour de l'appel à effectuer_recherche_vols_selenium pour inclure le prix max
        resultats = effectuer_recherche_vols_selenium(date_debut_str, date_fin_str, lieu_depart, duree_sejour, prix_max)

        window.after(0, afficher_resultats, resultats)
    except Exception as e:
        window.after(0, lambda: messagebox.showerror("Erreur", f"Une erreur est survenue lors de la recherche : {e}"))

# Fonction pour jouer un effet sonore de fin de processus
def jouer_son_fin_processus():
    # Joue le son "bip-bip" deux fois : Fréquence = 1000 Hz, Durée = 200 ms
    for _ in range(2):
        winsound.Beep(1000, 200)
        winsound.Beep(1000, 200)

# Modification de la fonction pour intégrer l'effet sonore après l'affichage des résultats
def afficher_resultats(resultats):
    text_resultats.delete(1.0, tk.END)
    if not resultats:
        messagebox.showinfo("Aucune offre", "Aucune offre trouvée pour les critères spécifiés.")
    else:
        for resultat in resultats:
            text_resultats.insert(tk.END, resultat + "\n")
    
    window.after(2000, label_traitement.pack_forget)
    btn_rechercher.config(state='normal')
    
    # Jouer l'effet sonore de fin de processus
    jouer_son_fin_processus()

# Fonction pour ré-initialiser le formulaire et la zone de texte des résultats
def reinitialiser_formulaire():
    entry_date_debut.delete(0, tk.END)
    entry_date_fin.delete(0, tk.END)
    entry_lieu_depart.delete(0, tk.END)
    entry_duree_sejour.delete(0, tk.END)
    
    entry_date_debut.insert(0, date_debut_defaut)
    entry_date_fin.insert(0, date_fin_defaut)
    entry_lieu_depart.insert(0, lieu_depart_defaut)
    entry_duree_sejour.insert(0, duree_sejour_defaut)
    
    text_resultats.delete(1.0, tk.END)
    label_traitement.config(text='', bg='lightblue')
    btn_rechercher.config(state='normal')  # Réactive le bouton "Rechercher"

def choisir_date_debut():
    def set_date_debut():
        entry_date_debut.delete(0, tk.END)
        entry_date_debut.insert(0, cal.selection_get().strftime("%d-%m-%Y"))
        top.destroy()

    top = tk.Toplevel(window)
    cal = Calendar(top, selectmode='day', year=datetime.now().year, month=datetime.now().month, day=datetime.now().day)
    cal.pack(fill="both", expand=True)
    ttk.Button(top, text="ok", command=set_date_debut).pack()

def choisir_date_fin():
    def set_date_fin():
        entry_date_fin.delete(0, tk.END)
        entry_date_fin.insert(0, cal.selection_get().strftime("%d-%m-%Y"))
        top.destroy()

    top = tk.Toplevel(window)
    cal = Calendar(top, selectmode='day', year=datetime.now().year, month=datetime.now().month, day=datetime.now().day)
    cal.pack(fill="both", expand=True)
    ttk.Button(top, text="ok", command=set_date_fin).pack()

# Fonction pour mettre à jour le champ de saisie du lieu de départ
def choisir_aeroport(event):
    code_iata = combo_aeroports.get().split(" ")[0]  # Récupère le code IATA de la sélection
    entry_lieu_depart.delete(0, tk.END)
    entry_lieu_depart.insert(0, code_iata)

# Liste des aéroports (code IATA et nom complet)
aeroports= [
    ("BIQ", "Biarritz"),
    ("BOD", "Bordeaux"),
    ("BZR", "Béziers"),
    ("CFE", "Clermont-Ferrand"),
    ("GNB", "Grenoble"),
    ("LRH", "La Rochelle"),
    ("LIL", "Lille"),
    ("LIG", "Limoges"),
    ("LYS", "Lyon"),
    ("MRS", "Marseille"),
    ("MPL", "Montpellier"),
    ("NTE", "Nantes"),
    ("NCE", "Nice"),
    ("BVA", "Paris"),
    ("PGF", "Perpignan"),
    ("PIS", "Poitiers"),
    ("RNS", "Rennes"),
    ("SXB", "Strasbourg"),
    ("TLS", "Toulouse"),
    ("TUF", "Tours"),
]

# Configuration de la fenêtre principale de l'application
window = tk.Tk()
window.title("Voyage_Mini_Prix")
window.geometry('500x850')  # Ajuste la taille de la fenêtre selon tes besoins
window.configure(bg='lightblue')

# Configuration de la grille
window.grid_rowconfigure(0, weight=1)
window.grid_rowconfigure(1, weight=1)
window.grid_rowconfigure(0, weight=1)
window.grid_rowconfigure(1, weight=1)
window.grid_rowconfigure(0, weight=1)
window.grid_rowconfigure(1, weight=1)
window.grid_columnconfigure(0, weight=1)
window.grid_columnconfigure(1, weight=1) 

# Création et placement du logo
logo_image = tk.PhotoImage(file=r'C:\Users\FiercePC\Desktop\IA\RAYNAIR_2024\logo.png')
label_logo = Label(window, image=logo_image, bg='lightblue')
label_logo.grid(row=0, column=0, columnspan=3, pady=10, sticky="nsew")  # Utilisez columnspan=2 pour occuper deux colonnes au centre
label_logo.grid(row=0, column=0, columnspan=3, pady=10, sticky="nsew")

# Après la création et le positionnement du logo
label_instructions = tk.Label(window, text="📅 Sélectionnez une fenêtre de départ, par exemple de 1 à 3 mois, pour un séjour de quelques jours. Testez et un bip final (≈ 3 min) vous avertit de la fin de la recherche ! 🏖️", bg='lightblue', wraplength=350)  # Ajustez `wraplength` selon la largeur souhaitée
label_instructions.grid(row=1, column=0, columnspan=3, pady=10, sticky="nsew")

# Création et placement des widgets
label_traitement = Label(window, text='', bg='lightblue')
label_date_debut = Label(window, text="Début de la période de départ")
label_date_fin = Label(window, text="Fin de la période de départ")
label_lieu_depart = Label(window, text="Aéroport de départ")
label_duree_sejour = Label(window, text="Durée du séjour")
label_prix_max = Label(window, text="Prix max en €")

# Création et initialisation des champs de saisie avec valeurs par défaut
date_demain = datetime.now() + timedelta(days=1)
date_debut_defaut = date_demain.strftime("%d-%m-%Y")
date_fin_defaut = (date_demain + timedelta(days=90)).strftime("%d-%m-%Y")
lieu_depart_defaut = "MRS"
duree_sejour_defaut = "5"
prix_max_defaut = "50"

# Création et positionnement des Entry et Button
entry_date_debut = Entry(window)
entry_date_fin = Entry(window)
entry_lieu_depart = Entry(window)
entry_duree_sejour = Entry(window)
entry_prix_max = Entry(window)
btn_rechercher = Button(window, text="Rechercher", command=lancer_recherche_vols)

# Insérer les valeurs par défaut APRES la création des Entry
entry_date_debut.insert(0, date_debut_defaut)
entry_date_fin.insert(0, date_fin_defaut)
entry_lieu_depart.insert(0, lieu_depart_defaut)
entry_duree_sejour.insert(0, duree_sejour_defaut)
entry_prix_max.insert(0, prix_max_defaut)

# Positionnement des widgets de saisie (s'assurer que les valeurs de row sont correctes)
entry_date_debut.grid(row=2, column=1, padx=10, pady=5, sticky="w")  # row ajusté à 2
entry_date_fin.grid(row=3, column=1, padx=10, pady=5, sticky="w")    # row ajusté à 3
entry_lieu_depart.grid(row=4, column=1, padx=10, pady=5, sticky="w") # row ajusté à 4
entry_duree_sejour.grid(row=5, column=1, padx=10, pady=5, sticky="w")# row ajusté à 5
entry_prix_max.grid(row=6, column=1, padx=10, pady=5, sticky="w")

# Création et positionnement du bouton Rechercher
btn_rechercher = Button(window, text="Rechercher", command=lancer_recherche_vols)
btn_rechercher.grid(row=7, column=1, padx=10, pady=10, sticky="w") 

# Création et positionnement du bouton Stop juste à droite du bouton Rechercher
btn_stop = Button(window, text="Stopper", command=reinitialiser_formulaire)
btn_stop.grid(row=8, column=1, padx=10, pady=5, sticky="w")  

# Remplacement des Entry par des boutons pour ouvrir le calendrier
# pour créer une version executable, mettre en commentaire les lignes 267, 268 + 277,278
# btn_date_debut = tk.Button(window, text="📅", command=choisir_date_debut) 
# btn_date_fin = tk.Button(window, text="📅", command=choisir_date_fin)

# Création du Combobox pour la sélection d'aéroports
combo_aeroports = ttk.Combobox(window, values=[f"{code} {nom}" for code, nom in aeroports], state="readonly")
combo_aeroports.grid(row=4, column=2, padx=(0, 15), pady=5, sticky="w")
combo_aeroports.bind("<<ComboboxSelected>>", choisir_aeroport)

# Positionnement des boutons de calendrier plus proche des Entry
# pour une version executable, mettre en commentaire les deux lignes suivantes
# btn_date_debut.grid(row=2, column=2, padx=(0, 15), pady=5, sticky="w") 
# btn_date_fin.grid(row=3, column=2, padx=(0, 15), pady=5, sticky="w") 

# Positionnement des widgets
label_logo.grid(row=0, column=0, columnspan=3, pady=10)

label_date_debut.grid(row=2, column=0, padx=2, pady=5, sticky="e")
label_date_fin.grid(row=3, column=0, padx=2, pady=5, sticky="e")
label_lieu_depart.grid(row=4, column=0, padx=2, pady=5, sticky="e")
label_duree_sejour.grid(row=5, column=0, padx=2, pady=5, sticky="e")
label_prix_max.grid(row=6, column=0, padx=2, pady=5, sticky="e")

# Création et positionnement des Entry et Button
entry_date_debut = Entry(window)
entry_date_fin = Entry(window)
entry_lieu_depart = Entry(window)
entry_duree_sejour = Entry(window)

# Positionnement des widgets de saisie (s'assurer que les valeurs de row sont correctes)
entry_date_debut.grid(row=2, column=1, padx=10, pady=5, sticky="w")
entry_date_fin.grid(row=3, column=1, padx=10, pady=5, sticky="w")
entry_lieu_depart.grid(row=4, column=1, padx=10, pady=5, sticky="w")
entry_duree_sejour.grid(row=5, column=1, padx=10, pady=5, sticky="w")

# Insérer les valeurs par défaut
entry_date_debut.insert(0, date_debut_defaut)
entry_date_fin.insert(0, date_fin_defaut)
entry_lieu_depart.insert(0, lieu_depart_defaut)
entry_duree_sejour.insert(0, duree_sejour_defaut)

# Création et positionnement de la zone de texte des résultats
text_resultats = scrolledtext.ScrolledText(window, height=15, width=80)
text_resultats.grid(row=10, column=0, columnspan=3, padx=10, pady=10, sticky="nsew") # Attention

# Création et positionnement du label de traitement
label_traitement = Label(window, text='', bg='lightblue')

# Création et positionnement du label des contacts
label_contacts = tk.Label(window, text="Création : Sotoca Online - Version 1 - 022024", bg='lightblue')
label_contacts.grid(row=11, column=0, columnspan=3, pady=10, sticky="nsew")

# Lancement de l'application
window.mainloop()