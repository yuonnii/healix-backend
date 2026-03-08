"""
Healix Database Seeder — Algerian Data
========================================
Usage:
    python manage.py seed                    # seed everything
    python manage.py seed --clear            # wipe all data first, then seed
    python manage.py seed --only users       # seed only users
    python manage.py seed --only doctors     # seed only doctors + specialties
    python manage.py seed --only pharmacies  # seed only pharmacies + medicines
    python manage.py seed --only appointments
    python manage.py seed --only prescriptions
"""

import random
from datetime import date, time, timedelta, datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


# ─── Algerian Data ────────────────────────────────────────────────────────────

WILAYAS = [
    "Alger", "Oran", "Constantine", "Annaba", "Blida",
    "Sétif", "Tlemcen", "Béjaïa", "Batna", "Tizi Ouzou",
]

ALGERIAN_FIRST_NAMES_MALE = [
    "Karim", "Mohamed", "Yacine", "Amine", "Bilal", "Rayan",
    "Sofiane", "Mehdi", "Ilyas", "Hichem", "Nassim", "Walid",
    "Tarek", "Rachid", "Djamel", "Farid", "Hamza", "Anis",
    "Sami", "Adel", "Fares", "Lotfi", "Omar", "Khalil",
    "Nabil", "Mourad", "Samir", "Toufik", "Zakaria", "Amar",
]

ALGERIAN_FIRST_NAMES_FEMALE = [
    "Sara", "Amira", "Nadia", "Lyna", "Imane", "Yasmine",
    "Sonia", "Fatima", "Houria", "Meriem", "Rania", "Asma",
    "Dalila", "Nawel", "Samira", "Leila", "Hajar", "Souad",
    "Djamila", "Karima", "Wafa", "Zineb", "Sabrina", "Nawal",
    "Amel", "Hafsa", "Sihem", "Dounia", "Khaoula", "Louiza",
]

ALGERIAN_LAST_NAMES = [
    "Benali", "Boudiaf", "Mammeri", "Kaci", "Ait Ahmed",
    "Bensalem", "Hamidouche", "Meziane", "Kerroum", "Ouali",
    "Bouzid", "Cherif", "Hadj Ali", "Benkhaled", "Rahmani",
    "Mekki", "Belloumi", "Amrani", "Ferhat", "Ziane",
    "Boukhari", "Sellami", "Djaafri", "Touati", "Belkacemi",
    "Mebarki", "Hadjadj", "Tebboune", "Sahraoui", "Guenifi",
    "Benmoussa", "Chibane", "Larbaoui", "Yahi", "Mokrani",
    "Bouazza", "Drif", "Bencheikh", "Hamouche", "Boudoukha",
]

ALGERIAN_STREETS = [
    "Rue Didouche Mourad", "Rue Larbi Ben M'hidi", "Rue Belouizdad",
    "Boulevard Zighoud Youcef", "Rue Hassiba Ben Bouali",
    "Avenue du 1er Novembre", "Rue Ali Boumendjel",
    "Boulevard Colonel Amirouche", "Rue des Frères Bouadou",
    "Avenue Pasteur", "Rue Abane Ramdane", "Boulevard Salah Bouakouir",
    "Rue Mohamed Khemisti", "Avenue du Peuple", "Rue Khelifa Boukhalfa",
    "Boulevard de la République", "Rue Ferhat Boussaad",
    "Cité des Orangers", "Rue Bab El Oued", "Avenue de l'ALN",
]

ALGERIAN_PHONE_PREFIXES = ["0555", "0770", "0660", "0699", "0561", "0550", "0771", "0662"]

SPECIALTIES_DATA = [
    {"name": "Médecine Générale",      "icon": "stethoscope",   "description": "Soins primaires et médecine préventive pour tous les âges."},
    {"name": "Cardiologie",            "icon": "heart",         "description": "Diagnostic et traitement des maladies cardiovasculaires."},
    {"name": "Dermatologie",           "icon": "skin",          "description": "Traitement des affections de la peau, des cheveux et des ongles."},
    {"name": "Pédiatrie",              "icon": "baby",          "description": "Soins médicaux pour les nourrissons, enfants et adolescents."},
    {"name": "Gynécologie-Obstétrique","icon": "female",        "description": "Santé féminine, grossesse et accouchement."},
    {"name": "Ophtalmologie",          "icon": "eye",           "description": "Soins des yeux et traitement des troubles visuels."},
    {"name": "Orthopédie",             "icon": "bone",          "description": "Chirurgie et traitement des os, articulations et muscles."},
    {"name": "Neurologie",             "icon": "brain",         "description": "Diagnostic et traitement des troubles du système nerveux."},
    {"name": "Psychiatrie",            "icon": "mind",          "description": "Santé mentale, diagnostic et traitement des troubles psychiatriques."},
    {"name": "Endocrinologie",         "icon": "gland",         "description": "Troubles hormonaux, diabète et maladies thyroïdiennes."},
    {"name": "Gastro-entérologie",     "icon": "stomach",       "description": "Maladies du système digestif, estomac, foie et intestins."},
    {"name": "Pneumologie",            "icon": "lungs",         "description": "Maladies respiratoires, asthme et bronchopneumopathies."},
    {"name": "Rhumatologie",           "icon": "joint",         "description": "Maladies articulaires, arthrite et maladies auto-immunes."},
    {"name": "Urologie",               "icon": "kidney",        "description": "Affections des voies urinaires et de l'appareil génital masculin."},
    {"name": "ORL",                    "icon": "ear",           "description": "Oreille, nez, gorge et chirurgie cervico-faciale."},
]

DOCTOR_BIOS = [
    "Médecin spécialiste avec plus de {years} ans d'expérience, formé à l'Université d'Alger. Membre actif de la Société Algérienne de {specialty}.",
    "Praticien dévoué, diplômé de la Faculté de Médecine de Constantine. {years} ans d'expérience clinique et hospitalière en {specialty}.",
    "Spécialiste certifié en {specialty}, avec une formation complémentaire en France et en Belgique. {years} ans de pratique en Algérie.",
    "Ancien chef de service au CHU de {wilaya}, spécialisé en {specialty}. Plus de {years} ans d'expérience au service des patients.",
    "Médecin praticien passionné, {years} ans d'expérience en {specialty}. Approche centrée sur le patient et la médecine préventive.",
]

CLINIC_NAMES = [
    "Cabinet Médical {name}", "Clinique {name}", "Centre de Santé {name}",
    "Polyclinique {name}", "Cabinet Spécialisé Dr. {name}",
    "Centre Médical {specialty}", "Clinique Privée {name}",
]

