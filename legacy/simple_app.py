#!/usr/bin/env python3

import mysql.connector
import os
from dotenv import load_dotenv
from decimal import Decimal
import sys

print(sys.stdout.encoding)

load_dotenv()


def create_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=os.getenv("DB_PORT"),
        ssl_ca=os.getenv("DB_CA"),
        ssl_verify_cert=True,
        ssl_verify_identity=True,
        charset="utf8mb4",
        collation="utf8mb4_unicode_ci",
    )


def insert_wine(conn, wine_data):
    query = """
    INSERT INTO wines (
        wine_name, winery, country, region, sub_region, vintage,
        color_style, grape_variety, abv, price, tasting_date,
        rating, tasting_notes, serving_temperature, aging_potential,
        food_pairing, purchase_location, bottle_size, closure_type,
        organic, biodynamic    
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    try:
        cursor = conn.cursor()
        cursor.execute(query, wine_data)
        conn.commit()
        print("Wine added successfully!")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
    finally:
        cursor.close()


def get_wine_input():
    print("\nEnter Wine Details:")
    return (
        input("Wine Name: "),
        input("Winery: "),
        input("Country: "),
        input("Region (optional): ") or None,
        input("Sub-region (optional): ") or None,
        input("Vintage (YYYY) (optional): ") or None,
        input("Color Style [Red/White/Rosé/Sparkling/Dessert/Fortified]: "),
        input("Grape Variety/Varieties (comma-separated): "),
        Decimal(input("ABV (e.g., 13.5): ")),
        Decimal(input("Price (optional): ") or 0),
        input("Tasting Date (YYYY-MM-DD): "),
        int(input("Rating (0-100): ")),
        input("Tasting Notes: "),
        input("Serving Temperature (optional): ") or None,
        input("Aging Potential (optional): ") or None,
        input("Food Pairing (optional): ") or None,
        input("Purchase Location (optional): ") or None,
        Decimal(input("Bottle Size (liters, default 0.75): ") or 0.75),
        input("Closure Type [Cork/Screwcap/Glass/Synthetic]: "),
        input("Organic? [y/N]: ").lower() == "y",
        input("Biodynamic? [y/N]: ").lower() == "y",
    )


if __name__ == "__main__":
    conn = create_connection()
    try:
        while True:
            wine_data = get_wine_input()
            insert_wine(conn, wine_data)
            if input("Add another? [y/N]: ").lower() != "y":
                break
    except KeyboardInterrupt:
        print("\nCancelled!")
        conn.rollback()
    finally:
        conn.close()
