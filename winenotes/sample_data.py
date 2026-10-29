"""
Curated sample wine tasting notes for initial demonstration.
"""

from winenotes.models import Wine

SAMPLE_WINES = [
    Wine(
        wine_name="Château Pontet-Canet",
        winery="Château Pontet-Canet",
        country="France",
        region="Bordeaux",
        sub_region="Pauillac (5ème Grand Cru Classé)",
        vintage=2015,
        color_style="Red",
        grape_variety="65% Cabernet Sauvignon, 30% Merlot, 4% Cabernet Franc, 1% Petit Verdot",
        abv=14.0,
        price=135.0,
        tasting_date="2026-05-18",
        rating=97,
        tasting_notes=(
            "Deep garnet-purple color. Sensational bouquet of crème de cassis, blackberry compote, "
            "graphite, dried violets, and cigar box. Full-bodied with breathtaking depth, silky yet "
            "commanding tannins, vibrant acidity, and an extraordinarily long mineral finish. "
            "Biodynamic farming shows in its pure, electric energy."
        ),
        serving_temperature=17,
        aging_potential="2025 - 2045+",
        food_pairing="Roasted rack of lamb with rosemary and garlic jus, dry-aged ribeye steak.",
        purchase_location="Berry Bros. & Rudd",
        bottle_size=0.75,
        closure_type="Cork",
        organic=True,
        biodynamic=True,
    ),
    Wine(
        wine_name="Gevrey-Chambertin 'Clos Saint-Jacques' 1er Cru",
        winery="Domaine Armand Rousseau",
        country="France",
        region="Burgundy",
        sub_region="Côte de Nuits / Gevrey-Chambertin",
        vintage=2019,
        color_style="Red",
        grape_variety="100% Pinot Noir",
        abv=13.5,
        price=450.0,
        tasting_date="2026-06-22",
        rating=98,
        tasting_notes=(
            "Translucent ruby hue. Breathtakingly perfumed with wild cherries, crushed rose petals, "
            "blood orange rind, forest floor, and subtle truffles. On the palate, pure lace and velvet—"
            "weightless power, laser-like precision, and a finish that echoes for minutes."
        ),
        serving_temperature=15,
        aging_potential="2027 - 2050",
        food_pairing="Duck breast with morel mushrooms, roasted squab, aged Comté cheese.",
        purchase_location="Private Cellar Allocation",
        bottle_size=0.75,
        closure_type="Cork",
        organic=True,
        biodynamic=False,
    ),
    Wine(
        wine_name="Sancerre 'Monts Damnés'",
        winery="Domaine François Cotat",
        country="France",
        region="Loire Valley",
        sub_region="Chavignol / Sancerre",
        vintage=2021,
        color_style="White",
        grape_variety="100% Sauvignon Blanc",
        abv=13.5,
        price=75.0,
        tasting_date="2026-07-12",
        rating=94,
        tasting_notes=(
            "Pale straw with green highlights. Flinty crushed-rock minerality immediately takes center stage, "
            "accompanied by lemon curd, white peach, kaffir lime, and beeswax. Rich, textured mid-palate "
            "backed by chiseled, mouthwatering limestone acidity."
        ),
        serving_temperature=10,
        aging_potential="2024 - 2036",
        food_pairing="Pan-seared Dover sole meunière, goat cheese (Crottin de Chavignol), oysters.",
        purchase_location="The Fine Wine Exchange",
        bottle_size=0.75,
        closure_type="Cork",
        organic=True,
        biodynamic=False,
    ),
    Wine(
        wine_name="Grande Cuvée 170ème Édition Brut",
        winery="Champagne Krug",
        country="France",
        region="Champagne",
        sub_region="Montagne de Reims",
        vintage=None,
        color_style="Sparkling",
        grape_variety="51% Pinot Noir, 38% Chardonnay, 11% Meunier",
        abv=12.5,
        price=240.0,
        tasting_date="2026-08-01",
        rating=96,
        tasting_notes=(
            "Luminous gold with superfine, endless effervescence. Aromas of toasted brioche, marzipan, "
            "roasted hazelnut, candied citrus peel, and baked apple. The mousse is pillowy and luxurious, "
            "with profound depth from 195 reserve wines spanning 12 vintages."
        ),
        serving_temperature=9,
        aging_potential="Drink now or cellar 15+ years",
        food_pairing="Ibérico bellota ham, turbot with white truffle butter, aged parmesan gougères.",
        purchase_location="Majestic Wine",
        bottle_size=0.75,
        closure_type="Cork",
        organic=False,
        biodynamic=False,
    ),
    Wine(
        wine_name="Bandol Rosé",
        winery="Domaine Tempier",
        country="France",
        region="Provence",
        sub_region="Bandol",
        vintage=2022,
        color_style="Rosé",
        grape_variety="50% Mourvèdre, 28% Grenache, 20% Cinsault, 2% Carignan",
        abv=13.0,
        price=36.0,
        tasting_date="2026-08-15",
        rating=93,
        tasting_notes=(
            "Intense pale peach-salmon color. Notes of blood peach, garrigue herbs, pomegranate, "
            "and subtle pink peppercorn. A gastronomic rosé with serious phenolic grip, savory undertones, "
            "and remarkable salinity on the refreshing finish."
        ),
        serving_temperature=11,
        aging_potential="Drink now - 2030",
        food_pairing="Bouillabaisse, grilled red mullet, provencal tapenade on crusty sourdough.",
        purchase_location="Local Wine Merchant",
        bottle_size=0.75,
        closure_type="Cork",
        organic=True,
        biodynamic=True,
    ),
    Wine(
        wine_name="Barolo 'Bricco delle Viole'",
        winery="G.D. Vajra",
        country="Italy",
        region="Piedmont",
        sub_region="Barolo / Vergne",
        vintage=2018,
        color_style="Red",
        grape_variety="100% Nebbiolo",
        abv=14.5,
        price=85.0,
        tasting_date="2026-09-04",
        rating=95,
        tasting_notes=(
            "Luminous translucent ruby. Ethereal nose of sour red cherries, dried rose petals, "
            "tar, licorice, and orange peel. Taut, noble Nebbiolo tannins with striking freshness and "
            "salivating minerality from Vajra's highest altitude vineyard."
        ),
        serving_temperature=16,
        aging_potential="2025 - 2045",
        food_pairing="Tajarin pasta with shaved white truffles, slow-braised osso buco.",
        purchase_location="Enoteca Pinchiorri Store",
        bottle_size=0.75,
        closure_type="Cork",
        organic=True,
        biodynamic=False,
    ),
]