MEDICINES_DATA = [
    # Antibiotics
    {"name": "Amoxicilline", "generic_name": "Amoxicilline trihydrate", "brand_name": "Clamoxyl",
     "dosage_form": "capsule", "strength": "500mg", "category": "Antibiotique",
     "requires_prescription": True, "description": "Antibiotique de la famille des pénicillines."},
    {"name": "Amoxicilline + Acide Clavulanique", "generic_name": "Co-amoxiclav", "brand_name": "Augmentin",
     "dosage_form": "tablet", "strength": "875mg/125mg", "category": "Antibiotique",
     "requires_prescription": True, "description": "Association antibiotique et inhibiteur de bêta-lactamase."},
    {"name": "Azithromycine", "generic_name": "Azithromycine", "brand_name": "Zithromax",
     "dosage_form": "tablet", "strength": "500mg", "category": "Antibiotique",
     "requires_prescription": True, "description": "Antibiotique macrolide à large spectre."},
    {"name": "Ciprofloxacine", "generic_name": "Ciprofloxacine HCl", "brand_name": "Ciproxine",
     "dosage_form": "tablet", "strength": "500mg", "category": "Antibiotique",
     "requires_prescription": True, "description": "Fluoroquinolone à large spectre."},
    {"name": "Métronidazole", "generic_name": "Métronidazole", "brand_name": "Flagyl",
     "dosage_form": "tablet", "strength": "500mg", "category": "Antibiotique",
     "requires_prescription": True, "description": "Antibiotique et antiparasitaire."},

    # Pain & Anti-inflammatory
    {"name": "Paracétamol", "generic_name": "Paracétamol", "brand_name": "Doliprane",
     "dosage_form": "tablet", "strength": "1000mg", "category": "Analgésique",
     "requires_prescription": False, "description": "Antalgique et antipyrétique de référence."},
    {"name": "Ibuprofène", "generic_name": "Ibuprofène", "brand_name": "Brufen",
     "dosage_form": "tablet", "strength": "400mg", "category": "Anti-inflammatoire",
     "requires_prescription": False, "description": "AINS indiqué dans la douleur et la fièvre."},
    {"name": "Diclofénac", "generic_name": "Diclofénac sodique", "brand_name": "Voltarène",
     "dosage_form": "tablet", "strength": "50mg", "category": "Anti-inflammatoire",
     "requires_prescription": True, "description": "Anti-inflammatoire non stéroïdien."},
    {"name": "Tramadol", "generic_name": "Tramadol HCl", "brand_name": "Topalgic",
     "dosage_form": "capsule", "strength": "50mg", "category": "Analgésique opioïde",
     "requires_prescription": True, "description": "Antalgique central à action mixte."},
    {"name": "Kétoprofène", "generic_name": "Kétoprofène", "brand_name": "Profénid",
     "dosage_form": "tablet", "strength": "100mg", "category": "Anti-inflammatoire",
     "requires_prescription": True, "description": "AINS utilisé dans les douleurs articulaires."},

    # Cardiovascular
    {"name": "Amlodipine", "generic_name": "Amlodipine bésylate", "brand_name": "Amlor",
     "dosage_form": "tablet", "strength": "5mg", "category": "Antihypertenseur",
     "requires_prescription": True, "description": "Inhibiteur calcique pour l'hypertension."},
    {"name": "Ramipril", "generic_name": "Ramipril", "brand_name": "Triatec",
     "dosage_form": "tablet", "strength": "5mg", "category": "Antihypertenseur",
     "requires_prescription": True, "description": "IEC utilisé dans l'hypertension et l'insuffisance cardiaque."},
    {"name": "Atorvastatine", "generic_name": "Atorvastatine calcique", "brand_name": "Tahor",
     "dosage_form": "tablet", "strength": "20mg", "category": "Hypolipémiant",
     "requires_prescription": True, "description": "Statine pour réduire le cholestérol."},
    {"name": "Bisoprolol", "generic_name": "Bisoprolol fumarate", "brand_name": "Cardensiel",
     "dosage_form": "tablet", "strength": "5mg", "category": "Bêtabloquant",
     "requires_prescription": True, "description": "Bêtabloquant cardiosélectif."},
    {"name": "Aspirine", "generic_name": "Acide acétylsalicylique", "brand_name": "Aspégic",
     "dosage_form": "tablet", "strength": "100mg", "category": "Antiagrégant plaquettaire",
     "requires_prescription": False, "description": "Antiagrégant plaquettaire faible dose."},

    # Diabetes
    {"name": "Metformine", "generic_name": "Metformine HCl", "brand_name": "Glucophage",
     "dosage_form": "tablet", "strength": "500mg", "category": "Antidiabétique",
     "requires_prescription": True, "description": "Biguanide de référence pour le diabète de type 2."},
    {"name": "Glibenclamide", "generic_name": "Glibenclamide", "brand_name": "Daonil",
     "dosage_form": "tablet", "strength": "5mg", "category": "Antidiabétique",
     "requires_prescription": True, "description": "Sulfonylurée pour le diabète de type 2."},
    {"name": "Insuline Glargine", "generic_name": "Insuline glargine", "brand_name": "Lantus",
     "dosage_form": "injection", "strength": "100UI/ml", "category": "Insuline",
     "requires_prescription": True, "description": "Insuline basale longue durée d'action."},

    # Respiratory
    {"name": "Salbutamol", "generic_name": "Salbutamol sulfate", "brand_name": "Ventoline",
     "dosage_form": "inhaler", "strength": "100mcg/dose", "category": "Bronchodilatateur",
     "requires_prescription": True, "description": "Bronchodilatateur de courte durée d'action."},
    {"name": "Beclométasone", "generic_name": "Dipropionate de béclométasone", "brand_name": "Becotide",
     "dosage_form": "inhaler", "strength": "250mcg/dose", "category": "Corticoïde inhalé",
     "requires_prescription": True, "description": "Corticoïde inhalé pour l'asthme persistant."},
    {"name": "Ambroxol", "generic_name": "Ambroxol HCl", "brand_name": "Mucosolvan",
     "dosage_form": "syrup", "strength": "15mg/5ml", "category": "Mucolytique",
     "requires_prescription": False, "description": "Fluidifiant bronchique."},
    {"name": "Codéine + Paracétamol", "generic_name": "Codéine phosphate / Paracétamol", "brand_name": "Dafalgan Codéiné",
     "dosage_form": "tablet", "strength": "30mg/500mg", "category": "Antitussif",
     "requires_prescription": True, "description": "Antitussif opioïde associé à un antalgique."},

    # Gastroenterology
    {"name": "Oméprazole", "generic_name": "Oméprazole", "brand_name": "Mopral",
     "dosage_form": "capsule", "strength": "20mg", "category": "Inhibiteur pompe à protons",
     "requires_prescription": False, "description": "IPP pour les ulcères et le reflux gastro-œsophagien."},
    {"name": "Ranitidine", "generic_name": "Ranitidine HCl", "brand_name": "Azantac",
     "dosage_form": "tablet", "strength": "150mg", "category": "Anti-ulcéreux",
     "requires_prescription": False, "description": "Anti-H2 pour les troubles gastriques."},
    {"name": "Dompéridone", "generic_name": "Dompéridone maléate", "brand_name": "Motilium",
     "dosage_form": "tablet", "strength": "10mg", "category": "Prokinétique",
     "requires_prescription": False, "description": "Antiémétique et prokinétique."},
    {"name": "Lopéramide", "generic_name": "Lopéramide HCl", "brand_name": "Imodium",
     "dosage_form": "capsule", "strength": "2mg", "category": "Antidiarrhéique",
     "requires_prescription": False, "description": "Antidiarrhéique de courte durée."},

    # Neurology / Psychiatry
    {"name": "Sertraline", "generic_name": "Sertraline HCl", "brand_name": "Zoloft",
     "dosage_form": "tablet", "strength": "50mg", "category": "Antidépresseur",
     "requires_prescription": True, "description": "ISRS indiqué dans la dépression et les troubles anxieux."},
    {"name": "Bromazépam", "generic_name": "Bromazépam", "brand_name": "Lexomil",
     "dosage_form": "tablet", "strength": "6mg", "category": "Anxiolytique",
     "requires_prescription": True, "description": "Benzodiazépine à visée anxiolytique."},
    {"name": "Carbamazépine", "generic_name": "Carbamazépine", "brand_name": "Tégrétol",
     "dosage_form": "tablet", "strength": "200mg", "category": "Antiépileptique",
     "requires_prescription": True, "description": "Anticonvulsivant pour l'épilepsie."},
    {"name": "Gabapentine", "generic_name": "Gabapentine", "brand_name": "Neurontin",
     "dosage_form": "capsule", "strength": "300mg", "category": "Antiépileptique",
     "requires_prescription": True, "description": "Utilisé dans l'épilepsie et les douleurs neuropathiques."},

    # Ophthalmology
    {"name": "Timolol (collyre)", "generic_name": "Maléate de timolol", "brand_name": "Timoptol",
     "dosage_form": "drops", "strength": "0.5%", "category": "Glaucome",
     "requires_prescription": True, "description": "Bêtabloquant en collyre pour le glaucome."},
    {"name": "Fluorométholone (collyre)", "generic_name": "Fluorométholone", "brand_name": "FML",
     "dosage_form": "drops", "strength": "0.1%", "category": "Corticoïde ophtalmique",
     "requires_prescription": True, "description": "Anti-inflammatoire corticoïde ophtalmique."},

    # Vitamins & Supplements
    {"name": "Vitamine C", "generic_name": "Acide ascorbique", "brand_name": "Cévit",
     "dosage_form": "tablet", "strength": "500mg", "category": "Vitamine",
     "requires_prescription": False, "description": "Supplément en vitamine C."},
    {"name": "Vitamine D3", "generic_name": "Cholécalciférol", "brand_name": "ZymaD",
     "dosage_form": "drops", "strength": "400UI/goutte", "category": "Vitamine",
     "requires_prescription": False, "description": "Supplément en vitamine D3."},
    {"name": "Fer + Acide Folique", "generic_name": "Fumarate ferreux + Acide folique", "brand_name": "Gynéfer",
     "dosage_form": "tablet", "strength": "200mg/5mg", "category": "Complément nutritionnel",
     "requires_prescription": False, "description": "Supplément martial pour la grossesse et l'anémie."},

    # Dermatology
    {"name": "Betaméthasone (crème)", "generic_name": "Valérate de bétaméthasone", "brand_name": "Betnéval",
     "dosage_form": "cream", "strength": "0.1%", "category": "Dermocorticoïde",
     "requires_prescription": True, "description": "Corticoïde topique pour les dermatoses inflammatoires."},
    {"name": "Kétoconazole (shampooing)", "generic_name": "Kétoconazole", "brand_name": "Nizoral",
     "dosage_form": "other", "strength": "2%", "category": "Antifongique",
     "requires_prescription": False, "description": "Antifongique pour les affections du cuir chevelu."},

    # Thyroid
    {"name": "Lévothyroxine", "generic_name": "Lévothyroxine sodique", "brand_name": "Levothyrox",
     "dosage_form": "tablet", "strength": "50mcg", "category": "Hormone thyroïdienne",
     "requires_prescription": True, "description": "Traitement de l'hypothyroïdie."},

    # Allergy
    {"name": "Cétirizine", "generic_name": "Cétirizine diHCl", "brand_name": "Zyrtec",
     "dosage_form": "tablet", "strength": "10mg", "category": "Antihistaminique",
     "requires_prescription": False, "description": "Antihistaminique H1 de 2ème génération."},
    {"name": "Loratadine", "generic_name": "Loratadine", "brand_name": "Clarityne",
     "dosage_form": "tablet", "strength": "10mg", "category": "Antihistaminique",
     "requires_prescription": False, "description": "Antihistaminique non sédatif pour les allergies."},
]

