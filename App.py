import streamlit as st
from PIL import Image
import json
from Classifier import KNearestNeighbours
from bs4 import BeautifulSoup
import requests, io
import PIL.Image
from urllib.request import urlopen
import psycopg2
from streamlit import session_state

st.set_page_config(
    page_title="Movie Recommender System",
)

placeholder = st.empty()


def add_user_to_database(username, user_password):
    try:
        dbname = "filmreco_database"
        user = "postgres"
        password = "1A2n3D4r5E6w7666postgres"
        host = "localhost"
        port = "5433"

        # st.write("Connecting to the db")
        conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        cur = conn.cursor()

        # st.write("Inserting")
        cur.execute("SELECT MAX(id) FROM users")
        max_id = cur.fetchone()[0]
        new_id = max_id + 1 if max_id is not None else 1

        sql = "INSERT INTO users (id, username, password) VALUES (%s, %s, %s)"
        user_data = (new_id, username, user_password)
        cur.execute(sql, user_data)
        conn.commit()

        cur.close()
        conn.close()
        # st.write("User added successfully.")
    except psycopg2.Error as e:
        st.write("Error:", e)


def save_movie_to_database(username, movie_title):
    try:
        dbname = "filmreco_database"
        user = "postgres"
        password = "1A2n3D4r5E6w7666postgres"
        host = "localhost"
        port = "5433"

        conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        cur = conn.cursor()

        cur.execute("SELECT film_title FROM films WHERE username = %s", (username,))
        existing_movies = cur.fetchone()

        if existing_movies:
            movies = existing_movies[0].split(", ")
            if movie_title not in movies:
                movies.append(movie_title)
                updated_movies = ", ".join(movies)
                cur.execute("UPDATE films SET film_title = %s WHERE username = %s", (updated_movies, username))
        else:
            cur.execute("INSERT INTO films (username, film_title) VALUES (%s, %s)", (username, movie_title))

        conn.commit()

        cur.close()
        conn.close()
    except psycopg2.Error as e:
        st.write("Error:", e)


def show_saved_films(username):
    try:
        dbname = "filmreco_database"
        user = "postgres"
        password = "1A2n3D4r5E6w7666postgres"
        host = "localhost"
        port = "5433"

        conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        cur = conn.cursor()

        cur.execute("SELECT film_title FROM films WHERE username = %s", (username,))
        saved_films = cur.fetchone()

        if saved_films:
            st.subheader("Saved Films")
            for film in saved_films[0].split(", "):
                st.write(film)
        else:
            st.write("No saved films found for this user.")

        cur.close()
        conn.close()
    except psycopg2.Error as e:
        st.error("Error fetching saved films:", e)

with open('./Data/movie_data.json', 'r+', encoding='utf-8') as f:
    data = json.load(f)
with open('./Data/movie_titles.json', 'r+', encoding='utf-8') as f:
    movie_titles = json.load(f)
# hdr = {'User-Agent': 'Mozilla/5.0'}
hdr = {
    'User-Agent': 'Mozilla/5.0',
    'Accept-Language': 'en-US,en;q=0.9'
}


def movie_poster_fetcher(imdb_link):
    ## Display Movie Poster
    url_data = requests.get(imdb_link, headers=hdr).text
    s_data = BeautifulSoup(url_data, 'html.parser')
    imdb_dp = s_data.find("meta", property="og:image")
    movie_poster_link = imdb_dp.attrs['content']
    u = urlopen(movie_poster_link)
    raw_data = u.read()
    image = PIL.Image.open(io.BytesIO(raw_data))
    image = image.resize((158, 301), )
    st.image(image, use_column_width=False)


def get_movie_info(imdb_link):
    url_data = requests.get(imdb_link, headers=hdr).text
    s_data = BeautifulSoup(url_data, 'html.parser')
    imdb_content = s_data.find("meta", attrs={"name": "description"})

    if imdb_content is not None:
        movie_descr = imdb_content.attrs.get('content', '').split('.')

        if len(movie_descr) >= 3:
            movie_director = movie_descr[0]
            movie_cast = str(movie_descr[1]).replace('With', 'Cast: ').strip()
            movie_story = 'Story: ' + str(movie_descr[2]).strip() + '.'
            # rating = s_data.find("span", class_="sc-bde20123-3 gPVQxL")
            # movie_rating = 'Total Rating count: ' + str(rating.text) if rating else 'Rating not available'
            rating = s_data.find("div", class_="sc-bde20123-3 gPVQxL")
            rating = str(rating).split('<div class="sc-bde20123-3 gPVQxL')
            rating = str(rating[1]).split("</div>")
            rating = str(rating[0]).replace(''' "> ''', '').replace('">', '')

            movie_rating = 'Total Rating count: ' + rating

            return movie_director, movie_cast, movie_story, movie_rating
        else:
            return 'Data not available', 'Data not available', 'Data not available', 'Rating not available'
    else:
        return 'Data not available', 'Data not available', 'Data not available', 'Rating not available'


