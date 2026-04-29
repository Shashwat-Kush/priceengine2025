import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import os
from src.utils.config import PROCESSED_DIR

def compute_vader_features(reviews_df):
    '''
    Input : DataFrame with columns [model_key, review_text, star_rating]
    Output: per-SKU sentiment DataFrame
    '''
    if 'review_text' not in reviews_df.columns or 'model_key' not in reviews_df.columns:
        # Return empty df if required columns missing
        return pd.DataFrame()
        
    sia = SentimentIntensityAnalyzer()
    reviews_df['compound'] = reviews_df['review_text'].apply(
        lambda t: sia.polarity_scores(str(t))['compound']
    )
    
    # Aggregate per SKU
    agg = reviews_df.groupby('model_key').agg(
        sentiment_avg   = ('compound', 'mean'),
        one_star_pct    = ('star_rating', lambda x: (x==1).mean() if 'star_rating' in reviews_df else 0),
        four_five_pct   = ('star_rating', lambda x: (x>=4).mean() if 'star_rating' in reviews_df else 0),
        review_count    = ('compound', 'count'),
    ).reset_index()
    
    # Review Velocity
    if 'review_date' in reviews_df.columns:
        reviews_df['review_date'] = pd.to_datetime(reviews_df['review_date'])
        first_review = reviews_df.groupby('model_key')['review_date'].min()
        last_review  = reviews_df.groupby('model_key')['review_date'].max()
        months_active = ((last_review - first_review).dt.days / 30).clip(lower=1)
        velocity = (reviews_df.groupby('model_key').size() / months_active).rename('review_velocity')
        agg = agg.merge(velocity, on='model_key')
    else:
        agg['review_velocity'] = 0.0
        
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    agg.to_csv(os.path.join(PROCESSED_DIR, 'sku_sentiments.csv'), index=False)
    
    return agg

def get_sku_embedding(reviews_text_list, top_n=50):
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        top = reviews_text_list[:top_n]
        embeddings = model.encode(top, batch_size=32, show_progress_bar=False)
        return embeddings.mean(axis=0)
    except ImportError:
        return None