PHARMACIES_DATA = [
    {"name": "Pharmacie Centrale d'Alger",    "wilaya": "Alger",       "street": "Rue Didouche Mourad",         "lat": 36.7369, "lng": 3.0869,  "open_24h": True},
    {"name": "Pharmacie Bab El Oued",          "wilaya": "Alger",       "street": "Rue de la Liberté",           "lat": 36.7803, "lng": 3.0458,  "open_24h": False},
    {"name": "Pharmacie El Mouradia",          "wilaya": "Alger",       "street": "Boulevard Zighoud Youcef",    "lat": 36.7500, "lng": 3.0500,  "open_24h": False},
    {"name": "Pharmacie Hydra",                "wilaya": "Alger",       "street": "Cité Verte, Hydra",           "lat": 36.7339, "lng": 3.0239,  "open_24h": False},
    {"name": "Pharmacie Kouba",                "wilaya": "Alger",       "street": "Avenue Ahmed Ghermoul",       "lat": 36.7186, "lng": 3.1028,  "open_24h": True},
    {"name": "Pharmacie Ibn Rochd",            "wilaya": "Oran",        "street": "Boulevard Millénium",         "lat": 35.6969, "lng": -0.6331, "open_24h": False},
    {"name": "Pharmacie Es-Salam",             "wilaya": "Oran",        "street": "Rue Khémisti",                "lat": 35.6911, "lng": -0.6411, "open_24h": True},
    {"name": "Pharmacie Bir El Djir",          "wilaya": "Oran",        "street": "Avenue de l'ALN",             "lat": 35.7236, "lng": -0.5994, "open_24h": False},
    {"name": "Pharmacie du Bey",               "wilaya": "Constantine", "street": "Rue Bencherif Ahmed",        "lat": 36.3650, "lng": 6.6147,  "open_24h": False},
    {"name": "Pharmacie Ain El Bey",           "wilaya": "Constantine", "street": "Route de Batna",              "lat": 36.3500, "lng": 6.6317,  "open_24h": True},
    {"name": "Pharmacie El Shifa",             "wilaya": "Constantine", "street": "Boulevard Zaamoum",           "lat": 36.3767, "lng": 6.6050,  "open_24h": False},
    {"name": "Pharmacie Annaba Centre",        "wilaya": "Annaba",      "street": "Rue du 1er Novembre",         "lat": 36.9014, "lng": 7.7528,  "open_24h": False},
    {"name": "Pharmacie Sidi Amar",            "wilaya": "Annaba",      "street": "Cité Pont de Fer",            "lat": 36.8917, "lng": 7.7761,  "open_24h": True},
    {"name": "Pharmacie Blida",                "wilaya": "Blida",       "street": "Avenue du Colonel Amirouche", "lat": 36.4703, "lng": 2.8300,  "open_24h": False},
    {"name": "Pharmacie Bougara",              "wilaya": "Blida",       "street": "Rue des Martyrs",             "lat": 36.5367, "lng": 3.0833,  "open_24h": False},
    {"name": "Pharmacie Sétif Centre",         "wilaya": "Sétif",       "street": "Place de l'Indépendance",     "lat": 36.1900, "lng": 5.4139,  "open_24h": True},
    {"name": "Pharmacie Tlemcen",              "wilaya": "Tlemcen",     "street": "Rue Khaldounia",              "lat": 34.8786, "lng": -1.3153, "open_24h": False},
    {"name": "Pharmacie Bejaia Port",          "wilaya": "Béjaïa",      "street": "Boulevard des Martyrs",       "lat": 36.7528, "lng": 5.0844,  "open_24h": False},
    {"name": "Pharmacie Tizi Ouzou Centre",    "wilaya": "Tizi Ouzou",  "street": "Avenue Mouloud Mammeri",      "lat": 36.7169, "lng": 4.0472,  "open_24h": True},
    {"name": "Pharmacie Batna El Alia",        "wilaya": "Batna",       "street": "Rue Chahid Boukhlouf",        "lat": 35.5550, "lng": 6.1742,  "open_24h": False},
]

