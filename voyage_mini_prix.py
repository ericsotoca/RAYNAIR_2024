import tkinter as tk
from ttkthemes import ThemedStyle
from tkinter import scrolledtext, Label, Entry, Button, messagebox
from tkinter import font
from tkcalendar import Calendar
import threading
import re
import os
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

# Ajout d'une variable globale pour contrôler le clignotement
clignotement_en_cours = False

# Variable globale pour contrôler l'état de la recherche
recherche_active = False

def effectuer_recherche_vols_selenium(date_debut_str, date_fin_str, lieu_depart, durees_sejour, prix_max):
    global recherche_active
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    service = FirefoxService(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=options)
    
    date_debut = datetime.strptime(date_debut_str, "%d-%m-%Y")
    duree_max_sejour = max([int(duree.strip()) for duree in durees_sejour.split(',')])
    date_fin = datetime.strptime(date_fin_str, "%d-%m-%Y") + timedelta(days=duree_max_sejour)

    meilleures_offres_par_duree = {}

    for duree_sejour_str in durees_sejour.split(','):
        duree_sejour = int(duree_sejour_str.strip())
        meilleures_offres = {}
        date_actuelle = date_debut
        while date_actuelle + timedelta(days=duree_sejour) <= date_fin:
            if not recherche_active:
                print("Recherche arrêtée par l'utilisateur.")
                driver.quit()
                return None
            date_out = date_actuelle.strftime("%Y-%m-%d")
            date_in = (date_actuelle + timedelta(days=duree_sejour)).strftime("%Y-%m-%d")

            url = f"https://www.ryanair.com/fr/fr/cheap-flights-beta?originIata={lieu_depart}&destinationIata=ANY&isReturn=true&isMacDestination=false&promoCode=&adults=1&teens=0&children=0&infants=0&dateOut={date_out}&dateIn={date_in}&daysTrip={duree_sejour}&dayOfWeek=TUESDAY&isExactDate=true&outboundFromHour=00:00&outboundToHour=23:59&inboundFromHour=00:00&inboundToHour=23:59&priceValueTo={prix_max}&currency=EUR&isFlexibleDay=false"
            
            driver.get(url)
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.country-card__content")))
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
                print("TimeoutException pour la date de départ:", date_out)

            date_actuelle += timedelta(days=1)

        meilleures_offres_par_duree[duree_sejour] = sorted(meilleures_offres.items(), key=lambda offre: offre[1]['prix'])

    driver.quit()
    return meilleures_offres_par_duree

def faire_clignoter_label():
    global clignotement_en_cours
    if clignotement_en_cours:
        current_text = label_traitement.cget("text")
        new_text = "" if current_text else "Recherche en cours..."
        label_traitement.config(text=new_text)
        # Continue à alterner le texte toutes les 500 ms
        window.after(500, faire_clignoter_label)

# Fonction appelée lorsque l'utilisateur clique sur le bouton Rechercher
def lancer_recherche_vols():
    global recherche_active
    recherche_active = True
    global clignotement_en_cours
    clignotement_en_cours = True  # Démarre le clignotement
    faire_clignoter_label()  # Commence à faire clignoter le texte
    btn_rechercher.config(state='disabled')
    threading.Thread(target=rechercher_vols).start()    

# Fonction pour exécuter la recherche de vols et mettre à jour l'interface avec les résultats
def rechercher_vols():
    global resultats
    try:
        date_debut_str = entry_date_debut.get()
        date_fin_str = entry_date_fin.get()
        lieu_depart = entry_lieu_depart.get()
        durees_sejour = entry_duree_sejour.get()  # Maintenant, plusieurs durées possibles
        prix_max = float(entry_prix_max.get())

        resultats_par_duree = effectuer_recherche_vols_selenium(date_debut_str, date_fin_str, lieu_depart, durees_sejour, prix_max)
        window.after(0, afficher_resultats, resultats_par_duree)
    except Exception as e:
        window.after(0, lambda: messagebox.showerror("Erreur", f"Une erreur est survenue lors de la recherche : {e}"))

# Fonction pour jouer un effet sonore de fin de processus
def jouer_son_fin_processus():
    # Joue le son "bip-bip" deux fois : Fréquence = 1000 Hz, Durée = 200 ms
    for _ in range(2):
        winsound.Beep(1000, 200)
        winsound.Beep(1000, 200)

