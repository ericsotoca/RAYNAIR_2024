import tkinter as tk
from tkinter import scrolledtext, Label, Entry, Button, messagebox
from tkinter import font
# from ttkthemes import ThemedStyle
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

# Configuration de la grille
window.grid_rowconfigure(0, weight=1)
window.grid_rowconfigure(1, weight=1)
window.grid_columnconfigure(0, weight=0)
window.grid_columnconfigure(1, weight=1)
window.grid_columnconfigure(2, weight=1)


# Initialisation du driver en dehors de la fonction effectuer_recherche_vols_selenium
options = webdriver.FirefoxOptions()
options.add_argument("--headless")
service = FirefoxService(GeckoDriverManager().install())
driver = webdriver.Firefox(service=service, options=options)

def effectuer_recherche_vols_selenium(driver, date_debut_str, date_fin_str, lieu_depart, durees_sejour, prix_max):
    global recherche_active
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
                return None

            date_out_affichage = date_actuelle.strftime("%d-%m-%Y")
            date_in_affichage = (date_actuelle + timedelta(days=duree_sejour)).strftime("%d-%m-%Y")
            date_out = date_actuelle.strftime("%Y-%m-%d")
            date_in = (date_actuelle + timedelta(days=duree_sejour)).strftime("%Y-%m-%d")

            url = f"https://www.ryanair.com/fr/fr/cheap-flights-beta?originIata={lieu_depart}&destinationIata=ANY&isReturn=true&isMacDestination=false&promoCode=&adults=1&teens=0&children=0&infants=0&dateOut={date_out}&dateIn={date_in}&daysTrip={duree_sejour}&dayOfWeek=TUESDAY&isExactDate=true&outboundFromHour=00:00&outboundToHour=23:59&inboundFromHour=00:00&inboundToHour=23:59&priceValueTo={prix_max}&currency=EUR&isFlexibleDay=false"
            
            driver.get(url)
            try:
                WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.country-card__content")))
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
                        if pays == "République":
                            pays = "République tchèque"

                        if pays not in meilleures_offres or meilleures_offres[pays]["prix"] > prix:
                            meilleures_offres[pays] = {"prix": prix, "details": details_vol}
            except TimeoutException:
                print(f"TimeoutException pour la date de départ: {date_out_affichage}")

            date_actuelle += timedelta(days=1)

        meilleures_offres_par_duree[duree_sejour] = sorted(meilleures_offres.items(), key=lambda offre: offre[1]['prix'])

    return meilleures_offres_par_duree

# Définissez recherche_active sur True pour éviter une sortie anticipée de la fonction
recherche_active = True

# Lancement de l'application et exécution des recherches dans un bloc try...finally
try:
    # Exécutez la fonction et imprimez les résultats
    date_debut_test = "15-02-2024"
    date_fin_test = "19-02-2024"
    lieu_depart_test = "MRS"
    durees_sejour_test = "3,4"
    prix_max_test = "150"

    resultats = effectuer_recherche_vols_selenium(driver, date_debut_test, date_fin_test, lieu_depart_test, durees_sejour_test, prix_max_test)
    print(resultats)
finally:
    driver.quit()  # Cette ligne assure que le navigateur se ferme correctement.

window.mainloop()