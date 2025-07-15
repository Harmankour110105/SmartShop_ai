# 🛍️ SmartShop - Price Comparison App

SmartShop is a web application that helps users find the best deals across multiple e-commerce platforms like Amazon, Zepto, and Blinkit.

## ✨ Features

- 🔐 Secure user authentication with JWT tokens
- 🔍 Smart product search across multiple platforms
- 💰 Automatic price comparison and best deal highlighting
- 🛒 Personal shopping cart with:
  - ➕ Add items to cart
  - ❌ Remove individual items
  - 🧹 Clear entire cart
  - 🚫 Duplicate item prevention

## 🚀 Setup

1. Install dependencies:
   ```bash
   pip install -e .
   ```

2. Start MongoDB:
   Make sure MongoDB is running on your system.

3. Start the backend server:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

4. Start the frontend:
   ```bash
   cd frontend
   streamlit run main.py
   ```

5. Open your browser and navigate to:
   - Frontend: http://localhost:8501
   - Backend API docs: http://localhost:8000/docs

## 🔒 Authentication

The app uses JWT tokens for secure authentication. Tokens are automatically managed by the frontend.

## 🛠️ Tech Stack

- Frontend: Streamlit
- Backend: FastAPI
- Database: MongoDB
- Authentication: JWT with bcrypt password hashing

## 📝 Note

This is an MVP version using mock data for demonstration purposes. In a production environment, you would need to:
1. Set proper environment variables for secrets
2. Implement real e-commerce platform integrations
3. Add proper error handling and logging
4. Set up proper database indexes and security
