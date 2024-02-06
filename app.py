import streamlit as st
import mysql.connector
import matplotlib.pyplot as plt
import pandas as pd
import hashlib

# Function to connect to the database
def connect_to_database():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Qunta729",
        database="blog"
    )

# CRUD Operations (placeholders)
def read_posts(offset, limit):
    connection = connect_to_database()  # Establish a connection to the database
    cursor = connection.cursor()  # Create a cursor object to execute SQL queries
    
    # SQL query to retrieve posts along with their titles, content, and author usernames
    query = """
    SELECT p.title, p.content, IFNULL(u.username, 'Unknown') AS username
    FROM posts p
    LEFT JOIN users u ON p.user_id = u.id
    ORDER BY p.created_at DESC
    LIMIT %s OFFSET %s
"""

    
    print("Query:", query)  # Print the SQL query for debugging purposes
    
    # Execute the SQL query with the provided limit and offset
    cursor.execute(query, (limit, offset))
    
    # Fetch all the retrieved posts from the database
    posts = cursor.fetchall()
    
    # Close the database connection
    connection.close()
    
    print("Fetched posts:", posts)  # Print the fetched posts for debugging purposes
    
    # Return the fetched posts
    return posts
    
def create_post(user_id, title, content, category_names):
    connection = connect_to_database()
    cursor = connection.cursor()
    query = "INSERT INTO posts (title, content, user_id) VALUES (%s, %s, %s)"
    cursor.execute(query, (title, content, user_id))
    post_id = cursor.lastrowid
    
    # Retrieve category IDs for the selected category names
    category_ids = []
    for category_name in category_names:
        query = "SELECT id FROM categories WHERE name = %s"
        cursor.execute(query, (category_name,))
        result = cursor.fetchone()
        if result:
            category_id = result[0]
            category_ids.append(category_id)
    
    # Insert the post ID and category IDs into the post_categories table
    for category_id in category_ids:
        query = "INSERT INTO post_categories (post_id, category_id) VALUES (%s, %s)"
        cursor.execute(query, (post_id, category_id))
    
    connection.commit()
    connection.close()

def read_categories():
    # Predefined categories
    predefined_categories = ["Python", "AWS", "GCP", "Azure", "MySQL", "Streamlit", "Heroku"]
    
    # Fetch categories from the database
    connection = connect_to_database()
    cursor = connection.cursor()
    query = "SELECT name FROM categories ORDER BY name"
    cursor.execute(query)
    categories_from_db = [row[0] for row in cursor.fetchall()]
    connection.close()
    
    # Combine predefined and database categories, removing duplicates
    categories = list(set(predefined_categories + categories_from_db))
    categories.sort()  # Sort alphabetically
    
    return categories


# User Authentication
def authenticate(username, password):
    connection = connect_to_database()
    cursor = connection.cursor()
    query = "SELECT username, password FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    user = cursor.fetchone()
    connection.close()
    
    if user:
        # Retrieve stored hashed password
        stored_password = user[1]
        
        # Hash the provided password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Compare hashed passwords
        if stored_password == hashed_password:
            return True
    return False



def read_posts_by_category(category_id):
    connection = connect_to_database()
    cursor = connection.cursor()
    query = """
        SELECT p.title, p.content
        FROM posts p
        INNER JOIN post_categories pc ON p.id = pc.post_id
        WHERE pc.category_id = %s
    """
    cursor.execute(query, (category_id,))
    posts = cursor.fetchall()
    connection.close()
    return posts

def search_posts(category, query, offset, limit):
    connection = connect_to_database()
    cursor = connection.cursor()
    query = """
        SELECT p.title, p.content
        FROM posts p
        INNER JOIN post_categories pc ON p.id = pc.post_id
        WHERE pc.category_id = %s
        AND (p.title LIKE %s OR p.content LIKE %s)
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
    """
    cursor.execute(query, (category, f'%{query}%', f'%{query}%', limit, offset))
    posts = cursor.fetchall()
    connection.close()
    return posts

