"""Base de connaissances MONDE (au-delà de Mayotte) — sujets à fort potentiel viral.

Thèmes fascinants, vérifiés, pensés pour « percer » sur TikTok : espace,
animaux extraordinaires, lieux extrêmes, corps humain. Chaque titre est un
hook. Chaque fait est sourcé et exact (les pièges viraux faux ont été écartés).

Même structure que mayotte_knowledge (KnowledgeEntry) + anti-répétition
séparée (output/world_used_topics.json). Voir GLOBAL_CONTEXT_PROMPT_WORLD
pour le cadrage LLM générique (PAS de contexte Mayotte imposé).
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


# === ESPACE & UNIVERS ===
ESPACE: list[KnowledgeEntry] = [
    {
        "title": "La planète où il pleut du verre en travers à 7000 km/h",
        "key_facts": [
            "HD 189733b est une géante gazeuse à 63 années-lumière de la Terre",
            "Sa température dépasse 1000 °C : les silicates s'y condensent en verre fondu",
            "Des vents de 7000 km/h projettent ce verre presque à l'horizontale",
            "Vue de l'espace, la planète est d'un bleu azur profond comme la Terre",
            "Cette couleur bleue vient probablement de cette pluie de verre",
        ],
        "search_seeds": ["blue exoplanet space", "glass rain planet", "alien world storm"],
        "visual_hints": ["a deep blue gas giant exoplanet with violent glass rain storms, sideways rain, dramatic space art, photorealistic cinematic"],
        "avoid": [],
    },
    {
        "title": "Une cuillère de cette étoile pèse un milliard de tonnes",
        "key_facts": [
            "Une étoile à neutrons est le cœur effondré d'une étoile massive",
            "Elle concentre plus de masse que le Soleil dans une sphère de 20 km de diamètre",
            "Une cuillère à café de sa matière pèserait environ un milliard de tonnes sur Terre",
            "La matière y est si comprimée que les atomes sont écrasés en neutrons",
            "Les plus rapides, les pulsars, tournent plus de 700 fois par seconde",
        ],
        "search_seeds": ["neutron star space", "pulsar rotating", "dense star cosmos"],
        "visual_hints": ["a glowing neutron star, tiny ultra-dense sphere with intense magnetic field lines, deep space, photorealistic cosmic art"],
        "avoid": ["citer un chiffre unique : dire « environ un milliard de tonnes »"],
    },
    {
        "title": "Sur cette planète, il pleut du fer en fusion",
        "key_facts": [
            "WASP-76b se trouve à environ 640 années-lumière, dans la constellation des Poissons",
            "Sur sa face jour, la température atteint 2400 °C, assez pour vaporiser le fer",
            "Des vents transportent cette vapeur vers la face nuit, plus fraîche",
            "Là, à 1500 °C, la vapeur de fer se condense et retombe en pluie de fer liquide",
            "La planète montre toujours la même face à son étoile, comme la Lune vers la Terre",
        ],
        "search_seeds": ["molten iron rain planet", "hot exoplanet lava", "alien planet fire sky"],
        "visual_hints": ["a scorching exoplanet with molten iron rain, glowing orange atmosphere, day-night boundary, photorealistic space art"],
        "avoid": [],
    },
    {
        "title": "Cette étoile engloutirait tout le système solaire jusqu'à Saturne",
        "key_facts": [
            "Stephenson 2-18 est une supergéante rouge, la plus grande étoile connue",
            "Son rayon vaut environ 2150 fois celui du Soleil",
            "À la place du Soleil, sa surface s'étendrait au-delà de l'orbite de Saturne",
            "Son volume représente environ 10 milliards de fois celui du Soleil",
            "Elle est si lointaine que sa taille exacte reste incertaine",
        ],
        "search_seeds": ["red supergiant star giant", "huge star comparison", "cosmic scale star"],
        "visual_hints": ["a colossal red supergiant star dwarfing the sun and planets, sense of immense scale, deep space, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Il pleut des diamants à l'intérieur de Neptune et Uranus",
        "key_facts": [
            "Dans le manteau de ces géantes de glace, le méthane est écrasé sous une pression immense",
            "La pression dépasse un million de fois celle de l'atmosphère terrestre",
            "Le carbone libéré cristallise alors en diamants solides",
            "Ces diamants pleuvent lentement vers le cœur de la planète",
            "Le phénomène a été recréé en laboratoire en comprimant du plastique avec des lasers",
        ],
        "search_seeds": ["diamond rain planet", "neptune interior blue", "ice giant planet"],
        "visual_hints": ["the deep blue interior of an ice giant planet with diamonds forming and falling, cross-section cosmic art, photorealistic"],
        "avoid": ["formuler « les scientifiques pensent que » — phénomène modélisé, pas observé"],
    },
    {
        "title": "L'objet humain le plus lointain met un jour à nous répondre",
        "key_facts": [
            "Voyager 1, lancée en 1977, est l'objet fabriqué par l'homme le plus éloigné",
            "Elle est dans l'espace interstellaire depuis 2012",
            "Sa distance représente environ 26 milliards de kilomètres",
            "Un signal radio, à la vitesse de la lumière, met environ 24 heures à l'atteindre",
            "Quand les ingénieurs envoient une commande, la réponse ne revient que deux jours plus tard",
        ],
        "search_seeds": ["voyager probe deep space", "spacecraft stars distance", "interstellar probe"],
        "visual_hints": ["the Voyager space probe drifting alone in deep interstellar space, tiny against vast starfield, photorealistic cinematic"],
        "avoid": [],
    },
    {
        "title": "Sur cette planète, un jour dure plus longtemps qu'une année",
        "key_facts": [
            "Vénus met 243 jours terrestres pour tourner une fois sur elle-même",
            "Mais elle fait le tour du Soleil en seulement 225 jours : son jour dure plus que son année",
            "Elle tourne à l'envers : depuis sa surface, le Soleil se lèverait à l'ouest",
            "C'est la planète la plus chaude : 465 °C en surface, de quoi faire fondre le plomb",
            "Sa pression atmosphérique est 92 fois celle de la Terre",
        ],
        "search_seeds": ["venus planet surface", "hot cloudy planet", "venus atmosphere"],
        "visual_hints": ["the surface of Venus, thick toxic yellow clouds, scorching volcanic landscape, oppressive atmosphere, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Cette petite lune crache de l'eau dans l'espace",
        "key_facts": [
            "Encelade, lune de Saturne, ne fait que 500 km de diamètre",
            "Elle projette des geysers d'eau depuis son pôle sud",
            "Ces jets éjectent environ 200 kg d'eau par seconde dans l'espace",
            "Sous sa croûte de glace se cache un océan d'eau salée global",
            "On y trouve des indices de sources hydrothermales, un milieu potentiellement propice à la vie",
        ],
        "search_seeds": ["enceladus moon geysers", "ice moon water jets", "saturn moon space"],
        "visual_hints": ["Enceladus icy moon shooting giant water geysers into space above Saturn, blue icy surface, photorealistic space art"],
        "avoid": [],
    },
    {
        "title": "La NASA a enregistré le son d'un trou noir",
        "key_facts": [
            "Le trou noir au centre de l'amas de Persée émet des ondes de pression dans le gaz qui l'entoure",
            "Cet amas est à environ 240 millions d'années-lumière",
            "Ces ondes correspondent à une note, un si bémol, 57 octaves sous le do central",
            "Une seule oscillation de cette note dure environ 10 millions d'années",
            "En 2022, la NASA a remonté ce son pour le rendre audible : il est devenu viral",
        ],
        "search_seeds": ["black hole space sound", "galaxy cluster gas", "cosmic sound waves"],
        "visual_hints": ["a supermassive black hole surrounded by glowing hot gas with ripples of pressure waves, deep space, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Cette planète est plus chaude que certaines étoiles",
        "key_facts": [
            "KELT-9b, à 670 années-lumière, est l'exoplanète la plus chaude connue",
            "Sa face jour atteint environ 4300 °C",
            "C'est plus chaud que la surface de certaines étoiles",
            "Il y fait si chaud que les molécules d'hydrogène sont déchirées en atomes le jour",
            "Son étoile hôte est brûlante, environ 10 000 °C",
        ],
        "search_seeds": ["ultra hot exoplanet", "glowing planet star", "extreme heat planet space"],
        "visual_hints": ["an ultra-hot exoplanet glowing like an ember next to its blazing blue-white star, photorealistic space art"],
        "avoid": [],
    },
    {
        "title": "Rejoindre l'étoile la plus proche prendrait 73 000 ans",
        "key_facts": [
            "Proxima du Centaure est l'étoile la plus proche du Soleil, à 4,25 années-lumière",
            "Avec la sonde la plus rapide jamais lancée, il faudrait environ 73 000 ans pour y arriver",
            "Même à la vitesse de la lumière, le trajet durerait 4,25 ans",
            "Cela illustre à quel point les distances entre étoiles sont vertigineuses",
            "Et Proxima est pourtant notre voisine la plus proche",
        ],
        "search_seeds": ["nearest star space travel", "red dwarf star", "interstellar distance stars"],
        "visual_hints": ["a small red dwarf star Proxima Centauri glowing in deep space, vast empty distance, starfield, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le plus grand volcan du système solaire est sur Mars",
        "key_facts": [
            "Olympus Mons, sur Mars, culmine à environ 22 km de hauteur",
            "C'est près de 2,5 fois la hauteur de l'Everest",
            "Sa base fait environ 600 km de large, la superficie de l'Italie",
            "C'est un volcan bouclier à pente très douce, comme ceux d'Hawaï",
            "Debout dessus, on ne verrait pas ses bords, cachés par la courbure de Mars",
        ],
        "search_seeds": ["olympus mons mars volcano", "mars landscape red", "giant volcano space"],
        "visual_hints": ["Olympus Mons, the giant Martian shield volcano seen from orbit, red planet surface, immense scale, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Voici ce qui arrive vraiment à ton corps dans le vide spatial",
        "key_facts": [
            "Contrairement au mythe, le corps n'explose pas dans le vide",
            "On perd connaissance en 10 à 15 secondes seulement",
            "Le manque de pression fait bouillir les fluides du corps, comme la salive sur la langue",
            "La mort survient en une à deux minutes environ",
            "En 1966, un ingénieur NASA a subi une dépressurisation, a senti sa salive bouillir, et a survécu",
        ],
        "search_seeds": ["astronaut space vacuum", "spacesuit space", "astronaut floating danger"],
        "visual_hints": ["an astronaut floating in the vacuum of space near a spacecraft, dramatic lighting, sense of peril, photorealistic cinematic"],
        "avoid": ["ne pas dire que le corps explose — c'est un mythe"],
    },
    {
        "title": "Ce trou noir est plus lourd que toutes les étoiles de notre galaxie",
        "key_facts": [
            "TON 618 est un trou noir supermassif à environ 10 milliards d'années-lumière",
            "Sa masse vaut entre 40 et 66 milliards de fois celle du Soleil",
            "C'est plus que toutes les étoiles de la Voie lactée réunies",
            "Son horizon des événements mesure environ 390 milliards de km de diamètre",
            "Il est des milliers de fois plus massif que le trou noir au centre de notre galaxie",
        ],
        "search_seeds": ["supermassive black hole", "quasar space", "black hole accretion disk"],
        "visual_hints": ["an immense supermassive black hole with a glowing orange accretion disk and quasar jets, cosmic scale, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Cette tempête fait rage depuis plus de 190 ans",
        "key_facts": [
            "La Grande Tache Rouge de Jupiter est une tempête plus large que la Terre entière",
            "Ses vents soufflent jusqu'à 430 à 680 km/h",
            "Elle est observée en continu depuis les années 1830",
            "Elle existe peut-être depuis le 17e siècle, soit plus de 350 ans",
            "Elle persiste car Jupiter n'a pas de surface solide pour freiner ses tourbillons",
        ],
        "search_seeds": ["jupiter great red spot", "jupiter storm gas giant", "planet storm swirl"],
        "visual_hints": ["Jupiter's Great Red Spot, a massive swirling storm larger than Earth, detailed cloud bands, photorealistic space art"],
        "avoid": [],
    },
]

# === ANIMAUX EXTRAORDINAIRES ===
ANIMAUX: list[KnowledgeEntry] = [
    {
        "title": "Cet animal a survécu 10 jours dans le vide de l'espace",
        "key_facts": [
            "Le tardigrade, ou ourson d'eau, mesure environ un demi-millimètre",
            "En 2007, une mission spatiale européenne l'a exposé 10 jours au vide et aux radiations",
            "Beaucoup ont survécu, ont été réhydratés sur Terre, et se sont reproduits",
            "Il tolère de -272 °C, près du zéro absolu, jusqu'à environ 150 °C",
            "Son secret : il se dessèche et réduit son métabolisme à moins de 0,01 % de la normale",
        ],
        "search_seeds": ["tardigrade microscope", "water bear creature", "microscopic animal"],
        "visual_hints": ["a tardigrade water bear extreme close-up, translucent chubby micro-animal, scientific macro, photorealistic detailed"],
        "avoid": ["ne pas dire « immortel » : il n'est indestructible que déshydraté"],
    },
    {
        "title": "La seule créature qui peut rajeunir à l'infini",
        "key_facts": [
            "La méduse Turritopsis dohrnii mesure à peine 4,5 mm",
            "Face au stress, à une blessure ou à la vieillesse, elle inverse tout son cycle de vie",
            "Elle redevient un polype, son stade juvénile, puis recommence une vie",
            "Ce processus s'appelle la transdifférenciation : ses cellules se reprogramment",
            "En théorie elle peut répéter ce cycle indéfiniment : on la dit biologiquement immortelle",
        ],
        "search_seeds": ["immortal jellyfish tiny", "transparent jellyfish ocean", "small jellyfish glowing"],
        "visual_hints": ["a tiny translucent immortal jellyfish glowing in dark ocean water, delicate ethereal, macro, photorealistic"],
        "avoid": ["préciser qu'elle peut quand même mourir mangée ou malade"],
    },
    {
        "title": "Elle frappe aussi vite qu'une balle de calibre 22",
        "key_facts": [
            "La crevette-mante, ou squille, projette sa massue à environ 23 mètres par seconde dans l'eau",
            "Son coup accélère comme une balle de calibre 22, en moins d'une milliseconde",
            "Le coup crée une bulle qui, en implosant, frappe la proie une deuxième fois",
            "Elle peut briser la coquille d'un crabe ou une vitre d'aquarium",
            "Ses yeux comptent 12 à 16 types de photorécepteurs, contre trois chez l'humain",
        ],
        "search_seeds": ["mantis shrimp colorful", "peacock mantis shrimp reef", "colorful crustacean"],
        "visual_hints": ["a vivid peacock mantis shrimp on a coral reef, brilliant rainbow colors, powerful raptorial claws, macro, photorealistic"],
        "avoid": ["c'est l'accélération qui égale une balle, pas la vitesse — ne pas dire « plus vite qu'une balle »"],
    },
    {
        "title": "Cet animal a trois cœurs, du sang bleu et neuf cerveaux",
        "key_facts": [
            "La pieuvre possède trois cœurs : deux pour les branchies, un pour le corps",
            "Son sang est bleu car il transporte l'oxygène avec du cuivre, pas du fer",
            "Elle a environ 500 millions de neurones, dont les deux tiers dans ses bras",
            "On la dit dotée de neuf cerveaux : un central, plus un amas de neurones par bras",
            "Chaque bras peut goûter, toucher et réagir de façon presque autonome",
        ],
        "search_seeds": ["octopus underwater", "octopus tentacles ocean", "octopus intelligent eyes"],
        "visual_hints": ["an intelligent octopus underwater, expressive eyes, curling tentacles, rich colors, dramatic light, photorealistic"],
        "avoid": ["« neuf cerveaux » est une image : préciser « on la surnomme »"],
    },
    {
        "title": "Ce requin nageait déjà à l'époque de Louis XIV",
        "key_facts": [
            "Le requin du Groenland est le vertébré vivant le plus âgé connu",
            "Sa durée de vie atteint au moins 272 ans, le plus vieux estimé à environ 392 ans",
            "Il n'atteint la maturité sexuelle qu'à environ 150 ans",
            "Il ne grandit que d'environ un centimètre par an",
            "Son âge a été daté grâce au carbone 14 présent dans le cristallin de son œil",
        ],
        "search_seeds": ["greenland shark deep", "old shark cold water", "deep sea shark"],
        "visual_hints": ["a Greenland shark gliding slowly through dark cold deep water, ancient and mysterious, photorealistic underwater"],
        "avoid": ["grande incertitude : dire « au moins 272 ans, peut-être près de 400 »"],
    },
    {
        "title": "Ce rongeur ignore le cancer et respire comme une plante",
        "key_facts": [
            "Le rat-taupe nu peut vivre plus de 30 ans, un record pour un rongeur",
            "Il est extrêmement résistant au cancer",
            "Il survit 18 minutes sans oxygène en basculant sur un métabolisme au fructose, comme une plante",
            "Il est quasi insensible à la douleur liée à l'acidité",
            "Son risque de mourir n'augmente presque pas avec l'âge, contrairement à nous",
        ],
        "search_seeds": ["naked mole rat", "underground rodent", "strange animal burrow"],
        "visual_hints": ["a naked mole-rat in an underground tunnel, wrinkled pink skin, buck teeth, curious scientific portrait, photorealistic"],
        "avoid": ["« ne vieillit pas » est débattu : rester sur « son risque de mourir n'augmente pas avec l'âge »"],
    },
    {
        "title": "Cet animal repousse son cerveau et son cœur",
        "key_facts": [
            "L'axolotl est une salamandre du Mexique qui régénère presque tout son corps",
            "Il repousse pattes, moelle épinière, cœur, portions de cerveau et même ses yeux",
            "Il le fait sans jamais former de cicatrice",
            "Il reste toute sa vie sous forme larvaire, avec ses branchies en panache",
            "Il est en danger critique d'extinction dans la nature",
        ],
        "search_seeds": ["axolotl pink smiling", "axolotl aquarium", "cute amphibian water"],
        "visual_hints": ["a pink smiling axolotl underwater with feathery external gills, adorable and alien, soft light, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Cet oiseau vole d'un pôle à l'autre chaque année",
        "key_facts": [
            "La sterne arctique détient la plus longue migration connue du règne animal",
            "Chaque année, elle fait l'aller-retour entre l'Arctique et l'Antarctique",
            "Elle parcourt entre 70 000 et 90 000 km par an",
            "Elle profite ainsi des deux étés, à chaque bout de la planète",
            "En voyant deux étés par an, elle voit plus de lumière du jour qu'aucun autre animal",
        ],
        "search_seeds": ["arctic tern flying", "seabird migration ocean", "tern bird flight"],
        "visual_hints": ["an arctic tern in flight over the ocean, elegant white seabird, long journey, dramatic sky, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Ce poisson produit 860 volts d'électricité",
        "key_facts": [
            "L'anguille électrique de Volta produit jusqu'à 860 volts",
            "C'est la plus forte décharge électrique de tout le règne animal",
            "Elle génère cette décharge avec des milliers de cellules empilées comme des piles",
            "Elle vit dans les eaux d'Amazonie et s'en sert pour étourdir ses proies",
            "Ce n'est même pas une vraie anguille, mais un poisson-couteau",
        ],
        "search_seeds": ["electric eel water", "amazon river fish", "eel dark water"],
        "visual_hints": ["an electric eel in murky Amazon water with faint electric glow around its body, dramatic underwater, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Cet oiseau imite la tronçonneuse à la perfection",
        "key_facts": [
            "L'oiseau-lyre d'Australie est sans doute le meilleur imitateur du règne animal",
            "Il imite les cris de plus de 20 espèces d'oiseaux, si bien que les vrais s'y trompent",
            "Il reproduit aussi des bruits mécaniques : tronçonneuse, appareil photo, alarme de voiture",
            "Il possède l'organe vocal le plus complexe de tous les oiseaux",
            "Les imitations mécaniques viennent surtout d'oiseaux vivant près des humains",
        ],
        "search_seeds": ["lyrebird tail display", "australian bird forest", "lyrebird feathers"],
        "visual_hints": ["a superb lyrebird displaying its spectacular lyre-shaped tail feathers in a misty forest, photorealistic detailed"],
        "avoid": [],
    },
    {
        "title": "Cette crevette crée un point plus chaud que le Soleil",
        "key_facts": [
            "La crevette-pistolet referme sa pince à plus de 100 km/h",
            "Ce claquement crée une bulle de cavitation qui implose aussitôt",
            "En implosant, la bulle atteint environ 4700 °C, presque la température de surface du Soleil",
            "Le claquement produit un des sons les plus puissants de l'océan, assez fort pour assommer une proie",
            "Ce point brûlant est microscopique et ne dure que quelques nanosecondes",
        ],
        "search_seeds": ["pistol shrimp claw", "snapping shrimp reef", "small shrimp macro"],
        "visual_hints": ["a pistol shrimp with its oversized snapping claw on a reef, tiny cavitation bubble flash, macro, photorealistic"],
        "avoid": ["préciser que la chaleur est microscopique et fugace"],
    },
    {
        "title": "Cette grenouille gèle en bloc tout l'hiver, cœur arrêté",
        "key_facts": [
            "La grenouille des bois survit à l'hiver en gelant presque entièrement",
            "Jusqu'à 65 % de l'eau de son corps se transforme en glace",
            "Elle arrête de respirer et son cœur cesse de battre, parfois plusieurs mois",
            "Son foie inonde son corps de sucre qui agit comme un antigel naturel",
            "Au dégel printanier, le cœur redémarre et elle repart comme si de rien n'était",
        ],
        "search_seeds": ["wood frog winter", "frog on ice", "frog forest floor"],
        "visual_hints": ["a wood frog frozen among ice crystals on a forest floor, delicate frost, scientific nature shot, photorealistic"],
        "avoid": [],
    },
    {
        "title": "L'animal le plus rapide du monde n'est ni un guépard ni une voiture",
        "key_facts": [
            "Le faucon pèlerin est l'animal le plus rapide de la planète",
            "En piqué, il dépasse 320 km/h",
            "C'est plus rapide que n'importe quelle voiture de course de série",
            "Il fond sur ses proies en repliant ses ailes comme un projectile",
            "Ses narines ont des cloisons qui l'empêchent d'avoir le souffle coupé à cette vitesse",
        ],
        "search_seeds": ["peregrine falcon dive", "falcon flying fast", "bird of prey sky"],
        "visual_hints": ["a peregrine falcon in a high-speed dive, wings tucked, plunging through the sky, dynamic motion, photorealistic"],
        "avoid": ["chiffre solide « plus de 320 km/h » ; 389 km/h était une expérience spéciale"],
    },
    {
        "title": "Ce mammifère pond des œufs et brille dans le noir",
        "key_facts": [
            "L'ornithorynque est un mammifère qui pond des œufs",
            "Son bec détecte les champs électriques des muscles de ses proies",
            "Le mâle est venimeux : ses éperons injectent un venin très douloureux",
            "Il n'a pas d'estomac : son œsophage débouche directement dans l'intestin",
            "Sous lumière ultraviolette, sa fourrure émet une lueur bleu-vert encore inexpliquée",
        ],
        "search_seeds": ["platypus water", "platypus swimming river", "strange mammal australia"],
        "visual_hints": ["a platypus swimming in a river, duck bill and webbed feet, quirky and unique, soft light, photorealistic"],
        "avoid": ["« brille » = fluorescence sous UV, il ne produit pas sa propre lumière"],
    },
    {
        "title": "Le son le plus puissant de la planète sort de cet animal",
        "key_facts": [
            "Le cachalot produit les sons les plus forts du règne animal, environ 230 décibels sous l'eau",
            "Il a le plus gros cerveau de tous les animaux, plus de cinq fois celui d'un humain",
            "Il plonge à plus de 2000 mètres de profondeur pour chasser le calmar géant",
            "Il dort à la verticale, tête vers le haut, près de la surface",
            "Ses clics lui servent de sonar pour repérer ses proies dans le noir total",
        ],
        "search_seeds": ["sperm whale deep", "giant whale ocean", "whale diving dark water"],
        "visual_hints": ["a massive sperm whale diving into the dark deep ocean, immense scale, shafts of light, photorealistic underwater"],
        "avoid": ["230 dB sous l'eau ≠ dans l'air : ne pas dire que ça tuerait depuis la plage"],
    },
    {
        "title": "Ce corbeau planifie mieux son avenir qu'un enfant de 4 ans",
        "key_facts": [
            "Les corbeaux anticipent l'avenir jusqu'à 17 heures à l'avance",
            "Dans des tests, ils surpassent les enfants de 4 ans et rivalisent avec les grands singes",
            "Les corneilles calédoniennes fabriquent des crochets pour attraper leur nourriture",
            "En 2002, une corneille a spontanément plié un fil de fer en crochet",
            "Ce sont les seuls animaux connus, à part l'humain, à fabriquer des hameçons dans la nature",
        ],
        "search_seeds": ["crow raven intelligent", "black bird tool", "raven close-up"],
        "visual_hints": ["a clever raven holding a small tool with its beak, intelligent gaze, dark glossy feathers, photorealistic detailed"],
        "avoid": [],
    },
    {
        "title": "Le carabe qui se défend avec une explosion à 100 degrés",
        "key_facts": [
            "Le carabe bombardier projette un jet chimique brûlant pour se défendre",
            "Il stocke séparément deux produits qu'il mélange dans une chambre de réaction",
            "La réaction est explosive et éjecte un spray à 100 °C, la température de l'eau bouillante",
            "Le jet part avec un « pop » audible et peut être tiré en salves répétées",
            "Il peut orienter ce jet vers son agresseur avec précision",
        ],
        "search_seeds": ["bombardier beetle macro", "beetle close-up", "insect defense"],
        "visual_hints": ["a bombardier beetle on a leaf releasing a tiny puff of hot chemical spray, dramatic macro, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Son cœur bat 1200 fois par minute",
        "key_facts": [
            "Le colibri a le métabolisme le plus rapide du règne animal",
            "En vol, son cœur peut battre entre 1200 et 1260 fois par minute",
            "Ses ailes battent jusqu'à 80 fois par seconde",
            "C'est le seul oiseau capable de voler en marche arrière",
            "La nuit, il entre en torpeur : son cœur ralentit et sa température chute pour économiser l'énergie",
        ],
        "search_seeds": ["hummingbird flower", "hummingbird flying nectar", "tiny bird wings"],
        "visual_hints": ["a hummingbird hovering at a bright flower, wings blurred with speed, iridescent feathers, macro, photorealistic"],
        "avoid": [],
    },
]

# === LIEUX EXTRÊMES ===
LIEUX: list[KnowledgeEntry] = [
    {
        "title": "Cet endroit n'a pas vu la pluie depuis 500 ans",
        "key_facts": [
            "Le cœur du désert d'Atacama, au Chili, est l'endroit le plus sec de la planète",
            "Dans certaines zones, aucune pluie n'avait été enregistrée depuis au moins 500 ans",
            "La ville d'Arica détient le record : 172 mois d'affilée sans une goutte de pluie",
            "Certaines stations n'ont jamais enregistré la moindre pluie",
            "Quand une averse surprise est tombée en 2015, elle a tué les micro-organismes du sol, noyés",
        ],
        "search_seeds": ["atacama desert dry", "driest desert landscape", "cracked desert ground"],
        "visual_hints": ["the hyper-arid Atacama desert, cracked lifeless red-brown ground stretching to distant mountains, harsh light, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Ce lac transforme les animaux en statues de pierre",
        "key_facts": [
            "Le lac Natron, en Tanzanie, est un lac de soude ultra-alcalin, presque aussi caustique que l'ammoniaque",
            "Il peut atteindre 60 °C par forte chaleur",
            "Sa chimie calcifie les carcasses des animaux qui y meurent, comme figées dans la pierre",
            "Sa couleur rouge sang vient de micro-organismes qui prolifèrent quand la salinité grimpe",
            "Paradoxe : c'est le premier site de reproduction au monde du flamant nain",
        ],
        "search_seeds": ["lake natron red", "alkaline lake tanzania", "blood red lake aerial"],
        "visual_hints": ["Lake Natron, blood-red alkaline water with swirling white salt patterns, aerial view, otherworldly, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Ici, il a fait 56,7 degrés : le record de chaleur de la planète",
        "key_facts": [
            "La Vallée de la Mort, en Californie, détient le record officiel de chaleur de l'air sur Terre",
            "56,7 °C ont été relevés le 10 juillet 1913 à Furnace Creek",
            "Ce record est reconnu par l'Organisation météorologique mondiale",
            "La température fiable la plus élevée depuis est de 54,4 °C, en 2020 et 2021",
            "Le sol peut y dépasser 90 °C en plein été",
        ],
        "search_seeds": ["death valley desert", "hot desert dunes", "sun scorched valley"],
        "visual_hints": ["Death Valley under blazing sun, cracked salt flats and golden dunes, shimmering heat haze, photorealistic"],
        "avoid": [],
    },
    {
        "title": "L'endroit le plus profond de la planète : 11 km sous la mer",
        "key_facts": [
            "Le point le plus profond de l'océan est le Challenger Deep, dans la fosse des Mariannes",
            "Sa profondeur atteint environ 10 935 mètres",
            "Si on y plongeait l'Everest, son sommet resterait encore à plus de 2000 m sous la surface",
            "La pression au fond dépasse 1000 fois la pression atmosphérique",
            "Plus d'humains ont marché sur la Lune que descendus tout au fond",
        ],
        "search_seeds": ["deep ocean trench", "deep sea darkness", "abyss underwater"],
        "visual_hints": ["the crushing darkness of the deepest ocean trench, faint light fading into black abyss, eerie, photorealistic"],
        "avoid": [],
    },
    {
        "title": "À cet endroit de l'océan, les humains les plus proches sont dans l'espace",
        "key_facts": [
            "Le Point Nemo, dans le Pacifique Sud, est le lieu de l'océan le plus éloigné de toute terre",
            "Les terres les plus proches sont à environ 2688 km",
            "Souvent, les humains les plus proches sont les astronautes de la Station spatiale, à 400 km d'altitude",
            "C'est le cimetière des vaisseaux spatiaux : près de 300 engins y ont été précipités",
            "La station Mir y repose, et la Station spatiale internationale doit y finir vers 2031",
        ],
        "search_seeds": ["remote ocean horizon", "empty sea vast", "open ocean isolation"],
        "visual_hints": ["an endless empty ocean stretching to the horizon under a vast sky, total isolation, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Ce cratère brûle sans interruption depuis plus de 50 ans",
        "key_facts": [
            "La Porte de l'Enfer, au Turkménistan, est un cratère de gaz en feu depuis 1971",
            "Il mesure environ 60 à 70 mètres de diamètre et 30 mètres de profondeur",
            "Un forage soviétique a percé une poche de gaz, le sol s'est effondré, et on y a mis le feu",
            "Les ingénieurs pensaient que ça s'éteindrait en quelques jours",
            "Des centaines de flammes illuminent en permanence le fond et les parois",
        ],
        "search_seeds": ["darvaza gas crater fire", "burning crater night", "flaming pit desert"],
        "visual_hints": ["the Darvaza flaming gas crater at night, huge fiery pit glowing orange in the dark desert, photorealistic dramatic"],
        "avoid": [],
    },
    {
        "title": "Le plus grand miroir du monde fait 10 000 km carrés",
        "key_facts": [
            "Le Salar d'Uyuni, en Bolivie, est la plus grande étendue de sel du monde",
            "Il couvre environ 10 582 km², perché à 3656 m d'altitude",
            "Pendant la saison des pluies, une fine couche d'eau le transforme en immense miroir naturel",
            "Sa surface est si plate qu'elle sert à calibrer les altimètres des satellites",
            "Sous la croûte se cache une immense réserve de lithium",
        ],
        "search_seeds": ["salar uyuni mirror", "salt flat reflection sky", "bolivia salt desert"],
        "visual_hints": ["the Uyuni salt flat as a perfect mirror reflecting the sky and clouds, infinite horizon, surreal, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Dans ce village, il a fait -67 degrés, et 500 personnes y vivent",
        "key_facts": [
            "Oymiakon, en Sibérie, est le lieu habité en permanence le plus froid de la Terre",
            "La température officielle la plus basse y est de -67,7 °C, en 1933",
            "La moyenne hivernale tourne autour de -50 °C",
            "Le village est piégé dans une cuvette où l'air glacé stagne",
            "Les voitures doivent tourner en continu, sous peine de ne plus redémarrer",
        ],
        "search_seeds": ["coldest village siberia", "frozen village snow", "extreme cold winter"],
        "visual_hints": ["a tiny remote Siberian village buried in ice and snow, frozen mist, houses with smoking chimneys, harsh cold light, photorealistic"],
        "avoid": ["record officiel -67,7 °C ; le -71 °C célèbre est non officiel"],
    },
    {
        "title": "Cette grotte cache des cristaux plus grands qu'un bus",
        "key_facts": [
            "La Grotte des Cristaux de Naica, au Mexique, abrite les plus grands cristaux naturels connus",
            "Le plus grand mesure 11,40 mètres de long, pour environ 12 tonnes",
            "Ce sont des cristaux de gypse, formés très lentement sur au moins 500 000 ans",
            "La grotte se trouve à 300 mètres de profondeur",
            "L'air y est mortel : jusqu'à 58 °C et près de 100 % d'humidité, quelques minutes maximum sans équipement",
        ],
        "search_seeds": ["giant crystal cave", "selenite crystals cave", "huge crystals underground"],
        "visual_hints": ["the Naica cave of giant translucent selenite crystals, enormous glowing crystal beams crossing a cavern, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le paysage le plus proche de l'enfer sur Terre",
        "key_facts": [
            "Le site de Dallol, en Éthiopie, affiche des couleurs irréelles : jaune soufre, vert acide, rouge",
            "La région du Danakil est l'endroit habité le plus chaud du monde, avec plus de 34 °C de moyenne annuelle",
            "Les sources de Dallol crachent des saumures plus chaudes que 100 °C",
            "Certaines mares sont plus acides que l'acide de batterie",
            "Les mares les plus extrêmes sont totalement stériles : une limite absolue de la vie",
        ],
        "search_seeds": ["dallol ethiopia colorful", "acid hot springs", "sulfur landscape alien"],
        "visual_hints": ["the Dallol hydrothermal field, surreal acid pools of yellow green and orange, alien volcanic landscape, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Cette île ressemble à une autre planète",
        "key_facts": [
            "L'île de Socotra, au large du Yémen, abrite une flore digne de la science-fiction",
            "Sur ses 825 espèces de plantes, 37 % n'existent nulle part ailleurs sur Terre",
            "90 % de ses reptiles sont également uniques au monde",
            "Son emblème est l'arbre du sang du dragon, en forme de parasol, à la résine rouge sang",
            "C'est l'une des plus fortes concentrations de plantes uniques au monde",
        ],
        "search_seeds": ["socotra dragon blood tree", "alien island trees", "strange umbrella trees"],
        "visual_hints": ["Socotra island with its otherworldly dragon blood trees, umbrella-shaped canopies on rocky terrain, alien landscape, photorealistic"],
        "avoid": [],
    },
    {
        "title": "La plus haute falaise verticale de la planète",
        "key_facts": [
            "Le mont Thor, au Canada, possède la plus grande chute verticale pure au monde",
            "Sa face ouest tombe de 1250 mètres",
            "Elle est même en surplomb : la paroi penche au-delà de la verticale",
            "Un objet lâché du sommet tomberait dans le vide sans jamais toucher la paroi",
            "Sa première ascension, en 1985, a demandé 33 jours d'escalade",
        ],
        "search_seeds": ["mount thor cliff", "vertical rock face", "sheer cliff mountain"],
        "visual_hints": ["Mount Thor's sheer vertical granite cliff plunging into a valley, dizzying overhang, dramatic scale, photorealistic"],
        "avoid": [],
    },
    {
        "title": "40 000 colonnes de pierre parfaites : nature ou magie ?",
        "key_facts": [
            "La Chaussée des Géants, en Irlande du Nord, est formée de plus de 40 000 colonnes de basalte",
            "La plupart sont parfaitement hexagonales, à six côtés",
            "Elles se sont formées il y a 50 à 60 millions d'années lors d'une intense activité volcanique",
            "En refroidissant lentement, la lave s'est fissurée en angles réguliers",
            "Les plus hautes colonnes atteignent environ 12 mètres",
        ],
        "search_seeds": ["giants causeway columns", "basalt columns hexagonal", "rock formation coast"],
        "visual_hints": ["the Giant's Causeway, thousands of interlocking hexagonal basalt columns by the sea, dramatic coastal light, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Dans cette mer, il est impossible de couler",
        "key_facts": [
            "La mer Morte borde le point le plus bas de la terre ferme, à plus de 430 mètres sous le niveau de la mer",
            "Sa salinité atteint environ 34 %, près de dix fois plus que l'océan",
            "Sa densité est telle qu'on y flotte sans effort, comme assis dans l'eau",
            "Ce sel extrême empêche toute vie animale ou végétale, d'où son nom",
            "Elle est en train de disparaître : son niveau baisse d'environ un mètre par an",
        ],
        "search_seeds": ["dead sea floating", "salt sea person floating", "salty lake shore"],
        "visual_hints": ["the Dead Sea with a person floating effortlessly on the surface, salt crusted shore, hazy desert light, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Ce lac est coupé du monde depuis 15 millions d'années",
        "key_facts": [
            "Le lac Vostok, en Antarctique, est un immense lac d'eau douce enfoui sous la glace",
            "Il est scellé sous près de 4 km de glace",
            "Il s'étend sur environ 240 km de long, la taille du lac Ontario",
            "Il serait isolé de l'air et de la lumière depuis environ 15 millions d'années",
            "Il sert de répétition pour chercher la vie sous les océans glacés des lunes de Jupiter et Saturne",
        ],
        "search_seeds": ["antarctica ice sheet", "subglacial lake ice", "frozen antarctic landscape"],
        "visual_hints": ["a vast Antarctic ice sheet with a hidden subglacial lake beneath kilometers of ice, cross-section concept, cold blue light, photorealistic"],
        "avoid": [],
    },
]

# === CORPS HUMAIN & CERVEAU ===
CORPS: list[KnowledgeEntry] = [
    {
        "title": "Ton estomac se refait une paroi neuve tous les 4 jours",
        "key_facts": [
            "L'acide de ton estomac est de l'acide chlorhydrique, aussi corrosif que celui qui décape l'acier",
            "Plongée dedans, une lame de rasoir perd environ un tiers de sa masse en 24 heures",
            "Pour ne pas se digérer lui-même, l'estomac se protège avec un mucus alcalin",
            "Il renouvelle entièrement sa paroi interne environ tous les 4 jours",
            "Sans ce renouvellement, il commencerait à s'attaquer lui-même",
        ],
        "search_seeds": ["human stomach anatomy", "digestive system medical", "stomach acid concept"],
        "visual_hints": ["a detailed anatomical illustration of the human stomach with glowing acid inside, medical 3D render, photorealistic"],
        "avoid": ["l'acide attaque le métal lentement, pas instantanément"],
    },
    {
        "title": "Tu es à moitié bactérie, mais pas à 90 % comme on te l'a dit",
        "key_facts": [
            "Ton corps abrite environ autant de bactéries que de cellules humaines, à peu près moitié-moitié",
            "Le fameux « 10 bactéries pour 1 cellule » est faux : c'était une vieille estimation jamais vérifiée",
            "Elle a été corrigée en 2016 par des chercheurs de l'Institut Weizmann",
            "Une seule visite aux toilettes évacue des milliards de bactéries",
            "Sur tes cellules humaines, la grande majorité sont des globules rouges",
        ],
        "search_seeds": ["bacteria microbiome", "gut bacteria illustration", "microscopic bacteria"],
        "visual_hints": ["a colorful illustration of gut bacteria and microbiome, teeming microscopic life, scientific macro, photorealistic"],
        "avoid": ["le « 10 pour 1 » est un mythe corrigé"],
    },
    {
        "title": "Ton cerveau pèse 2 % de ton corps mais dévore 20 % de ton énergie",
        "key_facts": [
            "Le cerveau ne représente qu'environ 2 % du poids du corps",
            "Mais il consomme environ 20 % de l'oxygène et de l'énergie au repos",
            "Il capte jusqu'à un quart du sucre de tout l'organisme",
            "Il ne sait quasiment pas stocker de carburant",
            "Quelques minutes sans oxygène ou sans sucre suffisent à l'endommager",
        ],
        "search_seeds": ["human brain glowing", "brain energy concept", "neurons brain illustration"],
        "visual_hints": ["a glowing human brain with pulsing energy and neural connections, dark background, scientific 3D render, photorealistic"],
        "avoid": ["ne pas dire qu'on n'utilise que 10 % du cerveau : c'est un mythe"],
    },
    {
        "title": "À poids égal, ton os est plus solide que l'acier",
        "key_facts": [
            "À masse égale, l'os résiste autant qu'une barre d'acier bien plus lourde",
            "Un petit cube d'os peut théoriquement supporter plusieurs tonnes",
            "Le secret de l'os, c'est son exceptionnel rapport solidité sur poids",
            "L'acier est solide mais environ quatre fois plus dense que l'os",
            "L'os se répare aussi tout seul quand il se casse, ce que l'acier ne fait pas",
        ],
        "search_seeds": ["human bone structure", "bone anatomy medical", "skeleton bone close-up"],
        "visual_hints": ["a cross-section of human bone showing its porous honeycomb inner structure, scientific macro render, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Il y a un trou dans ta vision, et ton cerveau invente pour le combler",
        "key_facts": [
            "Chaque œil a une zone sans aucun capteur, là où le nerf optique quitte la rétine",
            "À cet endroit précis, tu es littéralement aveugle",
            "Pourtant tu ne vois aucun trou dans ton champ de vision",
            "Le cerveau comble la zone manquante en inventant la couleur et la texture autour",
            "On peut le prouver soi-même en fermant un œil et en fixant un point",
        ],
        "search_seeds": ["human eye anatomy", "retina optic nerve", "eye vision concept"],
        "visual_hints": ["a detailed human eye with the retina and optic nerve highlighted, medical illustration, dramatic light, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Tes nerfs envoient des signaux à plus de 400 km/h",
        "key_facts": [
            "Les fibres nerveuses les plus rapides conduisent le signal jusqu'à 120 mètres par seconde",
            "Cela représente environ 430 km/h",
            "Le signal saute de nœud en nœud le long de la fibre, au lieu de la parcourir en continu",
            "Mais les fibres de la douleur chronique, elles, rampent à environ un mètre par seconde",
            "C'est pour ça qu'une douleur sourde arrive parfois « en retard »",
        ],
        "search_seeds": ["nerve cells signal", "neuron synapse illustration", "nervous system glowing"],
        "visual_hints": ["glowing nerve signals traveling along a neuron with electric sparks, dark background, scientific 3D, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Coupe-lui 70 % : le foie est le seul organe qui repousse",
        "key_facts": [
            "Le foie peut se reconstituer même après l'ablation d'environ 70 % de sa masse",
            "Chez l'humain, il retrouve son volume en quelques semaines à trois mois",
            "C'est ce qui rend possible le don de foie entre personnes vivantes",
            "Le foie du donneur comme celui du receveur repoussent",
            "Il retrouve sa masse et sa fonction, mais pas exactement sa forme d'origine",
        ],
        "search_seeds": ["human liver anatomy", "liver organ medical", "liver illustration body"],
        "visual_hints": ["a detailed anatomical human liver, deep red organ, medical 3D render on dark background, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Ton cœur battra environ 3 milliards de fois dans ta vie",
        "key_facts": [
            "Au repos, le cœur bat environ 100 000 fois par jour",
            "Cela fait près de 37 millions de battements par an",
            "Sur une vie entière, cela représente environ 2,5 à 3 milliards de battements",
            "Il ne se repose jamais, sauf l'instant infime entre deux battements",
            "Il pompe assez de sang dans une vie pour remplir des dizaines de piscines",
        ],
        "search_seeds": ["human heart beating", "heart anatomy medical", "heart pulse illustration"],
        "visual_hints": ["a realistic human heart with glowing pulse of blood flow, anatomical 3D render, dark background, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Tu as un deuxième cerveau, dans ton ventre",
        "key_facts": [
            "L'intestin possède son propre système nerveux, environ 500 millions de neurones",
            "C'est plus que la moelle épinière : on le surnomme le deuxième cerveau",
            "Il fonctionne en partie de façon autonome",
            "La grande majorité de la sérotonine du corps est fabriquée dans l'intestin, pas dans la tête",
            "L'information circule surtout de bas en haut : de l'intestin vers le cerveau",
        ],
        "search_seeds": ["gut brain connection", "intestines nervous system", "digestive concept glowing"],
        "visual_hints": ["an illustration of the gut-brain connection, glowing nerve network along the intestines, scientific concept, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Ton hoquet est un vieux réflexe hérité des poissons",
        "key_facts": [
            "L'hypothèse la mieux étayée : le hoquet est un vestige de nos ancêtres aquatiques",
            "La séquence du hoquet ressemble à la respiration des branchies d'un têtard",
            "Une inspiration brusque, puis la fermeture de la gorge, le fameux « hic »",
            "Ce réflexe empêchait l'eau d'entrer dans les poumons primitifs",
            "Le signal naît dans la même partie du cerveau qui commandait la respiration branchiale",
        ],
        "search_seeds": ["tadpole gills water", "evolution fish amphibian", "frog tadpole macro"],
        "visual_hints": ["a tadpole with visible gills swimming in clear water, early evolutionary life, soft macro light, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Ton cerveau fabrique environ 700 neurones neufs chaque jour",
        "key_facts": [
            "Dans l'hippocampe, la zone de la mémoire, l'adulte produirait environ 700 nouveaux neurones par jour",
            "Ce chiffre a été établi grâce au carbone laissé par les essais nucléaires des années 1950",
            "Ce carbone sert d'horodatage pour dater la naissance des cellules",
            "Cela représente un lent renouvellement de la mémoire au fil des années",
            "La fabrication de neurones adultes chez l'humain reste toutefois débattue",
        ],
        "search_seeds": ["neurons brain new", "hippocampus memory brain", "neural growth illustration"],
        "visual_hints": ["new glowing neurons growing and connecting in the brain's hippocampus, scientific 3D concept, dark background, photorealistic"],
        "avoid": ["la neurogenèse adulte humaine est encore débattue"],
    },
    {
        "title": "Ta chair de poule est un réflexe hérité de tes ancêtres à fourrure",
        "key_facts": [
            "La chair de poule vient d'un petit muscle à la base de chaque poil",
            "Chez les animaux à fourrure, il gonfle le pelage pour se réchauffer ou paraître plus gros",
            "Chez l'humain presque glabre, ça ne sert plus à rien : c'est un vestige",
            "En 2020, des chercheurs de Harvard ont découvert que ce muscle a un rôle caché",
            "Son nerf stimule aussi les cellules souches qui font repousser le poil",
        ],
        "search_seeds": ["goosebumps skin macro", "human skin hair follicle", "skin close-up cold"],
        "visual_hints": ["extreme macro of human skin with goosebumps and raised hair follicles, cold reaction, scientific detail, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Tu perds des dizaines de milliers de cellules de peau par minute",
        "key_facts": [
            "La peau perd environ 30 000 à 40 000 cellules mortes par minute",
            "Cela représente près de 4 kg de peau perdue par an",
            "L'épiderme se renouvelle entièrement en environ 4 à 6 semaines",
            "Une bonne partie de la poussière de la maison est faite de peau morte humaine",
            "Tu portes en permanence une peau plus jeune que le reste de ton corps",
        ],
        "search_seeds": ["human skin layers", "skin cells macro", "dermatology skin illustration"],
        "visual_hints": ["a cross-section illustration of human skin layers with cells shedding from the surface, scientific macro render, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Tu ne bâilles pas par manque d'oxygène",
        "key_facts": [
            "L'idée qu'on bâille par manque d'oxygène est fausse",
            "En laboratoire, respirer de l'oxygène pur ne change pas la fréquence des bâillements",
            "La théorie la mieux soutenue : le bâillement sert à refroidir le cerveau",
            "L'inspiration profonde d'air frais agit comme un radiateur",
            "Le bâillement contagieux est lié à l'empathie : plus on est proche de quelqu'un, plus on l'attrape",
        ],
        "search_seeds": ["person yawning", "yawn tired face", "sleepy human concept"],
        "visual_hints": ["a person mid-yawn with a subtle glowing brain overlay suggesting cooling, soft light, conceptual, photorealistic"],
        "avoid": ["ne pas dire qu'on bâille par manque d'oxygène : c'est un mythe"],
    },
    {
        "title": "La partie de ton œil qui respire l'air directement",
        "key_facts": [
            "La cornée, à l'avant de l'œil, n'a aucun vaisseau sanguin",
            "C'est indispensable pour qu'elle reste parfaitement transparente",
            "Presque toutes les cellules du corps sont collées à un vaisseau sanguin, sauf elle",
            "Yeux ouverts, elle prend son oxygène directement dans l'air, via le film de larmes",
            "C'est pour ça que des lentilles mal oxygénées peuvent étouffer l'œil",
        ],
        "search_seeds": ["human eye cornea", "eye close-up macro", "eye iris detail"],
        "visual_hints": ["an extreme close-up of a human eye showing the transparent cornea and detailed iris, sharp macro, photorealistic"],
        "avoid": [],
    },
]


# === HISTOIRES VRAIES STUPÉFIANTES ===
HISTOIRES: list[KnowledgeEntry] = [
    {
        "title": "Il a survécu à DEUX bombes atomiques, à 3 jours d'intervalle",
        "key_facts": [
            "Tsutomu Yamaguchi, ingénieur japonais, est à Hiroshima le 6 août 1945 quand la bombe explose",
            "Il se trouve à environ 3 km de l'épicentre et est brûlé, mais survit",
            "Il rentre chez lui à Nagasaki et retourne au travail le 9 août, jour de la seconde bombe",
            "Il est le seul reconnu officiellement comme double survivant par le Japon",
            "Il est mort en 2010, à 93 ans",
        ],
        "search_seeds": ["hiroshima 1945 historical", "atomic bomb mushroom cloud", "post war japan black white"],
        "visual_hints": ["a solemn historical scene of a Japanese city after 1945, dramatic sky, muted documentary tones, photorealistic cinematic"],
        "avoid": ["rester sobre et respectueux : c'est un drame humain réel"],
    },
    {
        "title": "Il a survécu 3 jours au fond de l'océan dans une bulle d'air",
        "key_facts": [
            "En mai 2013, un remorqueur chavire au large du Nigeria et coule à l'envers, à 30 mètres de profondeur",
            "Le cuisinier Harrison Okene, 29 ans, se retrouve piégé dans une poche d'air, dans le noir total",
            "Il survit environ 60 heures, près de trois jours, en sous-vêtements",
            "Les onze autres membres d'équipage sont morts noyés",
            "Des plongeurs venus récupérer les corps le découvrent vivant",
        ],
        "search_seeds": ["sunken ship underwater dark", "diver deep sea rescue", "shipwreck ocean floor"],
        "visual_hints": ["a diver's light illuminating a sunken capsized ship on the dark ocean floor, eerie underwater atmosphere, photorealistic"],
        "avoid": ["dire « près de 3 jours, environ 60 heures » pour rester exact"],
    },
    {
        "title": "À 17 ans, elle tombe d'un avion et survit 11 jours dans la jungle",
        "key_facts": [
            "En décembre 1971, un avion se désintègre en plein orage au-dessus de l'Amazonie péruvienne",
            "Juliane Koepcke, 17 ans, chute d'environ 3000 mètres, toujours attachée à son siège, et touche le sol vivante",
            "Sur 92 personnes à bord, elle est l'unique survivante",
            "Blessée, elle marche et dérive dans une rivière pendant 11 jours avant de trouver des secours",
            "Ses parents zoologistes lui avaient appris à survivre en forêt",
        ],
        "search_seeds": ["amazon jungle dense", "rainforest river survival", "thick jungle canopy"],
        "visual_hints": ["a dense misty Amazon rainforest with a winding river, sense of isolation and survival, dramatic light, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Elle est tombée de 10 000 mètres sans parachute — record du monde",
        "key_facts": [
            "En janvier 1972, une explosion détruit un avion au-dessus de la Tchécoslovaquie",
            "L'hôtesse Vesna Vulović, coincée dans une partie du fuselage, chute de 10 160 mètres",
            "Elle est la seule survivante",
            "Elle subit de multiples fractures, reste dans le coma, puis remarche",
            "Le Guinness des records homologue la plus haute chute survécue sans parachute",
        ],
        "search_seeds": ["airplane sky clouds high", "falling through clouds", "aircraft fuselage sky"],
        "visual_hints": ["a dramatic view high above the clouds with a sense of vertigo and altitude, cinematic sky, photorealistic"],
        "avoid": ["préciser « selon le Guinness World Records » : l'altitude a été contestée"],
    },
    {
        "title": "133 jours seul sur un radeau : un record qui tient depuis 1943",
        "key_facts": [
            "En novembre 1942, un sous-marin allemand coule le cargo de Poon Lim, marin chinois, dans l'Atlantique",
            "Il survit 133 jours seul sur un petit radeau de bois",
            "Il récupère l'eau de pluie, pêche, et attrape des oiseaux de mer",
            "Des pêcheurs brésiliens le sauvent en avril 1943",
            "Il détient toujours le record du plus long temps de survie seul sur un radeau",
        ],
        "search_seeds": ["life raft ocean alone", "small raft open sea", "castaway ocean horizon"],
        "visual_hints": ["a lone wooden raft adrift on a vast empty ocean under a huge sky, sense of isolation, cinematic, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Perdu 9 jours dans le Sahara, il a survécu à l'impossible",
        "key_facts": [
            "En 1994, l'Italien Mauro Prosperi court un marathon dans le désert marocain quand une tempête de sable le désoriente",
            "Il erre environ 9 jours, buvant sa propre urine et mangeant des chauves-souris",
            "Désespéré, il tente de mettre fin à ses jours, mais son sang trop épais ne coule pas",
            "Il est retrouvé par des nomades en Algérie, à des centaines de kilomètres de sa route",
            "Il avait perdu près de 16 kilos",
        ],
        "search_seeds": ["sahara desert dunes vast", "sandstorm desert", "endless sand dunes sunset"],
        "visual_hints": ["a vast Sahara desert of golden dunes stretching to infinity, a lone figure tiny in the distance, harsh sun, photorealistic"],
        "avoid": ["évoquer la tentative de suicide avec pudeur, ou l'omettre"],
    },
    {
        "title": "Son corps est descendu à 13 degrés, et elle est revenue à la vie",
        "key_facts": [
            "En 1999, une médecin suédoise chute en skiant et passe sous la glace d'un torrent gelé",
            "Elle reste piégée sous la glace environ 80 minutes",
            "Sa température corporelle chute à 13,7 °C, la plus basse jamais enregistrée chez un survivant",
            "À l'hôpital, son cœur est arrêté : elle est cliniquement morte",
            "Réchauffée lentement par une machine cœur-poumon, son cœur repart, et elle reprend son métier",
        ],
        "search_seeds": ["frozen river ice", "icy mountain stream", "cold winter medical rescue"],
        "visual_hints": ["a frozen mountain stream with ice and snow, cold blue light, dramatic wintry atmosphere, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Coincé 5 jours sous un rocher, il se coupe le bras pour survivre",
        "key_facts": [
            "En avril 2003, l'alpiniste Aron Ralston descend seul un canyon de l'Utah",
            "Un rocher de 360 kg se détache et écrase son avant-bras contre la paroi",
            "Il reste piégé 127 heures, soit cinq jours, sans que personne ne sache où il est",
            "À bout, il casse les deux os de son bras puis l'ampute avec un petit canif",
            "Il redescend ensuite une paroi de 20 mètres et marche 11 km avant d'être secouru",
        ],
        "search_seeds": ["slot canyon utah narrow", "red rock canyon", "desert canyon boulder"],
        "visual_hints": ["a narrow red rock slot canyon in Utah with a wedged boulder, dramatic shafts of light, sense of entrapment, photorealistic"],
        "avoid": ["décrire l'amputation avec retenue"],
    },
    {
        "title": "Il a continué la Seconde Guerre mondiale pendant 29 ans",
        "key_facts": [
            "Hiroo Onoda, soldat japonais, est envoyé sur une île des Philippines fin 1944",
            "Refusant de croire à la fin de la guerre, il mène une guérilla dans la jungle près de 29 ans",
            "En 1974, un aventurier le retrouve, mais Onoda refuse de se rendre sans ordre",
            "Son ancien supérieur doit venir en personne lever ses ordres",
            "Il se rend officiellement le 10 mars 1974",
        ],
        "search_seeds": ["jungle soldier vintage", "dense tropical jungle", "philippine jungle green"],
        "visual_hints": ["a dense tropical jungle on a Philippine island, thick green foliage, mysterious atmosphere, documentary tone, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Un seul homme a empêché une guerre nucléaire",
        "key_facts": [
            "En septembre 1983, l'officier soviétique Stanislav Petrov est de garde dans un centre d'alerte",
            "Le système signale le tir de cinq missiles nucléaires américains vers l'URSS",
            "Le protocole imposait de prévenir la hiérarchie, ce qui aurait pu déclencher une riposte",
            "Petrov juge qu'une vraie attaque n'aurait pas visé avec seulement cinq missiles, et conclut à une fausse alerte",
            "Il avait raison : le système avait pris le reflet du soleil sur des nuages pour des missiles",
        ],
        "search_seeds": ["cold war bunker control room", "radar screen dark", "soviet military monitor night"],
        "visual_hints": ["a dim Cold War era control room with glowing radar screens, tense atmosphere, single figure, cinematic, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Il a sauvé 669 enfants et l'a caché pendant 50 ans",
        "key_facts": [
            "En 1939, le Britannique Nicholas Winton organise l'évacuation de 669 enfants, en majorité juifs, de Tchécoslovaquie",
            "Il les fait passer en Angleterre par des trains, avant l'invasion nazie",
            "Il garde ce secret près de 50 ans",
            "En 1988, une émission de télévision l'invite, entouré sans qu'il le sache de plusieurs de ces enfants devenus adultes",
            "Fait chevalier, il est mort en 2015 à 106 ans",
        ],
        "search_seeds": ["old train station vintage", "steam train 1930s", "children evacuation historical"],
        "visual_hints": ["a vintage 1930s railway platform with a steam train, nostalgic historical atmosphere, warm muted tones, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Elle a survécu au Titanic, puis à deux autres naufrages",
        "key_facts": [
            "Violet Jessop, hôtesse et infirmière, est à bord de l'Olympic en 1911 lors d'une collision",
            "Elle survit au naufrage du Titanic en avril 1912",
            "En 1916, elle est à bord du Britannic, navire jumeau du Titanic, qui coule après avoir heurté une mine",
            "Elle saute d'un canot, se blesse à la tête, mais survit encore",
            "Elle a donc côtoyé les trois grands paquebots jumeaux dans leurs pires moments",
        ],
        "search_seeds": ["ocean liner vintage sea", "titanic era ship", "old steamship ocean"],
        "visual_hints": ["a majestic early 1900s ocean liner at sea under a dramatic sky, vintage grandeur, cinematic, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Il s'est fait envoyer volontairement à Auschwitz pour espionner",
        "key_facts": [
            "En 1940, le résistant polonais Witold Pilecki se laisse volontairement arrêter pour être déporté à Auschwitz",
            "À l'intérieur, il monte un réseau de résistance clandestin",
            "Il fait sortir parmi les premiers témoignages détaillés sur le camp, transmis aux Alliés",
            "Après près de trois ans, il s'évade du camp en 1943",
            "C'est l'un des actes de courage les plus stupéfiants de la guerre",
        ],
        "search_seeds": ["barbed wire fence historical", "concentration camp memorial", "dark historical fence snow"],
        "visual_hints": ["a somber historical scene of a barbed wire fence under a grey winter sky, respectful memorial tone, muted, photorealistic"],
        "avoid": ["sujet grave : rester factuel, sobre et respectueux"],
    },
    {
        "title": "Il a été foudroyé 7 fois et a survécu à chaque fois",
        "key_facts": [
            "Roy Sullivan, garde forestier américain de Virginie, a été foudroyé sept fois entre 1942 et 1977",
            "Il a survécu à chacune de ces foudroiements",
            "Il a perdu un ongle, ses sourcils, et a eu les cheveux et les vêtements en feu à plusieurs reprises",
            "Le Guinness des records homologue son record du plus grand nombre de foudroiements survécus",
            "Les probabilités d'un tel enchaînement sont astronomiques",
        ],
        "search_seeds": ["lightning strike storm", "thunderstorm dramatic sky", "lightning bolt night"],
        "visual_hints": ["a dramatic lightning bolt striking down from a dark stormy sky, electric energy, cinematic, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Un roman de 1838 a prédit un vrai naufrage, même nom compris",
        "key_facts": [
            "En 1838, Edgar Allan Poe publie un roman où des naufragés affamés tuent et mangent un jeune marin nommé Richard Parker",
            "En 1884, un yacht coule réellement, et les survivants à la dérive dévorent le mousse",
            "Ce mousse s'appelait lui aussi Richard Parker",
            "La coïncidence du nom et du scénario est authentique et documentée",
            "L'affaire réelle est devenue un cas célèbre du droit pénal britannique",
        ],
        "search_seeds": ["old book vintage pages", "stormy sea shipwreck", "antique novel candle"],
        "visual_hints": ["an antique open book beside a stormy sea backdrop, mysterious literary atmosphere, warm candlelight, photorealistic"],
        "avoid": [],
    },
]


ALL_TOPICS_BY_THEME: dict[str, list[KnowledgeEntry]] = {
    "espace": ESPACE,
    "animaux": ANIMAUX,
    "lieux_extremes": LIEUX,
    "corps_humain": CORPS,
    "histoires_vraies": HISTOIRES,
}


# Anti-répétition dédiée au monde (fichier séparé de Mayotte).
_USED_FILE = Path(__file__).resolve().parent.parent / "output" / "world_used_topics.json"


def _read_used() -> dict[str, list[str]]:
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
    """Choisit un sujet monde pour le thème, en évitant les répétitions.

    Même logique que mayotte_knowledge.pick_topic_for, avec un fichier d'état
    séparé (world_used_topics.json).
    """
    pool = ALL_TOPICS_BY_THEME.get(theme, [])
    if not pool:
        raise ValueError(f"Thème monde inconnu : {theme}")

    used = _read_used()
    used_titles = set(used.get(theme, []))
    available = [e for e in pool if e["title"] not in used_titles]
    if not available:
        print(f"   ♻️  Tous les sujets « {theme} » ont été utilisés — nouveau cycle.")
        last_used = used.get(theme, [])[-1:]
        used[theme] = []
        available = [e for e in pool if e["title"] not in last_used] or list(pool)

    entry = random.choice(available)
    used.setdefault(theme, [])
    used[theme].append(entry["title"])
    _write_used(used)

    remaining = len(pool) - len(used[theme])
    print(f"   📚 Sujet monde pioché ({remaining}/{len(pool)} restants ce cycle)")
    return entry


def random_topic_for(theme: str) -> KnowledgeEntry:
    """Alias compat."""
    return pick_topic_for(theme)


GLOBAL_CONTEXT_PROMPT_WORLD = """Tu écris pour une chaîne TikTok francophone de vulgarisation « le sais-tu ? » : sujets fascinants, faits incroyables mais VRAIS (espace, animaux, lieux extrêmes, corps humain, sciences).

RÈGLES D'OR :
- Chaque fait énoncé doit être EXACT. On ne raconte que des choses vérifiées.
- Ton : émerveillement, curiosité, « tu vas pas me croire mais… ». Direct, tutoiement, dynamique.
- Style oral, phrases courtes et percutantes, comme un pote passionné qui te raconte un truc dingue.
- Pas de jargon : on explique simplement, avec des images parlantes et des comparaisons concrètes.
- On garde le SUSPENS : on distille l'info, on relance la curiosité entre les scènes.

À ÉVITER ABSOLUMENT :
- Ne jamais exagérer un fait pour le rendre plus spectaculaire : la vérité suffit.
- Pas de mythes déboulonnés présentés comme vrais (ex : « on n'utilise que 10 % du cerveau » = FAUX).
- Pas de contenu anxiogène, gore, ou putaclic trompeur.
- Rester factuel et bienveillant."""
