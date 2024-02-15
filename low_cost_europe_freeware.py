# Importation optimisée des modules
from tkinter import messagebox, scrolledtext, Label, Entry, Button, font, ttk, Tk, PhotoImage, Frame
import tkinter as tk
from tkcalendar import Calendar
import threading
import re
import sys
import os
import winsound
import webbrowser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import logging
from selenium.common.exceptions import TimeoutException, WebDriverException
import numpy as np


# Configure le journalisation pour écrire dans un fichier avec le niveau de détails DEBUG
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Exemple de comment loguer des informations
logging.info('Démarrage de l\'application')

options = webdriver.FirefoxOptions()
options.add_argument("--headless")
service = FirefoxService(GeckoDriverManager().install())
driver = webdriver.Firefox(service=service, options=options)

# Configuration de la fenêtre principale de l'application
window = tk.Tk()
window.title("Low Cost Europe - Freeware - V1")
window.geometry('1000x550')  # Ajuste la taille de la fenêtre selon tes besoins
window.configure(bg='lightblue')

# Variable globale pour contrôler l'état de la recherche
recherche_active = False

def stopper_et_reinitialiser():
    global recherche_active
    # Arrête la recherche
    recherche_active = False
    logging.info('Recherche stoppée par l\'utilisateur')

    # Réinitialise les champs du formulaire
    # entry_date_debut.delete(0, tk.END)
    # entry_date_fin.delete(0, tk.END)
    # entry_lieu_depart.delete(0, tk.END)
    # entry_duree_sejour.delete(0, tk.END)
    # entry_prix_max.delete(0, tk.END)

    # Vous pouvez réinsérer les valeurs par défaut si nécessaire
    entry_date_debut.insert(0, date_debut_defaut)
    entry_date_debut.config(state='disabled')
    
    entry_date_fin.insert(0, date_fin_defaut)
    entry_date_fin.config(state='disabled')
        
    entry_lieu_depart.insert(0, lieu_depart_defaut)
    
    entry_duree_sejour.insert(0, duree_sejour_defaut)
    entry_duree_sejour.config(state='disabled')
    
    entry_prix_max.insert(50, prix_max_defaut)
    entry_prix_max.config(state='disabled')

    # Efface les résultats précédents
    text_resultats.delete(1.0, tk.END)


def chemin_relatif(fichier):
    if getattr(sys, 'frozen', False):
        dossier_application = sys._MEIPASS
    else:
        dossier_application = os.path.dirname(os.path.abspath(__file__))
    chemin_complet = os.path.join(dossier_application, fichier)
    return chemin_complet

# Fonction pour jouer un effet sonore de fin de processus
def jouer_son_fin_processus():
    # Joue le son "bip-bip" deux fois : Fréquence = 1000 Hz, Durée = 200 ms
    for _ in range(2):
        winsound.Beep(1000, 200)
        winsound.Beep(1000, 200)

def ouvrir_lien(url):
    def callback(e):
        webbrowser.open(url, new=2)
    return callback