def register_user(username, password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    # Insert the username and hashed password into the database
    connection = connect_to_database()
    cursor = connection.cursor()
    query = "INSERT INTO users (username, password) VALUES (%s, %s)"
    cursor.execute(query, (username, hashed_password))
    connection.commit()
    connection.close()

# Pagination logic
def get_total_posts():
    connection = connect_to_database()
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM posts")
    total_posts = cursor.fetchone()[0]
    connection.close()
    return total_posts

def calculate_total_pages(total_posts, posts_per_page):
    return (total_posts + posts_per_page - 1) // posts_per_page

# Data Visualization
def visualize_post_trends():
    # Fetch data from the database
    connection = connect_to_database()
    cursor = connection.cursor()
    query = "SELECT DATE(created_at) AS date, COUNT(*) AS num_posts FROM posts GROUP BY DATE(created_at)"
    cursor.execute(query)
    data = cursor.fetchall()
    connection.close()

    # Convert data to DataFrame
    df = pd.DataFrame(data, columns=['Date', 'Num_Posts'])
    df['Date'] = pd.to_datetime(df['Date'])

    # Plot post trends
    plt.figure(figsize=(10, 6))
    plt.plot(df['Date'], df['Num_Posts'], marker='o', linestyle='-')
    plt.title('Posts Trends Over Time')
    plt.xlabel('Date')
    plt.ylabel('Number of Posts')
    plt.grid(True)
    st.pyplot()

# Function to display posts
def display_posts(posts):
    print("Displaying posts:", posts)  # Add this line for debugging
    for post_index, post in enumerate(posts, start=1):
        title = post[0]
        content = post[1]
        author = post[2]  # Assuming the username is in the third column
        print("Post:", post_index)
        print("Title:", title)
        print("Content:", content)
        print("Author:", author)


# Function to display the main interface
def main():
    init_session_state()  # Initialize session state
    st.title("BlogPost App")

    menu = ["Home", "New Post", "Manage Posts", "Login", "Register"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        st.header("Home")
        
        # Set posts per page
        posts_per_page = 10
        
        # Fetch total number of posts
        total_posts = get_total_posts()
        
        # Calculate total pages
        total_pages = calculate_total_pages(total_posts, posts_per_page)
        
        # Get current page from session state
        current_page = st.session_state.current_page
        
        # Calculate offset for fetching posts
        offset = (current_page - 1) * posts_per_page
        
        # Fetch posts for the current page
        posts = read_posts(offset, posts_per_page)
        
        # Display posts
        for post_index, post in enumerate(posts, start=1):
            title = post[0]
            content = post[1]
            author = post[2]  # Assuming the username is in the third column
            st.write("Post:", post_index)
            st.write("Title:", title)
            st.write("Content:", content)
            st.write("Author:", author)

        # Pagination controls
        st.sidebar.markdown(f"Page {current_page}/{total_pages}")
        if current_page > 1:
            if st.sidebar.button("Previous"):
                st.session_state.current_page -= 1
        if current_page < total_pages:
            if st.sidebar.button("Next"):
                st.session_state.current_page += 1

    elif choice == "New Post":
        st.header("Create New Post")
        if st.session_state.get('authenticated'):
            title = st.text_input("Title")
            content = st.text_area("Content", height=200)
            
            # Fetch categories
            categories = read_categories()
            
            # Display category selection
            selected_categories = st.multiselect("Categories", categories)
            
            if st.button("Create Post"):
                if not title or not content:
                    st.warning("Please enter both title and content.")
                elif not selected_categories:
                    st.warning("Please select at least one category.")
                else:
                    create_post(title, content, selected_categories)
                    st.success("Post created successfully!")
        else:
            st.info("Please login to create a new post.")



    elif choice == "Manage Posts":
        st.header("Manage Posts")
        # Implement manage posts functionality

    elif choice == "Login":
        st.header("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if authenticate(username, password):
                st.session_state.authenticated = True
                st.success("Logged in successfully!")
            else:
                st.error("Invalid username or password")

    elif choice == "Register":
        st.header("Register")
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        if st.button("Register"):
            if new_password == confirm_password:
                register_user(new_username, new_password)
                st.success("Registration successful! You can now login.")
            else:
                st.error("Passwords do not match.")

def init_session_state():
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

if __name__ == "__main__":
    main()