# Modification de la fonction pour intégrer l'effet sonore après l'affichage des résultats
def afficher_resultats(resultats_par_duree):
    global clignotement_en_cours
    clignotement_en_cours = False  # Arrête le clignotement
    label_traitement.config(text='')  # Efface le texte
    text_resultats.delete(1.0, tk.END)
    if not resultats_par_duree:
        messagebox.showinfo("Aucune offre", "Aucune offre trouvée pour les critères spécifiés.")
    else:
        for duree, offres in resultats_par_duree.items():
            text_resultats.insert(tk.END, f"Voyage de {duree} jours\n")
            for pays, infos in offres:
                text_resultats.insert(tk.END, f"{pays}: {infos['details']}\n")
            text_resultats.insert(tk.END, "-"*50 + "\n")
    
    window.after(2000, label_traitement.pack_forget)
    btn_rechercher.config(state='normal')
    jouer_son_fin_processus()

# Fonction pour ré-initialiser le formulaire et la zone de texte des résultats
def reinitialiser_formulaire():
    global recherche_active, clignotement_en_cours
    recherche_active = False  # Pour arrêter la recherche
    clignotement_en_cours = False  # Pour arrêter le clignotement
    label_traitement.config(text='')  # Efface le texte du label

    entry_date_debut.delete(0, tk.END)
    entry_date_fin.delete(0, tk.END)
    entry_lieu_depart.delete(0, tk.END)
    entry_duree_sejour.delete(0, tk.END)
    
    entry_date_debut.insert(0, date_debut_defaut)
    entry_date_fin.insert(0, date_fin_defaut)
    entry_lieu_depart.insert(0, lieu_depart_defaut)
    entry_duree_sejour.insert(0, duree_sejour_defaut)
    
    text_resultats.delete(1.0, tk.END)
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
window.geometry('1000x500')  # Ajuste la taille de la fenêtre selon tes besoins
window.configure(bg='lightblue')

style = ThemedStyle(window)
# Appliquer un thème de ttkthemes
style.theme_use('elegance')

# Configuration de la grille
window.grid_rowconfigure(0, weight=1)
window.grid_rowconfigure(1, weight=1)
window.grid_columnconfigure(0, weight=0)
window.grid_columnconfigure(1, weight=1)
window.grid_columnconfigure(2, weight=2)

# Initialiser le style TTK et choisir le thème
style = ttk.Style()
style.theme_use('clam')  # Remplacez 'clam' par le thème de votre choix

# Définit une largeur pour les champs
largeur_champs = 20  

# Définis une police de caractères plus grande pour le label d'instructions
police_grande = font.Font(family="Helvetica", size=10)  # Tu peux ajuster la taille et la famille de police ici

# Obtient le chemin d'accès au dossier actuel où se trouve le script
dossier_courant = os.path.dirname(__file__)

# Construit le chemin d'accès au fichier logo.png
chemin_logo = os.path.join(dossier_courant, 'logo.png')

# Création et placement du logo
logo_image = tk.PhotoImage(file=chemin_logo)
label_logo = Label(window, image=logo_image, bg='lightblue')

# Définit une police de caractères plus grande pour le label d'instructions
police_grande = font.Font(family="Helvetica", size=10)  # Tu peux ajuster la taille et la famille de police ici

# Texte d'accueil mis à jour avec des sauts de ligne pour une meilleure présentation
texte_accueil = (
    "📅 Sélectionnez une fenêtre de départ pour\n"
    "votre voyage et indiquez le début de votre\n"
    "période de retour.\n\n"
    "La recherche de vols tiendra compte de la\n"
    "durée du séjour pour déterminer la date\n"
    "de retour.\n\n"
    "Un bip final vous avertira, dans quelques\n"
    "minutes ! 🏖️"
)

# Définis une largeur de wrap adaptée pour que le texte reste dans sa colonne sans l'élargir
wraplength_desire = 500  # Ajuste cette valeur en pixels selon tes besoins

# Création et placement du label d'instructions avec la nouvelle police et le wraplength ajusté
label_instructions = tk.Label(
    window,
    text=texte_accueil,
    bg='lightblue',
    font=police_grande,
    wraplength=wraplength_desire,  # Utilise la largeur de wrap que tu as définie
    justify="left"
)
label_instructions.grid(row=0, column=1, padx=1, pady=1, sticky="nsew")  # Utilise sticky="nsew" pour étendre le label dans toutes les directions

# Création et placement du label d'instructions avec la nouvelle police
# label_instructions = tk.Label(window, text="📅 Sélectionnez une fenêtre de départ, par exemple de 1 à 3 mois, pour un séjour de quelques jours. Testez et un bip final (≈ 3 min) vous avertit de la fin de la recherche ! 🏖️", bg='lightblue', wraplength=350, font=police_grande)  # Ajoute `font=police_grande` ici
# label_instructions.grid(row=0, column=1, padx=5, pady=5, sticky="w")