def afficher_resultats(resultats_par_duree):
    global clignotement_en_cours
    clignotement_en_cours = False  # Arrête le clignotement
    label_traitement.config(text='')  # Efface le texte
    text_resultats.delete(1.0, tk.END)
    print("Affichage des résultats...")  # Débogage
    if not resultats_par_duree:
        messagebox.showinfo("Aucune offre", "Aucune offre trouvée pour les critères spécifiés.")
        print("Aucun résultat à afficher.")  # Débogage
    else:
        for duree, offres in resultats_par_duree.items():
            print(f"Duree: {duree}, Offres: {offres}") 
            text_resultats.insert(tk.END, f"Voyage de {duree} jours\n\n")
            
            # Tri des offres par prix
            offres_triees_par_prix = sorted(offres.items(), key=lambda x: float(x[1]['details'].split(' | ')[1].split('€')[1]))
            
            for pays, infos in offres_triees_par_prix:
                # Le reste du traitement reste inchangé, seul le tri par prix est ajouté avant cette boucle
                details_vol = infos['details']
                date_out, rest = details_vol.split(" - ")
                date_in, prix_vol = rest.split(" | ")
                date_out_affichage_fr = datetime.strptime(date_out, "%Y-%m-%d").strftime("%d-%m-%Y")
                date_in_affichage_fr = datetime.strptime(date_in, "%Y-%m-%d").strftime("%d-%m-%Y")
                url = f"https://www.ryanair.com/fr/fr/cheap-flights-beta?originIata={entry_lieu_depart.get()}&destinationIata=ANY&isReturn=true&isMacDestination=false&promoCode=&adults=1&teens=0&children=0&infants=0&dateOut={date_out}&dateIn={date_in}&daysTrip={duree}&dayOfWeek=TUESDAY&isExactDate=true&outboundFromHour=00:00&outboundToHour=23:59&inboundFromHour=00:00&inboundToHour=23:59&priceValueTo={entry_prix_max.get()}&currency=EUR&isFlexibleDay=false"
                text_resultats.insert(tk.END, pays)
                tag_name = f"link_{pays.replace(' ', '_')}_{date_out.replace('-', '_')}"
                text_resultats.tag_add(tag_name, "end-1c linestart", "end-1c")
                text_resultats.tag_config(tag_name, foreground="blue", underline=1)
                text_resultats.tag_bind(tag_name, "<Button-1>", ouvrir_lien(url))
                text_resultats.insert(tk.END, f" : {date_out_affichage_fr} - {date_in_affichage_fr} | {prix_vol}\n")
            text_resultats.insert(tk.END, "-"*50 + "\n")
        texte_explicatif = "\nCliquez sur les noms des pays pour voir les offres\ndétaillées par ville sur le site de Ryanair."
        text_resultats.insert(tk.END, texte_explicatif)
    window.after(2000, label_traitement.pack_forget)
    btn_rechercher.config(state='normal')
    jouer_son_fin_processus()


