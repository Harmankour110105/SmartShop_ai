import logging

def get_mock_results(product_info: dict) -> list:
    """Generate mock results based on product info."""
    logger = logging.getLogger(__name__)
    
    # Base mock data with more products
    mock_data = [
        {
            "product": "Amul Gold Milk 500ml",
            "price": 30.00,
            "platform": "BigBasket",
            "delivery": 30
        },
        {
            "product": "Amul Gold Milk 500ml",
            "price": 32.00,
            "platform": "Grofers",
            "delivery": 45
        },
        {
            "product": "Amul Taaza Milk 500ml",
            "price": 25.00,
            "platform": "BigBasket",
            "delivery": 30
        },
        {
            "product": "Amul Taaza Milk 500ml",
            "price": 26.00,
            "platform": "Grofers",
            "delivery": 45
        },
        {
            "product": "Amul Butter 500g",
            "price": 250.00,
            "platform": "BigBasket",
            "delivery": 30
        },
        {
            "product": "Amul Butter 500g",
            "price": 245.00,
            "platform": "Grofers",
            "delivery": 45
        },
        {
            "product": "Mother Dairy Full Cream Milk 500ml",
            "price": 28.00,
            "platform": "BigBasket",
            "delivery": 30
        },
        {
            "product": "Mother Dairy Full Cream Milk 500ml",
            "price": 27.00,
            "platform": "Grofers",
            "delivery": 45
        },
        {
            "product": "Mother Dairy Toned Milk 500ml",
            "price": 24.00,
            "platform": "BigBasket",
            "delivery": 30
        },
        {
            "product": "Mother Dairy Toned Milk 500ml",
            "price": 23.00,
            "platform": "Grofers",
            "delivery": 45
        }
    ]
    
    # Get search terms from query
    query = product_info.get("query", "").lower()
    search_terms = query.split()
    logger.info(f"[DEBUG] Search terms: {search_terms}")
    
    # Handle unit conversions
    unit_mappings = {
        'gms': ['g', 'gm', 'gram', 'grams', 'ml', 'milliliter', 'millilitre'],
        'ml': ['milliliter', 'millilitre', 'milliliters', 'millilitres', 'g', 'gm', 'gms', 'gram']
    }
    
    # Filter results based on search terms
    if search_terms:
        filtered_results = []
        for item in mock_data:
            product_text = item["product"].lower()
            logger.info(f"[DEBUG] Checking product: {product_text}")
            
            # Check each search term
            matches_all = True
            for term in search_terms:
                logger.info(f"[DEBUG] Checking term: {term}")
                # Check direct match first
                if term in product_text:
                    logger.info(f"[DEBUG] Direct match found for term: {term}")
                    continue
                    
                # Check for unit variations
                term_matched = False
                for unit, variants in unit_mappings.items():
                    # If the term contains any variant, replace with the standard unit
                    for variant in variants + [unit]:
                        if variant in term:
                            # Replace the variant with the standard unit in both strings
                            normalized_term = term.replace(variant, unit)
                            normalized_product = product_text.replace(variant, unit)
                            logger.info(f"[DEBUG] Checking normalized term '{normalized_term}' against '{normalized_product}'")
                            if normalized_term in normalized_product:
                                term_matched = True
                                logger.info(f"[DEBUG] Normalized match found!")
                                break
                    if term_matched:
                        break
                
                if not term_matched:
                    logger.info(f"[DEBUG] No match found for term: {term}")
                    matches_all = False
                    break
            
            if matches_all:
                logger.info(f"[DEBUG] Adding product to results: {item['product']}")
                filtered_results.append(item)
        
        logger.info(f"[DEBUG] Final results count: {len(filtered_results)}")
        return filtered_results
    
    return mock_data

