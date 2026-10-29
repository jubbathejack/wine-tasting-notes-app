#!/usr/bin/env python3

from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, DECIMAL, Date, Enum
from config import Config
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

class Wine(db.Model):
    __tablename__ = 'wines'
    wine_id = Column(Integer, primary_key=True)
    wine_name = Column(String(100), nullable=False)
    winery = Column(String(100), nullable=False)
    country = Column(String(50), nullable=False)
    region = Column(String(50))
    sub_region = Column(String(50))
    vintage = Column(Integer)
    color_style = Column(Enum("Red","White", "Rosé", "Sparkling", "Dessert", "Fortified"), nullable=False)
    grape_variety = Column(String(100), nullable=False)
    abv = Column(DECIMAL, nullable=False)
    price = Column(DECIMAL, nullable=False)
    tasting_date = Column(Date, nullable=False)
    rating = Column(Integer, nullable=False)
    tasting_notes = Column(Text, nullable=False)
    serving_temperature = Column(Integer)
    aging_potential = Column(String(50))
    food_pairing = Column(Text)
    purchase_location = Column(String(100))
    bottle_size = Column(DECIMAL)
    closure_type = Column(Enum("Cork", "Screwcap", "Glass", "Synthetic"))
    organic = Column(String(1))
    biodynamic = Column(String(1))

    def __repr__(self):
        return f'<Wine {self.wine_name}>'
    
@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    wines = Wine.query.paginate(page=page, per_page=10)
    return render_template('index.html', wines=wines)
    
@app.route('/wine/<int:wine_id>')
def wine_detail(wine_id):
    wine = Wine.query.get_or_404(wine_id)
    return render_template('wine_detail.html', wine=wine)
    
@app.route('/add', methods=['GET', 'POST'])
def add_wine():
    current_year = datetime.now().year
    if request.method == 'POST':
        price = request.form.get('price', 0.0)  # Default to 0.0 if missing
        try:
            price_value = float(price) if price.strip() else None
        except AttributeError:  # Handle case where price is None
            price_value = None
        new_wine = Wine(
            # Required fields
            wine_name=request.form['wine_name'],
            winery=request.form['winery'],
            country=request.form['country'],
            tasting_date=request.form['tasting_date'],
            rating=int(request.form['rating']),
            tasting_notes=request.form['tasting_notes'],
            color_style=request.form['color_style'],
            
            # Optional fields with proper handling
            price=price_value,
            region=request.form.get('region'),
            sub_region=request.form.get('sub_region'),
            vintage=int(request.form.get('vintage')) if request.form.get('vintage') else None,

            grape_variety=request.form.get('grape_variety'),
            abv=float(request.form['abv']) if request.form['abv'].strip() else None,
            serving_temperature=request.form.get('serving_temperature'),
            aging_potential=request.form.get('aging_potential'),
            food_pairing=request.form.get('food_pairing'),
            purchase_location=request.form.get('purchase_location'),
            bottle_size=request.form.get('bottle_size'),
            closure_type=request.form.get('closure_type'),
            organic=request.form.get('organic'),
            biodynamic=request.form.get('biodynamic')
        )
        db.session.add(new_wine)
        db.session.commit()
        return redirect('/')
    return render_template('add_wine.html', current_year=current_year)

if __name__ == '__main__':
    app.run(debug=True)