def effectuer_recherche_vols_selenium(driver, date_debut_str, date_fin_str, lieu_depart, durees_sejour, prix_max):
    global recherche_active
    recherche_active = True
    logging.info('Recherche active: {}'.format(recherche_active))
    date_debut = datetime.strptime(date_debut_str, "%d-%m-%Y")
    date_fin = datetime.strptime(date_fin_str, "%d-%m-%Y")
    
    meilleures_offres_par_duree = {}
    for duree_sejour_str in durees_sejour.split('/'):
        duree_sejour = int(duree_sejour_str.strip())
        date_actuelle = date_debut

        while date_actuelle + timedelta(days=duree_sejour) <= date_fin:
            if not recherche_active:
                print("Recherche arrêtée par l'utilisateur.")
                return None
            
            date_de_fin_sejour = date_actuelle + timedelta(days=duree_sejour)
            if date_de_fin_sejour > date_fin:  # Assure que la date de fin de séjour ne dépasse pas la plage autorisée.
                break

            date_out = date_actuelle.strftime("%Y-%m-%d")
            date_in = date_de_fin_sejour.strftime("%Y-%m-%d")
            meilleures_offres = {}  # Initialisation correcte de meilleures_offres

            url = f"https://www.ryanair.com/fr/fr/cheap-flights-beta?originIata={lieu_depart}&destinationIata=ANY&isReturn=true&isMacDestination=false&promoCode=&adults=1&teens=0&children=0&infants=0&dateOut={date_out}&dateIn={date_in}&daysTrip={duree_sejour}&dayOfWeek=TUESDAY&isExactDate=true&outboundFromHour=00:00&outboundToHour=23:59&inboundFromHour=00:00&inboundToHour=23:59&priceValueTo={prix_max}&currency=EUR&isFlexibleDay=false"
            driver.get(url)
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.country-card__content")))
                content = driver.page_source
                soup = BeautifulSoup(content, 'html.parser')
                cards = soup.select("div.country-card__content")
                meilleures_offres = {}
                for card in cards:
                    try:
                        # Hypothétique : extraction du nom du pays et du prix à partir de la structure de la carte
                        pays_text = card.find(class_="country-card__country").get_text(strip=True)
                        pays_match = re.match(r"^[^\d]*", pays_text)
                        if pays_match:
                            pays = pays_match.group(0)  # Utiliser group(0) pour obtenir la chaîne correspondante entière
                        else:
                            pays = None  # ou une chaîne vide si vous préférez ''

                        prix_text = card.find(class_="country-card__price").get_text(strip=True)
                        prix = float(prix_text.strip('€').replace(',', '.'))
                        details_vol = f"{date_out} - {date_in} | Prix: €{prix}"
                        
                        # Stocke ou traite les données extraites ici
                        if pays not in meilleures_offres or prix < meilleures_offres[pays]['prix']:
                            meilleures_offres[pays] = {'prix': prix, 'details': details_vol}
                    except Exception as e:
                        logging.error(f"Une erreur est survenue lors de la recherche: {e}", exc_info=True)
                        print(f"Erreur lors de l'extraction des données d'une carte: {e}")
                        continue

            except TimeoutException:
                print(f"TimeoutException pour la date de départ: {date_out}")
            
            date_actuelle += timedelta(days=1)

            if meilleures_offres:  # Vérifie si des offres ont été trouvées durant l'itération actuelle
                for pays, offre in meilleures_offres.items():
                    details_vol = offre['details']
                    prix = offre['prix']
                    if duree_sejour not in meilleures_offres_par_duree or prix < meilleures_offres_par_duree[duree_sejour].get(pays, {'prix': float('inf')})['prix']:
                        # Si l'offre actuelle est meilleure (moins chère) que celle déjà enregistrée, ou si aucune offre n'est enregistrée pour ce pays et cette durée
                        meilleures_offres_par_duree.setdefault(duree_sejour, {})[pays] = {'prix': prix, 'details': details_vol}

    # Après avoir terminé toutes les itérations et collecté les données, on retourne le dictionnaire contenant les meilleures offres par durée de séjour.
    return meilleures_offres_par_duree

# Activation de la recherche.
recherche_active = True

def lancer_recherche_vols():
    global recherche_active, driver
    recherche_active = True  # Assurez-vous que la recherche est activée
    logging.info('Lancement de la recherche de vols')
    
    # Récupérer les valeurs des champs de saisie
    date_debut_str = entry_date_debut.get()
    date_fin_str = entry_date_fin.get()
    lieu_depart = entry_lieu_depart.get()
    durees_sejour = entry_duree_sejour.get()  # Assurez-vous que ce champ est formaté correctement, par ex. "3,5,7"
    prix_max = entry_prix_max.get()

    # Appeler la fonction de recherche avec les paramètres récupérés
    try:
        resultats = effectuer_recherche_vols_selenium(driver, date_debut_str, date_fin_str, lieu_depart, durees_sejour, prix_max)
        afficher_resultats(resultats)  # Afficher les résultats dans le widget ScrolledText
    except Exception as e:
        logging.error(f"Une erreur est survenue lors de la recherche: {e}", exc_info=True)
        messagebox.showerror("Erreur", f"Une erreur est survenue lors de la recherche: {e}")
    finally:
        recherche_active = False  # Désactiver la recherche une fois terminée

