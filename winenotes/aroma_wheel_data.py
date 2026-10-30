"""
Wine Tasting Aroma & Flavor Wheel Data Structure.
Faithful reproduction of the classic wine aroma wheel taxonomy:
Primary, Secondary, Tertiary Aromas, and Wine Faults.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional


@dataclass(frozen=True)
class DescriptorInfo:
    name: str
    tier1: str
    tier2: str
    color_hex: str
    text_color_hex: str

    @property
    def rgb(self) -> Tuple[float, float, float]:
        hex_clean = self.color_hex.lstrip("#")
        return (
            int(hex_clean[0:2], 16) / 255.0,
            int(hex_clean[2:4], 16) / 255.0,
            int(hex_clean[4:6], 16) / 255.0,
        )


@dataclass(frozen=True)
class SubcategoryInfo:
    name: str
    tier1: str
    color_hex: str
    text_color_hex: str
    descriptors: Tuple[str, ...]

    @property
    def rgb(self) -> Tuple[float, float, float]:
        hex_clean = self.color_hex.lstrip("#")
        return (
            int(hex_clean[0:2], 16) / 255.0,
            int(hex_clean[2:4], 16) / 255.0,
            int(hex_clean[4:6], 16) / 255.0,
        )


# Hierarchical Wheel Definition in Clockwise Order (matching the visual wheel)
AROMA_CATEGORIES_DATA = [
    # Tier 1: PRIMARY AROMAS
    {
        "tier1": "PRIMARY AROMAS",
        "tier1_color": "#4a7ebb",
        "subcategories": [
            {
                "name": "Flower",
                "color": "#6173b5",
                "text_color": "#ffffff",
                "descriptors": (
                    "Iris", "Peony", "Elderflower", "Acacia", "Lilac",
                    "Jasmine", "Honeysuckle", "Violet", "Lavender", "Rose",
                    "Potpourri", "Hibiscus"
                ),
            },
            {
                "name": "Citrus",
                "color": "#79ba3c",
                "text_color": "#ffffff",
                "descriptors": (
                    "Lime", "Lemon", "Grapefruit", "Orange", "Marmalade"
                ),
            },
            {
                "name": "Tree Fruit",
                "color": "#f2a25b",
                "text_color": "#ffffff",
                "descriptors": (
                    "Quince", "Apple", "Pear", "Nectarine", "Peach", "Apricot", "Persimmon"
                ),
            },
            {
                "name": "Tropical Fruit",
                "color": "#e55223",
                "text_color": "#ffffff",
                "descriptors": (
                    "Pineapple", "Mango", "Guava", "Kiwi", "Lychee", "Bubblegum"
                ),
            },
            {
                "name": "Red Fruit",
                "color": "#b82329",
                "text_color": "#ffffff",
                "descriptors": (
                    "Cranberry", "Red Plum", "Pomegranate", "Sour Cherry",
                    "Strawberry", "Cherry", "Raspberry"
                ),
            },
            {
                "name": "Black Fruit",
                "color": "#60142e",
                "text_color": "#ffffff",
                "descriptors": (
                    "Boysenberry", "Black Currant", "Black Cherry", "Plum",
                    "Blackberry", "Blueberry", "Olive"
                ),
            },
            {
                "name": "Dried Fruit",
                "color": "#9e2a6c",
                "text_color": "#ffffff",
                "descriptors": (
                    "Raisin", "Date", "Fig", "Fruitcake"
                ),
            },
            {
                "name": "Noble Rot",
                "color": "#70a0cb",
                "text_color": "#ffffff",
                "descriptors": (
                    "Beeswax", "Ginger", "Saffron"
                ),
            },
            {
                "name": "Spice",
                "color": "#029b90",
                "text_color": "#ffffff",
                "descriptors": (
                    "White Pepper", "Red Pepper", "Black Pepper", "Cinnamon",
                    "Anise", "Asian 5-Spice", "Fennel", "Eucalyptus", "Mint", "Thyme"
                ),
            },
            {
                "name": "Vegetable",
                "color": "#1d8745",
                "text_color": "#ffffff",
                "descriptors": (
                    "Grass", "Tomato Leaf", "Gooseberry", "Bell Pepper",
                    "Jalapeño", "Green Almond", "Tomato", "Sun Dried Tomato", "Black Tea"
                ),
            },
            {
                "name": "Earth",
                "color": "#54812f",
                "text_color": "#ffffff",
                "descriptors": (
                    "Clay Pot", "Slate", "Wet Gravel", "Potting Soil",
                    "Red Beet", "Volcanic Rocks", "Petroleum"
                ),
            },
        ],
    },
    # Tier 1: SECONDARY AROMAS
    {
        "tier1": "SECONDARY AROMAS",
        "tier1_color": "#8fa82b",
        "subcategories": [
            {
                "name": "Microbial",
                "color": "#a2b826",
                "text_color": "#ffffff",
                "descriptors": (
                    "Butter", "Cream", "Sourdough", "Lager", "Truffle", "Mushroom"
                ),
            },
        ],
    },
    # Tier 1: TERTIARY AROMAS
    {
        "tier1": "TERTIARY AROMAS",
        "tier1_color": "#af742d",
        "subcategories": [
            {
                "name": "Oak Aging",
                "color": "#ba7c2b",
                "text_color": "#ffffff",
                "descriptors": (
                    "Vanilla", "Coconut", "Baking Spices", "Cigar Box", "Smoke", "Dill"
                ),
            },
            {
                "name": "General Aging",
                "color": "#be6e3a",
                "text_color": "#ffffff",
                "descriptors": (
                    "Dried Fruit", "Nuts", "Tobacco", "Coffee", "Cocoa", "Leather"
                ),
            },
        ],
    },
    # Tier 1: FAULTS
    {
        "tier1": "FAULTS",
        "tier1_color": "#8f4453",
        "subcategories": [
            {
                "name": "TCA (Corked)",
                "color": "#9d6953",
                "text_color": "#ffffff",
                "descriptors": (
                    "Musty Cardboard", "Wet Dog"
                ),
            },
            {
                "name": "Sulfides & Mercaptans",
                "color": "#cc5b40",
                "text_color": "#ffffff",
                "descriptors": (
                    "Cured Meat", "Boiled Eggs", "Burnt Rubber", "Match Box",
                    "Garlic", "Onion", "Cat Pee"
                ),
            },
            {
                "name": "Brettanomyces",
                "color": "#9f4350",
                "text_color": "#ffffff",
                "descriptors": (
                    "Black Cardamom", "Band-Aid", "Sweaty Leather Saddle", "Horse Manure"
                ),
            },
            {
                "name": "Cooked",
                "color": "#902c55",
                "text_color": "#ffffff",
                "descriptors": (
                    "Toffee", "Stewed Fruit"
                ),
            },
            {
                "name": "Volatile Acidity",
                "color": "#6e2d78",
                "text_color": "#ffffff",
                "descriptors": (
                    "Vinegar", "Balsamic"
                ),
            },
        ],
    },
]

# Build flat lookups
SUBCATEGORIES: List[SubcategoryInfo] = []
DESCRIPTOR_MAP: Dict[str, DescriptorInfo] = {}
CATEGORY_MAP: Dict[str, SubcategoryInfo] = {}
ALL_DESCRIPTORS_ORDERED: List[str] = []

for tier1_group in AROMA_CATEGORIES_DATA:
    t1_name = tier1_group["tier1"]
    for subcat in tier1_group["subcategories"]:
        s_info = SubcategoryInfo(
            name=subcat["name"],
            tier1=t1_name,
            color_hex=subcat["color"],
            text_color_hex=subcat["text_color"],
            descriptors=subcat["descriptors"],
        )
        SUBCATEGORIES.append(s_info)
        CATEGORY_MAP[s_info.name] = s_info

        for desc in subcat["descriptors"]:
            # Note: "Dried Fruit" appears in both Primary (Dried Fruit) and Tertiary (General Aging).
            # To handle gracefully, DESCRIPTOR_MAP stores the primary or first occurrence.
            if desc not in DESCRIPTOR_MAP:
                d_info = DescriptorInfo(
                    name=desc,
                    tier1=t1_name,
                    tier2=s_info.name,
                    color_hex=s_info.color_hex,
                    text_color_hex=s_info.text_color_hex,
                )
                DESCRIPTOR_MAP[desc] = d_info
            ALL_DESCRIPTORS_ORDERED.append(desc)


def get_descriptor_info(name: str) -> Optional[DescriptorInfo]:
    """Retrieve metadata for a given descriptor."""
    return DESCRIPTOR_MAP.get(name)


def get_descriptor_css_class(name: str) -> str:
    """Return CSS badge class for a given descriptor based on its aroma family."""
    info = get_descriptor_info(name)
    if not info:
        return "aroma-cat-default"
    mapping = {
        "Flower": "aroma-cat-flower",
        "Citrus": "aroma-cat-citrus",
        "Tree Fruit": "aroma-cat-tree-fruit",
        "Tropical Fruit": "aroma-cat-tropical-fruit",
        "Red Fruit": "aroma-cat-red-fruit",
        "Black Fruit": "aroma-cat-black-fruit",
        "Dried Fruit": "aroma-cat-dried-fruit",
        "Noble Rot": "aroma-cat-noble-rot",
        "Spice": "aroma-cat-spice",
        "Vegetable": "aroma-cat-vegetable",
        "Earth": "aroma-cat-earth",
        "Microbial": "aroma-cat-microbial",
        "Oak Aging": "aroma-cat-oak-aging",
        "General Aging": "aroma-cat-general-aging",
        "TCA (Corked)": "aroma-cat-tca",
        "Sulfides & Mercaptans": "aroma-cat-sulfides",
        "Brettanomyces": "aroma-cat-brettanomyces",
        "Cooked": "aroma-cat-cooked",
        "Volatile Acidity": "aroma-cat-volatile-acidity",
    }
    return mapping.get(info.tier2, "aroma-cat-default")


def format_keywords_sentence(keywords: List[str]) -> str:
    """Format keywords into a smooth English tasting sentence."""
    if not keywords:
        return ""
    clean = [k.strip() for k in keywords if k.strip()]
    if not clean:
        return ""
    if len(clean) == 1:
        return f"Prominent notes of {clean[0].lower()}."
    elif len(clean) == 2:
        return f"Expressive notes of {clean[0].lower()} and {clean[1].lower()}."
    else:
        all_but_last = ", ".join(k.lower() for k in clean[:-1])
        return f"Expressive aromas and palate of {all_but_last}, and {clean[-1].lower()}."
