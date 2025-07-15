import streamlit as st
import requests
from datetime import datetime, timedelta
import logging
import time
import json
import urllib3

# Set page config first, before any other Streamlit commands
st.set_page_config(page_title="SmartShop – Price Comparator", layout="wide")

# Custom CSS for background and minimal styling

st.markdown(
    """
    <style>
    .stApp {
        background-image: url("https://images.pexels.com/photos/6250874/pexels-photo-6250874.jpeg");
        background-size: cover;
        background-position: right center;
        background-attachment: fixed;
    }

    .block-container {
        background-color: rgba(255, 255, 255, 0.85); /* Light overlay for better readability */
        padding: 2rem;
        border-radius: 15px;
    }

    h1, h2, h3 {
        color: #1a1a1a;
    }

    .stButton>button {
        font-weight: bold;
        border-radius: 8px;
        background-color: #4CAF50;
        color: white;
    }

    input, textarea {
        background-color: rgba(255,255,255,0.9) !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)






# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def handle_add_to_cart(item):
    """Callback function for Add to Cart button clicks"""
    logger.info("=== Add to Cart button clicked ===")
    logger.info(f"Selected item: {item}")
    st.session_state.clicked_add_to_cart = True
    st.session_state.selected_item = item

# Initialize session state
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "cart_items" not in st.session_state:
    st.session_state.cart_items = []
if "last_added_item" not in st.session_state:
    st.session_state.last_added_item = None
if "clicked_add_to_cart" not in st.session_state:
    st.session_state.clicked_add_to_cart = False
if "selected_item" not in st.session_state:
    st.session_state.selected_item = None

def add_to_cart_callback(item):
    """Add an item to the cart"""
    try:
        # Prepare request
        cart_item = {
            "username": st.session_state.username,
            "product": str(item["product"]),
            "price": float(item["price"]),
            "platform": str(item["platform"]),
            "delivery": int(item["delivery"]),
            "url": str(item.get("url", ""))
        }
        
        logger.info(f"Adding to cart: {cart_item}")
        
        # Make API call
        response = requests.post(
            f"{BACKEND_URL}/add_to_cart",
            json=cart_item,
            timeout=5
        )
        
        if response.status_code == 200:
            st.success(f"✅ Added {item['product']} to cart!")
            if "cart_items" not in st.session_state:
                st.session_state.cart_items = []
            st.session_state.cart_items.append(cart_item)
            st.rerun()
            
        elif response.status_code == 400:
            st.warning("⚠️ This item is already in your cart")
            
        else:
            st.error("❌ Failed to add item to cart")
            logger.error(f"Error: {response.text}")
            
    except Exception as e:
        logger.error(f"Error adding to cart: {str(e)}")
        st.error("❌ Something went wrong")

# Backend URL
BACKEND_URL = "http://localhost:8000"

def is_token_valid():
    return st.session_state.access_token is not None

def get_headers():
    if st.session_state.access_token:
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
        logger.info(f"Using headers: {headers}")
        return headers
    logger.warning("No access token found!")
    return {}

st.sidebar.title("SmartShop Assistant")

# Check if user is logged in
if not st.session_state.access_token:
    # If not logged in, only show Login and Signup options
    page = st.sidebar.radio("Select", ["Login", "Signup"])
else:
    # If logged in, show all options
    page = st.sidebar.radio("Select", ["Search", "Cart"])
    # Show logged in user and logout button
    st.sidebar.success(f"Logged in as: {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.access_token = None
        st.session_state.username = None
        st.session_state.cart_items = []
        st.rerun()

if page == "Login":
    st.header("Login")
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        try:
            # Log the login attempt
            logger.info(f"Attempting login for user: {user}")
            
            # Send login request with form data
            res = requests.post(
                f"{BACKEND_URL}/token",
                data={
                    "grant_type": "password",  # Required by OAuth2 spec
                    "username": user,
                    "password": pwd
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
            
            # Log the response
            logger.info(f"Login response status: {res.status_code}")
            
            if res.status_code == 200:
                token_data = res.json()
                st.session_state.access_token = token_data["access_token"]
                st.session_state.username = user
                
                # Log successful login
                logger.info(f"Login successful for user: {user}")
                logger.info(f"Access token received (first 10 chars): {st.session_state.access_token[:10]}...")
                
                st.success("Logged in successfully!")
                st.rerun()
            else:
                error_msg = res.json().get("detail", "Login failed. Please check your username and password.")
                logger.error(f"Login failed with status {res.status_code}: {res.text}")
                st.error(error_msg)
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            st.error(f"Error: {str(e)}")

elif page == "Signup":
    st.header("Signup")
    user = st.text_input("Choose Username")
    pwd = st.text_input("Choose Password", type="password")
    if st.button("Signup"):
        try:
            res = requests.post(
                f"{BACKEND_URL}/signup",
                json={"username": user, "password": pwd}
            )
            if res.status_code == 200:
                st.success("Account created! Please login.")
            else:
                st.error("Signup failed")
        except Exception as e:
            st.error(f"Error: {str(e)}")

elif page == "Search":
    st.title("SmartShop")
    
    # Create two columns for search bar and mic button
    search_col, mic_col = st.columns([6, 1])
    
    with search_col:
        # Initialize search input in session state if not exists
        if "search_input" not in st.session_state:
            st.session_state.search_input = ""
        user_input = st.text_input("🔍 What are you looking for?", 
                                 value=st.session_state.search_input,
                                 placeholder="e.g. I want Amul butter 500g")
    
    with mic_col:
        if st.button("🎤", help="Click to use voice search"):
            with st.spinner("Listening... Speak now"):
                try:
                    response = requests.post("http://localhost:8000/recognize/mic")
                    if response.status_code == 200:
                        text = response.json()["text"]
                        st.success(f"Recognized: {text}")
                        # Update session state with recognized text
                        st.session_state.search_input = text
                        # Rerun to update the UI
                        st.rerun()
                    else:
                        st.error("Failed to recognize speech")
                except Exception as e:
                    st.error(f"Error during voice search: {str(e)}")
    
    if st.button("Find Best Deal") or st.session_state.search_input:
        logger.info("Search initiated")
        search_query = user_input or st.session_state.search_input
        if search_query:
            with st.spinner("Comparing prices across platforms..."):
                try:
                    response = requests.post(f"{BACKEND_URL}/query", json={"query": search_query})
                    result = response.json()
                    
                    if result.get("results"):
                        st.success("Here's what we found!")
                        
                        # Display each result
                        for idx, item in enumerate(result["results"]):
                            is_cheapest = item['price'] == min(i['price'] for i in result["results"])
                            
                            # Create a container for each item
                            with st.container():
                                st.markdown("---")
                                
                                # Create columns for better layout
                                img_col, info_col, action_col = st.columns([2, 4, 2])
                                
                                with img_col:
                                    if item.get('image_url'):
                                        st.image(item['image_url'], width=150)
                                    else:
                                        st.markdown("🖼️ No image available")
                                
                                with info_col:
                                    # Product title and platform
                                    if is_cheapest:
                                        st.markdown(f"### ✨ {item['product']} (Best Price!)")
                                    else:
                                        st.markdown(f"### {item['product']}")
                                    
                                    # Product details
                                    st.markdown(f"**Platform**: {item['platform']}")
                                    st.markdown(f"**Price**: ₹{item['price']}")
                                    st.markdown(f"**Delivery**: {item['delivery']} mins")
                                    
                                    # Direct link to product
                                    if item.get('url'):
                                        st.markdown(f"[🔗 View on {item['platform']}]({item['url']})")
                                
                                with action_col:
                                    # Add to Cart button
                                    if st.button("🛒 Add to Cart", key=f"add_{idx}", on_click=handle_add_to_cart, args=(item,)):
                                        logger.info(f"Button clicked for item: {item['product']}")
                                    
                                    # Buy Now button (redirects to platform)
                                    if item.get('url'):
                                        st.markdown(f"[🛍️ Buy Now]({item['url']})")
                        
                        # Handle add to cart action
                        if st.session_state.clicked_add_to_cart and st.session_state.selected_item:
                            logger.info("Processing add to cart action")
                            add_to_cart_callback(st.session_state.selected_item)
                            # Reset the state
                            st.session_state.clicked_add_to_cart = False
                            st.session_state.selected_item = None
                    
                    else:
                        st.info("No results found. Try a different search!")

                except Exception as e:
                    logger.error(f"Search error: {str(e)}")
                    st.error(f"Error: {str(e)}")

elif page == "Cart":
    st.title("Your Cart")
    
    try:
        # Get cart items
        response = requests.get(f"{BACKEND_URL}/get_cart?username={st.session_state.username}")
        
        if response.status_code == 200:
            cart_items = response.json()
            
            if not cart_items:
                st.info("Your cart is empty. Add some items from the Search page!")
            else:
                total = sum(item["price"] for item in cart_items)
                
                st.write(f"Total Items: {len(cart_items)}")
                st.write(f"Total Value: ₹{total:.2f}")
                
                for idx, item in enumerate(cart_items):
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                        
                        with col1:
                            st.markdown(f"### 🛍️ {item['product']}")
                            st.markdown(f"**Platform**: {item['platform']}")
                            if item.get('url'):
                                st.markdown(f"[🔗 View on {item['platform']}]({item['url']})")
                        
                        with col2:
                            st.markdown(f"**₹{item['price']}**")
                        
                        with col3:
                            st.markdown(f"⏱️ {item['delivery']} mins")
                        
                        with col4:
                            remove_key = f"remove_btn_{item['product']}_{item['platform']}"
                            if st.button("🗑️ Remove", key=remove_key):
                                try:
                                    with st.spinner("Removing item..."):
                                        # Use query parameters instead of path parameters
                                        remove_response = requests.delete(
                                            f"{BACKEND_URL}/remove_from_cart",
                                            params={
                                                "username": st.session_state.username,
                                                "product": item['product']
                                            }
                                        )
                                    
                                    if remove_response.status_code == 200:
                                        st.success("✅ Item removed!")
                                        time.sleep(0.5)
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to remove item. Please try again.")
                                        logger.error(f"Error removing item: {remove_response.text}")
                                except Exception as e:
                                    st.error("❌ Something went wrong. Please try again.")
                                    logger.error(f"Error removing item: {str(e)}")
                
                if st.button("🗑️ Clear Cart", key="clear_cart_btn"):
                    try:
                        with st.spinner("Clearing cart..."):
                            clear_response = requests.delete(
                                f"{BACKEND_URL}/clear_cart/{st.session_state.username}"
                            )
                        
                        if clear_response.status_code == 200:
                            st.success("✅ Cart cleared!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ Failed to clear cart. Please try again.")
                            logger.error(f"Error clearing cart: {clear_response.text}")
                    except Exception as e:
                        st.error("❌ Something went wrong. Please try again.")
                        logger.error(f"Error clearing cart: {str(e)}")
                        
        else:
            st.error("❌ Failed to load cart. Please try again.")
            logger.error(f"Error loading cart: {response.text}")
            
    except Exception as e:
        st.error("❌ Something went wrong. Please try again.")
        logger.error(f"Error loading cart: {str(e)}")