def reinitialiser_formulaire():
    global recherche_active
    # Arrête la recherche en cours en mettant à jour la variable globale
    recherche_active = False
    
    # Réinitialise les champs de saisie aux valeurs par défaut
    entry_date_debut.delete(0, tk.END)
    entry_date_debut.insert(0, date_debut_defaut)
    entry_date_debut.config(state='disabled')
    
    entry_date_fin.delete(0, tk.END)
    entry_date_fin.insert(0, date_fin_defaut)
    entry_date_fin.config(state='disabled')
    
    entry_lieu_depart.delete(0, tk.END)
    entry_lieu_depart.insert(0, lieu_depart_defaut)
    
    entry_duree_sejour.delete(0, tk.END)
    entry_duree_sejour.insert(0, duree_sejour_defaut)
    entry_duree_sejour.config(state='disabled')
    
    entry_prix_max.delete(0, tk.END)
    entry_prix_max.insert(0, prix_max_defaut)
    entry_prix_max.config(state='disabled')
    
    # Efface le contenu de la zone de texte des résultats
    text_resultats.delete(1.0, tk.END)
    
    # Affiche un message ou réinitialise l'état d'autres éléments de l'UI si nécessaire
    label_traitement.config(text="Démarrer le processus !")
    btn_rechercher.config(state='normal')  # Réactive le bouton de recherche si désactivé
    
    # Optionnel : Affiche une notification indiquant que le formulaire a été réinitialisé
    messagebox.showinfo("Réinitialisation", "Le formulaire a été réinitialisé.")

def creer_action_changement_langue(nom_drapeau):
    def action():
        print(f"Drapeau cliqué : {nom_drapeau}")
        # Vous pouvez ajouter ici le code pour changer la langue ou naviguer vers un site web spécifique
    return action

def creer_action_changement_langue(langue):
    return lambda: changer_langue(langue)