APPOINTMENT_REASONS = [
    ("Douleurs thoraciques", "Essoufflement à l'effort, douleur irradiant vers l'épaule gauche"),
    ("Hypertension artérielle", "Maux de tête fréquents, vertiges, tension élevée depuis 2 semaines"),
    ("Diabète de type 2", "Polydipsie, polyurie, fatigue persistante. Glycémie à 2.1 g/L à jeun"),
    ("Douleurs lombaires", "Lombalgie chronique depuis 3 mois, aggravée par la station debout prolongée"),
    ("Rhinite allergique", "Éternuements fréquents, rhinorrhée, larmoiements depuis le printemps"),
    ("Infection urinaire", "Brûlures mictionnelles, pollakiurie, urines troubles depuis 3 jours"),
    ("Dermatite atopique", "Eczéma récidivant sur les membres, prurit intense, peau sèche"),
    ("Migraines", "Céphalées pulsatiles unilatérales avec nausées, 2-3 crises par mois"),
    ("Anémie ferriprive", "Fatigue intense, pâleur, hémoglobine à 8 g/dL au dernier bilan"),
    ("Hypothyroïdie", "Prise de poids, frilosité, constipation, TSH élevée"),
    ("Asthme bronchique", "Dyspnée, sibilances, toux nocturne, DEP à 60% de la théorique"),
    ("Gastrite chronique", "Douleurs épigastriques, pyrosis, nausées à jeun"),
    ("Anxiété généralisée", "Inquiétudes excessives, insomnie, tensions musculaires depuis 6 mois"),
    ("Contrôle annuel", "Bilan de santé annuel, vaccinations, mise à jour du carnet de santé"),
    ("Bilan lipidique", "Cholestérol total à 2.8 g/L, antécédents familiaux de maladies cardiaques"),
    ("Cervicalgie", "Douleurs cervicales irradiant vers le bras droit, paresthésies digitales"),
    ("Conjonctivite", "Œil rouge, sécrétions purulentes, photophobie depuis 48h"),
    ("Otite moyenne", "Otalgie droite, fièvre à 38.5°C, diminution de l'acuité auditive"),
    ("Kyste pilonidal", "Douleur et tuméfaction au niveau du sillon inter-fessier"),
    ("Suivi grossesse", "Première consultation prénatale, 8 semaines d'aménorrhée"),
]

DIAGNOSES = [
    "Hypertension artérielle stade 1 — Initiation d'un traitement par IEC et mesures hygiéno-diététiques.",
    "Diabète de type 2 déséquilibré — Ajustement thérapeutique, contrôle glycémique renforcé.",
    "Infection urinaire basse — Traitement antibiotique par ciprofloxacine 500mg x2/j pendant 7 jours.",
    "Lombalgie commune — Repos relatif, AINS, kinésithérapie en ambulatoire.",
    "Rhinite allergique persistante — Traitement antihistaminique et corticoïde nasal.",
    "Gastrite à Helicobacter Pylori — Triple thérapie d'éradication.",
    "Asthme bronchique persistant modéré — Corticoïde inhalé + bêta-2 agoniste longue durée.",
    "Anémie ferriprive — Supplémentation en fer par voie orale pendant 3 mois.",
    "Hypothyroïdie franche — Initiation de la lévothyroxine, contrôle TSH à 6 semaines.",
    "Migraine sans aura — Traitement de fond par bêtabloquant, traitement de crise par triptan.",
    "Anxiété généralisée — Thérapie cognitive-comportementale + sérotoninergique.",
    "Hypercholestérolémie — Statine prescrite, régime pauvre en graisses saturées.",
    "Bilan de santé normal — Aucune anomalie détectée, prochain bilan dans 12 mois.",
    "Otite moyenne aiguë — Amoxicilline 1g x3/j pendant 7 jours.",
    "Conjonctivite bactérienne — Collyre antibiotique 5 jours.",
]


def rand_phone():
    prefix = random.choice(ALGERIAN_PHONE_PREFIXES)
    return f"{prefix}{random.randint(100000, 999999)}"


def rand_name(gender="male"):
    first = random.choice(ALGERIAN_FIRST_NAMES_MALE if gender == "male" else ALGERIAN_FIRST_NAMES_FEMALE)
    last  = random.choice(ALGERIAN_LAST_NAMES)
    return first, last


def rand_address(wilaya=None):
    w      = wilaya or random.choice(WILAYAS)
    street = random.choice(ALGERIAN_STREETS)
    num    = random.randint(1, 120)
    return f"{num}, {street}, {w}"