def KNN_Movie_Recommender(test_point, k):
    # Create dummy target variable for the KNN Classifier
    target = [0 for item in movie_titles]
    # Instantiate object for the Classifier
    model = KNearestNeighbours(data, target, test_point, k=k)
    # Run the algorithm
    model.fit()
    # Print list of 10 recommendations < Change value of k for a different number >
    table = []
    for i in model.indices:
        # Returns back movie title and imdb link
        table.append([movie_titles[i][0], movie_titles[i][2], data[i][-1]])
    print(table)
    return table


def login_form():
    with placeholder.form(key='login_form'):
        st.subheader("Log in")
        st.markdown('<span style="color: blue;">To save movies, please log in:</span>', unsafe_allow_html=True)
        username = st.text_input('Username')
        password = st.text_input('Password', type='password')
        login_button = st.form_submit_button('Log in')
        if login_button:
            placeholder.empty()
    return username, password, login_button


def signup_form():
    with placeholder.form(key='signup_form'):
        st.subheader("Sign in")
        st.markdown('<span style="color: blue;">Create an account:</span>', unsafe_allow_html=True)

        new_username = st.text_input('New Username')
        new_password = st.text_input('New Password', type='password')
        signup_button = st.form_submit_button('Sign up')
        if signup_button:
            placeholder.empty()
    return new_username, new_password, signup_button


def show_recommendations(username):
    if st.button("Show saved films"):
        show_saved_films(username)
    img1 = Image.open('./meta/logo3.jpg')
    img1 = img1.resize((700, 205), )
    st.image(img1, use_column_width=False)
    st.title("FilmFusion")
    st.markdown('''<h4 style='text-align: left; color: #d73b5c;'>* Data is based "IMDB 5000 Movie Dataset"</h4>''',
                unsafe_allow_html=True)
    genres = ['Action', 'Adventure', 'Animation', 'Biography', 'Comedy', 'Crime', 'Documentary', 'Drama', 'Family',
              'Fantasy', 'Film-Noir', 'Game-Show', 'History', 'Horror', 'Music', 'Musical', 'Mystery', 'News',
              'Reality-TV', 'Romance', 'Sci-Fi', 'Short', 'Sport', 'Thriller', 'War', 'Western']
    movies = [title[0] for title in movie_titles]
    category = ['--Select--', 'By Movie', 'By Genre']
    cat_op = st.selectbox('Select Recommendation Type', category)
    if cat_op == category[0]:
        st.warning('Please select Recommendation Type!')
    elif cat_op == category[1]:
        select_movie = st.selectbox('Select movie: (Recommendation will be based on this selection)',
                                    ['--Select--'] + movies)
        dec = st.radio("Want to Fetch Movie Poster?", ('Yes', 'No'))
        st.markdown(
            '''<h4 style='text-align: left; color: #d73b5c;'>* Fetching a Movie Posters will take a time."</h4>''',
            unsafe_allow_html=True)
        if dec == 'No':
            if select_movie == '--Select--':
                st.warning('Please select Movie!')
            else:
                no_of_reco = st.slider('Number of movies you want Recommended:', min_value=5, max_value=20, step=1)
                genres = data[movies.index(select_movie)]
                test_points = genres
                table = KNN_Movie_Recommender(test_points, no_of_reco + 1)
                table.pop(0)
                c = 0
                st.success('Some of the movies from our Recommendation, have a look below')
                for movie, link, ratings in table:
                    c += 1
                    director, cast, story, total_rat = get_movie_info(link)
                    st.markdown(f"({c})[ {movie}]({link})")
                    st.markdown(director)
                    st.markdown(cast)
                    st.markdown(story)
                    st.markdown(total_rat)
                    st.markdown('IMDB Rating: ' + str(ratings) + '⭐')
        else:
            if select_movie == '--Select--':
                st.warning('Please select Movie!')
            else:
                no_of_reco = st.slider('Number of movies you want Recommended:', min_value=5, max_value=20, step=1)
                genres = data[movies.index(select_movie)]
                test_points = genres
                table = KNN_Movie_Recommender(test_points, no_of_reco + 1)
                table.pop(0)
                c = 0
                st.success('Some of the movies from our Recommendation, have a look below')
                for movie, link, ratings in table:
                    c += 1
                    st.markdown(f"({c})[ {movie}]({link})")

                    if st.button(f"Save Movie: {movie}"):
                        save_movie_to_database(username, movie)

                    movie_poster_fetcher(link)
                    director, cast, story, total_rat = get_movie_info(link)
                    st.markdown(director)
                    st.markdown(cast)
                    st.markdown(story)
                    st.markdown(total_rat)
                    st.markdown('IMDB Rating: ' + str(ratings) + '⭐')
    elif cat_op == category[2]:
        sel_gen = st.multiselect('Select Genres:', genres)
        dec = st.radio("Want to Fetch Movie Poster?", ('Yes', 'No'))
        st.markdown(
            '''<h4 style='text-align: left; color: #d73b5c;'>* Fetching a Movie Posters will take a time."</h4>''',
            unsafe_allow_html=True)
        if dec == 'No':
            if sel_gen:
                imdb_score = st.slider('Choose IMDb score:', 1, 10, 8)
                no_of_reco = st.number_input('Number of movies:', min_value=5, max_value=20, step=1)
                test_point = [1 if genre in sel_gen else 0 for genre in genres]
                test_point.append(imdb_score)
                table = KNN_Movie_Recommender(test_point, no_of_reco)
                c = 0
                st.success('Some of the movies from our Recommendation, have a look below')
                for movie, link, ratings in table:
                    c += 1
                    st.markdown(f"({c})[ {movie}]({link})")
                    director, cast, story, total_rat = get_movie_info(link)
                    st.markdown(director)
                    st.markdown(cast)
                    st.markdown(story)
                    st.markdown(total_rat)
                    st.markdown('IMDB Rating: ' + str(ratings) + '⭐')
        else:
            if sel_gen:
                imdb_score = st.slider('Choose IMDb score:', 1, 10, 8)
                no_of_reco = st.number_input('Number of movies:', min_value=5, max_value=20, step=1)
                test_point = [1 if genre in sel_gen else 0 for genre in genres]
                test_point.append(imdb_score)
                table = KNN_Movie_Recommender(test_point, no_of_reco)
                c = 0
                st.success('Some of the movies from our Recommendation, have a look below')
                for movie, link, ratings in table:
                    c += 1
                    st.markdown(f"({c})[ {movie}]({link})")
                    movie_poster_fetcher(link)
                    director, cast, story, total_rat = get_movie_info(link)
                    st.markdown(director)
                    st.markdown(cast)
                    st.markdown(story)
                    st.markdown(total_rat)
                    st.markdown('IMDB Rating: ' + str(ratings) + '⭐')