# Dictionnaire des traductions 
traductions = {
    'france': {
        'titre': "Low Cost Europe",
        'texte_accueil' : ("Envie d'évasion prochainement ?                          \n\n"
                           "Si vous êtes flexible,\n"
                           "profitez des tarifs les plus bas !\n\n"
                           "Démarrez la recherche et attendez\n"
                           "le signal de fin. Patience !"),
        'rechercher': "Rechercher",
        'stopper': "Réinitialiser",
        'debut_recherche': "Début de la plage de recherche",
        'fin_recherche': "Fin de la plage de recherche",
        'aeroport_depart': "Aéroport de départ (code AITA)",
        'duree_sejour': "Durée du séjour",
        'prix_max': "Prix max en €",
        'demarrer_processus': "Démarrer le processus !",
        'choisir': "Choisir",
        'creation_info': "Création: Sotoca-Online - Version 1 - 022024",
        'aucune_offre': "Aucune offre trouvée pour les critères spécifiés.",
        'voyage_de': "Voyage de",
        'jours': "jours",
        'erreur_recherche': "Une erreur est survenue lors de la recherche :",
    },
    'royaume': {
        'titre': "Low Cost Europe",
        'texte_accueil': ("Looking for a getaway soon?                                \n\n"
                          "If you're flexible with your dates,\n"
                          "you can enjoy the best prices!\n\n"
                          "Start the search, and a final beep\n"
                          "will notify you, please be patient!"),
        'rechercher': "Search",
        'stopper': "Reset",
        'debut_recherche': "Start of search range",
        'fin_recherche': "End of search range",
        'aeroport_depart': "Departure airport (IATA code)",
        'duree_sejour': "Duration of stay",
        'prix_max': "Max price in €",
        'demarrer_processus': "Start the process!",
        'choisir': "Choose",
        'creation_info': "Creation: Sotoca-Online.com - Version 1 - 022024",
        'aucune_offre': "No offers found for the specified criteria.",
        'voyage_de': "Trip of",
        'jours': "days",
        'erreur_recherche': "An error occurred during the search:",
    },
    'italie': {
        'titre': "Low Cost Europe",
        'texte_accueil': ("Cerchi una fuga prossimamente?                    \n\n"
                          "Se sei flessibile con le date,\n"
                          "puoi approfittare dei migliori prezzi!\n\n"
                          "Avvia la ricerca e un segnale finale\n"
                          "ti avviserà, per favore sii paziente!"),
        'rechercher': "Cerca",
        'stopper': "Resettare",
        'debut_recherche': "Inizio dell'intervallo di ricerca",
        'fin_recherche': "Fine dell'intervallo di ricerca",
        'aeroport_depart': "Aeroporto di partenza (IATA)",
        'duree_sejour': "Durata del soggiorno",
        'prix_max': "Prezzo massimo in €",
        'demarrer_processus': "Avvia il processo!",
        'creation_info': "Creazione: Sotoca-Online.com - Versione 1 - 022024",
    },
    'espagne': {
        'titre': "Low Cost Europe",
        'texte_accueil': ("¿Buscas una escapada pronto?                       \n\n"
                          "Si tienes flexibilidad de fechas,\n"
                          "¡puedes disfrutar de los mejores precios!\n\n"
                          "Inicia la búsqueda, y un pitido final\n"
                          "te notificará, ¡por favor ten paciencia!"),
        'rechercher': "Buscar",
        'stopper': "Restablecer",
        'debut_recherche': "Inicio del periodo de búsqueda",
        'fin_recherche': "Fin del periodo de búsqueda",
        'aeroport_depart': "Aeropuerto de salida (IATA)",
        'duree_sejour': "Duración de la estancia",
        'prix_max': "Precio máximo en €",
        'demarrer_processus': "¡Iniciar el proceso!",
        'choisir': "Elegir",
        'creation_info': "Creación: Sotoca-Online.com - Versión 1 - 022024",
    },
    'allemagne': {
        'titre': "Low Cost Europe",
        'texte_accueil': ("Suchst du bald einen Kurzurlaub?                        \n\n"
                          "Wenn du mit deinen Daten flexibel bist,\n"
                          "kannst du die besten Preise genießen!\n\n"
                          "Starte die Suche, und ein abschließendes Piepen\n"
                          "wird dich benachrichtigen, bitte gedulde dich!"),
        'rechercher': "Suchen",
        'stopper': "Zurücksetzen",
        'debut_recherche': "Beginn des Suchzeitraums",
        'fin_recherche': "Ende des Suchzeitraums",
        'aeroport_depart': "Abflughafen (IATA-Code)",
        'duree_sejour': "Aufenthaltsdauer",
        'prix_max': "Maximalpreis in €",
        'demarrer_processus': "Prozess starten!",
        'choisir': "Wählen",
        'creation_info': "Erstellung: Sotoca-Online.com - Version 1 - 022024",
    },
}

# Fonction pour changer la langue
def changer_langue(langue):
    # Met à jour le titre de la fenêtre
    window.title(traductions[langue]['titre'])
    # Met à jour les textes des boutons et labels
    btn_rechercher.config(text=traductions[langue]['rechercher'])
    
    btn_stop.config(text=traductions[langue]['stopper'])
    btn_stop.config(command=stopper_et_reinitialiser)
    
    label_date_debut.config(text=traductions[langue]['debut_recherche'])
    label_date_fin.config(text=traductions[langue]['fin_recherche'])
    label_lieu_depart.config(text=traductions[langue]['aeroport_depart'])
    label_duree_sejour.config(text=traductions[langue]['duree_sejour'])
    label_prix_max.config(text=traductions[langue]['prix_max'])
    label_instructions.config(text=traductions[langue]['texte_accueil']) 
    label_contacts.config(text=traductions[langue]['creation_info']) 
    label_traitement.config(text=traductions[langue]['demarrer_processus']) 
# Définition des polices du texte principal
police_grande = font.Font(family="Helvetica", size=10) 
largeur_champs = 20

# Texte d'accueil et label d'instructions
texte_accueil = (
    "Envie d'évasion prochainement ?                          \n\n"
    "Si vous êtes flexible,\n"
    "profitez des tarifs les plus bas !\n\n"
    "Démarrez la recherche et attendez\n"
    "le signal de fin. Patience !"
)
wraplength_desire = 500
label_instructions = tk.Label(
    window,
    text=texte_accueil,
    bg='lightblue',
    font=police_grande,
    wraplength=wraplength_desire,
    justify="left"
)
label_instructions.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

