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

# Fonction pour démarrer la mise à jour de la barre de progression
def start_progress():
    progress["value"] = 0  # Réinitialisez la valeur de départ
    window.after(100, update_progress)

# Ajustez votre fonction update_progress pour tenir compte de recherche_active
def update_progress():
    global recherche_active 
    if recherche_active:
        # Mise à jour plus lente pour simuler une longue opération
        new_value = progress['value'] + (100 / (15 * 60 / 0.5)) 
        if new_value < progress['maximum']:
            progress['value'] = new_value
            window.after(500, update_progress)
        else:
            progress['value'] = progress['maximum']
            recherche_active = False
            btn_rechercher.config(state='normal')
            messagebox.showinfo("Recherche terminée", "La recherche est terminée.")
    else:
        progress['value'] = 0 
        btn_rechercher.config(state='normal')

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

    },
    'royaume': {
        'titre': "Travel_Low_Cost",

    },
    'italie': {
        'titre': "Viaggio_A_Basso_Costo",
        
    },
    'espagne': {
        'titre': "Viaje_Mini_Precio",

    },
    'allemagne': {
        'titre': "Reise_zum_Kleinen_Preis",

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

# Initialisation du driver en dehors de la fonction effectuer_recherche_vols_selenium
options = webdriver.FirefoxOptions()
options.add_argument("--headless")
service = FirefoxService(GeckoDriverManager().install())
driver = webdriver.Firefox(service=service, options=options)

def attendre_resultats_ou_absence(driver, results_selector="div.country-card__content", no_results_selector="ffr-no-results.ng-star-inserted, span.no-flights_primary-title", timeout=10):
    try:
        # Attend que l'un des éléments soit visible
        WebDriverWait(driver, timeout).until(
            lambda driver: driver.find_elements(By.CSS_SELECTOR, results_selector) or driver.find_elements(By.CSS_SELECTOR, no_results_selector)
        )
        # Vérifie quel élément est présent
        if driver.find_elements(By.CSS_SELECTOR, results_selector):
            return "results"
        elif driver.find_elements(By.CSS_SELECTOR, no_results_selector):
            return "no_results"
    except TimeoutException:
        return "timeout"

# Utilisation de la fonction
status = attendre_resultats_ou_absence(driver)
if status == "results":
    print("Des résultats sont disponibles.")
elif status == "no_results":
    print("Aucun résultat correspondant à la recherche.")
else:
    print("Le chargement de la page a dépassé le temps d'attente.")



def effectuer_recherche_vols_selenium(driver, date_debut_str, date_fin_str, lieu_depart, durees_sejour, prix_max):
    global recherche_active
    date_debut = datetime.strptime(date_debut_str, "%d-%m-%Y")
    duree_max_sejour = max(durees_sejour)
    date_fin = datetime.strptime(date_fin_str, "%d-%m-%Y") + timedelta(days=duree_max_sejour)

    meilleures_offres_par_duree = {}

    for duree_sejour in durees_sejour:  # Utilisez directement les entiers de la liste
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
                # WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.country-card__content")))

                status = attendre_resultats_ou_absence(driver)
                if status == "no_results":
                    print("Aucun résultat pour cette recherche.")
                    continue  # Passe à la prochaine itération de la boucle de recherche
                elif status == "timeout":
                    print("Le chargement de la page a dépassé le temps d'attente.")
                    continue  # Optionnel : gérer le timeout selon tes besoins
                # Traite les résultats si status == "results"

                
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

def ouvrir_lien(url):
    def callback(e):
        webbrowser.open(url, new=2)
    return callback

# Obtient le chemin d'accès au dossier actuel où se trouve le script
dossier_courant = os.path.dirname(__file__)
chemin_images = dossier_courant 

noms_drapeaux = ['france', 'royaume', 'espagne', 'italie', 'allemagne']
labels_drapeaux = []

# Crée un Frame pour contenir tous les drapeaux
frame_drapeaux = tk.Frame(window, bg='lightblue')
frame_drapeaux.grid(row=8, column=0, columnspan=3, padx=20, pady=2, sticky="w")  # Étendre le Frame sur les colonnes nécessaires
   
# Création du Frame pour les drapeaux et chargement des images avec chemin_relatif
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
    print("faire_clignoter_label appelée, clignotement_en_cours:", clignotement_en_cours)  # Ajout pour le débogage
    if clignotement_en_cours:
        current_text = label_traitement.cget("text")
        new_text = "" if current_text else "Recherche en cours..."
        label_traitement.config(text=new_text)
        window.after(500, faire_clignoter_label)
    else:
        label_traitement.config(text="")  # Assurez-vous que le texte est vide si le clignotement est désactivé

# Fonction appelée lorsque l'utilisateur clique sur le bouton Rechercher
def lancer_recherche_vols():
    global recherche_active, clignotement_en_cours
    if not recherche_active:
        recherche_active = True
        clignotement_en_cours = True  # définir cette variable sur True pour commencer le clignotement
        faire_clignoter_label()  # Commencez le clignotement
        btn_rechercher.config(state='disabled')
        progress['value'] = 0
        start_progress()
        threading.Thread(target=rechercher_vols, daemon=True).start()

# Fonction pour exécuter la recherche de vols et mettre à jour l'interface avec les résultats
def rechercher_vols():
    global recherche_active
    recherche_active = True
    start_progress()  # Démarrez la progression ici
    try:
        date_debut_str = entry_date_debut.get()
        date_fin_str = entry_date_fin.get()
        lieu_depart = entry_lieu_depart.get()
        # durees_sejour = entry_duree_sejour.get()  # Maintenant, plusieurs durées possibles
        durees_sejour_str = entry_duree_sejour.get()  # Récupère la chaîne
        durees_sejour = [int(d.strip()) for d in durees_sejour_str.split(',')]  # Convertit en liste d'entiers
        prix_max = float(entry_prix_max.get())

        resultats_par_duree = effectuer_recherche_vols_selenium(driver, date_debut_str, date_fin_str, lieu_depart, durees_sejour, prix_max)
        # resultats_par_duree = effectuer_recherche_vols_selenium(date_debut_str, date_fin_str, lieu_depart, durees_sejour, prix_max)
        print(f"Résultats obtenus: {resultats_par_duree}")  # Débogage
        window.after(0, afficher_resultats, resultats_par_duree)
    except Exception as e:
        window.after(0, lambda e=e: messagebox.showerror("Erreur", f"Une erreur est survenue lors de la recherche : {e}"))
        print(f"Erreur lors de la recherche: {e}")  # Débogage
    finally:
        recherche_active = False
        window.after(0, update_progress)  # Assurez-vous de mettre à jour l'interface utilisateur dans le thread principal

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
    print("Affichage des résultats...")  # Débogage
    if not resultats_par_duree:
        messagebox.showinfo("Aucune offre", "Aucune offre trouvée pour les critères spécifiés.")
        print("Aucun résultat à afficher.")  # Débogage
    else:
        
        for duree, offres in resultats_par_duree.items():
            text_resultats.insert(tk.END, f"Voyage de {duree} jours\n\n")
            for pays, infos in offres:
                # Extrais les détails du vol qui incluent les dates au format international et le prix
                details_vol = infos['details']  # Cette variable devrait contenir "YYYY-MM-DD - YYYY-MM-DD | Prix: €XXX.XX"
                date_out, rest = details_vol.split(" - ")
                date_in, prix_vol = rest.split(" | ")
                
                # Convertis les dates au format français pour l'affichage
                # date_out_affichage_fr = datetime.strptime(date_out, "%Y-%m-%d").strftime("%d-%m-%Y")
                # date_in_affichage_fr = datetime.strptime(date_in, "%Y-%m-%d").strftime("%d-%m-%Y")
                # Convertis les dates au format français pour l'affichage
                date_out_affichage_fr = datetime.strptime(date_out, "%Y-%m-%d").strftime("%d/%m")
                date_in_affichage_fr = datetime.strptime(date_in, "%Y-%m-%d").strftime("%d/%m")
                
                # Construction de l'URL avec les dates au format international pour les liens
                url = f"https://www.ryanair.com/fr/fr/cheap-flights-beta?originIata={entry_lieu_depart.get()}&destinationIata=ANY&isReturn=true&isMacDestination=false&promoCode=&adults=1&teens=0&children=0&infants=0&dateOut={date_out}&dateIn={date_in}&daysTrip={duree}&dayOfWeek=TUESDAY&isExactDate=true&outboundFromHour=00:00&outboundToHour=23:59&inboundFromHour=00:00&inboundToHour=23:59&priceValueTo={entry_prix_max.get()}&currency=EUR&isFlexibleDay=false"
                
                # Insère le nom du pays (qui sera cliquable)
                text_resultats.insert(tk.END, pays)
                
                # Ajoute le tag de lien uniquement au nom du pays
                tag_name = f"link_{pays.replace(' ', '_')}_{date_out.replace('-', '_')}"
                text_resultats.tag_add(tag_name, "end-1c linestart", "end-1c")
                text_resultats.tag_config(tag_name, foreground="blue", underline=1)
                text_resultats.tag_bind(tag_name, "<Button-1>", ouvrir_lien(url))

                # Continue d'insérer le reste des détails du vol sans les rendre cliquables
                text_resultats.insert(tk.END, f" : {date_out_affichage_fr} - {date_in_affichage_fr} | {prix_vol}\n")
                
            text_resultats.insert(tk.END, "-"*50 + "\n")
            
        # Insérez le texte explicatif ici
        texte_explicatif = "\nCliquez sur les noms des pays pour voir les offres\ndétaillées par ville sur le site de Ryanair."
        text_resultats.insert(tk.END, texte_explicatif)
    
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
    entry_prix_max.delete(0, tk.END)
    
    # Réinsérer les valeurs par défaut
    entry_date_debut.insert(0, date_debut_defaut)
    entry_date_fin.insert(0, date_fin_defaut)
    entry_lieu_depart.insert(0, lieu_depart_defaut)
    entry_duree_sejour.insert(0, duree_sejour_defaut)
    entry_prix_max.insert(0, prix_max_defaut)    
    
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
    ("AAA", "A venir !"),
]

