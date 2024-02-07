import tkinter as tk
from tkinter import scrolledtext, Label, Entry, Button, messagebox
from tkinter import font
from ttkthemes import ThemedStyle
from tkcalendar import Calendar
import threading
import re
import sys
import os
from tkinter import ttk
import winsound
import webbrowser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException

# Configuration de la fenêtre principale de l'application
window = tk.Tk()
window.title("Voyage_Mini_Prix")
window.geometry('1000x500')  # Ajuste la taille de la fenêtre selon tes besoins
window.configure(bg='lightblue')

# Variable globale pour contrôler le clignotement
clignotement_en_cours = False

# Variable globale pour contrôler l'état de la recherche
recherche_active = False

# Modification pour le chemin des images dans un contexte exécutable
def chemin_relatif(fichier):
    if getattr(sys, 'frozen', False):
        dossier_application = sys._MEIPASS
    else:
        dossier_application = os.path.dirname(os.path.abspath(__file__))
    chemin_complet = os.path.join(dossier_application, fichier)

    # Ajoute un débogage pour voir si le chemin est correct
    print(f"Chemin d'accès à la ressource: {chemin_complet}")

    return chemin_complet

# Dictionnaire des traductions (en cours)
traductions = {
    'france': {
        'titre': "Voyage_Mini_Prix",
        'texte_accueil': ("Vous aimeriez partir dans les\nprochaines semaines, les prochains mois ?\n\n"
                          "Et vous êtes plutôt du genre disponibles ?\nRetraité ? Nomad Digital ? Au chômage !...\n\n"
                          "Si vous pouvez choisir vos dates alors\nvous pourrez profiter des meilleurs prix !\n\n"
                          "Lancez la recherche, un bip final vous\navertira, soyez patient quelques minutes !"),
        'rechercher': "Rechercher",
        'stopper': "Stopper",
        'debut_recherche': "Début de la plage de recherche",
        'fin_recherche': "Fin de la plage de recherche",
        'aeroport_depart': "Aéroport de départ",
        'duree_sejour': "Durée du séjour",
        'prix_max': "Prix max en €",
        'demarrer_processus': "Démarrer le processus !",
        'choisir': "Choisir",
        'creation_info': "Création: Sotoca-Online - Version 1.3 - 022024",
        'aucune_offre': "Aucune offre trouvée pour les critères spécifiés.",
        'voyage_de': "Voyage de",
        'jours': "jours",
        'erreur_recherche': "Une erreur est survenue lors de la recherche :",
    },
    'royaume': {
        'titre': "Travel_Low_Cost",
        'texte_accueil': ("Would you like to go away in the\ncoming weeks or months?\n\n"
                          "And are you generally available?\nRetired? Digital Nomad? Unemployed!...\n\n"
                          "If you can choose your dates then\nyou can take advantage of the best prices!\n\n"
                          "Start the search, a final beep will\nalert you, please be patient for a few minutes!"),
        'rechercher': "Search",
        'stopper': "Stop",
        'debut_recherche': "Start of search range",
        'fin_recherche': "End of search range",
        'aeroport_depart': "Departure airport",
        'duree_sejour': "Duration of stay",
        'prix_max': "Max price in €",
        'demarrer_processus': "Start the process!",
        'choisir': "Choose",
        'creation_info': "Creation: Sotoca-Online.com - Version 1.3 - 022024",
        'aucune_offre': "No offers found for the specified criteria.",
        'voyage_de': "Trip of",
        'jours': "days",
        'erreur_recherche': "An error occurred during the search:",
    },
    'italie': {
        'titre': "Viaggio_A_Basso_Costo",
        'rechercher': "Cerca",
        'stopper': "Fermare",
        'debut_recherche': "Inizio dell'intervallo di ricerca",
        'fin_recherche': "Fine dell'intervallo di ricerca",
        'aeroport_depart': "Aeroporto di partenza",
        'duree_sejour': "Durata del soggiorno",
        'prix_max': "Prezzo massimo in €",
        'demarrer_processus': "Avvia il processo!",
        'texte_accueil': ("Vorresti partire nelle\nprossime settimane o mesi?\n\n"
                          "E sei generalmente disponibile?\nPensionato? Nomade Digitale? Disoccupato!...\n\n"
                          "Se puoi scegliere le tue date\npotrai approfittare dei migliori prezzi!\n\n"
                          "Avvia la ricerca, un segnale acustico finale ti\navviserà, per favore sii paziente per qualche minuto!"),
        'creation_info': "Creazione: Sotoca-Online.com - Versione 1.3 - 022024",
    },
    'espagne': {
        'titre': "Viaje_Mini_Precio",
        'texte_accueil': ("¿Te gustaría partir en las\npróximas semanas o meses?\n\n"
                          "¿Eres de los que tienen disponibilidad?\n¿Jubilado? ¿Nómada Digital? ¿Desempleado?...\n\n"
                          "Si puedes elegir tus fechas,\nentonces podrás aprovechar los mejores precios.\n\n"
                          "Inicia la búsqueda, un bip final te avisará,\n¡ten paciencia unos minutos!"),
        'rechercher': "Buscar",
        'stopper': "Detener",
        'debut_recherche': "Inicio del periodo de búsqueda",
        'fin_recherche': "Fin del periodo de búsqueda",
        'aeroport_depart': "Aeropuerto de salida",
        'duree_sejour': "Duración de la estancia",
        'prix_max': "Precio máximo en €",
        'demarrer_processus': "¡Iniciar el proceso!",
        'choisir': "Elegir",
        'creation_info': "Creación: Sotoca-Online.com - Versión 1.3 - 022024",
    },
    # Correction de la section 'allemand' avec les traductions allemandes appropriées
    'allemagne': {
        'titre': "Reise_zum_Kleinen_Preis",
        'texte_accueil': ("Möchten Sie in den kommenden\nWochen oder Monaten verreisen?\n\n"
                          "Sind Sie im Allgemeinen verfügbar?\nRentner? Digitaler Nomade? Arbeitslos?...\n\n"
                          "Wenn Sie Ihre Termine wählen können,\ndann können Sie die besten Preise nutzen.\n\n"
                          "Starten Sie die Suche, ein abschließendes\nPiepsignal wird Sie informieren,\nbitte haben Sie ein paar Minuten Geduld!"),
        'rechercher': "Suchen",
        'stopper': "Stoppen",
        'debut_recherche': "Beginn des Suchzeitraums",
        'fin_recherche': "Ende des Suchzeitraums",
        'aeroport_depart': "Abflughafen",
        'duree_sejour': "Aufenthaltsdauer",
        'prix_max': "Maximalpreis in €",
        'demarrer_processus': "Prozess starten!",
        'choisir': "Wählen",
        'creation_info': "Erstellung: Sotoca-Online.com - Version 1.3 - 022024",
    },
}

