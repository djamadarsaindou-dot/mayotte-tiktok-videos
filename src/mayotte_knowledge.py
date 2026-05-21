"""Base de connaissances Mayotte vérifiées.

Chaque entrée est ancrée et factuelle. Le LLM doit narrer un sujet précis
de cette base, sans inventer ni mélanger.

Chaque entrée a :
- title : titre court du sujet
- key_facts : liste de faits factuels précis (3-7 éléments)
- search_seeds : suggestions de mots-clés en anglais pour stock vidéo
- visual_hints : indications spécifiques pour les visuels (pour l'image IA)
- avoid : pièges à éviter dans le récit

Banque enrichie (~120 sujets) — faits vérifiés par recherche documentaire.
Le choix d'un sujet passe par pick_topic_for() qui applique l'anti-répétition.
"""
import json
import random
from pathlib import Path
from typing import TypedDict


class KnowledgeEntry(TypedDict):
    title: str
    key_facts: list[str]
    search_seeds: list[str]
    visual_hints: list[str]
    avoid: list[str]


# === LIEUX & GÉOGRAPHIE ===
PLACES: list[KnowledgeEntry] = [
    {
        "title": "Le Mont Choungui — sentinelle du Sud",
        "key_facts": [
            "Mont Choungui culmine à 594 mètres dans le sud de Grande-Terre",
            "Sa silhouette parfaitement conique en fait un emblème de Mayotte",
            "Son nom vient du shimaoré et signifie « la pointe »",
            "L'ascension prend environ 1h30 et offre une vue à 360° sur le lagon",
            "Selon la légende, deux sœurs furent transformées en pierre au sommet",
            "Le mont est visible depuis la quasi-totalité de l'île",
        ],
        "search_seeds": ["volcanic conical mountain", "tropical mountain hike", "panoramic island view", "sunrise over island peak"],
        "visual_hints": ["Mount Choungui Mayotte aerial drone view, conical volcanic peak rising from green tropical landscape, sunset golden light, photorealistic"],
        "avoid": ["confondre avec Mont Bénara qui est plus haut (660m)"],
    },
    {
        "title": "Le double lagon — joyau géologique mondial",
        "key_facts": [
            "Mayotte possède l'un des rares doubles lagons fermés au monde",
            "Le lagon est l'un des plus vastes lagons fermés de la planète",
            "Une longue barrière de corail entoure presque toute l'île",
            "Le récif intérieur double la barrière externe sur certaines zones",
            "Plus de 250 espèces de coraux et près de 600 espèces de poissons y vivent",
            "La passe en S, à l'est, est mondialement connue des plongeurs",
        ],
        "search_seeds": ["aerial double coral reef", "tropical lagoon turquoise water", "coral atoll drone view", "barrier reef aerial"],
        "visual_hints": ["Mayotte double lagoon aerial drone, two parallel coral reef barriers, turquoise gradient water, photorealistic"],
        "avoid": [],
    },
    {
        "title": "L'îlot de Mtsamboro et les ilots du Nord",
        "key_facts": [
            "L'îlot Mtsamboro est situé au nord de Grande-Terre, accessible en barque",
            "Il abrite des plages de sable blanc parmi les plus pures de l'archipel",
            "Le site est classé en réserve naturelle marine",
            "On y observe baleines à bosse de juillet à octobre",
            "Les villageois pratiquent toujours la pêche traditionnelle",
        ],
        "search_seeds": ["white sand islet boat", "tropical island reserve", "humpback whale ocean", "traditional fishing net"],
        "visual_hints": ["uninhabited tropical islet white sand pristine beach, turquoise water, photorealistic"],
        "avoid": [],
    },
    {
        "title": "La plage de N'Gouja et les tortues vertes",
        "key_facts": [
            "N'Gouja est la plage la plus célèbre de Mayotte, située au sud",
            "Les tortues vertes viennent y brouter les herbiers à quelques mètres du rivage",
            "On peut nager avec elles toute l'année, sans bateau",
            "La ponte des tortues a lieu sur les plages voisines",
            "Le site est protégé par la réserve naturelle nationale",
        ],
        "search_seeds": ["green sea turtle swimming", "snorkeling tropical beach", "turtle laying eggs beach", "underwater turtle reef"],
        "visual_hints": ["green sea turtle swimming in turquoise lagoon shallow water, sunlight rays, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Petite-Terre et le lac Dziani",
        "key_facts": [
            "Petite-Terre est l'une des deux îles principales de Mayotte avec Grande-Terre",
            "On y trouve l'aéroport international de Pamandzi",
            "Le lac Dziani est un cratère volcanique aux eaux vert émeraude",
            "Il mesure environ 700 mètres de diamètre et serait sacré selon les traditions",
            "Petite-Terre ne couvre que 11 km² environ",
        ],
        "search_seeds": ["volcanic crater lake green", "small tropical island airport", "emerald lake aerial", "volcanic island"],
        "visual_hints": ["volcanic crater lake emerald green water aerial drone, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le Mont Bénara — le toit de Mayotte",
        "key_facts": [
            "Le Mont Bénara culmine à 660 mètres : c'est le point le plus haut de Mayotte",
            "On l'appelle aussi le mont Mavingoni",
            "Il s'étend sur trois communes du sud : Dembéni, Bandrélé et Chirongui",
            "Son sommet voisin, le Bépilipili, culmine à 643 mètres",
            "Son massif abrite l'une des forêts humides les mieux préservées de l'île",
        ],
        "search_seeds": ["tropical mountain rainforest", "lush green mountain peak", "misty tropical summit", "rainforest aerial"],
        "visual_hints": ["Mount Bénara Mayotte, highest forested peak, aerial drone view, lush rainforest, morning mist, photorealistic"],
        "avoid": ["ne pas confondre avec le Mont Choungui (594 m), plus bas mais plus célèbre"],
    },
    {
        "title": "La Passe en S — le joyau des plongeurs",
        "key_facts": [
            "La Passe en S est un chenal naturel en forme de S qui traverse la barrière de corail à l'est de Mayotte",
            "Son nom en shimaoré est Longogori",
            "Elle mesure environ 2 km de long et jusqu'à 65 mètres de profondeur",
            "C'est un ancien lit de rivière, creusé quand le niveau de la mer était bien plus bas",
            "Depuis 1990, la passe et 1400 hectares autour sont classés en réserve de pêche",
            "On y croise poissons-Napoléon, raies, tortues et parfois des dugongs",
        ],
        "search_seeds": ["coral reef pass underwater", "scuba diving tropical reef", "drone coral barrier", "turquoise reef channel"],
        "visual_hints": ["aerial drone view of an S-shaped channel cutting through a coral barrier reef, turquoise water, photorealistic"],
        "avoid": [],
    },
    {
        "title": "L'îlot de Sable Blanc — l'île qui disparaît",
        "key_facts": [
            "L'îlot de Sable Blanc est un banc de sable corallien au sud-est de Mayotte",
            "Il se situe à environ 1,7 km de la pointe Saziley",
            "Son nom shimaoré, Mtsanga Tsoholé, signifie « plage de riz »",
            "À marée basse il peut mesurer 453 mètres de long sur 148 de large",
            "À marée haute il est presque entièrement submergé",
            "Sa blancheur vient de la forte proportion de débris de corail",
        ],
        "search_seeds": ["white sand bank ocean", "sandbar turquoise water aerial", "tiny sand islet", "low tide sandbank"],
        "visual_hints": ["a pure white sandbar in the middle of a turquoise lagoon, aerial drone view, comma shape, photorealistic"],
        "avoid": [],
    },
    {
        "title": "La pointe Saziley — le sanctuaire des tortues",
        "key_facts": [
            "La pointe Saziley, au sud de Mayotte, est l'endroit le plus sec de l'île",
            "Elle compte dix plages où les tortues vertes viennent pondre",
            "Un réseau d'environ 21 km de sentiers parcourt la pointe",
            "Environ 700 baobabs sont répartis le long de son littoral",
            "Le site est protégé par le Conservatoire du littoral",
        ],
        "search_seeds": ["dry tropical coast baobab", "turtle nesting beach", "coastal hiking trail tropical", "wild tropical headland"],
        "visual_hints": ["wild dry tropical headland with baobab trees along a white sand beach, turquoise sea, photorealistic"],
        "avoid": [],
    },
    {
        "title": "La cascade de Soulou — l'eau douce qui rejoint la mer",
        "key_facts": [
            "La cascade de Soulou se trouve dans le nord-ouest de Mayotte, sur la commune de Tsingoni",
            "Sa particularité : elle tombe directement sur la plage à marée basse",
            "À marée haute, l'eau de la chute se jette dans la mer",
            "On y accède en traversant une bambouseraie depuis la plage",
            "C'est l'un des rares endroits où une chute d'eau douce rencontre l'océan",
        ],
        "search_seeds": ["waterfall on beach", "tropical waterfall ocean", "bamboo forest path", "cascade meeting sea"],
        "visual_hints": ["a tropical waterfall flowing directly onto a sandy beach by the ocean, lush vegetation, photorealistic"],
        "avoid": ["ne pas annoncer de hauteur de chute précise — les sources divergent"],
    },
    {
        "title": "La plage de Sakouli — la plage au sable sombre",
        "key_facts": [
            "La plage de Sakouli se situe dans le sud-est de Mayotte, sur la commune de Bandrélé",
            "Elle est composée de sable brun foncé, d'origine volcanique",
            "Elle est bordée de baobabs et de cocotiers",
            "Elle fait face à l'îlot Bandrélé, accessible en kayak",
            "C'est l'un des spots les plus fréquentés de l'île le week-end",
        ],
        "search_seeds": ["dark volcanic sand beach", "tropical beach baobab", "palm tree beach islet", "tropical bay kayak"],
        "visual_hints": ["tropical beach with dark volcanic sand, baobab and coconut trees, small islet offshore, photorealistic"],
        "avoid": [],
    },
    {
        "title": "La mangrove de Mayotte — la forêt entre terre et mer",
        "key_facts": [
            "Les mangroves couvrent environ 667 hectares à Mayotte",
            "Elles bordent 76 km de littoral, soit près de 29 % des côtes de l'île",
            "Sept espèces de palétuviers y sont présentes",
            "La plus représentée est le palétuvier rouge",
            "La mangrove protège le littoral de l'érosion et sert de nurserie aux poissons",
            "En 40 ans, sa superficie a reculé d'environ 20 %",
        ],
        "search_seeds": ["mangrove forest roots", "mangrove aerial tropical", "tangled mangrove roots water", "coastal mangrove"],
        "visual_hints": ["dense mangrove forest with tangled roots in shallow turquoise water, aerial view, photorealistic"],
        "avoid": [],
    },
    {
        "title": "La baie de Bouéni — la plus grande baie de l'île",
        "key_facts": [
            "La baie de Bouéni se situe dans le sud-ouest de Mayotte",
            "Elle mesure environ 5 km de large à son embouchure et 10 km de long",
            "Elle abrite la plus grande mangrove de Mayotte, près de 200 hectares",
            "C'est la plus grande mangrove de tout l'archipel des Comores",
            "La baie est protégée et reconnue zone importante pour les oiseaux",
        ],
        "search_seeds": ["large tropical bay aerial", "mangrove bay drone", "calm tropical bay", "coastal wetland birds"],
        "visual_hints": ["vast tropical bay with extensive green mangrove, aerial drone view, calm water, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Mamoudzou — le chef-lieu de Mayotte",
        "key_facts": [
            "Mamoudzou, sur Grande-Terre, est la préfecture et la plus grande ville de Mayotte",
            "Elle est la commune la plus peuplée du département",
            "Elle concentre l'essentiel des structures administratives et commerciales",
            "Ses quais voient partir les barges qui relient Grande-Terre et Petite-Terre",
            "Son marché couvert est un cœur animé de la vie locale",
        ],
        "search_seeds": ["tropical town harbour", "busy island market", "ferry dock tropical", "colorful coastal town"],
        "visual_hints": ["lively tropical town by the sea with a busy harbour and ferries, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le récif barrière — le mur de corail de Mayotte",
        "key_facts": [
            "Le récif barrière entoure Mayotte sur environ 140 km et délimite le lagon",
            "Il est percé de douze passes ouvertes sur l'océan",
            "Ces passes laissent le lagon se vider et se remplir avec les marées",
            "Au nord, plus de 40 km de barrières immergées prolongent le récif",
            "Mayotte possède une rare double barrière de corail",
        ],
        "search_seeds": ["barrier reef aerial", "coral reef waves break", "reef pass ocean", "turquoise reef line"],
        "visual_hints": ["aerial drone view of a long coral barrier reef with waves breaking, turquoise lagoon inside, photorealistic"],
        "avoid": [],
    },
    {
        "title": "La Réserve des Forêts de Mayotte",
        "key_facts": [
            "La Réserve Naturelle Nationale des Forêts de Mayotte a été créée en 2021",
            "Elle couvre 2801 hectares répartis sur six massifs forestiers de Grande-Terre",
            "Elle protège les dernières forêts humides primaires de l'île",
            "Elle abrite le maki, les roussettes et le drongo de Mayotte",
            "Ces forêts d'altitude sont des châteaux d'eau naturels pour l'île",
        ],
        "search_seeds": ["primary tropical rainforest", "lush jungle canopy", "rainforest mist mountain", "protected forest reserve"],
        "visual_hints": ["dense primary tropical rainforest on a mountain slope, mist between trees, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le Mont M'tsapéré — la montagne qui veille sur Mamoudzou",
        "key_facts": [
            "Le Mont M'tsapéré culmine à 572 mètres d'altitude",
            "C'est l'un des cinq principaux sommets de Mayotte",
            "Il domine directement Mamoudzou, le chef-lieu",
            "Ses pentes abritent la forêt humide de Majimbini",
            "L'ascension jusqu'au sommet demande environ six heures de marche",
        ],
        "search_seeds": ["forested mountain over town", "tropical peak hiking", "green mountain ridge", "rainforest mountain"],
        "visual_hints": ["green forested mountain rising above a tropical coastal town, aerial view, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le volcan Fani Maoré — le géant né au large",
        "key_facts": [
            "En 2018, Mayotte se met à trembler : des dizaines de séismes par jour pendant des mois",
            "En 2019, les scientifiques découvrent la cause : un volcan sous-marin à 50 km à l'est",
            "Baptisé Fani Maoré, il s'élève à environ 820 mètres sur un fond marin de 3500 mètres",
            "Pendant l'éruption, Mayotte s'est déplacée de 24 cm vers l'est et a baissé de 19 cm",
            "C'est l'une des plus importantes éruptions sous-marines jamais documentées",
        ],
        "search_seeds": ["underwater volcano eruption", "deep sea volcano", "submarine lava", "ocean floor volcano"],
        "visual_hints": ["a massive underwater volcano on the deep ocean floor, glowing lava, dark blue water, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le lac Karihani — le seul lac d'eau douce de l'île",
        "key_facts": [
            "Le lac Karihani, entre Tsingoni et Combani, est le seul lac d'eau douce naturel de Mayotte",
            "Son niveau varie de 0 à 2,5 mètres selon la saison, car il est alimenté par le ruissellement",
            "C'est le deuxième site le plus important pour les oiseaux de Mayotte",
            "Plus de 57 espèces d'oiseaux y ont été recensées",
            "Son nom vient du « kariha », la gallinule poule-d'eau en shimaoré",
        ],
        "search_seeds": ["freshwater lake tropical", "lake water lilies birds", "calm lake reflection", "wetland birds lake"],
        "visual_hints": ["a calm freshwater lake with purple water lilies and birds, tropical vegetation around, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Tahiti plage — la carte postale de Sada",
        "key_facts": [
            "Tahiti plage se situe dans le centre-ouest de Grande-Terre, sur la commune de Sada",
            "Les habitants l'appellent Mtsagnougni",
            "Elle s'étend sur environ 800 mètres de sable blond",
            "Elle est bordée de filaos, des arbres qui ressemblent à des pins",
            "C'est l'une des plages les plus connues et fréquentées de Mayotte",
        ],
        "search_seeds": ["golden sand beach palm", "tropical paradise beach", "casuarina trees beach", "idyllic tropical shore"],
        "visual_hints": ["a long golden sand beach lined with casuarina trees, turquoise sea, photorealistic"],
        "avoid": [],
    },
]

# === FAUNE & FLORE ===
NATURE: list[KnowledgeEntry] = [
    {
        "title": "Le dugong — sirène en voie de disparition",
        "key_facts": [
            "Le dugong est un mammifère marin herbivore proche du lamantin",
            "Mayotte abrite l'une des dernières populations de dugongs de l'océan Indien occidental",
            "Il n'en resterait qu'une poignée d'individus dans le lagon de Mayotte",
            "Le dugong se nourrit exclusivement d'herbes marines",
            "Il peut peser jusqu'à 400 kg et mesurer 3 mètres",
            "Les marins l'auraient confondu avec des sirènes au fil des siècles",
        ],
        "search_seeds": ["dugong manatee underwater", "sea cow swimming", "marine mammal seagrass", "endangered species ocean"],
        "visual_hints": ["dugong swimming in turquoise lagoon, seagrass bed, photorealistic underwater"],
        "avoid": ["dire que le dugong est abondant — il est en danger critique à Mayotte"],
    },
    {
        "title": "Les baleines à bosse — visiteuses majestueuses",
        "key_facts": [
            "Les baleines à bosse fréquentent Mayotte de juillet à octobre",
            "Elles viennent de l'Antarctique pour mettre bas dans les eaux chaudes du lagon",
            "Durant leur séjour, elles ne se nourrissent pas et vivent sur leurs réserves de graisse",
            "Les mâles chantent des mélodies complexes",
            "Une baleine adulte peut peser 30 tonnes et mesurer 15 mètres",
            "Le lagon, large et calme, protège les mères et leurs baleineaux",
        ],
        "search_seeds": ["humpback whale breach", "whale watching boat", "whale tail underwater", "mother whale calf"],
        "visual_hints": ["humpback whale breaching ocean surface, dramatic spray, photorealistic"],
        "avoid": [],
    },
    {
        "title": "L'ylang-ylang — la fleur d'or de Mayotte",
        "key_facts": [
            "Mayotte a longtemps produit une large part de l'ylang-ylang mondial",
            "Cette fleur jaune sert à l'extraction d'huile essentielle pour la parfumerie",
            "Elle entre dans la composition de grands parfums",
            "La récolte se fait à la main, à l'aube, avant que le soleil n'altère le parfum",
            "Un kilogramme d'huile nécessite une grande quantité de fleurs",
            "La distillation traditionnelle se fait dans des alambics en cuivre",
        ],
        "search_seeds": ["yellow tropical flower harvest", "perfume distillation copper", "tropical plantation", "essential oil extraction"],
        "visual_hints": ["ylang ylang yellow flower close-up, harvested in tropical plantation morning light, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Les makis — lémuriens de Mayotte",
        "key_facts": [
            "Le maki de Mayotte est un lémurien brun, sous-espèce propre à l'île",
            "On estime sa population à environ 2000 individus",
            "C'est le seul primate sauvage présent sur l'île",
            "Il vit surtout dans les forêts humides et se nourrit de fruits et de feuilles",
            "Les groupes comptent généralement 5 à 15 individus",
            "C'est un animal protégé, devenu une figure familière de Mayotte",
        ],
        "search_seeds": ["lemur tropical forest", "primate jumping branches", "brown lemur", "lemur eating fruit"],
        "visual_hints": ["brown lemur sitting on tree branch in tropical rainforest, photorealistic"],
        "avoid": ["le maki descend des lémuriens de Madagascar — ne pas dire qu'il est apparu à Mayotte"],
    },
    {
        "title": "Le baobab — arbre légendaire",
        "key_facts": [
            "Mayotte compte des baobabs centenaires, notamment dans le sud de l'île",
            "Le baobab peut vivre très longtemps et stocker des milliers de litres d'eau dans son tronc",
            "Selon une légende, Dieu aurait planté l'arbre à l'envers",
            "Ses fruits, appelés pains de singe, sont riches en vitamine C",
            "Son tronc creux a longtemps servi d'abri aux voyageurs",
        ],
        "search_seeds": ["baobab tree silhouette", "ancient tree sunset", "african baobab", "iconic tropical tree"],
        "visual_hints": ["massive baobab tree silhouette at sunset, golden hour, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le caméléon de Mayotte — l'animal unique au monde",
        "key_facts": [
            "Le caméléon de Mayotte est la seule espèce de vertébré strictement endémique de l'île",
            "Il n'existe sur aucune autre île au monde",
            "Le mâle est vert avec des écailles labiales blanches ; la femelle est plutôt jaunâtre",
            "Il peut bouger ses deux yeux indépendamment l'un de l'autre",
            "Sa langue projetable lui sert à capturer ses proies",
            "Il porte un casque crânien prolongé par une crête le long du dos",
        ],
        "search_seeds": ["chameleon close-up branch", "green chameleon tropical", "chameleon eye macro", "chameleon tongue catching insect"],
        "visual_hints": ["a green chameleon with white lips on a branch in tropical foliage, macro detail, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le drongo de Mayotte — l'oiseau noir menacé",
        "key_facts": [
            "Le drongo de Mayotte est un oiseau endémique de l'île",
            "Son corps est entièrement noir avec des reflets bleu-vert et un iris rouge brique",
            "Il possède une longue queue fourchue très caractéristique",
            "Il chasse les insectes en vol, en s'élançant depuis un perchoir",
            "Il vit dans la forêt humide d'altitude",
            "Sa population est très réduite, ce qui en fait une espèce très menacée",
        ],
        "search_seeds": ["black bird forked tail", "tropical black bird branch", "bird catching insect flight", "rainforest bird"],
        "visual_hints": ["a glossy black bird with a long forked tail perched on a branch in a rainforest, photorealistic"],
        "avoid": [],
    },
    {
        "title": "La tortue verte — 3000 pontes par an",
        "key_facts": [
            "La tortue verte est l'une des deux espèces de tortues marines qui pondent à Mayotte",
            "Chaque année, des milliers de tortues vertes viennent pondre sur les plages de l'île",
            "Les principaux sites de ponte sont Moya et Saziley",
            "Une tortue verte adulte peut mesurer 1,5 m de carapace et peser jusqu'à 230 kg",
            "C'est la seule tortue marine herbivore à l'âge adulte : elle broute les herbiers",
            "De nombreuses tortues s'alimentent en permanence dans les herbiers du lagon",
        ],
        "search_seeds": ["green sea turtle beach nesting", "turtle swimming reef", "baby turtles hatching", "sea turtle seagrass"],
        "visual_hints": ["a green sea turtle on a moonlit beach laying eggs in the sand, photorealistic"],
        "avoid": [],
    },
    {
        "title": "La tortue imbriquée — la plus rare de Mayotte",
        "key_facts": [
            "La tortue imbriquée est la seconde espèce de tortue marine qui pond à Mayotte",
            "Elle est bien plus rare que la tortue verte",
            "Seule une centaine vient pondre sur les plages mahoraises chaque année",
            "Elle mesure de 70 cm à 1 m et ne dépasse pas environ 130 kg",
            "Son bec pointu lui permet de chercher sa nourriture dans les anfractuosités du récif",
        ],
        "search_seeds": ["hawksbill turtle reef", "sea turtle coral", "turtle swimming underwater", "tropical turtle close-up"],
        "visual_hints": ["a hawksbill sea turtle with a pointed beak swimming over a colorful coral reef, photorealistic"],
        "avoid": [],
    },
    {
        "title": "La raie manta — le géant doux du lagon",
        "key_facts": [
            "La raie manta de récif réside dans le lagon de Mayotte",
            "Son envergure, d'une nageoire à l'autre, atteint 4 à 5 mètres",
            "Malgré sa taille, elle est totalement inoffensive : elle filtre le plancton",
            "Chaque raie porte des taches noires uniques sur le ventre, comme une empreinte digitale",
            "Elle est plus facilement observable d'avril à septembre",
        ],
        "search_seeds": ["manta ray swimming", "giant manta underwater", "manta ray filter feeding", "ray gliding ocean"],
        "visual_hints": ["a giant manta ray gliding gracefully through clear blue water, wings spread wide, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Les dauphins de Mayotte — 21 espèces dans le lagon",
        "key_facts": [
            "Au total, 21 espèces de dauphins ont été observées dans les eaux de Mayotte",
            "Trois espèces résident toute l'année autour de l'île",
            "Le grand dauphin de l'Indo-Pacifique se voit directement dans le lagon",
            "Il se déplace en petits groupes de 5 à 20 individus",
            "Le dauphin à long bec, lui, évolue en haute mer en bancs beaucoup plus grands",
        ],
        "search_seeds": ["dolphins jumping ocean", "dolphin pod swimming", "dolphins lagoon aerial", "dolphin underwater"],
        "visual_hints": ["a pod of dolphins leaping out of turquoise ocean water, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le coelacanthe — le fossile vivant des Comores",
        "key_facts": [
            "Le coelacanthe est un poisson considéré comme un « fossile vivant »",
            "Son groupe était cru disparu depuis des dizaines de millions d'années",
            "Le premier spécimen vivant a été identifié en 1938",
            "Sa population vit sur les pentes volcaniques de l'archipel des Comores, voisin de Mayotte",
            "Il vit en profondeur, généralement entre 150 et 250 mètres",
            "Le jour, il se réfugie en petits groupes dans des grottes de lave",
        ],
        "search_seeds": ["coelacanth deep sea fish", "prehistoric fish", "deep ocean fish dark", "ancient fish"],
        "visual_hints": ["a large prehistoric coelacanth fish swimming near dark volcanic rocks in deep blue water, photorealistic"],
        "avoid": ["le coelacanthe vit aux Comores voisines — ne pas dire qu'il est pêché à Mayotte"],
    },
    {
        "title": "Les coraux du lagon — une cité sous-marine",
        "key_facts": [
            "Le lagon de Mayotte abrite environ 300 espèces de coraux",
            "Plus de 2300 espèces marines y ont été recensées",
            "Les coraux durs bâtissent les récifs où vit toute cette biodiversité",
            "Mayotte possède même une seconde barrière interne de corail",
            "Le cyclone Chido de 2024 a durement endommagé ces récifs",
        ],
        "search_seeds": ["colorful coral reef", "coral garden underwater", "reef fish coral", "vibrant coral ecosystem"],
        "visual_hints": ["a vibrant colorful coral reef teeming with tropical fish, sun rays through clear water, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le poisson-perroquet à bosse — le bâtisseur de plages",
        "key_facts": [
            "Le poisson-perroquet à bosse est le plus grand des poissons-perroquets",
            "Il peut atteindre 130 cm de long et peser jusqu'à 75 kg",
            "Avec son bec puissant, il broute le corail en creusant la roche calcaire",
            "Il rejette le corail digéré sous forme de sable fin",
            "Un grand individu peut produire plusieurs tonnes de sable corallien par an",
            "Il est protégé à Mayotte, sa capture y est interdite",
        ],
        "search_seeds": ["parrotfish coral reef", "large parrotfish swimming", "parrotfish biting coral", "colorful reef fish"],
        "visual_hints": ["a large bumphead parrotfish biting a coral reef, blue-green scales, photorealistic"],
        "avoid": [],
    },
    {
        "title": "La roussette — la chauve-souris géante de Mayotte",
        "key_facts": [
            "La roussette de Mayotte est une grande chauve-souris frugivore",
            "Son envergure peut dépasser le mètre",
            "Elle se reconnaît à sa couleur brun foncé et à son collier roussâtre",
            "Elle se nourrit de fruits, de nectar et de feuilles",
            "En visitant les fleurs, elle pollinise des arbres comme le baobab",
            "Elle est protégée à Mayotte par un arrêté préfectoral",
        ],
        "search_seeds": ["fruit bat hanging tree", "flying fox bat", "large bat tropical", "bat in flight night"],
        "visual_hints": ["a large fruit bat (flying fox) hanging from a tree branch at dusk, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le crabier blanc — l'oiseau le plus menacé de Mayotte",
        "key_facts": [
            "Le crabier blanc est un petit héron de 45 à 48 cm",
            "C'est l'oiseau le plus menacé de Mayotte, classé en danger critique d'extinction",
            "En période de reproduction, il arbore un plumage blanc neige et un bec bleu vif",
            "Environ 200 couples nicheurs ont choisi Mayotte",
            "Cela représente près de 20 % de la population mondiale de l'espèce",
            "Il niche principalement dans les mangroves",
        ],
        "search_seeds": ["white heron mangrove", "egret wading bird", "white bird wetland", "heron fishing shallow water"],
        "visual_hints": ["a pure white heron with a bright blue beak standing in a mangrove, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le poisson-pierre — le plus venimeux du monde",
        "key_facts": [
            "Le poisson-pierre vit dans le lagon de Mayotte : c'est le poisson le plus venimeux du monde",
            "Maître du camouflage, il ressemble à une simple pierre couverte d'algues",
            "Il porte sur le dos treize épines venimeuses",
            "Le danger vient des baigneurs qui marchent dessus sans le voir",
            "Sa piqûre provoque une douleur extrême et nécessite des soins en urgence",
            "C'est un poisson solitaire et presque immobile, qui ne fuit pas",
        ],
        "search_seeds": ["stonefish camouflage reef", "stonefish sandy bottom", "venomous fish ocean floor", "camouflaged fish rocks"],
        "visual_hints": ["a stonefish perfectly camouflaged among rocks and algae on the seabed, photorealistic"],
        "avoid": [],
    },
    {
        "title": "La vanille de Mayotte — la fleur fécondée à la main",
        "key_facts": [
            "La vanille de Mayotte est une orchidée, sous l'appellation « vanille Bourbon »",
            "Sa fleur ne s'ouvre qu'une seule fois, seulement quelques heures",
            "Hors de son Mexique d'origine, la fleur ne peut pas se féconder seule",
            "Chaque fleur doit donc être pollinisée à la main, une par une",
            "Cette technique a été mise au point en 1841 par Edmond Albius, un jeune esclave de 12 ans",
            "Son geste a fondé toute l'industrie vanillière de l'océan Indien",
        ],
        "search_seeds": ["vanilla orchid flower", "vanilla pods plantation", "hand pollination vanilla", "vanilla vine tropical"],
        "visual_hints": ["close-up of a pale vanilla orchid flower on a vine, tropical plantation, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le jacquier — le plus gros fruit du monde",
        "key_facts": [
            "Le jacquier est un arbre cultivé à Mayotte, proche parent de l'arbre à pain",
            "Son fruit, le jacque, est le plus gros fruit comestible de la planète",
            "Il peut peser de 1 à 50 kg",
            "À maturité, sa chair sucrée rappelle un mélange d'ananas et de mangue",
            "Le fruit à pain, son cousin, se consomme cuit et rappelle la pomme de terre",
        ],
        "search_seeds": ["jackfruit tree huge fruit", "breadfruit tree tropical", "giant fruit hanging tree", "tropical fruit market"],
        "visual_hints": ["an enormous spiky jackfruit hanging from a tree trunk, tropical garden, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le gecko vert — le petit joyau de Mayotte",
        "key_facts": [
            "Le gecko de Robert Mertens est un petit lézard diurne endémique strict de Mayotte",
            "Il mesure environ 11 centimètres",
            "Il est vert vif, souvent marqué d'une ligne dorsale orangée",
            "Il a été décrit scientifiquement seulement en 1980",
            "On le rencontre souvent sur les bananiers et dans les anciennes plantations",
            "C'est une espèce menacée",
        ],
        "search_seeds": ["green day gecko leaf", "bright green lizard tropical", "gecko on banana leaf", "small colorful gecko"],
        "visual_hints": ["a vivid green day gecko with orange markings on a banana leaf, macro detail, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le paille-en-queue — l'oiseau marin de Mayotte",
        "key_facts": [
            "Le paille-en-queue, ou phaéton à bec jaune, est le seul oiseau marin qui niche à Mayotte",
            "Son envergure atteint 90 à 95 centimètres",
            "Il se reconnaît à deux longues plumes blanches qui prolongent sa queue",
            "Il plane longuement au-dessus de l'océan avant de plonger pour pêcher",
            "Il est classé comme espèce vulnérable",
        ],
        "search_seeds": ["tropicbird flying ocean", "white seabird long tail", "seabird cliff coast", "tropicbird soaring"],
        "visual_hints": ["a white tropicbird with long tail feathers soaring over the ocean near coastal cliffs, photorealistic"],
        "avoid": [],
    },
    {
        "title": "L'hippocampe — Mayotte, l'île en forme de cheval de mer",
        "key_facts": [
            "Mayotte est parfois surnommée « l'île aux hippocampes » à cause de la forme de son territoire",
            "Des hippocampes vivent réellement dans les herbiers du lagon",
            "L'hippocampe est un poisson qui nage à la verticale",
            "Chez l'hippocampe, c'est le mâle qui porte les œufs dans une poche ventrale",
            "C'est donc le père qui « met au monde » les petits",
        ],
        "search_seeds": ["seahorse seagrass", "seahorse underwater macro", "seahorse coral", "tiny seahorse ocean"],
        "visual_hints": ["a delicate seahorse clinging to seagrass in clear turquoise water, macro detail, photorealistic"],
        "avoid": [],
    },
    {
        "title": "La flore endémique des forêts de Mayotte",
        "key_facts": [
            "Mayotte abrite environ 610 espèces de plantes indigènes",
            "Parmi elles, une soixantaine sont strictement endémiques de l'île",
            "Ces plantes ne poussent nulle part ailleurs sur Terre",
            "Plus de 70 % de cette flore endémique est aujourd'hui menacée",
            "L'isolement de l'île a permis l'apparition de ces espèces uniques",
        ],
        "search_seeds": ["lush tropical plants forest", "rare tropical flower", "endemic plants jungle", "tropical undergrowth green"],
        "visual_hints": ["lush tropical forest undergrowth with rare flowering plants, soft light, photorealistic"],
        "avoid": [],
    },
]

# === TRADITIONS & CULTURE ===
TRADITIONS: list[KnowledgeEntry] = [
    {
        "title": "Le manzaraka — mariage traditionnel mahorais",
        "key_facts": [
            "Le manzaraka est le mariage coutumier traditionnel à Mayotte",
            "La cérémonie peut s'étaler sur plusieurs jours, parfois une semaine",
            "Elle réunit toute la famille élargie et le village",
            "La mariée est richement parée d'or et de salouva colorées",
            "Les chants debaa et les danses chigoma rythment les festivités",
            "Le mariage scelle aussi des alliances entre lignages",
        ],
        "search_seeds": ["traditional wedding ceremony africa", "bride gold jewelry", "drum dance celebration", "colorful traditional dress"],
        "visual_hints": ["traditional Comoran wedding ceremony, bride in colorful salouva with gold, drumming celebration, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le debaa — chants féminins sacrés",
        "key_facts": [
            "Le debaa est un chant religieux pratiqué exclusivement par les femmes mahoraises",
            "Il puise dans la tradition soufie et célèbre le prophète Mahomet",
            "Les femmes sont parées de robes colorées et coiffées de bijoux",
            "Les chœurs sont accompagnés de tambourins",
            "Les performances ont lieu lors de mariages et fêtes religieuses",
        ],
        "search_seeds": ["women singing traditional", "religious ceremony africa", "tambourine performance", "colorful headscarves"],
        "visual_hints": ["group of women in colorful Comoran dress singing religious hymn, tambourine, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le m'biwi — rythme du quotidien",
        "key_facts": [
            "Le m'biwi est une musique-danse traditionnelle féminine mahoraise",
            "Elle est exécutée à mains nues, avec battements de mains et de cuisses",
            "Les femmes forment un cercle et frappent des rythmes complexes",
            "La pratique remonte aux temps précoloniaux",
            "Elle accompagne mariages, naissances et fêtes du village",
        ],
        "search_seeds": ["women clapping circle dance", "traditional rhythm dance africa", "village celebration women"],
        "visual_hints": ["women in colorful dresses forming circle, clapping rhythmic dance, village setting, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le masque de santal — beauté quotidienne",
        "key_facts": [
            "Le masque de santal jaune est emblématique des femmes mahoraises",
            "Il s'appelle « msindzano » en shimaoré",
            "Il est obtenu par broyage de bois de santal sur une pierre humide",
            "Il sert de soin de peau, de protection solaire et d'expression esthétique",
            "Les femmes l'appliquent en motifs sur le visage avant de sortir",
            "C'est un marqueur identitaire de l'archipel des Comores et de Mayotte",
        ],
        "search_seeds": ["yellow face mask traditional", "sandalwood beauty ritual", "comoran woman portrait", "natural skincare africa"],
        "visual_hints": ["Comoran woman portrait wearing yellow sandalwood face mask, traditional beauty, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le voulé — repas convivial sur la plage",
        "key_facts": [
            "Le voulé est un barbecue traditionnel mahorais sur la plage",
            "On y grille poissons, brochettes de viande et bananes plantains",
            "Le repas se fait pieds dans le sable, en famille ou entre amis",
            "Le mataba, feuilles de manioc pilées au coco, est souvent servi",
            "C'est le rituel dominical par excellence pour beaucoup de Mahorais",
        ],
        "search_seeds": ["beach barbecue tropical", "grilled fish coconut palm", "family beach picnic", "tropical food beach"],
        "visual_hints": ["beach barbecue with grilled fish, family gathering at sunset, palm trees, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le mtsolola — le ragoût emblématique de Mayotte",
        "key_facts": [
            "Le mtsolola est un ragoût mahorais à base de banane plantain et de manioc",
            "Il est mijoté avec de la viande de bœuf, du poulet ou parfois du poisson",
            "Il est relevé de tomate et de citron",
            "C'est l'un des plats les plus représentatifs de la cuisine mahoraise quotidienne",
            "La cuisine de Mayotte mêle des influences africaines, malgaches, arabes et indiennes",
        ],
        "search_seeds": ["traditional stew pot cooking", "plantain cassava dish", "african home cooking", "tropical food close-up"],
        "visual_hints": ["a hearty tropical stew with plantain and cassava in a pot, home kitchen, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le mataba — feuilles de manioc au lait de coco",
        "key_facts": [
            "Le mataba est préparé à partir de feuilles de manioc pilées",
            "Elles sont mijotées dans du lait de coco",
            "Le plat est souvent servi en grande quantité lors des mariages traditionnels",
            "Le lait de coco, obtenu en pressant la chair de la noix, entre dans beaucoup de plats de l'île",
        ],
        "search_seeds": ["cassava leaves dish", "coconut milk cooking", "green leafy stew", "grating coconut"],
        "visual_hints": ["a green dish of pounded cassava leaves cooked in coconut milk, served in a bowl, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Les mabawa — les ailes de poulet de la rue",
        "key_facts": [
            "Les mabawa sont des ailes de poulet marinées puis grillées",
            "C'est le plat emblématique de la cuisine de rue à Mayotte",
            "On les déguste grillées au barbecue ou frites",
            "Elles sont servies avec du riz, du manioc ou de la banane verte",
            "On les achète auprès des « mama brochetti », les femmes qui les préparent sur des étals de rue",
        ],
        "search_seeds": ["grilled chicken wings street", "street food barbecue", "chicken wings charcoal grill", "street food stall night"],
        "visual_hints": ["grilled chicken wings on a street food charcoal grill at night, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le massalé — le mélange d'épices mahorais",
        "key_facts": [
            "Le massalé est un mélange d'épices au cœur de la cuisine mahoraise",
            "Il associe notamment cumin, coriandre, cardamome, poivre, clou de girofle et cannelle",
            "La cuisine mahoraise se caractérise par son usage généreux des épices",
            "Le marché couvert de Mamoudzou compte de nombreux marchands d'épices",
        ],
        "search_seeds": ["colorful spices market", "spice blend bowls", "spice market stall", "ground spices close-up"],
        "visual_hints": ["colorful piles of ground spices at a market stall, warm tones, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le mkatra foutra — le pain plat au lait de coco",
        "key_facts": [
            "Le mkatra foutra est un pain plat mahorais à base de farine et de lait de coco",
            "Il est généralement salé et parsemé de graines de sésame",
            "Il accompagne souvent le petit-déjeuner",
            "Les crêpes mahoraises, les mkatra, se garnissent de sucre ou de noix de coco râpée",
        ],
        "search_seeds": ["flatbread sesame seeds", "coconut flatbread cooking", "traditional bread pan", "tropical breakfast bread"],
        "visual_hints": ["round flatbread sprinkled with sesame seeds cooking on a pan, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le putu — la sauce piquante de tous les repas",
        "key_facts": [
            "Le putu est une sauce très piquante servie à presque chaque repas mahorais",
            "Il se compose de piment, de tomate, d'oignon et de citron",
            "Il sert à relever le goût des plats",
            "Chaque famille a sa façon de le préparer",
        ],
        "search_seeds": ["red chili sauce bowl", "spicy condiment", "fresh chili peppers", "tropical hot sauce"],
        "visual_hints": ["a small bowl of bright red spicy chili sauce with fresh peppers, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le wadaha — la danse du pilon",
        "key_facts": [
            "Le wadaha est une danse exclusivement féminine, exécutée autour d'un mortier et de pilons",
            "Le pilon et le mortier servaient autrefois à piler le riz cultivé sur l'île",
            "La danse est née de la solidarité villageoise au temps où l'on pilait le riz en commun",
            "Les danseuses jonglent avec les pilons en rythme",
            "Mariages, fêtes, célébrations : toutes les occasions sont bonnes pour danser le wadaha",
        ],
        "search_seeds": ["women dancing mortar pestle", "traditional african dance", "village women celebration", "rhythmic dance colorful"],
        "visual_hints": ["women in colorful dresses dancing around a wooden mortar, twirling pestles, village, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le shigoma — la danse masculine en cercle",
        "key_facts": [
            "Le shigoma est une danse réservée aux hommes",
            "Les danseurs forment un cercle au centre duquel des tambours rythment la danse",
            "Selon la tradition, ses origines remonteraient à Zanzibar",
            "Elle se danse sur un rythme langoureux ponctué de mouvements rapides",
            "Elle célèbre les événements importants de la communauté",
        ],
        "search_seeds": ["men circle dance drums", "traditional male dance africa", "drummers circle", "village dance celebration"],
        "visual_hints": ["a circle of men dancing around drummers, traditional celebration, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le mgodro — le rythme populaire de Mayotte",
        "key_facts": [
            "Le mgodro est un rythme et une danse emblématiques de Mayotte, dansés en cercle mixte",
            "Il s'inspire du salegy, une musique malgache",
            "Il se joue traditionnellement avec des instruments de l'océan Indien",
            "Il s'est modernisé en intégrant guitare, batterie et synthétiseur",
            "Il est pratiqué aujourd'hui par toutes les générations",
        ],
        "search_seeds": ["festive dance music", "people dancing circle joy", "tropical music celebration", "live music dance night"],
        "visual_hints": ["people of all ages dancing joyfully in a circle to live music, festive night, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le mkayamba — le hochet en radeau",
        "key_facts": [
            "Le mkayamba est un instrument de percussion mahorais, un hochet de forme rectangulaire",
            "Son cadre est fabriqué en raphia et recouvert de tiges végétales",
            "À l'intérieur, des graines enfermées produisent le son",
            "Cet instrument existe dans tout l'océan Indien sous d'autres noms, comme le kayamb à La Réunion",
        ],
        "search_seeds": ["handmade percussion instrument", "rattle instrument traditional", "african musical instrument", "shaker instrument hands"],
        "visual_hints": ["hands holding a flat rectangular rattle percussion instrument made of plant fibers, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le gabusi — le luth de l'océan Indien",
        "key_facts": [
            "Le gabusi est un instrument à cordes utilisé à Mayotte et aux Comores",
            "Le gabusi comorien possède cinq cordes",
            "Il a une forme de poire, la caisse et le manche formant une seule pièce",
            "Il accompagne notamment le mgodro dans sa forme traditionnelle",
        ],
        "search_seeds": ["traditional lute instrument", "string instrument wood", "musician playing lute", "handmade string instrument"],
        "visual_hints": ["a musician playing a pear-shaped traditional wooden lute, warm light, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le mouringué — la lutte traditionnelle de Mayotte",
        "key_facts": [
            "Le mouringué est un combat traditionnel à mains nues très pratiqué à Mayotte",
            "Il appartient à une famille de combats de l'océan Indien",
            "À Mayotte, les combats avaient lieu le soir et pouvaient durer toute la nuit",
            "Malgré son apparente liberté, il obéit à des règles précises",
            "Il est souvent accompagné de rituels et de danses au son des tambours",
        ],
        "search_seeds": ["traditional martial art fight", "barefoot combat night", "african wrestling drums", "fighters circle crowd"],
        "visual_hints": ["two barefoot fighters facing off in a circle of spectators at night, drums, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le salouva — la tenue des femmes mahoraises",
        "key_facts": [
            "Le salouva est une grande pièce de coton qui s'enroule autour du corps jusqu'aux pieds",
            "Il en existe plusieurs types : brodé pour les cérémonies, plus simple pour le quotidien",
            "Ses couleurs et motifs sont souvent vifs et éclatants",
            "Le vendredi est particulièrement associé au port du salouva",
        ],
        "search_seeds": ["colorful wrap dress woman", "traditional african fabric dress", "vibrant patterned clothing", "woman colorful textile"],
        "visual_hints": ["a woman wearing a brightly colored patterned wrap dress, traditional Comoran clothing, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le kishali — le châle qui complète le salouva",
        "key_facts": [
            "Le kishali est un voile fait du même tissu que le salouva",
            "Il se porte sur la tête ou sur les épaules",
            "Il n'a pas de connotation religieuse : il protège du soleil et exprime l'élégance",
            "Les femmes l'utilisent pour souligner leur gestuelle",
        ],
        "search_seeds": ["colorful shawl woman", "patterned scarf head", "vibrant fabric draped", "woman shawl tropical"],
        "visual_hints": ["a woman draping a colorful patterned shawl over her shoulders, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le kandzu et la kofia — la tenue masculine des cérémonies",
        "key_facts": [
            "Pour la mosquée et les cérémonies, les hommes portent le kandzu, une longue robe brodée",
            "Ils y associent la kofia, une calotte brodée à la main par les femmes",
            "Les motifs de la kofia comportent souvent des versets coraniques",
            "Lors des mariages, le kandzu est porté avec le djoho, un manteau brodé de fil d'or",
        ],
        "search_seeds": ["embroidered cap man", "traditional robe man africa", "muslim ceremonial dress", "embroidered hat detail"],
        "visual_hints": ["a man wearing a long embroidered robe and an embroidered cap, traditional ceremony, photorealistic"],
        "avoid": [],
    },
    {
        "title": "La société matrilocale mahoraise",
        "key_facts": [
            "Mayotte est une société traditionnellement matrilinéaire",
            "Le nom, les statuts et les biens se transmettent par les femmes",
            "Elle est aussi matrilocale : l'homme vient habiter dans la famille de son épouse",
            "À son mariage, la fille reçoit en principe une maison qu'elle gardera toute sa vie",
            "Cette organisation place la femme au centre de la famille et du patrimoine",
        ],
        "search_seeds": ["tropical family home", "women family gathering", "traditional house tropical", "grandmother mother daughter"],
        "visual_hints": ["three generations of women together in front of a colorful tropical family house, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le shioni — l'école coranique de Mayotte",
        "key_facts": [
            "Le shioni est l'école coranique traditionnelle, souvent installée dans la cour d'une maison",
            "C'est la plus ancienne institution d'enseignement de Mayotte",
            "Les enfants la fréquentent dès l'âge de 4 ans",
            "Le foundi, le maître coranique, fait répéter et réciter les versets par cœur",
            "Depuis les années 1980, des madrasas modernes se sont développées",
        ],
        "search_seeds": ["children learning outdoor", "quran school children", "kids reading wooden board", "village school africa"],
        "visual_hints": ["children sitting outdoors learning to read on wooden boards, village school, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le mawlid — la fête de la naissance du Prophète",
        "key_facts": [
            "Le mawlid célèbre la naissance du prophète Mahomet",
            "C'est une fête à la fois religieuse et culturelle importante à Mayotte",
            "C'est une pratique d'origine soufie où l'on chante les louanges du Prophète",
            "Un chœur dansant, conduit par un meneur, anime la célébration",
            "Le mawlid est un jour férié à Mayotte",
        ],
        "search_seeds": ["religious celebration singing", "muslim festival gathering", "chanting ceremony night", "community religious feast"],
        "visual_hints": ["a community gathered for a joyful religious chanting celebration, warm evening light, photorealistic"],
        "avoid": [],
    },
    {
        "title": "La circoncision — un rite de passage festif",
        "key_facts": [
            "Chez les jeunes Mahorais, la circoncision marque le passage de l'enfance à la jeunesse",
            "Elle est pratiquée pour des raisons religieuses",
            "Le matin, les hommes de la famille récitent une prière de protection",
            "La veille, les femmes pratiquent le heredza, un rite avec chants et plantes",
            "Certaines familles sacrifient un zébu dont la viande est partagée avec le quartier",
        ],
        "search_seeds": ["family celebration feast", "village ceremony gathering", "traditional rite celebration", "community festive meal"],
        "visual_hints": ["a festive family gathering for a rite of passage celebration, colorful, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le fundi et le mganga — la médecine traditionnelle",
        "key_facts": [
            "À Mayotte, le fundi désigne un maître ou un spécialiste, notamment des massages",
            "Le mganga est un guérisseur traditionnel",
            "Des femmes aux savoirs anciens préparent des remèdes à base de plantes",
            "Ces remèdes traditionnels coexistent avec la médecine moderne",
            "Certaines plantes utilisées ne sont toutefois pas sans risque",
        ],
        "search_seeds": ["traditional healer herbs", "medicinal plants hands", "herbal remedy preparation", "healer tropical plants"],
        "visual_hints": ["hands preparing herbal medicine from tropical plants, traditional healing, photorealistic"],
        "avoid": ["ne pas présenter ces remèdes comme un substitut à la médecine moderne"],
    },
    {
        "title": "La laka — la pirogue traditionnelle mahoraise",
        "key_facts": [
            "La laka est la pirogue traditionnelle de Mayotte, formée d'une coque et d'un balancier",
            "Elle est taillée dans le bois d'un seul arbre, choisi par le pêcheur",
            "Le balancier, un tronc fin sur le côté, assure sa stabilité",
            "Les pêcheurs y utilisent une ligne à main lestée d'hameçons",
            "La pirogue à balancier est peu à peu délaissée au profit des bateaux à moteur",
        ],
        "search_seeds": ["outrigger canoe ocean", "traditional fishing canoe", "wooden pirogue lagoon", "fisherman canoe sunrise"],
        "visual_hints": ["a wooden outrigger canoe with a fisherman on a calm turquoise lagoon at sunrise, photorealistic"],
        "avoid": [],
    },
    {
        "title": "La vannerie et la poterie — l'artisanat mahorais",
        "key_facts": [
            "La vannerie mahoraise utilise raphia, feuilles de cocotier, bambou et liane",
            "Elle produit nattes, paniers et chapeaux",
            "Les feuilles de cocotier tressées résistent au vent, à la pluie et aux charges",
            "La poterie est produite par des potières, notamment à Sohoa et Dembéni",
            "La poterie traditionnelle de Mayotte est inscrite au patrimoine culturel immatériel",
        ],
        "search_seeds": ["woven basket craft", "weaving palm leaves hands", "pottery hands clay", "handmade craft tropical"],
        "visual_hints": ["close-up of hands weaving a basket from palm leaves, traditional craft, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Les mamas shingo — le sel de Bandrélé",
        "key_facts": [
            "À Mayotte, la production de sel est portée par des femmes, les « mamas shingo »",
            "Elles exploitent la vase salée déposée sur la plaine côtière de Bandrélé",
            "La terre salée est filtrée puis le liquide est évaporé pour récolter le sel",
            "La production s'arrête pendant la saison des pluies",
            "Elles ne sont plus qu'une vingtaine à perpétuer cette pratique ancestrale",
        ],
        "search_seeds": ["salt harvesting women", "traditional salt production", "coastal salt flats", "women working salt"],
        "visual_hints": ["women harvesting sea salt on a coastal flat at golden hour, traditional method, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le mraha — le jeu de graines mahorais",
        "key_facts": [
            "Le mraha wa tso, « le jeu avec les graines », est un jeu de plateau traditionnel",
            "Il appartient à la grande famille des mancalas",
            "Il se joue à deux, sur un plateau en bois creusé de cases",
            "Les pions sont des graines ou des coquillages que l'on déplace de case en case",
            "Il est identique au bao joué à Zanzibar",
            "La famille des mancalas est très ancienne, vieille de plus de mille ans",
        ],
        "search_seeds": ["mancala board game seeds", "wooden game board", "hands playing board game", "traditional strategy game"],
        "visual_hints": ["close-up of hands playing a wooden mancala board game with seeds, photorealistic"],
        "avoid": [],
    },
    {
        "title": "L'Aïd el-Fitr — la fête de la fin du ramadan",
        "key_facts": [
            "L'Aïd el-Fitr marque la fin du ramadan",
            "C'est une fête essentielle pour les musulmans de Mayotte",
            "C'est l'occasion de renouveler sa garde-robe et de porter ses plus beaux habits",
            "Après la prière du matin, les festivités commencent par un grand repas partagé",
            "Ce jour-là, les maisons sont ouvertes et les plats circulent de maison en maison",
        ],
        "search_seeds": ["eid celebration family", "festive meal sharing", "muslim holiday feast", "colorful celebration food"],
        "visual_hints": ["a festive family table loaded with colorful dishes for a celebration, photorealistic"],
        "avoid": [],
    },
]

# === LÉGENDES ===
LEGENDS: list[KnowledgeEntry] = [
    {
        "title": "Trimba — le génie des rivières",
        "key_facts": [
            "Trimba est un esprit des eaux dans les croyances mahoraises",
            "Il habite les rivières, sources et points d'eau de l'île",
            "Selon la tradition, il peut bénir ou punir selon le respect qu'on lui porte",
            "Les anciens y déposaient des offrandes pour solliciter sa protection",
            "Il apparaîtrait sous forme humaine à ceux qui l'invoquent dignement",
            "Plusieurs sources de l'île portent encore son nom",
        ],
        "search_seeds": ["mystical waterfall jungle", "tropical river forest", "mystical fog forest", "sacred spring water"],
        "visual_hints": ["mystical waterfall in tropical forest, mist, fantasy atmosphere, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Les sept femmes de Choungui",
        "key_facts": [
            "Une légende raconte que sept sœurs furent transformées en pierre au sommet du Choungui",
            "Elles auraient désobéi à un esprit ancestral en montant sur la montagne sacrée",
            "Selon une variante, elles cherchaient à se cacher d'un mariage forcé",
            "Les rochers au sommet seraient leurs silhouettes pétrifiées",
            "Cette histoire transmet des valeurs sur le respect des anciens et de la nature",
        ],
        "search_seeds": ["mountain peak rocky silhouette", "stone formations sunset", "tropical mountain summit", "rocky outcrop tropical"],
        "visual_hints": ["seven mysterious rock formations at mountain summit, dramatic sky, fantasy atmosphere"],
        "avoid": [],
    },
    {
        "title": "Le djinn du baobab",
        "key_facts": [
            "Les baobabs sont considérés comme habités par des djinns dans la tradition mahoraise",
            "Les djinns sont des esprits invisibles présents dans le Coran et la culture islamique",
            "On évite de couper un vieux baobab sans rituel préalable",
            "Certains baobabs sont entourés d'offrandes par les villageois",
            "Selon la croyance, les djinns peuvent aider, ou nuire, selon le respect porté",
        ],
        "search_seeds": ["baobab tree mystical sunset", "ancient tree spiritual", "savanna baobab silhouette", "magical forest tree"],
        "visual_hints": ["ancient baobab tree silhouette against orange sunset, mystical glow, photorealistic"],
        "avoid": [],
    },
    {
        "title": "La fontaine de Combani",
        "key_facts": [
            "La source de Combani, au centre de l'île, est considérée comme sacrée",
            "Selon la légende, ses eaux auraient des vertus de fertilité et de guérison",
            "Les villageois s'y rendent encore pour des bénédictions",
            "Elle aurait jailli après qu'un saint homme y ait planté son bâton",
            "L'eau y est restée fraîche même durant les périodes sèches",
        ],
        "search_seeds": ["sacred spring water rocks", "natural fountain forest", "rainforest waterfall", "tropical jungle stream"],
        "visual_hints": ["sacred natural spring in tropical forest, clear water flowing over rocks, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Les Wana Issa — les esprits de la mangrove",
        "key_facts": [
            "Selon la tradition, les Wana Issa sont de petits esprits invisibles qui vivent dans les mangroves",
            "On dit qu'ils protègent la mangrove des hommes, sans posséder les humains",
            "La légende les décrit tantôt nains et poilus, tantôt comme de très belles petites femmes",
            "On raconte qu'ils exaucent les vœux de qui leur dépose des offrandes blanches : lait, riz, miel",
            "Les anciens recommandaient de rentrer avant 17 h pour ne pas être emporté par eux",
        ],
        "search_seeds": ["mysterious mangrove dusk", "misty mangrove forest", "dark mangrove roots water", "twilight tropical swamp"],
        "visual_hints": ["a misty mangrove forest at dusk, mysterious atmosphere, soft glowing light between roots, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Les madjini — le peuple invisible de Mayotte",
        "key_facts": [
            "Le mot djinn, madjini au pluriel, vient de l'arabe et signifie « génie »",
            "Selon la croyance, ce sont des êtres invisibles qui partagent le monde des humains",
            "Tous les djinns ne sont pas maléfiques : certains peuvent aider",
            "Leur diversité reflète le métissage de l'île : croyances arabes, malgaches et bantoues mêlées",
            "Pour s'attirer leurs faveurs, on dépose des offrandes dans les lieux qu'ils habitent",
        ],
        "search_seeds": ["mystical glowing forest", "invisible spirit fog", "supernatural night forest", "magical mist trees"],
        "visual_hints": ["a mysterious tropical forest at night with faint glowing lights suggesting invisible spirits, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Les patros — les djinns familiers de la forêt",
        "key_facts": [
            "Selon la tradition, les patros sont les esprits venus de la forêt",
            "Ils sont les plus proches et les plus familiers des humains parmi tous les djinns",
            "On dit que leur culte est arrivé avec la grande culture bantoue, via Zanzibar",
            "Lors d'une cérémonie nocturne, ils « déclarent leur identité » en prenant possession d'une personne en transe",
            "C'est l'un des nombreux cultes d'esprits recensés à Mayotte",
        ],
        "search_seeds": ["deep forest spirits night", "drum ceremony fire night", "mystical jungle ritual", "tribal night gathering"],
        "visual_hints": ["a nighttime ceremony with drums and firelight at the edge of a dark tropical forest, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le trumba — les esprits des rois malgaches",
        "key_facts": [
            "Le trumba désigne, selon la tradition, l'esprit des ancêtres venus posséder les vivants",
            "Cette croyance a été importée des Sakalava de Madagascar",
            "On dit que les trumba sont les esprits de familles royales malgaches",
            "Les cérémonies trumba concernent principalement les femmes",
            "Ce culte témoigne du lien profond entre Mayotte et Madagascar",
        ],
        "search_seeds": ["ancestral spirit ceremony", "ritual trance night", "mystical ancestor altar", "candlelight spiritual ritual"],
        "visual_hints": ["a solemn candlelit ceremony honoring ancestral spirits, mystical atmosphere, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le grand ngoma — la nuit où les esprits parlent",
        "key_facts": [
            "Le ngoma za madjini, « la danse des djinns », est une cérémonie nocturne de possession",
            "À Mayotte, le mot ngoma désigne à la fois les tambours et les danses qu'ils accompagnent",
            "Selon la croyance, durant la transe, c'est le djinn qui parle à la place de la personne",
            "La cérémonie dure toute la nuit, jusqu'à l'aube",
            "Elle vise à apaiser l'impétuosité des esprits par la musique",
        ],
        "search_seeds": ["night drum ceremony fire", "trance ritual drums", "nocturnal tribal dance", "firelight drummers night"],
        "visual_hints": ["an intense nighttime drum ceremony around a fire, dancers in trance, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le mawlida shenge — la veillée chantée jusqu'à la transe",
        "key_facts": [
            "Le mawlida shenge est une veillée soufie en l'honneur de la naissance du Prophète",
            "Elle dure du coucher au lever du soleil, mêlant chant, musique et danse jusqu'à la transe",
            "Un voile de tissu sépare l'espace : hommes et femmes communient sans se voir",
            "Chaque village a son association, dirigée par un fundi, « celui qui détient le savoir »",
            "Le mawlida shenge est classé au patrimoine culturel immatériel national depuis 2022",
        ],
        "search_seeds": ["night vigil singing candle", "spiritual chanting ceremony", "soufi gathering night", "religious vigil firelight"],
        "visual_hints": ["a nighttime spiritual vigil with people chanting by candlelight, mystical atmosphere, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le ziara de Polé — la mosquée en ruine des esprits",
        "key_facts": [
            "La mosquée-ziara de Polé, à Dzaoudzi, est l'une des premières mosquées de pierre de Mayotte",
            "Aujourd'hui en ruine, elle est classée Monument historique depuis 2017",
            "Le site est devenu un ziara, un lieu sacré et de pèlerinage",
            "Selon la tradition, on y organise certaines nuits des cérémonies pour invoquer les esprits",
            "Les offrandes déposées sur place témoignent de ces invocations",
        ],
        "search_seeds": ["ancient ruined mosque", "stone ruins tropical", "old ruins overgrown", "mystical ancient ruins dusk"],
        "visual_hints": ["the stone ruins of an ancient mosque overgrown by tropical vegetation at dusk, mystical mood, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Les ziyara — les lieux sacrés où l'on parle aux esprits",
        "key_facts": [
            "Un ziyara est un lieu sacralisé où se font, selon la croyance, les échanges avec les forces surnaturelles",
            "Ce peut être une rivière, un bois, une source, une habitation ou une tombe",
            "On y va « évoquer ses doléances » et demander protection",
            "Les fundi sont les intermédiaires habilités à parler aux esprits",
            "Le lac Dziani et certaines mangroves sont des ziyara célèbres",
        ],
        "search_seeds": ["sacred place offerings", "mystical natural shrine", "spiritual site forest", "sacred tree offerings"],
        "visual_hints": ["a sacred natural site with offerings laid at the foot of an old tree, mystical light, photorealistic"],
        "avoid": [],
    },
    {
        "title": "La légende du lac Dziani — la princesse offerte à la mer",
        "key_facts": [
            "Le lac Dziani est un lac de cratère vert émeraude de Petite-Terre",
            "La légende raconte qu'un roi voulut offrir sa fille en sacrifice au dieu de la Mer",
            "Selon le récit, la reine s'y opposa pour sauver leur fille",
            "Une croyance veut qu'au fond du lac se trouve « la porte des djinns »",
            "La population vient encore accomplir des rites sur ses rives",
        ],
        "search_seeds": ["emerald crater lake", "green volcanic lake mystical", "crater lake aerial", "mysterious green lake"],
        "visual_hints": ["a mysterious emerald-green crater lake seen from above, mystical atmosphere, photorealistic"],
        "avoid": [],
    },
    {
        "title": "M'tsanga Tsoholé — la légende de l'îlot de riz",
        "key_facts": [
            "La légende raconte qu'un roi maria sa fille et voulut que nul ne pose le pied à terre",
            "Tout le chemin du cortège devait être recouvert de riz",
            "Les villageois pilèrent du riz pendant des mois pour couvrir le sol",
            "Selon le récit, Dieu, courroucé par ce gaspillage, engloutit le village",
            "Le riz se transforma en sable et forma l'îlot de Sable Blanc",
            "Son nom shimaoré, M'tsanga Tsoholé, signifie « sable de riz »",
        ],
        "search_seeds": ["white sandbar ocean", "tiny sand island legend", "turquoise lagoon sandbank", "aerial white sand islet"],
        "visual_hints": ["a pure white sandbar in a turquoise lagoon, dramatic sky, legendary atmosphere, photorealistic"],
        "avoid": [],
    },
    {
        "title": "La femme changée en maki",
        "key_facts": [
            "Selon une légende mahoraise, une femme mêla un jour la nourriture à une souillure de son enfant",
            "Dieu, en colère, l'aurait transformée en maki, le lémurien de l'île, en punition",
            "La légende a une fonction morale : nourriture et impureté ne doivent jamais être mêlées",
            "C'est une légende explicative : elle donne une origine mythique à un animal familier",
        ],
        "search_seeds": ["brown lemur forest", "lemur in tree mystical", "lemur looking forest", "tropical forest creature"],
        "visual_hints": ["a brown lemur with expressive eyes in a misty tropical forest, storybook mood, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le territoire fady de Saziley",
        "key_facts": [
            "À la pointe de Saziley se trouve une zone que la tradition appelle « cœur du territoire fady »",
            "Elle est délimitée par deux baobabs",
            "De nombreux interdits y sont connus : ne pas fumer, ne pas porter de rouge, éviter certaines heures",
            "La légende parle d'un baobab interdit où une personne aurait disparu à jamais",
            "Ces interdits protègent de fait l'unique forêt sèche de l'île",
        ],
        "search_seeds": ["baobab forbidden land", "dry baobab forest dusk", "mystical baobab grove", "sacred forbidden grove"],
        "visual_hints": ["two large baobab trees marking the entrance to a forbidden sacred land, dramatic dusk light, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le mauvais œil — le regard qui rend malade",
        "key_facts": [
            "Selon la croyance mahoraise, certains troubles peuvent venir du mauvais œil, le dzitso",
            "Ce serait un regard jeté par une personne jalouse ou malveillante",
            "On craint particulièrement le regard d'un voisin envieux",
            "Face au malheur, la tradition distingue trois causes : la sorcellerie, les esprits, ou la maladie",
            "Cette croyance a des effets concrets sur la vie quotidienne",
        ],
        "search_seeds": ["protective amulet eye", "mystical eye symbol", "shadowy figure watching", "superstition dark mood"],
        "visual_hints": ["a symbolic protective eye amulet hanging in soft light, mysterious mood, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le hirizi — l'amulette qui protège",
        "key_facts": [
            "Le hirizi est une petite amulette de tissu contenant des versets coraniques",
            "On l'attache aux vêtements, en particulier ceux des bébés, ou on la place dans les maisons",
            "Selon la croyance, elle protège du mauvais œil et des esprits malveillants",
            "Les guérisseurs traditionnels la fabriquent, notamment pour les femmes enceintes et les nouveau-nés",
            "C'est un objet où se mêlent foi islamique et protection contre l'invisible",
        ],
        "search_seeds": ["protective amulet fabric", "small talisman cloth", "amulet hanging close-up", "traditional charm"],
        "visual_hints": ["a small cloth amulet close-up, soft warm light, traditional protective charm, photorealistic"],
        "avoid": [],
    },
    {
        "title": "La roqya — l'exorcisme qui chasse les djinns",
        "key_facts": [
            "Quand une personne tombe inexplicablement malade, la croyance veut qu'elle soit possédée par un djinn",
            "La roqya est un ensemble de méthodes spirituelles censées soigner ces « maladies occultes »",
            "Elle repose sur la récitation de versets coraniques",
            "Elle s'accompagne de l'usage d'eau, d'huile, de miel et d'herbes",
            "À Mayotte, cette pratique séduit de plus en plus, en concurrence avec les rituels animistes anciens",
        ],
        "search_seeds": ["spiritual healing ritual", "religious reading ceremony", "candlelit spiritual session", "prayer healing hands"],
        "visual_hints": ["a calm spiritual healing session with sacred texts and herbs in soft light, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le sahani ya madjini — le plat des ancêtres",
        "key_facts": [
            "Le sahani ya madjini est un plat rituel lié aux cultes des esprits à Mayotte",
            "Selon la tradition, il sert à communiquer avec les djinns et à honorer les ancêtres",
            "Derrière la figure du djinn, ce sont souvent les défunts de la famille qui sont invoqués",
            "On brûle des substances parfumées devant le plat en invoquant les anciens",
            "On dit que les défunts délivrent ainsi bénédictions et remèdes à leurs descendants",
        ],
        "search_seeds": ["ritual offering plate", "incense smoke ritual", "ancestral altar offerings", "spiritual offering bowl"],
        "visual_hints": ["a ritual plate with offerings and rising incense smoke, warm mystical light, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Les miko — les interdits de la femme enceinte",
        "key_facts": [
            "Les miko sont les interdits qui dictent ce qu'une future mère ne doit pas faire",
            "Chaque femme a ses propres miko, transmis par la belle-famille",
            "Exemples : ne pas rester seule, éviter certains lieux ou certains regards",
            "Le mari aussi a ses interdits pendant la grossesse de son épouse",
            "Tout au long de la grossesse, la famille organise des cérémonies de protection",
        ],
        "search_seeds": ["pregnant woman tropical", "protective family ritual", "expectant mother home", "soft warm family scene"],
        "visual_hints": ["a serene expectant mother surrounded by family in a warm tropical home, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le placenta enterré — l'ancrage du nouveau-né",
        "key_facts": [
            "À Mayotte, le placenta du nouveau-né fait l'objet d'un rituel précis",
            "Pour un garçon, il est enterré devant la maison familiale",
            "Ce geste représente l'ancrage de l'enfant dans sa famille et sa terre",
            "Selon la croyance, l'enterrer protège aussi le bébé des esprits malveillants",
            "À la première sortie, on maquille le bébé et on utilise un miroir pour effrayer les esprits",
        ],
        "search_seeds": ["newborn baby tropical home", "tender baby hands", "family welcoming baby", "soft baby portrait"],
        "visual_hints": ["a tender scene of a newborn baby cradled in a warm tropical home, soft light, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Les offrandes des pêcheurs — apaiser les esprits de la mer",
        "key_facts": [
            "Une vieille croyance, antérieure à l'islam, veut que la mer soit peuplée de djinns",
            "Les pêcheurs disent qu'il faut jeter un bijou ou un morceau d'étoffe en offrande en mer",
            "Le geste est surtout pratiqué près de lieux réputés sacrés, comme l'îlot de Sable Blanc",
            "Il vise à s'assurer que le voyage se passera bien",
            "Cette croyance reflète le rapport ambivalent des Mahorais à l'océan",
        ],
        "search_seeds": ["fisherman boat sunrise", "hand offering to sea", "traditional canoe ocean", "fisherman silhouette dawn"],
        "visual_hints": ["a fisherman in a wooden canoe at dawn making an offering to the calm sea, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le rahuani — le djinn qui force à prier",
        "key_facts": [
            "Le rahuani est, selon la croyance, une catégorie de djinn qui prend possession de son hôte",
            "On dit qu'il oblige la personne à prier et ne la laisse pas en paix",
            "Étant lui-même musulman, il ne se manifeste ni le vendredi ni pendant le Ramadan",
            "On rapporte que la personne possédée peut parler arabe sans l'avoir appris",
            "Cette croyance reflète les anciennes influences perses et arabes de l'archipel",
        ],
        "search_seeds": ["praying figure silhouette", "spiritual possession mystical", "mosque prayer light", "mystical religious scene"],
        "visual_hints": ["a solitary praying figure in soft mystical light, spiritual atmosphere, photorealistic"],
        "avoid": [],
    },
]

# === FAITS INSOLITES ===
FACTS: list[KnowledgeEntry] = [
    {
        "title": "Mayotte, 101e département français",
        "key_facts": [
            "Mayotte est devenue le 101e département français le 31 mars 2011",
            "Elle est le département français le plus jeune",
            "L'île est française depuis 1841, quand le sultan Andriantsoly l'a cédée à la France",
            "En 1976, Mayotte a massivement voté pour rester française",
            "Plus de 95 % de la population est de confession musulmane",
            "Le français est la seule langue officielle, mais le shimaoré et le kibushi sont parlés au quotidien",
        ],
        "search_seeds": ["french overseas territory", "tropical island french flag", "department ceremony", "official building tropical"],
        "visual_hints": ["French flag waving on tropical island, official building, photorealistic"],
        "avoid": ["confondre avec les Comores indépendantes — Mayotte est française"],
    },
    {
        "title": "Mayotte, l'île la plus jeune de France",
        "key_facts": [
            "L'âge médian à Mayotte est d'environ 17 ans, le plus bas de France",
            "Plus de la moitié de la population a moins de 18 ans",
            "Le taux de natalité y est le plus élevé de France",
            "La maternité de Mamoudzou est la plus active de France et d'Europe",
            "On y compte environ 10 000 naissances par an",
        ],
        "search_seeds": ["children playing tropical school", "tropical island youth", "school kids africa", "newborn baby hospital"],
        "visual_hints": ["happy children playing in tropical schoolyard, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le multilinguisme mahorais quotidien",
        "key_facts": [
            "Trois langues coexistent au quotidien : français, shimaoré et kibushi",
            "Le shimaoré est une langue bantoue, parente du swahili",
            "Le kibushi est une langue austronésienne, parente du malgache",
            "Ces deux langues témoignent des migrations africaines et malgaches",
            "L'enseignement scolaire se fait en français, mais le foyer parle souvent les langues locales",
            "Cette richesse linguistique fait de Mayotte un cas unique en France",
        ],
        "search_seeds": ["classroom students africa", "multilingual school", "books library tropical", "students reading"],
        "visual_hints": ["children in classroom with books, multilingual learning, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Les saisons mahoraises : kashkasi et kusi",
        "key_facts": [
            "Mayotte connaît seulement deux saisons, contrairement aux quatre métropolitaines",
            "Kashkasi est la saison des pluies, chaude et humide, de novembre à avril",
            "Kusi est la saison sèche, plus fraîche, de mai à octobre",
            "La température moyenne oscille entre 24 et 30 degrés toute l'année",
            "Les cyclones peuvent frapper en kashkasi, comme Chido en décembre 2024",
        ],
        "search_seeds": ["tropical rain monsoon", "tropical sunny dry beach", "tropical storm clouds", "lush green tropical"],
        "visual_hints": ["tropical island during rainy season, lush green vegetation, dramatic clouds"],
        "avoid": [],
    },
    {
        "title": "Le banga — première maison du jeune mahorais",
        "key_facts": [
            "Le banga est une petite case que les jeunes garçons mahorais construisent dès l'adolescence",
            "C'est un rite de passage vers l'autonomie",
            "Elle est généralement faite de bambou, de tôles et peinte de couleurs vives",
            "Elle sert de chambre à part, marquant la transition vers la vie adulte",
            "Les bangas sont souvent ornés de slogans ou de fresques",
        ],
        "search_seeds": ["colorful tropical hut", "small wooden house tropics", "painted bamboo cabin", "tropical village house"],
        "visual_hints": ["colorful small wooden hut in tropical village, painted with vibrant patterns"],
        "avoid": [],
    },
    {
        "title": "La pêche traditionnelle au djarifa",
        "key_facts": [
            "Le djarifa est une pêche collective à pied pratiquée à marée basse",
            "Des dizaines de femmes forment une chaîne sur le platier corallien",
            "Elles tirent ensemble une grande senne à la main",
            "Cette pratique date d'avant la colonisation française",
            "Les prises sont partagées équitablement",
            "Le djarifa renforce le lien communautaire entre femmes du village",
        ],
        "search_seeds": ["traditional fishing women beach", "low tide reef walking", "communal fishing africa", "fishing net pulling"],
        "visual_hints": ["women in colorful dress pulling fishing net on tropical beach, low tide, photorealistic"],
        "avoid": [],
    },
    {
        "title": "1841 : Mayotte cédée à la France",
        "key_facts": [
            "Le 25 avril 1841, le sultan Andriantsoly cède Mayotte à la France",
            "Le traité de cession est signé avec le commandant français Pierre Passot",
            "Andriantsoly était un souverain d'origine malgache, le dernier à régner sur Mayotte",
            "Il cherchait des protecteurs face aux autres souverains de la région",
            "Le traité a été ratifié par la France en 1843",
        ],
        "search_seeds": ["old historical map island", "antique sailing ship sea", "vintage colonial document", "old map ocean"],
        "visual_hints": ["an antique map and an old sailing ship anchored off a tropical island, historical mood, photorealistic"],
        "avoid": [],
    },
    {
        "title": "1974-1976 : Mayotte refuse l'indépendance",
        "key_facts": [
            "En 1974, un référendum d'indépendance est organisé dans l'archipel des Comores",
            "Les Comores votent massivement pour l'indépendance, mais Mayotte vote pour rester française",
            "Les Comores déclarent leur indépendance le 6 juillet 1975",
            "En 1976, Mayotte confirme par référendum son rattachement à la France",
            "L'ONU continue de considérer que Mayotte fait partie de l'ensemble comorien",
        ],
        "search_seeds": ["ballot box vote", "tropical island flag pole", "historical voting", "french flag island wind"],
        "visual_hints": ["a French flag waving over a tropical island, solemn historical mood, photorealistic"],
        "avoid": ["rester factuel — ne pas prendre parti sur le statut de Mayotte"],
    },
    {
        "title": "Le cyclone Chido — décembre 2024",
        "key_facts": [
            "Le 14 décembre 2024, le cyclone Chido frappe Mayotte",
            "Classé en catégorie 4 sur 5, c'est le cyclone le plus intense depuis 90 ans sur l'île",
            "Le bilan officiel fait état de 39 morts et de plusieurs milliers de blessés",
            "Plus de 20 000 sinistres ont été déclarés dans les mois qui ont suivi",
            "C'est le cyclone le plus coûteux jamais enregistré dans le sud-ouest de l'océan Indien",
        ],
        "search_seeds": ["cyclone storm clouds", "tropical storm satellite", "storm damage palm trees", "dramatic storm sky"],
        "visual_hints": ["a powerful tropical cyclone seen from satellite over the Indian Ocean, dramatic, photorealistic"],
        "avoid": ["rester factuel et sobre — ne pas dramatiser ni spéculer sur le bilan"],
    },
    {
        "title": "Pourquoi Mayotte a soif — la crise de l'eau",
        "key_facts": [
            "Mayotte n'a pas de nappe phréatique abondante : l'eau dépend surtout des pluies",
            "L'île ne connaît que deux saisons, et une saison sèche trop longue assèche les réserves",
            "En 2023, une sécheresse exceptionnelle a provoqué une grave crise de l'eau",
            "Des coupures d'eau tournantes ont été mises en place sur toute l'île",
            "L'eau a même été acheminée par bateau depuis l'extérieur",
        ],
        "search_seeds": ["dry cracked earth", "water reservoir low", "rain tropical drought", "water tank village"],
        "visual_hints": ["a tropical landscape with a low water reservoir under a dry sky, photorealistic"],
        "avoid": ["rester factuel et pédagogique, sans misérabilisme"],
    },
    {
        "title": "Mayotte, l'un des territoires les plus denses",
        "key_facts": [
            "La population de Mayotte est estimée à environ 320 000 habitants (estimation 2025)",
            "L'île ne mesure que 374 km² : la densité y est très élevée",
            "Cela en fait l'un des départements les plus densément peuplés de France",
            "La population de l'île croît rapidement",
            "Les chiffres de population évoluent vite et sont régulièrement réévalués",
        ],
        "search_seeds": ["dense tropical town hillside", "colorful houses hill", "crowded island village", "aerial town tropical"],
        "visual_hints": ["colorful houses densely packed on a green tropical hillside, aerial view, photorealistic"],
        "avoid": [],
    },
    {
        "title": "La maternité de Mamoudzou, la plus grande de France",
        "key_facts": [
            "La maternité de Mamoudzou est considérée comme la plus grande de France, voire d'Europe",
            "Plusieurs milliers de bébés y naissent chaque année",
            "Elle représente une large part des naissances du département",
            "Elle est régulièrement sous forte tension du fait de cette activité",
            "Cette intensité reflète la jeunesse exceptionnelle de la population mahoraise",
        ],
        "search_seeds": ["newborn baby hospital", "maternity ward tropical", "baby tiny hands", "hospital nursery"],
        "visual_hints": ["a peaceful hospital nursery scene with a newborn baby, soft light, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le record de natalité de Mayotte",
        "key_facts": [
            "Mayotte détient le record de natalité de toute la France",
            "L'indice de fécondité y avoisine 4,5 enfants par femme (2023)",
            "C'est près de trois fois la moyenne de la France métropolitaine",
            "L'âge moyen des mères y est plus jeune qu'au niveau national",
            "Cette vitalité démographique façonne toute la société mahoraise",
        ],
        "search_seeds": ["children playing outdoor", "many kids tropical", "school children group", "happy children africa"],
        "visual_hints": ["a large joyful group of children playing outdoors in a tropical setting, photorealistic"],
        "avoid": [],
    },
    {
        "title": "D'où vient le nom « Mayotte » ?",
        "key_facts": [
            "Selon l'étymologie communément admise, le nom viendrait de l'arabe « Jazīrat al-Mawt »",
            "Cette expression signifierait « île de la mort », peut-être à cause des récifs dangereux",
            "Le nom aurait évolué en Maouti, puis Mayotta, puis Mayotte",
            "Le nom local de l'île en shimaoré est « Maore »",
            "Cette origine arabe reste discutée par les linguistes",
        ],
        "search_seeds": ["dangerous coral reef waves", "old nautical map", "rocky coast ocean", "reef breaking waves aerial"],
        "visual_hints": ["dangerous coral reefs with crashing waves around a tropical island, dramatic aerial view, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Mayotte, deux îles reliées par une barge",
        "key_facts": [
            "Mayotte est constituée de deux îles principales : Grande-Terre et Petite-Terre",
            "Grande-Terre couvre 363 km², Petite-Terre seulement 11 km²",
            "Mamoudzou et Dzaoudzi sont reliées par un service de barges",
            "La traversée dure environ 15 minutes",
            "Le service transporte plusieurs millions de passagers par an",
            "Beaucoup de Mahorais traversent chaque jour pour aller travailler",
        ],
        "search_seeds": ["ferry boat tropical strait", "passenger ferry sea", "ferry crossing islands", "boat dock commuters"],
        "visual_hints": ["a passenger ferry crossing a turquoise strait between two tropical islands, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Mayotte, à 9000 km de Paris et en avance sur l'heure",
        "key_facts": [
            "Mayotte est séparée de la France métropolitaine par environ 9000 km",
            "Un vol direct dure environ 8 heures",
            "L'île suit toute l'année le fuseau horaire UTC+3",
            "Elle ne pratique pas de changement d'heure saisonnier",
            "Quand il est midi à Paris en hiver, il est déjà 14 heures à Mayotte",
        ],
        "search_seeds": ["airplane tropical island", "world map distance", "clock time zone", "long flight ocean"],
        "visual_hints": ["an airplane flying over the ocean toward a tropical island at golden hour, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le trésor maritime de Mayotte",
        "key_facts": [
            "Grâce à Mayotte, la France dispose d'une zone maritime d'environ 74 000 km² dans le canal du Mozambique",
            "Cette zone est près de 200 fois plus grande que la surface terrestre de l'île",
            "Elle abrite une biodiversité marine exceptionnelle",
            "Le canal du Mozambique est une route maritime stratégique",
            "Cette immense zone fait de la petite Mayotte un acteur maritime majeur",
        ],
        "search_seeds": ["vast ocean horizon", "deep blue sea aerial", "ocean expanse drone", "open sea sunset"],
        "visual_hints": ["a vast expanse of deep blue ocean stretching to the horizon, aerial view, photorealistic"],
        "avoid": ["ne pas dire que c'est la 2e plus grande zone maritime de France — c'est inexact"],
    },
    {
        "title": "L'aéroport de Mayotte et sa piste trop courte",
        "key_facts": [
            "L'aéroport principal de Mayotte est situé à Pamandzi, sur Petite-Terre",
            "Sa piste mesure environ 1930 mètres",
            "Cette longueur ne permet pas aux gros avions de décoller à pleine charge",
            "Il n'y a donc pas de vol direct long-courrier à pleine capacité",
            "Le projet d'une piste plus longue, ou d'un nouvel aéroport, est débattu depuis des années",
        ],
        "search_seeds": ["small airport runway tropical", "airplane runway island", "airport aerial tropical", "plane landing island"],
        "visual_hints": ["a small airport runway on a narrow tropical island surrounded by sea, aerial view, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Mayotte, terre d'islam depuis le XVe siècle",
        "key_facts": [
            "Environ 95 % des Mahorais sont de confession musulmane, de rite sunnite",
            "L'islam est implanté à Mayotte depuis le XVe siècle",
            "La pratique de l'islam y est généralement décrite comme modérée",
            "L'islam s'y conjugue avec des rites traditionnels et la laïcité française",
            "Mayotte est souvent citée comme un exemple de pluralisme et de tolérance",
        ],
        "search_seeds": ["mosque tropical sunset", "minaret palm trees", "mosque call prayer", "white mosque island"],
        "visual_hints": ["a white mosque with a minaret among palm trees at sunset, peaceful, photorealistic"],
        "avoid": [],
    },
    {
        "title": "La mosquée de Tsingoni, la plus ancienne de France",
        "key_facts": [
            "La mosquée de Tsingoni est la plus ancienne mosquée de France encore en activité",
            "Une inscription dans le mihrab date une réalisation de 1538",
            "Des fouilles ont révélé une occupation du site dès le XIIe siècle",
            "Des textes anciens évoquent une mosquée à Tsingoni dès 1521",
            "Tsingoni fut un temps la capitale du sultanat de Mayotte",
        ],
        "search_seeds": ["ancient mosque architecture", "old white mosque", "historic mosque interior", "traditional mosque tropical"],
        "visual_hints": ["an ancient white mosque with traditional architecture, warm light, photorealistic"],
        "avoid": [],
    },
    {
        "title": "La justice cadiale, un héritage juridique unique",
        "key_facts": [
            "À Mayotte coexistent deux statuts civils : le droit commun et le droit local",
            "Le droit local est inspiré du droit musulman et de coutumes africaines et malgaches",
            "La justice rendue selon ce statut s'appelle la justice cadiale, rendue par des cadis",
            "L'institution du cadi remonte à plusieurs siècles dans l'archipel",
            "Une réforme de 2010 a retiré aux cadis leurs compétences de justice",
        ],
        "search_seeds": ["old courthouse tropical", "justice scales symbol", "traditional council elders", "historic document law"],
        "visual_hints": ["an elder figure of authority in a traditional setting, warm dignified light, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Mamoudzou, chef-lieu officialisé seulement en 2023",
        "key_facts": [
            "Mamoudzou est le chef-lieu de Mayotte ; avant, la capitale était Dzaoudzi",
            "Un décret de 1977 avait désigné Mamoudzou, mais sans arrêté d'application",
            "Pendant plus de 45 ans, la situation est restée juridiquement floue",
            "Le transfert n'a été officiellement confirmé qu'en août 2023",
            "Dzaoudzi reste le siège de la sous-préfecture",
        ],
        "search_seeds": ["coastal town hall tropical", "official building island", "town aerial tropical", "administrative building"],
        "visual_hints": ["an official administrative building in a tropical coastal town, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Mayotte devient une collectivité unique en 2026",
        "key_facts": [
            "Depuis le 1er janvier 2026, Mayotte est devenue une collectivité unique",
            "Elle s'appelle désormais le « Département-Région de Mayotte »",
            "Elle exerce à la fois les compétences d'un département et d'une région",
            "C'est le cas comme en Guyane et en Martinique",
            "L'ancien conseil départemental est devenu l'Assemblée de Mayotte",
        ],
        "search_seeds": ["official ceremony building", "tropical government building", "island administration", "flag official building"],
        "visual_hints": ["an official building with flags in a tropical setting, civic atmosphere, photorealistic"],
        "avoid": [],
    },
]


ALL_TOPICS_BY_THEME: dict[str, list[KnowledgeEntry]] = {
    "decouverte_mayotte": PLACES + NATURE,
    "tradition_mahoraise": TRADITIONS,
    "legende_mahoraise": LEGENDS,
    "fait_insolite": FACTS,
}


# Anti-répétition : on mémorise les sujets déjà utilisés (par titre, par
# thème) dans output/used_topics.json. Tant que tout le pool d'un thème n'a
# pas été utilisé, on ne ressort jamais le même sujet. Quand le pool est
# épuisé, il est réinitialisé → nouveau cycle, ordre rebrassé.
_USED_FILE = Path(__file__).resolve().parent.parent / "output" / "used_topics.json"


def _read_used() -> dict[str, list[str]]:
    """Renvoie {theme: [titres déjà utilisés]}. Tolérant aux erreurs."""
    try:
        data = json.loads(_USED_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_used(used: dict[str, list[str]]) -> None:
    try:
        _USED_FILE.parent.mkdir(parents=True, exist_ok=True)
        _USED_FILE.write_text(
            json.dumps(used, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass


def pick_topic_for(theme: str) -> KnowledgeEntry:
    """Choisit un sujet pour le thème, en évitant les sujets déjà utilisés.

    Anti-répétition : tant que tous les sujets du thème n'ont pas servi au
    moins une fois, on ne ressort jamais le même. Pool épuisé → réinitialisé.
    """
    pool = ALL_TOPICS_BY_THEME.get(theme, [])
    if not pool:
        raise ValueError(f"Thème inconnu : {theme}")

    used = _read_used()
    used_titles = set(used.get(theme, []))

    available = [e for e in pool if e["title"] not in used_titles]
    if not available:
        # Tous les sujets du thème ont été vus → on relance un cycle complet.
        # On exclut le tout dernier sujet utilisé pour ne pas le ressortir
        # immédiatement à la jonction des deux cycles.
        print(f"   ♻️  Tous les sujets « {theme} » ont été utilisés — nouveau cycle.")
        last_used = used.get(theme, [])[-1:]
        used[theme] = []
        available = [e for e in pool if e["title"] not in last_used] or list(pool)

    entry = random.choice(available)
    used.setdefault(theme, [])
    used[theme].append(entry["title"])
    _write_used(used)

    remaining = len(pool) - len(used[theme])
    print(f"   📚 Sujet pioché ({remaining}/{len(pool)} restants ce cycle)")
    return entry


def random_topic_for(theme: str) -> KnowledgeEntry:
    """Conservé pour compat — applique désormais l'anti-répétition."""
    return pick_topic_for(theme)


GLOBAL_CONTEXT_PROMPT = """Tu écris pour une chaîne TikTok francophone consacrée à Mayotte, le 101e département français.

CONNAISSANCES CLÉS À TOUJOURS RESPECTER :
- Le gentilé est « les Mahorais » (jamais « les Mayottes »)
- Mayotte est française depuis 1841, département depuis 2011
- L'archipel comprend Grande-Terre (Mahoré) et Petite-Terre (Pamandzi)
- 95% de la population est musulmane, le français est langue officielle
- Les langues locales sont le shimaoré (bantou) et le kibushi (austronésien)
- Le lagon mahorais est l'un des rares doubles lagons fermés au monde
- Le mont Choungui (594m) est l'emblème géographique, le mont Bénara (660m) le point culminant
- L'ylang-ylang est la fleur emblématique
- Les dugongs et baleines à bosse fréquentent le lagon

À ÉVITER ABSOLUMENT :
- Ne jamais mentionner le « kwassa-kwassa » comme un mode de transport touristique : c'est une embarcation tragiquement liée à l'immigration clandestine
- Ne pas confondre Mayotte avec les Comores indépendantes
- Ne pas inventer de noms de lieux, de personnages ou de légendes
- Pas de politique partisane, pas de polémique
- Pas de noms propres trop spécifiques que l'on ne pourrait vérifier

TON :
- Reportage chaleureux, accessible, type Brut ou France TV Slash
- Humain, concret, valorisant le territoire et ses habitants
- Phrases orales fluides, claires, sans jargon"""
