from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
from db import get_database
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["cart"])

@router.post("/add_to_cart")
async def add_to_cart(item: Dict):
    """Add item to user's cart"""
    try:
        logger.debug(f"Processing add_to_cart for user: {item.get('username', 'unknown')}")
        logger.debug(f"Raw request data: {item}")

        # Validate required fields
        required_fields = ['username', 'product', 'price', 'platform', 'delivery', 'url']
        for field in required_fields:
            if field not in item:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        # Get database instance
        db = await get_database()
        cart_collection = db.cart

        # Check if item already exists in cart
        existing_item = await cart_collection.find_one({
            "username": item["username"],
            "item.product": item["product"]
        })

        if existing_item:
            logger.debug("[DEBUG] Item already exists in cart")
            raise HTTPException(status_code=400, detail="Item already exists in cart")

        # Create cart item
        cart_item = {
            "username": item["username"],
            "item": {
                "product": item["product"],
                "price": float(item["price"]),
                "platform": item["platform"],
                "delivery": int(item["delivery"]),
                "url": item["url"]  # Store the product URL
            },
            "added_at": datetime.utcnow()
        }

        logger.debug(f"Created cart item: {cart_item}")

        # Insert into database
        result = await cart_collection.insert_one(cart_item)
        logger.debug("[DEBUG] Successfully inserted item into database")

        return {
            "message": "Item added to cart",
            "item_id": str(result.inserted_id)
        }

    except HTTPException as he:
        logger.debug(f"[DEBUG] HTTP Exception in add_to_cart: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"Error adding item to cart: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_cart")
async def get_cart(username: str):
    """Get user's cart items"""
    try:
        logger.debug(f"Fetching cart for user: {username}")
        
        # Get database instance
        db = await get_database()
        cart_collection = db.cart

        # Get all items in user's cart
        cursor = cart_collection.find({"username": username})
        cart_items = []
        async for doc in cursor:
            logger.debug(f"Cart item found: {doc['item']}")
            cart_items.append(doc['item'])

        logger.debug(f"Returning {len(cart_items)} items")
        return cart_items

    except Exception as e:
        logger.error(f"Error getting cart: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/remove_from_cart")
async def remove_from_cart(username: str, product: str):
    """Remove item from user's cart"""
    try:
        logger.debug(f"Removing item from cart for user: {username}")
        logger.debug(f"Product to remove: {product}")
        
        # Get database instance
        db = await get_database()
        cart_collection = db.cart

        # Remove item from cart
        result = await cart_collection.delete_one({
            "username": username,
            "item.product": product
        })

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Item not found in cart")

        return {"message": "Item removed from cart"}

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error removing item from cart: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/clear_cart/{username}")
async def clear_cart(username: str):
    """Clear all items from user's cart"""
    try:
        logger.debug(f"Clearing cart for user: {username}")
        
        # Get database instance
        db = await get_database()
        cart_collection = db.cart

        # Remove all items from cart
        result = await cart_collection.delete_many({"username": username})

        return {"message": f"Removed {result.deleted_count} items from cart"}

    except Exception as e:
        logger.error(f"Error clearing cart: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
