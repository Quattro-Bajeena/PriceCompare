# Price Compare

A simple web application that demonstrates price optimization in a shopping cart. The application simulates an online marketplace where users can compare prices from different sellers and optimize their cart for the best total price, taking into account shipping costs.

## Features

- Browse products from multiple sellers
- Add items to cart
- View cart contents
- Optimize cart for best total price (including shipping costs)
- Simple and clean interface

## Setup

1. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database with sample data:
```bash
python populate_db.py
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to `http://localhost:5000`

## How to Use

1. Browse products on the home page
2. Add items to your cart by clicking "Add to Cart" on any offer
3. View your cart by clicking "View Cart" in the header
4. Use the "Optimize Cart" button to find the best combination of sellers for your items
5. Remove items from your cart using the "Remove" button

## Sample Data

The application comes pre-populated with sample data including:
- 5 gaming-related products
- 5 different sellers with varying shipping costs
- Multiple offers per product from different sellers 