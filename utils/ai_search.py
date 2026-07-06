import re
from collections import Counter

def get_cosine_similarity(text1, text2):
    # Pure Python basic cosine similarity for text
    words1 = re.findall(r'\w+', text1.lower())
    words2 = re.findall(r'\w+', text2.lower())
    
    vec1 = Counter(words1)
    vec2 = Counter(words2)
    
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])
    
    sum1 = sum([vec1[x]**2 for x in vec1.keys()])
    sum2 = sum([vec2[x]**2 for x in vec2.keys()])
    denominator = (sum1**0.5) * (sum2**0.5)
    
    if not denominator:
        return 0.0
    return float(numerator) / denominator

def perform_ai_search(query, products):
    """
    products should be a list of dicts: [{'id': 1, 'name': '...', 'description': '...'}, ...]
    Returns a sorted list of products based on relevance to the query.
    """
    if not products or not query.strip():
        return products
        
    results = []
    for product in products:
        content = f"{product['name']} {product.get('description', '')}"
        
        # Calculate basic text similarity
        score = get_cosine_similarity(query, content)
        
        if score > 0:
            product['relevance'] = score
            results.append(product)
            
    # Sort by relevance descending
    results.sort(key=lambda x: x['relevance'], reverse=True)
    return results