# Création et placement des widgets
label_traitement = Label(window, text='', bg='lightblue')
label_date_debut = Label(window, text="Début de la plage de recherche")
label_date_fin = Label(window, text="Fin de la plage de recherche")
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
entry_date_debut = Entry(window, width=largeur_champs)
entry_date_fin = Entry(window, width=largeur_champs)
entry_lieu_depart = Entry(window, width=largeur_champs)
entry_duree_sejour = Entry(window, width=largeur_champs)
entry_prix_max = Entry(window, width=largeur_champs)
btn_rechercher = Button(window, text="Rechercher", command=lancer_recherche_vols)

# Insérer les valeurs par défaut APRES la création des Entry
entry_date_debut.insert(0, date_debut_defaut)
entry_date_fin.insert(0, date_fin_defaut)
entry_lieu_depart.insert(0, lieu_depart_defaut)
entry_duree_sejour.insert(0, duree_sejour_defaut)
entry_prix_max.insert(0, prix_max_defaut)

# Positionnement des Entry dans la grille
entry_date_debut.grid(row=2, column=1, padx=10, pady=5, sticky="w")
entry_date_fin.grid(row=3, column=1, padx=10, pady=5, sticky="w")
entry_lieu_depart.grid(row=4, column=1, padx=10, pady=5, sticky="w")
entry_duree_sejour.grid(row=5, column=1, padx=10, pady=5, sticky="w")
entry_prix_max.grid(row=6, column=1, padx=10, pady=5, sticky="w")

# Création et positionnement du bouton Rechercher
btn_rechercher = Button(window, text="Rechercher", command=lancer_recherche_vols)
btn_rechercher.grid(row=7, column=1, padx=10, pady=10, sticky="w") 

# Création et positionnement du bouton Stop juste à droite du bouton Rechercher
btn_stop = Button(window, text="Stopper", command=reinitialiser_formulaire)
btn_stop.grid(row=8, column=1, padx=10, pady=5, sticky="w")  

# Remplacement des Entry par des boutons pour ouvrir le calendrier
btn_date_debut = tk.Button(window, text="📅", command=choisir_date_debut) 
btn_date_fin = tk.Button(window, text="📅", command=choisir_date_fin)

# Création du Combobox pour la sélection d'aéroports
combo_aeroports = ttk.Combobox(window, values=[f"{code} {nom}" for code, nom in aeroports], state="readonly")
combo_aeroports.bind("<<ComboboxSelected>>", choisir_aeroport)

# Positionnement des boutons de calendrier plus proche des Entry
btn_date_debut.grid(row=2, column=1, padx=(0, 135), pady=5, sticky="e")  # Décalage vers la gauche avec padx
btn_date_fin.grid(row=3, column=1, padx=(0, 135), pady=5, sticky="e")    # Décalage vers la gauche avec padx
combo_aeroports.grid(row=4, column=1, padx=(0, 15), pady=5, sticky="e") # Décalage vers la gauche avec padx

# Positionnement des widgets
label_logo.grid(row=0, column=0, padx=10, pady=10, sticky="w")
label_date_debut.grid(row=2, column=0, padx=2, pady=5, sticky="e")
label_date_fin.grid(row=3, column=0, padx=2, pady=5, sticky="e")
label_lieu_depart.grid(row=4, column=0, padx=2, pady=5, sticky="e")
label_duree_sejour.grid(row=5, column=0, padx=2, pady=5, sticky="e")
label_prix_max.grid(row=6, column=0, padx=2, pady=5, sticky="e")

# Création et positionnement des Entry et Button
entry_date_debut = Entry(window, width=largeur_champs)
entry_date_fin = Entry(window, width=largeur_champs)
entry_lieu_depart = Entry(window, width=largeur_champs)
entry_duree_sejour = Entry(window, width=largeur_champs)

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
text_resultats = scrolledtext.ScrolledText(window, height=40, width=45)  
text_resultats.grid(row=0, column=2, rowspan=12, padx=10, pady=10, sticky="nsew")

# Création et positionnement du label de traitement
# label_traitement = Label(window, text='test', bg='lightblue')

label_traitement = Label(window, text="Démarrer le processus !", bg='lightblue')
label_traitement.grid(row=7, column=0, padx=10, pady=10, sticky="e")

# Test immédiat du clignotement
clignotement_en_cours = False
faire_clignoter_label()


# Création et positionnement du label des contacts
label_contacts = tk.Label(window, text="Création : Sotoca-Online - Version 1.1 - 022024", bg='lightblue')
label_contacts.grid(row=11, column=0, columnspan=3, pady=10, sticky="nsew")

# Lancement de l'application
window.mainloop()