class Command(BaseCommand):
    help = 'Seed the Healix database with realistic Algerian data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear', action='store_true',
            help='Delete ALL existing data before seeding.',
        )
        parser.add_argument(
            '--only', type=str, default=None,
            choices=['users', 'doctors', 'pharmacies', 'appointments', 'prescriptions'],
            help='Seed only one category.',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self._clear_all()

        only = options['only']

        if only is None or only == 'users':
            self._seed_specialties()
            self._seed_users()
        if only is None or only == 'doctors':
            self._seed_specialties()
            self._seed_doctors()
            self._seed_availability()
        if only is None or only == 'pharmacies':
            self._seed_medicines()
            self._seed_pharmacies()
            self._seed_inventory()
        if only is None or only == 'appointments':
            self._seed_appointments()
            self._seed_reviews()
        if only is None or only == 'prescriptions':
            self._seed_prescriptions()

        self.stdout.write(self.style.SUCCESS('\n✅  Seeding complete!'))
        self._print_summary()

    # ─── Clear ────────────────────────────────────────────────────────────────

    def _clear_all(self):
        self.stdout.write(self.style.WARNING('⚠  Clearing all data...'))
        from prescriptions.models import ScannedPrescription, PrescriptionItem, Prescription
        from appointments.models import Message, Appointment
        from doctors.models import DoctorReview, DoctorAvailability, DoctorProfile, Specialty
        from pharmacies.models import PharmacyInventory, Medicine, Pharmacy
        from accounts.models import PatientProfile, User

        ScannedPrescription.objects.all().delete()
        PrescriptionItem.objects.all().delete()
        Prescription.objects.all().delete()
        Message.objects.all().delete()
        DoctorReview.objects.all().delete()
        Appointment.objects.all().delete()
        DoctorAvailability.objects.all().delete()
        DoctorProfile.objects.all().delete()
        Specialty.objects.all().delete()
        PharmacyInventory.objects.all().delete()
        Pharmacy.objects.all().delete()
        Medicine.objects.all().delete()
        PatientProfile.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write(self.style.SUCCESS('   All data cleared.\n'))

    # ─── Specialties ──────────────────────────────────────────────────────────

    def _seed_specialties(self):
        from doctors.models import Specialty
        created = 0
        for s in SPECIALTIES_DATA:
            _, c = Specialty.objects.get_or_create(
                name=s['name'],
                defaults={'icon': s['icon'], 'description': s['description']},
            )
            if c:
                created += 1
        self.stdout.write(f'   Specialties   : {created} created')

    # ─── Users ────────────────────────────────────────────────────────────────

    @transaction.atomic
    def _seed_users(self):
        from accounts.models import User, PatientProfile
        created = 0

        patient_data = [
            # (first, last, gender, dob, blood_type, wilaya)
            ("Sara",    "Benali",     "female", "1995-03-20", "A+",      "Alger"),
            ("Amira",   "Kaci",       "female", "1988-07-14", "B+",      "Alger"),
            ("Nadia",   "Mammeri",    "female", "2000-11-05", "O+",      "Tizi Ouzou"),
            ("Mohamed", "Boudiaf",    "male",   "1975-02-28", "AB+",     "Oran"),
            ("Yacine",  "Meziane",    "male",   "1990-09-12", "A-",      "Constantine"),
            ("Lyna",    "Ait Ahmed",  "female", "2003-06-30", "O-",      "Béjaïa"),
            ("Karim",   "Hamidouche", "male",   "1983-04-17", "B-",      "Alger"),
            ("Imane",   "Ferhat",     "female", "1997-12-25", "A+",      "Blida"),
            ("Sofiane", "Ziane",      "male",   "1979-08-08", "O+",      "Sétif"),
            ("Rania",   "Cherif",     "female", "1992-01-19", "B+",      "Annaba"),
            ("Bilal",   "Boukhari",   "male",   "2001-05-03", "AB-",     "Alger"),
            ("Yasmine", "Rahmani",    "female", "1986-10-22", "O+",      "Tlemcen"),
            ("Mehdi",   "Bensalem",   "male",   "1994-03-11", "A+",      "Oran"),
            ("Asma",    "Touati",     "female", "1999-08-16", "B+",      "Constantine"),
            ("Walid",   "Mekki",      "male",   "1970-12-01", "O+",      "Alger"),
        ]

        for first, last, gender, dob, blood_type, wilaya in patient_data:
            email = f"{first.lower()}.{last.lower().replace(' ', '_').replace("'", '')}@healix-demo.dz"
            if User.objects.filter(email=email).exists():
                continue
            user = User.objects.create_user(
                email=email,
                password='Healix2026!',
                first_name=first,
                last_name=last,
                phone_number=rand_phone(),
                role='patient',
                is_verified=True,
            )
            allergies_choices = [
                "Pénicilline", "Aspirine", "Arachides", "Fruits de mer", "Latex", "Pollen", ""
            ]
            chronic_choices = [
                "Diabète de type 2", "Hypertension artérielle", "Asthme", "Hypothyroïdie", ""
            ]
            PatientProfile.objects.create(
                user=user,
                date_of_birth=date.fromisoformat(dob),
                gender=gender,
                blood_type=blood_type,
                allergies=random.choice(allergies_choices),
                chronic_conditions=random.choice(chronic_choices),
                address=rand_address(wilaya),
                emergency_contact_name=f"{random.choice(ALGERIAN_FIRST_NAMES_MALE)} {random.choice(ALGERIAN_LAST_NAMES)}",
                emergency_contact_phone=rand_phone(),
            )
            created += 1

        self.stdout.write(f'   Patients       : {created} created')
        self.stdout.write(f'   Patient login  : <email> / Healix2026!')

    # ─── Doctors ──────────────────────────────────────────────────────────────

    @transaction.atomic
    def _seed_doctors(self):
        from accounts.models import User
        from doctors.models import DoctorProfile, Specialty

        doctors_data = [
            # (first, last, gender, specialty, experience, wilaya, fee)
            ("Karim",    "Benali",      "male",   "Cardiologie",             15, "Alger",       3500),
            ("Nadia",    "Mammeri",     "female", "Pédiatrie",               10, "Alger",       2500),
            ("Sofiane",  "Hadj Ali",    "male",   "Médecine Générale",        8, "Oran",        1500),
            ("Amira",    "Bouzid",      "female", "Gynécologie-Obstétrique", 12, "Alger",       3000),
            ("Mohamed",  "Kerroum",     "male",   "Neurologie",              18, "Constantine", 4000),
            ("Yasmine",  "Sellami",     "female", "Dermatologie",             7, "Alger",       2500),
            ("Rachid",   "Belkacemi",   "male",   "Orthopédie",              14, "Oran",        3500),
            ("Houria",   "Mebarki",     "female", "Endocrinologie",          11, "Alger",       3000),
            ("Tarek",    "Hadjadj",     "male",   "Gastro-entérologie",       9, "Constantine", 2800),
            ("Samira",   "Boudoukha",   "female", "Psychiatrie",             13, "Alger",       3200),
            ("Djamel",   "Touati",      "male",   "Pneumologie",             16, "Annaba",      3000),
            ("Meriem",   "Ziane",       "female", "Ophtalmologie",            6, "Alger",       2000),
            ("Hamza",    "Chibane",     "male",   "Rhumatologie",            10, "Blida",       2800),
            ("Nawel",    "Mokrani",     "female", "ORL",                      8, "Sétif",       2200),
            ("Anis",     "Bencheikh",   "male",   "Urologie",                12, "Alger",       3200),
            ("Dalila",   "Larbaoui",    "female", "Médecine Générale",        5, "Béjaïa",      1200),
            ("Fares",    "Bouazza",     "male",   "Cardiologie",             20, "Oran",        4500),
            ("Sihem",    "Drif",        "female", "Pédiatrie",               14, "Tizi Ouzou",  2200),
            ("Adel",     "Belloumi",    "male",   "Neurologie",              11, "Alger",       3800),
            ("Karima",   "Belarbi",    "female", "Endocrinologie",           9, "Constantine", 2800),
        ]

        specialties = {s.name: s for s in Specialty.objects.all()}
        created = 0

        for first, last, gender, spec_name, exp, wilaya, fee in doctors_data:
            email = f"dr.{first.lower()}.{last.lower().replace(' ', '_').replace("'", '')}@healix-demo.dz"
            if User.objects.filter(email=email).exists():
                continue

            user = User.objects.create_user(
                email=email,
                password='Healix2026!',
                first_name=first,
                last_name=last,
                phone_number=rand_phone(),
                role='doctor',
                is_verified=True,
            )

            specialty_obj = specialties.get(spec_name)
            bio_template  = random.choice(DOCTOR_BIOS)
            bio           = bio_template.format(years=exp, specialty=spec_name, wilaya=wilaya)
            clinic_template = random.choice(CLINIC_NAMES)
            clinic_name   = clinic_template.format(name=last, specialty=spec_name)

            # Rough coordinates per wilaya
            wilaya_coords = {
                "Alger": (36.737 + random.uniform(-0.05, 0.05), 3.087 + random.uniform(-0.05, 0.05)),
                "Oran":  (35.697 + random.uniform(-0.05, 0.05), -0.633 + random.uniform(-0.05, 0.05)),
                "Constantine": (36.365 + random.uniform(-0.05, 0.05), 6.615 + random.uniform(-0.05, 0.05)),
                "Annaba": (36.901 + random.uniform(-0.05, 0.05), 7.753 + random.uniform(-0.05, 0.05)),
                "Blida":  (36.470 + random.uniform(-0.05, 0.05), 2.830 + random.uniform(-0.05, 0.05)),
                "Sétif":  (36.190 + random.uniform(-0.05, 0.05), 5.414 + random.uniform(-0.05, 0.05)),
                "Tlemcen":(34.878 + random.uniform(-0.05, 0.05), -1.315 + random.uniform(-0.05, 0.05)),
                "Béjaïa": (36.753 + random.uniform(-0.05, 0.05), 5.084 + random.uniform(-0.05, 0.05)),
                "Batna":  (35.555 + random.uniform(-0.05, 0.05), 6.174 + random.uniform(-0.05, 0.05)),
                "Tizi Ouzou": (36.717 + random.uniform(-0.05, 0.05), 4.047 + random.uniform(-0.05, 0.05)),
            }
            lat, lng = wilaya_coords.get(wilaya, (36.737, 3.087))

            langs = "Arabe, Français"
            if random.random() > 0.5:
                langs += ", Tamazight"

            DoctorProfile.objects.create(
                user=user,
                specialty=spec_name,
                specialty_obj=specialty_obj,
                license_number=f"DZ-{wilaya[:3].upper()}-{random.randint(10000, 99999)}",
                years_of_experience=exp,
                bio=bio,
                education=f"Faculté de Médecine d'{'Alger' if random.random() > 0.4 else wilaya}, Spécialisation {spec_name}",
                languages=langs,
                clinic_name=clinic_name,
                clinic_address=rand_address(wilaya),
                latitude=Decimal(str(round(lat, 6))),
                longitude=Decimal(str(round(lng, 6))),
                consultation_fee=Decimal(fee),
                is_available_for_booking=True,
                is_verified=True,
            )
            created += 1

        self.stdout.write(f'   Doctors        : {created} created')
        self.stdout.write(f'   Doctor login   : dr.<firstname>.<lastname>@healix-demo.dz / Healix2026!')

    # ─── Availability ─────────────────────────────────────────────────────────

    def _seed_availability(self):
        from doctors.models import DoctorProfile, DoctorAvailability

        # Working days patterns
        patterns = [
            # (days, start, end, duration)
            ([0, 1, 2, 3, 4],     time(8, 0),  time(16, 0), 30),   # Sunday–Thursday
            ([0, 1, 2, 3, 4],     time(9, 0),  time(17, 0), 30),
            ([6, 0, 1, 2, 3],     time(8, 30), time(13, 30), 20),   # Saturday–Wednesday
            ([0, 1, 2, 3, 4, 5],  time(10, 0), time(18, 0), 30),
            ([0, 1, 3, 4],        time(8, 0),  time(14, 0), 30),    # Split week
        ]

        created = 0
        for doctor in DoctorProfile.objects.all():
            pattern = random.choice(patterns)
            days, start, end, duration = pattern
            for day in days:
                _, c = DoctorAvailability.objects.get_or_create(
                    doctor=doctor,
                    day_of_week=day,
                    start_time=start,
                    defaults={
                        'end_time': end,
                        'slot_duration_minutes': duration,
                        'max_patients': 1,
                        'is_active': True,
                    },
                )
                if c:
                    created += 1
        self.stdout.write(f'   Availability   : {created} slots created')

    # ─── Medicines ────────────────────────────────────────────────────────────

    def _seed_medicines(self):
        from pharmacies.models import Medicine
        created = 0
        for med in MEDICINES_DATA:
            _, c = Medicine.objects.get_or_create(
                name=med['name'],
                strength=med['strength'],
                defaults={
                    'generic_name':          med['generic_name'],
                    'brand_name':            med['brand_name'],
                    'dosage_form':           med['dosage_form'],
                    'manufacturer':          'Laboratoires Saidal' if random.random() > 0.4 else 'Importé',
                    'description':           med['description'],
                    'requires_prescription': med['requires_prescription'],
                    'category':              med['category'],
                },
            )
            if c:
                created += 1
        self.stdout.write(f'   Medicines      : {created} created')

    # ─── Pharmacies ───────────────────────────────────────────────────────────

    @transaction.atomic
    def _seed_pharmacies(self):
        from accounts.models import User
        from pharmacies.models import Pharmacy
        created = 0

        for i, ph in enumerate(PHARMACIES_DATA):
            slug  = ph['name'].lower().replace(' ', '_').replace("'", '').replace("é", 'e').replace("è", 'e')[:20]
            email = f"pharmacie_{slug}_{i}@healix-demo.dz"
            if User.objects.filter(email=email).exists():
                continue

            first = random.choice(ALGERIAN_FIRST_NAMES_MALE)
            last  = random.choice(ALGERIAN_LAST_NAMES)
            user  = User.objects.create_user(
                email=email,
                password='Healix2026!',
                first_name=first,
                last_name=last,
                phone_number=rand_phone(),
                role='pharmacy',
                is_verified=True,
            )

            open_time  = time(8, 0)  if not ph['open_24h'] else None
            close_time = time(21, 0) if not ph['open_24h'] else None

            Pharmacy.objects.create(
                user=user,
                name=ph['name'],
                license_number=f"PH-{ph['wilaya'][:3].upper()}-{random.randint(1000, 9999):04d}",
                address=f"{random.randint(1, 50)}, {ph['street']}, {ph['wilaya']}",
                latitude=Decimal(str(round(ph['lat'] + random.uniform(-0.002, 0.002), 6))),
                longitude=Decimal(str(round(ph['lng'] + random.uniform(-0.002, 0.002), 6))),
                phone_number=rand_phone(),
                email=email,
                opening_time=open_time,
                closing_time=close_time,
                is_open_24h=ph['open_24h'],
                is_verified=True,
                is_active=True,
            )
            created += 1

        self.stdout.write(f'   Pharmacies     : {created} created')
        self.stdout.write(f'   Pharmacy login : pharmacie_<slug>_<n>@healix-demo.dz / Healix2026!')

    # ─── Inventory ────────────────────────────────────────────────────────────

    def _seed_inventory(self):
        from pharmacies.models import Pharmacy, Medicine, PharmacyInventory
        created = 0
        medicines = list(Medicine.objects.all())
        pharmacies = list(Pharmacy.objects.all())

        for pharmacy in pharmacies:
            # Each pharmacy stocks 60–80% of the medicine catalog
            sample = random.sample(medicines, k=int(len(medicines) * random.uniform(0.6, 0.85)))
            for medicine in sample:
                _, c = PharmacyInventory.objects.get_or_create(
                    pharmacy=pharmacy,
                    medicine=medicine,
                    defaults={
                        'stock_quantity': random.randint(10, 500),
                        'price': Decimal(str(round(random.uniform(80, 2800), 2))),
                        'expiry_date': date.today() + timedelta(days=random.randint(180, 900)),
                        'is_available': True,
                    },
                )
                if c:
                    created += 1
        self.stdout.write(f'   Inventory      : {created} stock entries created')

    # ─── Appointments ─────────────────────────────────────────────────────────

    @transaction.atomic
    def _seed_appointments(self):
        from accounts.models import PatientProfile
        from doctors.models import DoctorProfile, DoctorAvailability
        from appointments.models import Appointment, Message

        appt_created = 0
        msg_created  = 0

        patients = list(PatientProfile.objects.select_related('user').all())
        doctors  = list(DoctorProfile.objects.select_related('user').all())

        if not patients or not doctors:
            self.stdout.write(self.style.WARNING('   Skipping appointments — no patients or doctors found.'))
            return

        # We'll create appointments across a date window: 60 days ago → 14 days ahead
        today = date.today()

        doctor_slots = {}  # cache: doctor_id → set of (date, time) taken
        for doc in doctors:
            doctor_slots[doc.id] = set()

        # Generate ~60 appointments spread across past, present, future
        appointment_configs = []
        for _ in range(60):
            doctor  = random.choice(doctors)
            patient = random.choice(patients)

            # Pick a day in the range
            offset = random.randint(-45, 14)
            appt_date = today + timedelta(days=offset)

            # Get availability for that weekday
            avail = list(DoctorAvailability.objects.filter(
                doctor=doctor, day_of_week=appt_date.weekday(), is_active=True
            ))
            if not avail:
                continue
            slot_block = random.choice(avail)

            # Generate a slot time within the block
            start_mins = slot_block.start_time.hour * 60 + slot_block.start_time.minute
            end_mins   = slot_block.end_time.hour   * 60 + slot_block.end_time.minute
            duration   = slot_block.slot_duration_minutes
            slots = list(range(start_mins, end_mins, duration))
            if not slots:
                continue
            chosen_min = random.choice(slots)
            appt_time  = time(chosen_min // 60, chosen_min % 60)

            key = (doctor.id, appt_date, appt_time)
            if key in doctor_slots[doctor.id]:
                continue
            doctor_slots[doctor.id].add(key)

            appointment_configs.append((doctor, patient, appt_date, appt_time, offset))

        for doctor, patient, appt_date, appt_time, offset in appointment_configs:
            reason_tuple = random.choice(APPOINTMENT_REASONS)
            reason, symptoms = reason_tuple

            # Determine status based on date
            if offset < -30:
                status = random.choice(['completed', 'completed', 'completed', 'cancelled', 'no_show'])
            elif offset < -7:
                status = random.choice(['completed', 'completed', 'cancelled'])
            elif offset < 0:
                status = random.choice(['completed', 'confirmed'])
            elif offset == 0:
                status = random.choice(['confirmed', 'in_progress', 'in_progress'])
            else:
                status = random.choice(['pending', 'pending', 'confirmed'])

            appt_type = random.choice(['in_person', 'in_person', 'in_person', 'video', 'phone'])

            appt = Appointment(
                patient=patient,
                doctor=doctor,
                appointment_date=appt_date,
                appointment_time=appt_time,
                appointment_type=appt_type,
                status=status,
                reason_for_visit=reason,
                symptoms=symptoms,
                consultation_fee=doctor.consultation_fee,
            )

            if status in ('completed', 'confirmed', 'in_progress'):
                appt.checked_in_at = timezone.make_aware(
                    datetime.combine(appt_date, appt_time)
                )
            if status in ('completed', 'in_progress'):
                appt.started_at = appt.checked_in_at + timedelta(minutes=random.randint(5, 20))
            if status == 'completed':
                appt.completed_at = appt.started_at + timedelta(minutes=random.randint(15, 45))
                appt.notes_by_doctor = f"Consultation du {appt_date}. {random.choice(['Patient coopératif.', 'Antécédents familiaux notés.', 'Bilan biologique demandé.', 'Patient sous traitement chronique.'])}"
                appt.diagnosis = random.choice(DIAGNOSES)
            if status == 'cancelled':
                appt.cancelled_at = timezone.make_aware(
                    datetime.combine(appt_date - timedelta(days=random.randint(1, 3)), time(10, 0))
                )
                appt.cancellation_reason = random.choice([
                    "Empêchement personnel",
                    "Rendez-vous pris en urgence ailleurs",
                    "Voyage imprévu",
                    "Amélioration de l'état de santé",
                ])
                appt.cancelled_by = random.choice([patient.user, doctor.user])

            appt.save()
            appt_created += 1

            # Add messages to some completed appointments
            if status == 'completed' and random.random() > 0.4:
                messages = [
                    (patient.user, f"Bonjour Docteur, j'ai quelques questions concernant ma visite."),
                    (doctor.user,  f"Bonjour {patient.user.first_name}, bien sûr. Comment puis-je vous aider ?"),
                    (patient.user, random.choice([
                        "Dois-je continuer le traitement si les symptômes disparaissent ?",
                        "Puis-je prendre les médicaments avec des repas légers ?",
                        "Y a-t-il des aliments à éviter pendant le traitement ?",
                        "Quand dois-je revenir pour le contrôle ?",
                    ])),
                    (doctor.user, random.choice([
                        "Oui, continuez le traitement jusqu'à la fin même si vous vous sentez mieux.",
                        "Les médicaments peuvent être pris avec ou sans repas, mais évitez l'estomac vide.",
                        "Évitez les aliments gras pendant la durée du traitement.",
                        "Revenez dans 3 semaines pour le contrôle, ou plus tôt si les symptômes s'aggravent.",
                    ])),
                ]
                for sender, content in messages:
                    Message.objects.create(
                        appointment=appt,
                        sender=sender,
                        content=content,
                        is_read=True,
                        read_at=timezone.now(),
                    )
                    msg_created += 1

        self.stdout.write(f'   Appointments   : {appt_created} created')
        self.stdout.write(f'   Messages       : {msg_created} created')

        # Update total_appointments cache on each doctor
        from django.db.models import Count
        for doctor in doctors:
            count = Appointment.objects.filter(doctor=doctor, status='completed').count()
            DoctorProfile.objects.filter(pk=doctor.pk).update(total_appointments=count)

    # ─── Reviews ──────────────────────────────────────────────────────────────

    def _seed_reviews(self):
        from appointments.models import Appointment
        from doctors.models import DoctorReview

        review_comments = [
            "Excellent médecin, très à l'écoute et professionnel. Je recommande vivement.",
            "Consultation rapide et efficace. Diagnostic correct, traitement adapté.",
            "Docteur très compétent et humain. A pris le temps d'expliquer le diagnostic.",
            "Très bonne expérience. Cabinet propre, personnel accueillant.",
            "Médecin sérieux et rigoureux. Revenu après une semaine, déjà mieux.",
            "Bonne consultation mais temps d'attente un peu long.",
            "Docteur attentionné, a répondu à toutes mes questions patiemment.",
            "Très professionnel. A fait des examens complémentaires pertinents.",
            "Consultation satisfaisante. Prix raisonnable pour la qualité du service.",
            "Super expérience. Mon enfant a été mis en confiance dès le début.",
            "Médecin très expérimenté, diagnostic précis dès la première consultation.",
            "Accueil chaleureux, cabinet moderne et bien équipé.",
            "Docteur sérieux et à l'écoute. Traitement efficace, guéri en moins d'une semaine.",
            "Très bon médecin mais difficile d'avoir un rendez-vous rapidement.",
            "Consultation complète et détaillée. Je recommande sans hésitation.",
        ]

        completed_appts = list(
            Appointment.objects.filter(status='completed')
            .select_related('patient', 'doctor')
        )
        created = 0
        seen = set()

        for appt in completed_appts:
            if random.random() > 0.65:
                continue
            key = (appt.doctor_id, appt.patient_id)
            if key in seen:
                continue
            if DoctorReview.objects.filter(doctor=appt.doctor, patient=appt.patient).exists():
                continue
            seen.add(key)

            rating = random.choices([5, 4, 3, 2], weights=[50, 30, 15, 5])[0]
            DoctorReview.objects.create(
                doctor=appt.doctor,
                patient=appt.patient,
                appointment=appt,
                rating=rating,
                comment=random.choice(review_comments) if random.random() > 0.2 else "",
                is_anonymous=random.random() > 0.85,
            )
            created += 1

        self.stdout.write(f'   Reviews        : {created} created')

    # ─── Prescriptions ────────────────────────────────────────────────────────

    def _seed_prescriptions(self):
        from appointments.models import Appointment
        from pharmacies.models import Medicine
        from prescriptions.models import Prescription, PrescriptionItem

        prescription_items_data = [
            ("Amoxicilline 500mg Gélule",              "500mg",   "3 fois par jour",    "7 jours",    "Prendre pendant les repas",         21),
            ("Ibuprofène 400mg Comprimé",               "400mg",   "2 fois par jour",    "5 jours",    "Prendre avec un grand verre d'eau", 10),
            ("Paracétamol 1g Comprimé",                 "1g",      "3 fois par jour",    "5 jours",    "Ne pas dépasser 3g par jour",       15),
            ("Oméprazole 20mg Gélule",                  "20mg",    "1 fois par jour",    "1 mois",     "Prendre à jeun le matin",           30),
            ("Metformine 500mg Comprimé",               "500mg",   "2 fois par jour",    "3 mois",     "Prendre pendant les repas",         180),
            ("Amlodipine 5mg Comprimé",                 "5mg",     "1 fois par jour",    "1 mois",     "Prendre le matin",                  30),
            ("Ramipril 5mg Comprimé",                   "5mg",     "1 fois par jour",    "1 mois",     "Prendre le matin",                  30),
            ("Atorvastatine 20mg Comprimé",             "20mg",    "1 fois le soir",     "3 mois",     "Prendre le soir",                   90),
            ("Salbutamol 100mcg Inhalateur",            "100mcg",  "Au besoin",          "3 mois",     "2 bouffées en cas de crise",        1),
            ("Cétirizine 10mg Comprimé",                "10mg",    "1 fois par jour",    "15 jours",   "Prendre le soir",                   15),
            ("Sertraline 50mg Comprimé",                "50mg",    "1 fois par jour",    "3 mois",     "Prendre le matin",                  90),
            ("Azithromycine 500mg Comprimé",            "500mg",   "1 fois par jour",    "3 jours",    "Prendre à distance des repas",      3),
            ("Lévothyroxine 50mcg Comprimé",            "50mcg",   "1 fois par jour",    "3 mois",     "Prendre à jeun 30 min avant le repas", 90),
            ("Vitamine D3 400UI Gouttes",               "400UI",   "1 fois par jour",    "3 mois",     "À mélanger dans un repas",          1),
            ("Fer + Acide Folique 200mg/5mg Comprimé",  "200mg",   "1 fois par jour",    "2 mois",     "Prendre pendant les repas",         60),
            ("Ciprofloxacine 500mg Comprimé",           "500mg",   "2 fois par jour",    "7 jours",    "Éviter l'exposition au soleil",     14),
            ("Diclofénac 50mg Comprimé",                "50mg",    "2 fois par jour",    "10 jours",   "Prendre avec les repas",            20),
            ("Ambroxol 15mg/5ml Sirop",                 "15mg/5ml","3 fois par jour",    "7 jours",    "Bien agiter avant usage",           1),
        ]

        completed_appts = list(
            Appointment.objects.filter(status='completed')
            .select_related('patient', 'doctor')
            .exclude(prescription__isnull=False)
        )

        medicines_map = {m.name: m for m in Medicine.objects.all()}
        created = 0
        items_created = 0

        for appt in random.sample(completed_appts, k=min(len(completed_appts), 35)):
            if random.random() > 0.75:
                continue

            issue_date  = appt.appointment_date
            expiry_date = issue_date + timedelta(days=random.choice([30, 60, 90]))

            prescription = Prescription.objects.create(
                patient=appt.patient,
                doctor=appt.doctor,
                appointment=appt,
                status='pending',
                notes=random.choice([
                    "Respecter scrupuleusement les posologies. Revenez en consultation si pas d'amélioration sous 48h.",
                    "Ne pas arrêter le traitement sans avis médical.",
                    "Signaler tout effet indésirable. Prochain contrôle dans un mois.",
                    "Bilan biologique de contrôle dans 6 semaines.",
                    "Régime alimentaire adapté recommandé en complément du traitement.",
                ]),
                issue_date=issue_date,
                expiry_date=expiry_date,
            )
            created += 1

            # Add 1–4 prescription items
            num_items = random.randint(1, 4)
            items = random.sample(prescription_items_data, k=num_items)
            for med_name_raw, dosage, freq, duration, instructions, qty in items:
                # Try to link to a real medicine object
                linked_med = None
                for key, med in medicines_map.items():
                    if key.lower() in med_name_raw.lower():
                        linked_med = med
                        break

                PrescriptionItem.objects.create(
                    prescription=prescription,
                    medicine=linked_med,
                    medicine_name_raw=med_name_raw,
                    dosage=dosage,
                    frequency=freq,
                    duration=duration,
                    instructions=instructions,
                    quantity=qty,
                    is_dispensed=random.random() > 0.6,
                )
                items_created += 1

        self.stdout.write(f'   Prescriptions  : {created} created')
        self.stdout.write(f'   Prescription items: {items_created} created')

    # ─── Summary ──────────────────────────────────────────────────────────────

    def _print_summary(self):
        from accounts.models import User, PatientProfile
        from doctors.models import DoctorProfile, DoctorAvailability, DoctorReview, Specialty
        from pharmacies.models import Pharmacy, Medicine, PharmacyInventory
        from appointments.models import Appointment, Message
        from prescriptions.models import Prescription, PrescriptionItem

        self.stdout.write('\n' + '─' * 50)
        self.stdout.write(self.style.SUCCESS('📊  DATABASE SUMMARY'))
        self.stdout.write('─' * 50)
        self.stdout.write(f'   Users              : {User.objects.count()}')
        self.stdout.write(f'   Patients           : {PatientProfile.objects.count()}')
        self.stdout.write(f'   Doctors            : {DoctorProfile.objects.count()}')
        self.stdout.write(f'   Specialties        : {Specialty.objects.count()}')
        self.stdout.write(f'   Availability slots : {DoctorAvailability.objects.count()}')
        self.stdout.write(f'   Pharmacies         : {Pharmacy.objects.count()}')
        self.stdout.write(f'   Medicines          : {Medicine.objects.count()}')
        self.stdout.write(f'   Inventory entries  : {PharmacyInventory.objects.count()}')
        self.stdout.write(f'   Appointments       : {Appointment.objects.count()}')
        self.stdout.write(f'     ✓ Completed      : {Appointment.objects.filter(status="completed").count()}')
        self.stdout.write(f'     ✓ Confirmed      : {Appointment.objects.filter(status="confirmed").count()}')
        self.stdout.write(f'     ✓ Pending        : {Appointment.objects.filter(status="pending").count()}')
        self.stdout.write(f'     ✗ Cancelled      : {Appointment.objects.filter(status="cancelled").count()}')
        self.stdout.write(f'   Messages           : {Message.objects.count()}')
        self.stdout.write(f'   Reviews            : {DoctorReview.objects.count()}')
        self.stdout.write(f'   Prescriptions      : {Prescription.objects.count()}')
        self.stdout.write(f'   Prescription items : {PrescriptionItem.objects.count()}')
        self.stdout.write('─' * 50)
        self.stdout.write('\n🔑  All seeded accounts use password: Healix2026!')
        self.stdout.write('🌐  Admin panel: http://127.0.0.1:8000/admin/')
        self.stdout.write('📖  API docs:   http://127.0.0.1:8000/api/docs/\n')