# Fonction pour mettre à jour le champ de saisie du lieu de départ
def choisir_aeroport(event):
    code_iata = combo_aeroports.get().split(" ")[0]  # Récupère le code IATA de la sélection
    entry_lieu_depart.delete(0, tk.END)
    entry_lieu_depart.insert(0, code_iata)

# Liste des aéroports (code IATA et nom complet)
aeroports = [
  ("AJA", "Campo dell'Oro Airport"),
  ("BIA", "Poretta Airport"),
  ("BOD", "Mérignac Airport"),
  ("BVA", "Beauvais-Tillé Airport"),
  ("CDG", "Charles de Gaulle Airport"),
  ("FSC", "Figari Sud-Corse Airport"),
  ("LGB", "Grand Columbier Airport"),
  ("LIG", "Bellegarde Airport"),
  ("LRY", "La Rochelle Airport"),
  ("LYS", "Saint-Exupéry Airport"),
  ("MRS", "Provence Airport"),
  ("NTE", "Nantes Atlantique Airport"),
  ("ORY", "Orly Airport"),
  ("PIS", "Biard Airport"),
  ("PUF", "Pau-Pyrénées Airport"),
  ("TLN", "Hyères Le Palyvestre Airport"),
  ("TLS", "Blagnac Airport"),
  ("VRN", "Verona Airport"),
  ("MPL", "Montpellier Méditerranée Airport"),
  ("BIQ", "Biarritz Airport"),
  ("RNS", "Rennes Bretagne Airport"),
  ("CFR", "Carpiquet Airport"),
  ("LIL", "Lille Airport"),
  ("SXB", "Strasbourg Airport"),
  ("NCE", "Nice - Côte d'Azur Airport")
]

# Création et placement du logo
chemin_logo = chemin_relatif('logo.png')
logo_image = tk.PhotoImage(file=chemin_logo)
label_logo = Label(window, image=logo_image, bg='lightblue')
label_logo.grid(row=0, column=0, padx=10, pady=10, sticky="w")

# Création et placement de l'avion
chemin_avion = chemin_relatif('avion.gif')
avion_image = tk.PhotoImage(file=chemin_avion)
label_avion = Label(window, image=avion_image, bg='lightblue')
label_avion.grid(row=5, rowspan=6,column=1, padx=10, pady=10, sticky="e")

# Configuration des labels pour les champs de saisie
label_date_debut = Label(window, text="Début de la plage de recherche", bg='lightblue')
label_date_fin = Label(window, text="Fin de la plage de recherche", bg='lightblue')
label_lieu_depart = Label(window, text="Aéroport de départ (code AITA)", bg='lightblue')
label_duree_sejour = Label(window, text="Durée du séjour", bg='lightblue')
label_prix_max = Label(window, text="Prix max en €", bg='lightblue')

# Positionnement des labels
label_date_debut.grid(row=1, column=0, padx=10, pady=5, sticky="e")
label_date_fin.grid(row=2, column=0, padx=10, pady=5, sticky="e")
label_lieu_depart.grid(row=3, column=0, padx=10, pady=5, sticky="e")
label_duree_sejour.grid(row=4, column=0, padx=10, pady=5, sticky="e")
label_prix_max.grid(row=5, column=0, padx=10, pady=5, sticky="e")

# Création et positionnement des champs de saisie et boutons

combo_aeroports = ttk.Combobox(window, values=[f"{code} {nom}" for code, nom in aeroports], state="readonly")
combo_aeroports.bind("<<ComboboxSelected>>", choisir_aeroport)

