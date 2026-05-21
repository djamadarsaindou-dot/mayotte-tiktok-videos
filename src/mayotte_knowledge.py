"""Base de connaissances Mayotte vérifiées.

Chaque entrée est ancrée et factuelle. Le LLM doit narrer un sujet précis
de cette base, sans inventer ni mélanger.

Chaque entrée a :
- title : titre court du sujet
- key_facts : liste de faits factuels précis (3-7 éléments)
- search_seeds : suggestions de mots-clés en anglais pour stock vidéo
- visual_hints : indications spécifiques pour les visuels (pour Pollinations IA)
- avoid : pièges à éviter dans le récit
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
            "Mayotte possède l'un des deux seuls doubles lagons fermés au monde, avec la Nouvelle-Calédonie",
            "Le lagon couvre environ 1500 km², parmi les plus vastes lagons fermés de la planète",
            "Une barrière de corail de 195 km entoure l'île",
            "Le récif intérieur double la barrière externe sur certaines zones",
            "Plus de 250 espèces de coraux et 760 espèces de poissons y vivent",
            "La passe en S, au sud, est mondialement connue des plongeurs",
        ],
        "search_seeds": ["aerial double coral reef", "tropical lagoon turquoise water", "coral atoll drone view", "barrier reef aerial"],
        "visual_hints": ["Mayotte double lagoon aerial drone, two parallel coral reef barriers, turquoise gradient water, photorealistic, vertical 9:16"],
        "avoid": [],
    },
    {
        "title": "L'îlot de Mtsamboro et les ilots du Nord",
        "key_facts": [
            "L'îlot Mtsamboro est situé au nord de Grande-Terre, accessible en barque",
            "Il abrite des plages de sable blanc parmi les plus pures de l'archipel",
            "Le site est classé en réserve naturelle marine",
            "On y observe baleines à bosse de juillet à octobre",
            "Les villageois pratiquent toujours la pêche traditionnelle au djarifa",
        ],
        "search_seeds": ["white sand islet boat", "tropical island reserve", "humpback whale ocean", "traditional fishing net"],
        "visual_hints": ["uninhabited tropical islet white sand pristine beach, turquoise water, vertical 9:16"],
        "avoid": [],
    },
    {
        "title": "La plage de N'Gouja et les tortues vertes",
        "key_facts": [
            "N'Gouja est la plage la plus célèbre de Mayotte, située au sud",
            "Les tortues vertes viennent y brouter les herbiers à seulement quelques mètres du rivage",
            "On peut nager avec elles toute l'année, sans bateau",
            "La ponte des tortues a lieu de novembre à mars sur les plages voisines",
            "Le site est protégé par la réserve naturelle nationale",
        ],
        "search_seeds": ["green sea turtle swimming", "snorkeling tropical beach", "turtle laying eggs beach", "underwater turtle reef"],
        "visual_hints": ["green sea turtle swimming in turquoise lagoon shallow water, sunlight rays, photorealistic vertical"],
        "avoid": [],
    },
    {
        "title": "Petite-Terre et le lac Dziani",
        "key_facts": [
            "Petite-Terre est l'une des deux îles principales de Mayotte avec Grande-Terre",
            "On y trouve l'aéroport international de Pamandzi",
            "Le lac Dziani est un cratère volcanique aux eaux vert émeraude",
            "Il mesure 700 mètres de diamètre et serait sacré selon les traditions locales",
            "Mtsapéré et Sazile y abritent des sites de ponte de tortues",
        ],
        "search_seeds": ["volcanic crater lake green", "small tropical island airport", "emerald lake aerial", "volcanic island"],
        "visual_hints": ["volcanic crater lake emerald green water aerial drone, vertical 9:16"],
        "avoid": [],
    },
]

# === FAUNE & FLORE ===
NATURE: list[KnowledgeEntry] = [
    {
        "title": "Le dugong — sirène en voie de disparition",
        "key_facts": [
            "Le dugong est un mammifère marin herbivore proche du lamantin",
            "Mayotte abrite la dernière population de dugongs de l'océan Indien occidental",
            "Il ne resterait qu'une dizaine d'individus dans le lagon de Mayotte",
            "Le dugong se nourrit exclusivement d'herbes marines (phanérogames)",
            "Il peut peser jusqu'à 400 kg et mesurer 3 mètres",
            "Les marins l'auraient confondu avec des sirènes au fil des siècles",
        ],
        "search_seeds": ["dugong manatee underwater", "sea cow swimming", "marine mammal seagrass", "endangered species ocean"],
        "visual_hints": ["dugong swimming in turquoise lagoon, seagrass bed, photorealistic underwater, vertical 9:16"],
        "avoid": ["dire que le dugong est abondant — il est en danger critique à Mayotte"],
    },
    {
        "title": "Les baleines à bosse — visiteuses majestueuses",
        "key_facts": [
            "Les baleines à bosse migrent à Mayotte de juillet à octobre",
            "Elles viennent de l'Antarctique pour mettre bas et allaiter dans les eaux chaudes",
            "Les mâles chantent des mélodies complexes pour attirer les femelles",
            "Une baleine adulte peut peser 30 tonnes et mesurer 15 mètres",
            "Les sauts hors de l'eau sont fréquents, parfois à quelques centaines de mètres du rivage",
            "L'observation se fait depuis bateau, dans le respect d'une distance réglementaire",
        ],
        "search_seeds": ["humpback whale breach", "whale watching boat", "whale tail underwater", "mother whale calf"],
        "visual_hints": ["humpback whale breaching ocean surface, dramatic spray, vertical 9:16, photorealistic"],
        "avoid": [],
    },
    {
        "title": "L'ylang-ylang — la fleur d'or de Mayotte",
        "key_facts": [
            "Mayotte produit historiquement environ 80% de l'ylang-ylang mondial",
            "Cette fleur jaune sert à l'extraction d'huile essentielle pour la parfumerie",
            "Elle est l'ingrédient star du Chanel n°5 et de nombreux grands parfums",
            "La récolte se fait à la main, à l'aube, avant que le soleil n'altère le parfum",
            "Un kilogramme d'huile nécessite environ 100 kg de fleurs",
            "La distillation traditionnelle se fait dans des alambics en cuivre",
        ],
        "search_seeds": ["yellow tropical flower harvest", "perfume distillation copper", "tropical plantation", "essential oil extraction"],
        "visual_hints": ["ylang ylang yellow flower close-up, harvested in tropical plantation morning light, vertical 9:16"],
        "avoid": [],
    },
    {
        "title": "Les makis — lémuriens introduits",
        "key_facts": [
            "Le maki est un lémurien à face brune endémique de Madagascar, introduit à Mayotte",
            "Il s'agit du seul primate sauvage présent sur l'île",
            "Il vit principalement dans la forêt humide du nord",
            "Son régime est frugivore, complété de feuilles et de fleurs",
            "Les groupes comptent généralement 5 à 15 individus",
            "Les Mahorais le considèrent comme une figure familière de leur patrimoine naturel",
        ],
        "search_seeds": ["lemur tropical forest", "primate jumping branches", "madagascar wildlife", "brown lemur"],
        "visual_hints": ["brown lemur sitting on tree branch in tropical rainforest, photorealistic vertical 9:16"],
        "avoid": ["dire que le maki est endémique de Mayotte — il est endémique de Madagascar"],
    },
    {
        "title": "Le baobab — arbre légendaire",
        "key_facts": [
            "Mayotte compte des baobabs centenaires, notamment dans la région de Musicale-Plage",
            "Le baobab peut vivre plus de 1000 ans et stocker des milliers de litres d'eau",
            "Selon une légende locale, Dieu aurait planté l'arbre à l'envers",
            "Ses fruits, appelés pains de singe, sont riches en vitamine C",
            "Son tronc creux a longtemps servi d'abri aux voyageurs",
        ],
        "search_seeds": ["baobab tree silhouette", "ancient tree sunset", "african baobab", "iconic tropical tree"],
        "visual_hints": ["massive baobab tree silhouette at sunset, golden hour, vertical 9:16, photorealistic"],
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
        "visual_hints": ["traditional Comoran wedding ceremony, bride in colorful salouva with gold, drumming celebration, photorealistic vertical"],
        "avoid": [],
    },
    {
        "title": "Le debaa — chants féminins sacrés",
        "key_facts": [
            "Le debaa est un chant religieux pratiqué exclusivement par les femmes mahoraises",
            "Il puise dans la tradition soufie et célèbre le prophète Mahomet",
            "Les femmes sont parées de robes colorées et coiffées de bijoux",
            "Les chœurs sont accompagnés de tambourins (tari)",
            "Le debaa fait l'objet d'inscriptions au patrimoine immatériel",
            "Les performances ont lieu lors de mariages et fêtes religieuses",
        ],
        "search_seeds": ["women singing traditional", "religious ceremony africa", "tambourine performance", "colorful headscarves"],
        "visual_hints": ["group of women in colorful Comoran dress singing religious hymn, tambourine, vertical 9:16"],
        "avoid": [],
    },
    {
        "title": "Le m'biwi — rythme du quotidien",
        "key_facts": [
            "Le m'biwi est une musique-danse traditionnelle féminine mahoraise",
            "Elle est exécutée à mains nues, avec battements de mains et de cuisses",
            "Les femmes forment un cercle, frappent des rythmes complexes",
            "La pratique remonte aux temps précoloniaux",
            "Elle accompagne mariages, naissances et fêtes du village",
        ],
        "search_seeds": ["women clapping circle dance", "traditional rhythm dance africa", "village celebration women"],
        "visual_hints": ["women in colorful dresses forming circle, clapping rhythmic dance, village setting, vertical 9:16"],
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
            "C'est un marqueur identitaire de l'archipel des Comores et Mayotte",
        ],
        "search_seeds": ["yellow face mask traditional", "sandalwood beauty ritual", "comoran woman portrait", "natural skincare africa"],
        "visual_hints": ["Comoran woman portrait wearing yellow sandalwood face mask, traditional beauty, vertical 9:16, photorealistic"],
        "avoid": [],
    },
    {
        "title": "Le voulé — repas convivial sur la plage",
        "key_facts": [
            "Le voulé est un barbecue traditionnel mahorais sur la plage",
            "On y grille poissons, brochettes de viande et bananes plantains",
            "Le repas se fait pieds dans le sable, en famille ou entre amis",
            "Le mataba (feuilles de manioc pilé au coco) est souvent servi",
            "C'est le rituel dominical par excellence pour beaucoup de Mahorais",
        ],
        "search_seeds": ["beach barbecue tropical", "grilled fish coconut palm", "family beach picnic", "tropical food beach"],
        "visual_hints": ["beach barbecue with grilled fish, family gathering at sunset, palm trees, vertical 9:16"],
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
        "visual_hints": ["mystical waterfall in tropical forest, mist, fantasy atmosphere, vertical 9:16, photorealistic"],
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
        "visual_hints": ["seven mysterious rock formations at mountain summit, dramatic sky, fantasy atmosphere, vertical 9:16"],
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
        "visual_hints": ["ancient baobab tree silhouette against orange sunset, mystical glow, vertical 9:16, photorealistic"],
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
        "visual_hints": ["sacred natural spring in tropical forest, clear water flowing over rocks, vertical 9:16"],
        "avoid": [],
    },
]

# === FAITS INSOLITES ===
FACTS: list[KnowledgeEntry] = [
    {
        "title": "Mayotte, 101e département français",
        "key_facts": [
            "Mayotte est devenue le 101e département français le 31 mars 2011",
            "Elle est le département le plus jeune de France et le plus peuplé d'Outre-mer après La Réunion",
            "L'île est française depuis 1841 quand le sultan Andriantsoly l'a vendue à la France",
            "En 1974, Mayotte a voté à 63% pour rester française face à l'indépendance des Comores",
            "Plus de 95% de la population est de confession musulmane",
            "Le français est la seule langue officielle, mais le shimaoré et le kibushi sont parlés au quotidien",
        ],
        "search_seeds": ["french overseas territory", "tropical island french flag", "department ceremony", "official building tropical"],
        "visual_hints": ["French flag waving on tropical island, official building, photorealistic vertical"],
        "avoid": ["confondre avec les Comores indépendantes — Mayotte est française"],
    },
    {
        "title": "Mayotte, l'île la plus jeune de France",
        "key_facts": [
            "L'âge médian à Mayotte est de 23 ans, contre 42 ans en métropole",
            "Près de la moitié de la population a moins de 18 ans",
            "Le taux de natalité y est le plus élevé de France, avec environ 6 enfants par femme",
            "La maternité de Mamoudzou est la plus active de France et d'Europe",
            "Près de 10 000 naissances par an pour 320 000 habitants",
        ],
        "search_seeds": ["children playing tropical school", "tropical island youth", "school kids africa", "newborn baby hospital"],
        "visual_hints": ["happy children playing in tropical schoolyard, vertical 9:16, photorealistic"],
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
        "visual_hints": ["children in classroom with books, multilingual learning, vertical 9:16"],
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
        "visual_hints": ["tropical island during rainy season, lush green vegetation, dramatic clouds, vertical 9:16"],
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
        "visual_hints": ["colorful small wooden hut in tropical village, painted with vibrant patterns, vertical 9:16"],
        "avoid": [],
    },
    {
        "title": "La pêche traditionnelle au djarifa",
        "key_facts": [
            "Le djarifa est une pêche collective à pied pratiquée à marée basse",
            "Des dizaines de femmes forment une chaîne sur le platier corallien",
            "Elles tirent ensemble une grande senne à la main",
            "Cette pratique date d'avant la colonisation française",
            "Les prises (poissons, crabes, poulpes) sont partagées équitablement",
            "Le djarifa renforce le lien communautaire entre femmes du village",
        ],
        "search_seeds": ["traditional fishing women beach", "low tide reef walking", "communal fishing africa", "fishing net pulling"],
        "visual_hints": ["women in colorful dress pulling fishing net on tropical beach, low tide, vertical 9:16, photorealistic"],
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
- Le lagon mahorais est l'un des deux doubles lagons fermés au monde
- Le mont Choungui (594m) est l'emblème géographique
- L'ylang-ylang (~80% production mondiale historique) est la fleur emblématique
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
