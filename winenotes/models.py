"""
Data models and validation for Wine Tasting Notes.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any

COLOR_STYLES = ["Red", "White", "Rosé", "Sparkling", "Dessert", "Fortified"]
CLOSURE_TYPES = ["Cork", "Screwcap", "Glass", "Synthetic"]

@dataclass
class Wine:
    wine_name: str
    winery: str
    country: str
    tasting_notes: str
    color_style: str = "Red"
    grape_variety: str = ""
    rating: int = 90
    tasting_date: str = field(default_factory=lambda: date.today().isoformat())
    vintage: Optional[int] = None
    region: Optional[str] = None
    sub_region: Optional[str] = None
    abv: Optional[float] = None
    price: Optional[float] = None
    serving_temperature: Optional[int] = None
    aging_potential: Optional[str] = None
    food_pairing: Optional[str] = None
    purchase_location: Optional[str] = None
    bottle_size: Optional[float] = 0.75
    closure_type: Optional[str] = "Cork"
    organic: bool = False
    biodynamic: bool = False
    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @property
    def vintage_display(self) -> str:
        return str(self.vintage) if self.vintage else "NV (Non-Vintage)"

    @property
    def rating_stars(self) -> str:
        """Return a 5-star visual representation for ratings 0-100."""
        # 95-100: ★★★★★
        # 88-94:  ★★★★☆
        # 80-87:  ★★★☆☆
        # 70-79:  ★★☆☆☆
        # <70:    ★☆☆☆☆
        if self.rating >= 95:
            return "★★★★★"
        elif self.rating >= 88:
            return "★★★★☆"
        elif self.rating >= 80:
            return "★★★☆☆"
        elif self.rating >= 70:
            return "★★☆☆☆"
        else:
            return "★☆☆☆☆"

    @property
    def rating_level(self) -> str:
        """Human-readable classification."""
        if self.rating >= 95:
            return "Classic / Extraordinary"
        elif self.rating >= 90:
            return "Outstanding"
        elif self.rating >= 85:
            return "Very Good"
        elif self.rating >= 80:
            return "Good"
        else:
            return "Mediocre / Below Average"

    @property
    def style_badge_class(self) -> str:
        mapping = {
            "Red": "style-badge-red",
            "White": "style-badge-white",
            "Rosé": "style-badge-rose",
            "Sparkling": "style-badge-sparkling",
            "Dessert": "style-badge-dessert",
            "Fortified": "style-badge-fortified",
        }
        return mapping.get(self.color_style, "style-badge-default")

    @property
    def location_summary(self) -> str:
        parts = [p for p in [self.sub_region, self.region, self.country] if p]
        return ", ".join(parts) if parts else "Unknown origin"

    def validate(self) -> List[str]:
        errors = []
        if not self.wine_name or not self.wine_name.strip():
            errors.append("Wine name is required.")
        if not self.winery or not self.winery.strip():
            errors.append("Winery / Producer is required.")
        if not self.country or not self.country.strip():
            errors.append("Country is required.")
        if not (0 <= self.rating <= 100):
            errors.append("Rating must be between 0 and 100.")
        if self.color_style not in COLOR_STYLES:
            errors.append(f"Color style must be one of {', '.join(COLOR_STYLES)}.")
        if self.vintage is not None:
            current_year = datetime.now().year + 1
            if self.vintage < 1800 or self.vintage > current_year:
                errors.append(f"Vintage must be between 1800 and {current_year}.")
        if self.abv is not None and (self.abv < 0 or self.abv > 100):
            errors.append("ABV must be between 0% and 100%.")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> Wine:
        return cls(
            id=row.get("id"),
            wine_name=row.get("wine_name", ""),
            winery=row.get("winery", ""),
            country=row.get("country", ""),
            region=row.get("region"),
            sub_region=row.get("sub_region"),
            vintage=row.get("vintage"),
            color_style=row.get("color_style", "Red"),
            grape_variety=row.get("grape_variety", ""),
            abv=float(row["abv"]) if row.get("abv") is not None else None,
            price=float(row["price"]) if row.get("price") is not None else None,
            tasting_date=row.get("tasting_date", date.today().isoformat()),
            rating=int(row.get("rating", 90)),
            tasting_notes=row.get("tasting_notes", ""),
            serving_temperature=row.get("serving_temperature"),
            aging_potential=row.get("aging_potential"),
            food_pairing=row.get("food_pairing"),
            purchase_location=row.get("purchase_location"),
            bottle_size=float(row["bottle_size"]) if row.get("bottle_size") is not None else 0.75,
            closure_type=row.get("closure_type", "Cork"),
            organic=bool(row.get("organic", 0)),
            biodynamic=bool(row.get("biodynamic", 0)),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )
