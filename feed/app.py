import streamlit as st
import pandas as pd
from database import init_db, add_post, get_posts

# Initialize the database
init_db()

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
    for user, content, timestamp in posts:
        st.markdown(f"**{user}** at {timestamp}")
        st.write(content)
        st.markdown("---")
else:
    st.info("No posts yet. Be the first to share!")