# Fonction pour changer la langue
def changer_langue(langue):
    # Met à jour le titre de la fenêtre
    window.title(traductions[langue]['titre'])
    # Met à jour les textes des boutons et labels
    btn_rechercher.config(text=traductions[langue]['rechercher'])
    btn_stop.config(text=traductions[langue]['stopper'])
    label_date_debut.config(text=traductions[langue]['debut_recherche'])
    label_date_fin.config(text=traductions[langue]['fin_recherche'])
    label_lieu_depart.config(text=traductions[langue]['aeroport_depart'])
    label_duree_sejour.config(text=traductions[langue]['duree_sejour'])
    label_prix_max.config(text=traductions[langue]['prix_max'])
    label_instructions.config(text=traductions[langue]['texte_accueil']) 
    label_contacts.config(text=traductions[langue]['creation_info']) 
    label_traitement.config(text=traductions[langue]['demarrer_processus']) 
    

# Crée une fonction pour générer une action de changement de langue pour éviter les problèmes de portée de la lambda dans la boucle
def creer_action_changement_langue(langue):
    return lambda: changer_langue(langue)

chemin_logo = chemin_relatif('logo.png')

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

# Fonction pour ouvrir un lien dans le navigateur par défaut
def ouvrir_lien(url):
    webbrowser.open(url, new=2)  # new=2 indique d'ouvrir dans un nouvel onglet, si possible

# Obtient le chemin d'accès au dossier actuel où se trouve le script
dossier_courant = os.path.dirname(__file__)
chemin_images = dossier_courant 

noms_drapeaux = ['france', 'royaume', 'espagne', 'italie', 'allemagne']
labels_drapeaux = []