def run():
    st.sidebar.title("Account")
    mode = st.sidebar.radio("Choose mode:", ("Log in", "Sign up"))

    if mode == "Log in":
        username, user_password, login_button = login_form()
        if login_button:
            dbname = "filmreco_database"
            user = "postgres"
            password = "1A2n3D4r5E6w7666postgres"
            host = "localhost"
            port = "5433"
            conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
            cur = conn.cursor()
            cur.execute("SELECT username FROM users WHERE username = %s AND password = %s", (username, user_password))
            existing_username = cur.fetchone()
            cur.close()
            conn.close()
            if existing_username:
                session_state.username = username
                session_state.user_logged_in = True
                st.success(f"Logged in as {username}")
                st.sidebar.write(
                    f"<span style='color: blue; font-weight: bold; font-size: 20px;'>User:</span> <span style='color: "
                    f"blue; font-weight: bold; font-size: 20px;'>{username}</span>",
                    unsafe_allow_html=True)

                show_recommendations(username)
            else:
                st.error("Invalid username or password. Please refresh the page and enter the correct information.")
    elif mode == "Sign up":
        new_username, new_password, signup_button = signup_form()
        if signup_button:
            dbname = "filmreco_database"
            user = "postgres"
            password = "1A2n3D4r5E6w7666postgres"
            host = "localhost"
            port = "5433"
            conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
            cur = conn.cursor()
            cur.execute("SELECT username FROM users WHERE username = %s", (new_username,))
            existing_username = cur.fetchone()
            cur.close()
            conn.close()

            if existing_username:
                st.error("Username already exists. Please refresh the page and choose another username.")
            else:
                session_state.username = new_username
                session_state.user_logged_in = True
                add_user_to_database(new_username, new_password)
                st.success(f"Account created for {new_username}")
                st.sidebar.write(
                    f"<span style='color: blue; font-weight: bold; font-size: 20px;'>User:</span> <span style='color: "
                    f"blue; font-weight: bold; font-size: 20px;'>{new_username}</span>",
                    unsafe_allow_html=True)

                show_recommendations(new_username)


if 'user_logged_in' not in session_state:
    session_state.user_logged_in = False

if session_state.user_logged_in:
    show_recommendations(session_state.username)
else:
    run()