# Initialisation de style avant son utilisation
style = ttk.Style(window)
style.theme_use('default')  # autre thème comme 'clam', 'alt', 'classic', etc.

# Configurez le style de la barre de progression une fois que `style` a été initialisé
style.configure("green.Horizontal.TProgressbar", troughcolor='white', background='green')

# Créez la barre de progression en utilisant le style configuré
progress = ttk.Progressbar(window, style="green.Horizontal.TProgressbar", orient="horizontal", mode="determinate", length=200)

# Positionnez la barre de progression dans la grille avec un espace suffisant
progress.grid(row=8, column=2, padx=10, pady=10, sticky="ew")

# Initialisez la barre de progression avec un maximum et une valeur de départ
progress["maximum"] = 100
progress["value"] = 0

# Configuration de la grille
window.grid_rowconfigure(0, weight=1)
window.grid_rowconfigure(1, weight=1)
window.grid_columnconfigure(0, weight=0)
window.grid_columnconfigure(1, weight=1)
window.grid_columnconfigure(2, weight=1)

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

# Réglage - Création et initialisation des champs de saisie avec valeurs par défaut
date_demain = datetime.now() + timedelta(days=1)
date_debut_defaut = (date_demain + timedelta(days=25)).strftime("%d-%m-%Y")
date_fin_defaut = (date_demain + timedelta(days=50)).strftime("%d-%m-%Y")
lieu_depart_defaut = "MRS"
duree_sejour_defaut = "4,5"
prix_max_defaut = "100"

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

# Remplacez ces lignes
# btn_date_debut.grid(row=2, column=1, padx=(0, 135), pady=5, sticky="e")  
# btn_date_fin.grid(row=3, column=1, padx=(0, 135), pady=5, sticky="e")

# Avec ces lignes pour les retirer de la grille
btn_date_debut.grid_remove()  
btn_date_fin.grid_remove()  
combo_aeroports.grid(row=4, column=1, padx=(0, 15), pady=5, sticky="e") 

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

# Positionnement des widgets de saisie 
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
text_resultats = scrolledtext.ScrolledText(window, height=40, width=50)  
text_resultats.grid(row=0, column=2, rowspan=8, padx=10, pady=10, sticky="nsew")

label_traitement = Label(window, text="Démarrer le processus !", bg='lightblue')
label_traitement.grid(row=8, column=1, padx=10, pady=10, sticky="e")

# Test immédiat du clignotement
clignotement_en_cours = False
faire_clignoter_label()

# Création et positionnement du label des contacts
label_contacts = tk.Label(window, text="Création : Sotoca-Online - Version 1.4 - 022024", bg='lightblue')
label_contacts.grid(row=11, column=0, columnspan=3, pady=10, sticky="nsew")

# Lancement de l'application
window.mainloop()