entry_date_debut = Entry(window, width=12)
entry_date_fin = Entry(window, width=12)
entry_lieu_depart = Entry(window, width=12)
entry_duree_sejour = Entry(window, width=12)
entry_prix_max = Entry(window, width=12)

entry_date_debut.grid(row=1, column=1, padx=10, pady=5, sticky="w")
entry_date_fin.grid(row=2, column=1, padx=10, pady=5, sticky="w")
entry_lieu_depart.grid(row=3, column=1, padx=10, pady=5, sticky="w")
entry_duree_sejour.grid(row=4, column=1, padx=10, pady=5, sticky="w")
entry_prix_max.grid(row=5, column=1, padx=10, pady=5, sticky="w")

btn_rechercher = Button(window, text="Rechercher", command=lancer_recherche_vols, width=10)
btn_rechercher.grid(row=6, column=1, padx=10, pady=10, sticky="w")

btn_stop = Button(window, text="Réinitialiser", command=reinitialiser_formulaire, width=10)
btn_stop.grid(row=7, column=1, padx=10, pady=5, sticky="w")

combo_aeroports.grid(row=3, column=1, padx=(0, 15), pady=5, sticky="e") 

# Insérer les valeurs par défaut dans les champs de saisie - réglage
date_demain = datetime.now() + timedelta(days=1)
date_debut_defaut = (date_demain + timedelta(days=0)).strftime("%d-%m-%Y")
date_fin_defaut = (date_demain + timedelta(days=30)).strftime("%d-%m-%Y")
lieu_depart_defaut = "MRS"
duree_sejour_defaut = "5"
prix_max_defaut = "50"

entry_date_debut.insert(0, date_debut_defaut)
entry_date_debut.config(state='disabled')

entry_date_fin.insert(0, date_fin_defaut)
entry_date_fin.config(state='disabled')

entry_lieu_depart.insert(0, lieu_depart_defaut)

entry_duree_sejour.insert(0, duree_sejour_defaut)
entry_duree_sejour.config(state='disabled')

entry_prix_max.insert(0, prix_max_defaut)
entry_prix_max.config(state='disabled')
    
# Création et positionnement de la zone de texte pour les résultats
text_resultats = scrolledtext.ScrolledText(window, height=30, width=55)
text_resultats.grid(row=0, column=2, rowspan=8, padx=10, pady=10, sticky="ne")

# Label de traitement
label_traitement = Label(window, text="Démarrer le processus !", bg='lightblue')
label_traitement.grid(row=6, column=0, padx=10, pady=10, sticky="e")

# Label des contacts
label_contacts = tk.Label(window, text="Création : Sotoca-Online - Version 1 - 022024", bg='lightblue')
label_contacts.grid(row=8, column=0, columnspan=3, pady=10, sticky="nsew")

# Ajout des drapeaux
noms_drapeaux = ['france', 'royaume', 'espagne', 'italie', 'allemagne']
labels_drapeaux = []

# Crée un Frame pour contenir tous les drapeaux
frame_drapeaux = tk.Frame(window, bg='lightblue')
# frame_drapeaux.grid(row=8, column=0, columnspan=3, padx=20, pady=2, sticky="w")
frame_drapeaux.grid(row=7, column=0, columnspan=3, padx=20, pady=2, sticky="w")

# Création des boutons de drapeaux et chargement des images
for nom_drapeau in noms_drapeaux:
    chemin_image = chemin_relatif(f"{nom_drapeau}.png")
    image_drapeau = tk.PhotoImage(file=chemin_image).subsample(2)  # Ajustez la taille si nécessaire
    action_changement_langue = creer_action_changement_langue(nom_drapeau)
    label_drapeau = tk.Button(frame_drapeaux, image=image_drapeau, bg='lightblue', command=action_changement_langue)
    label_drapeau.image = image_drapeau  # Conservez une référence
    label_drapeau.pack(side="left", padx=3)

# Ajoutez votre code pour la boucle principale de Tkinter ici
window.mainloop()
