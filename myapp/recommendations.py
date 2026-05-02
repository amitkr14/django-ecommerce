import os
import django
from dotenv import load_dotenv

# Force Python to read the .env file
load_dotenv()
# 1. WAKE UP DJANGO FIRST
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings') 
django.setup()

# 2. NOW IMPORT EVERYTHING ELSE
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
import redis
from django.conf import settings

# 3. USE AN ABSOLUTE IMPORT (Change .models to myapp.models)
from myapp.models import Product

# Connect to your Redis instance
redis_client = redis.StrictRedis.from_url(settings.LOCAL_REDIS_URL, decode_responses=True)

def update_product_similarities():
    """Calculates TF-IDF cosine similarity for all products and caches in Redis."""
    print("Fetching products from database...")
    
    # 1. Fetch all active products
    products = Product.objects.filter(active=True).values('id', 'name', 'description')
    df = pd.DataFrame(products)

    if df.empty:
        print("No active products found.")
        return

    # 2. Create a "content block" to analyze
    # We repeat the name 3 times so the AI knows the Name is the most important part
    df['content'] = (df['name'] + " ") * 3 + df['description']
    df['content'] = df['content'].fillna('')

    print("Running machine learning matrix...")
    # 3. The ML Magic: Convert text to a TF-IDF Matrix
    tfv = TfidfVectorizer(stop_words='english')
    tfv_matrix = tfv.fit_transform(df['content'])

    # 4. Calculate the similarity score
    sig = cosine_similarity(tfv_matrix, tfv_matrix)

    # 5. Map the results and save to Redis
    indices = pd.Series(df.index, index=df['id']).drop_duplicates()

    for product_id in df['id']:
        idx = indices[product_id]
        sig_scores = list(enumerate(sig[idx]))
        sig_scores = sorted(sig_scores, key=lambda x: x[1], reverse=True)
        top_5_indices = [i[0] for i in sig_scores[1:6]]
        top_5_product_ids = df['id'].iloc[top_5_indices].tolist()
        
        # 6. Save directly to Redis
        redis_key = f"product:{product_id}:similar"
        redis_client.set(redis_key, json.dumps(top_5_product_ids))
        
    print("Successfully updated the AI recommendation matrix in Redis!")

# 4. ACTUALLY RUN THE FUNCTION
if __name__ == '__main__':
    update_product_similarities()