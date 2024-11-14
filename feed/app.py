import streamlit as st
import pandas as pd
from database import init_db, add_post, get_posts, add_interaction, get_user_interactions, get_likes_count
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Initialize the database
init_db()

# Function to load all posts into a DataFrame
def load_posts_df():
    posts = get_posts()
    df = pd.DataFrame(posts, columns=['user', 'content', 'timestamp'])
    df['post_id'] = df.index + 1  # Assign a post_id starting from 1
    return df

def get_recommended_posts(user, num_recommendations=5):
    posts_df = load_posts_df()

    # Get the posts that the user has liked
    user_interactions = get_user_interactions(user)
    if not user_interactions:
        return pd.DataFrame()  # Return an empty DataFrame if no interactions
    
    # Get like counts for all posts
    like_counts = get_likes_count()
    like_counts_df = pd.DataFrame(like_counts, columns=['post_id', 'like_count'])

    # Filter posts that the user has liked
    liked_posts_df = posts_df[posts_df['post_id'].isin(user_interactions)]

    # Merge the like counts with the liked posts
    liked_posts_with_counts = liked_posts_df.merge(like_counts_df, on='post_id', how='left')
    
    # Sort by the like count in descending order
    liked_posts_with_counts = liked_posts_with_counts.sort_values(by='like_count', ascending=False)
    
    # Return the top N recommended posts
    return liked_posts_with_counts.head(num_recommendations)

# Streamlit App
st.title("Simple Newsfeed")

# Form to add a new post
with st.form("post_form"):
    user = st.text_input("Name", max_chars=20)
    content = st.text_area("What's on your mind?", max_chars=280)
    submit = st.form_submit_button("Post")

    if submit and user and content:
        add_post(user, content)
        st.success("Post added successfully!")

st.subheader("Newsfeed")
posts = get_posts()

# Display posts
if posts:
    posts_df = load_posts_df()
    for i, row in posts_df.iterrows():
        st.markdown(f"**{row['user']}** at {row['timestamp']}")
        st.write(row['content'])
        
        # Add a like button
        if st.button(f"Like post {row['post_id']}", key=f"like_{row['post_id']}"):
            add_interaction(user, row['post_id'], 'like')
            st.success(f"You liked post {row['post_id']}!")
        st.markdown("---")
else:
    st.info("No posts yet. Be the first to share!")

# Display recommended posts
st.title("Personalized Newsfeed")
user = st.text_input("Enter your username", max_chars=20)

if user:
    st.subheader("Recommended for you")
    recommended_posts = get_recommended_posts(user)
    
    if not recommended_posts.empty:
        for _, row in recommended_posts.iterrows():
            st.markdown(f"**{row['user']}** at {row['timestamp']}")
            st.write(row['content'])
            st.markdown(f"👍 {row['like_count']} likes")
            st.markdown("---")
    else:
        st.info("No recommendations available. Try liking some posts!")