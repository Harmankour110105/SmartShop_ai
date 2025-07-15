# SmartShop API

A price comparison API that scrapes and compares prices from multiple e-commerce platforms including Amazon, Flipkart, and Meesho.

## Features

* Multi-platform price comparison (Amazon, Flipkart, Meesho)
* Shopping cart functionality
* JWT token-based authentication
* Clean and modern UI with Streamlit frontend

## Project Structure

```
smartshop-api/
├── backend/           # Backend API endpoints and logic
│   ├── auth.py       # Authentication handling
│   ├── cart.py       # Shopping cart operations
│   ├── db.py         # Database connections
│   ├── main.py       # Main FastAPI application
│   ├── mockdata.py   # Mock data for testing
│   └── queryhandler.py # Query processing
├── frontend/         # Streamlit frontend application
└── pyproject.toml    # Project dependencies and configuration
```

## Recent Updates

* Implemented JWT token-based authentication
* Added cart deduplication to prevent duplicate items
* Enhanced cart management with clear and remove functionality
* Improved UI with minimum price highlighting
* Removed orders functionality in favor of direct e-commerce links

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the backend:
```bash
cd backend
uvicorn main:app --reload
```

3. Run the frontend:
```bash
cd frontend
streamlit run main.py
```

## Note
Currently, scraping works successfully with Amazon and Flipkart. Meesho access is currently blocked (403 errors).