# Crée un Frame pour contenir tous les drapeaux
frame_drapeaux = tk.Frame(window, bg='lightblue')
frame_drapeaux.grid(row=8, column=0, columnspan=3, padx=20, pady=2, sticky="w")  # Étendre le Frame sur les colonnes nécessaires
   
# Création du Frame pour les drapeaux et chargement des images avec chemin_relatif (modifié pour associer les actions de changement de langue)
# Utilise la fonction ci-dessus pour définir l'action du bouton
for index, nom_drapeau in enumerate(noms_drapeaux):
    chemin_image = chemin_relatif(f"{nom_drapeau}.png")
    image_drapeau = tk.PhotoImage(file=chemin_image).subsample(2)  # Ajuste la taille des images si nécessaire
    action_changement_langue = creer_action_changement_langue(nom_drapeau)
    label_drapeau = tk.Button(frame_drapeaux, image=image_drapeau, bg='lightblue', command=action_changement_langue)
    label_drapeau.image = image_drapeau
    label_drapeau.pack(side="left", padx=5)

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

# Modification de la fonction `afficher_resultats` pour que le lien ne couvre que le pays
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
                # Extraire les dates de départ et de retour
                date_out, date_in = infos['details'].split(" | ")[0].split(" - ")

                # Construction de l'URL spécifique pour chaque pays
                url = f"https://www.ryanair.com/fr/fr/cheap-flights-beta?originIata={entry_lieu_depart.get()}&destinationIata=ANY&isReturn=true&isMacDestination=false&promoCode=&adults=1&teens=0&children=0&infants=0&dateOut={date_out}&dateIn={date_in}&daysTrip={duree}&dayOfWeek=TUESDAY&isExactDate=true&outboundFromHour=00:00&outboundToHour=23:59&inboundFromHour=00:00&inboundToHour=23:59&priceValueTo={entry_prix_max.get()}&currency=EUR&isFlexibleDay=false"
                
                # Insérer le nom du pays avec un lien cliquable
                text_resultats.insert(tk.END, f"{pays}")
                # Ajouter un tag unique pour chaque pays pour le lien
                tag_name = f"link_{pays.replace(' ', '_')}_{date_out.replace('-', '_')}"
                text_resultats.tag_add(tag_name, "end-1c linestart", "end-1c")
                text_resultats.tag_config(tag_name, foreground="blue", underline=1)
                text_resultats.tag_bind(tag_name, "<Button-1>", lambda e, url=url: ouvrir_lien(url))
                text_resultats.insert(tk.END, f" : {infos['details']}\n")
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

# Création et placement du logo
logo_image = tk.PhotoImage(file=chemin_logo)
label_logo = Label(window, image=logo_image, bg='lightblue')

# Définit une police de caractères plus grande pour le label d'instructions
police_grande = font.Font(family="Helvetica", size=10)  # Tu peux ajuster la taille et la famille de police ici

# Texte d'accueil mis à jour avec des sauts de ligne pour une meilleure présentation
texte_accueil = (
    "Vous aimeriez partir dans les\n"
    "prochaines semaines, les prochains mois ?\n\n"
    "Et vous êtes plutôt du genre disponibles ?\n"
    "Retraité ? Nomad Digital ? Au chômage !...\n\n"
    "Si vous pouvez choisir vos dates alors\n"
    "vous pourrez profiter des meilleurs prix !\n\n"
    "Lancez la recherche, un bip final vous\n"
    "avertira, soyez patient quelques minutes !"
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
text_resultats.grid(row=0, column=2, rowspan=10, padx=10, pady=10, sticky="nsew")

# Création et positionnement du label de traitement
# label_traitement = Label(window, text='test', bg='lightblue')

label_traitement = Label(window, text="Démarrer le processus !", bg='lightblue')
label_traitement.grid(row=7, column=0, padx=10, pady=10, sticky="e")

# Test immédiat du clignotement
clignotement_en_cours = False
faire_clignoter_label()

# Création et positionnement du label des contacts
label_contacts = tk.Label(window, text="Création : Sotoca-Online - Version 1.3 - 022024", bg='lightblue')
label_contacts.grid(row=11, column=0, columnspan=3, pady=10, sticky="nsew")

# Lancement de l'application
window.mainloop()