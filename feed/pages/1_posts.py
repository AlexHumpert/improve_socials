# pages/1_posts.py
import streamlit as st
import pandas as pd
from database import add_post, get_posts, add_interaction

def load_posts_df():
    posts = get_posts()
    df = pd.DataFrame(posts, columns=['post_id', 'user', 'content', 'timestamp'])
    return df

# Check if user is logged in
if not st.session_state.get('logged_in', False):
    st.warning("Please log in to access this page.")
    st.stop()

st.title("Posts")

# Post creation
with st.form("post_form"):
    content = st.text_area("What's on your mind?", max_chars=280)
    submit = st.form_submit_button("Post")

    if submit and content:
        add_post(st.session_state.username, content)
        st.success("Post added successfully!")

# Show all posts
st.subheader("All Posts")
posts_df = load_posts_df()
for _, row in posts_df.iterrows():
    st.markdown(f"**{row['user']}** at {row['timestamp']}")
    st.write(row['content'])
    
    if st.button(f"Like", key=f"like_all_{row['post_id']}"):
        add_interaction(st.session_state.username, row['post_id'], 'like')
        st.success("Post liked!")
        st.rerun()
    st.markdown("---")