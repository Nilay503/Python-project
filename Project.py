import streamlit as st #for the frontend
import pandas as pd #it returns data form database and it is use in hist
import folium # for map and marker
from streamlit_folium import st_folium #use to display the map inside the frontend
import uuid #to generate unique sireal no
import time #time
import re #regx for the validatation
import sqlite3 #database
import random #otp mate
import requests #api request feach
from datetime import datetime #date and time mate

# --- 1. CONFIGURATION & SETUP ---

st.set_page_config(page_title="CityCab Ultimate", page_icon="🚖", layout="wide")

#the cordinates to set the pins
AHMEDABAD_LOCATIONS = {
    "Kalupur Railway Station": (23.0263, 72.6000),
    "SVP Airport": (23.0734, 72.6266),
    "IIM Ahmedabad": (23.0300, 72.5000),
    "Riverfront Event Centre": (23.0345, 72.5714),
    "Science City": (23.0788, 72.4930),
    "Manek Chowk": (23.0225, 72.5880),
    "S.G. Highway": (23.0400, 72.5100),
    "Kankaria Lake": (23.0060, 72.6010),
    "ISRO Space Colony": (23.0300, 72.5300)
}


# --- 2. DATABASE & BACKEND ---
def get_db_connection():
    conn = sqlite3.connect('citycab_final_v2.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# tables quere
def init_db():
    conn = get_db_connection()
    c = conn.cursor()

    # Users & Drivers
    c.execute(
        '''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, wallet REAL, email TEXT, city TEXT)''')
    c.execute(
        '''CREATE TABLE IF NOT EXISTS drivers (username TEXT PRIMARY KEY, password TEXT, wallet REAL, rating REAL, rides_done INTEGER)''')

    # Rides Table
    c.execute('''CREATE TABLE IF NOT EXISTS rides (
                 id TEXT PRIMARY KEY, passenger TEXT, driver TEXT, 
                 pickup TEXT, drop_loc TEXT, price REAL, status TEXT, 
                 created_at TEXT, type TEXT, ride_otp TEXT, passenger2 TEXT, num_passengers INTEGER)''')

    # Platform Earnings
    c.execute('''CREATE TABLE IF NOT EXISTS platform (id INTEGER PRIMARY KEY, total_earnings REAL)''')
    c.execute("INSERT OR IGNORE INTO platform (id, total_earnings) VALUES (1, 0.0)")

    # Seed Test Data
    try:
        c.execute(
            "INSERT INTO users (username, password, wallet, city, email) VALUES ('passenger', '123', 5000.0, 'Ahmedabad', 'p1@citycab.com')")
        c.execute(
            "INSERT INTO users (username, password, wallet, city, email) VALUES ('passenger2', '123', 5000.0, 'Ahmedabad', 'p2@citycab.com')")
    except sqlite3.IntegrityError:
        pass
    try:
        c.execute(
            "INSERT INTO drivers (username, password, wallet, rating, rides_done) VALUES ('driver', '123', 0.0, 4.8, 0)")
    except sqlite3.IntegrityError:
        pass

    conn.commit()
    conn.close()


init_db()


# --- 3. WEATHER ENGINE ---
def get_weather_data():
    api_key = "2e55754982c2e40532abd1cac2d336d2" #api key
    city = "Ahmedabad"

# request use to feach the data
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            cond = data["weather"][0]["main"]
            weather = {"temp": data["main"]["temp"], "condition": cond, "is_rain": "Rain" in cond}
            st.session_state.static_weather = weather
            return weather
    except:
        pass

    if 'static_weather' in st.session_state:
        return st.session_state.static_weather

    import random
    conditions = ["Clear", "Haze", "Clouds", "Rain"]
    sim_cond = random.choice(conditions)
    return {
        "temp": random.randint(28, 42),
        "condition": sim_cond,
        "is_rain": sim_cond == "Rain"
    }


# --- 4. AUTHENTICATION SYSTEM ---
def auth_system():
    st.title("🚖 CityCab: Ultimate Edition")
    st.info(
        "💡 **Test Accounts:**\n1. Passenger: `passenger` / `123`\n2. Driver: `driver` / `123`\n3. Admin: `admin` / `admin`")

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        if 'login_step' not in st.session_state: st.session_state.login_step = 1

        if st.session_state.login_step == 1:
            with st.form("login_form"):
                role = st.radio("I am a:", ["Passenger", "Driver", "Admin"], horizontal=True)
                user = st.text_input("Username")
                pwd = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Send Login OTP")

                if submitted:
                    if role == "Admin" and user == "admin" and pwd == "admin":
                        st.session_state.current_user = "admin"
                        st.session_state.user_role = "Admin"
                        st.rerun()

                    conn = get_db_connection()
                    table = "users" if role == "Passenger" else "drivers"
                    acc = conn.execute(f"SELECT * FROM {table} WHERE username=? AND password=?", (user, pwd)).fetchone()
                    conn.close()

                    if acc:
                        st.session_state.temp_user = dict(acc)
                        st.session_state.temp_role = role
                        st.session_state.otp = str(random.randint(1000, 9999))
                        st.session_state.login_step = 2
                        st.rerun()
                    else:
                        st.error("Invalid Credentials.")

        elif st.session_state.login_step == 2:
            st.info(f"📩 SMS Sent: Your OTP is **{st.session_state.otp}**")
            with st.form("otp_form"):
                otp_input = st.text_input("Enter OTP")
                verify = st.form_submit_button("Verify & Login")
                if verify:
                    if otp_input == st.session_state.otp:
                        st.session_state.current_user = st.session_state.temp_user
                        st.session_state.user_role = st.session_state.temp_role
                        st.session_state.login_step = 1
                        st.success("Success!")
                        st.rerun()
                    else:
                        st.error("Wrong OTP")
            if st.button("Cancel"):
                st.session_state.login_step = 1
                st.rerun()

    with tab2:
        with st.form("signup_form"):
            new_role = st.radio("Join As", ["Passenger", "Driver"], horizontal=True)
            new_u = st.text_input("Username")
            new_email = st.text_input("Email Address")
            new_p = st.text_input("Password", type="password")
            new_city = st.text_input("City", value="Ahmedabad")
            submit = st.form_submit_button("Create Account")


            def is_valid_email(email):
                pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
                return re.match(pattern, email)

            def is_secure_password(password):
                # Pattern: 1+ Uppercase, 1+ Special Char, Min 6 characters
                pattern = r'^(?=.*[A-Z])(?=.*[!@#$%^&*(),.?":{}|<>]).{6,}$'
                if re.match(pattern, password):
                    return True
                return False
            if submit:
                if not is_valid_email(new_email):
                    st.error("Please enter a valid email address.")
                if not is_secure_password(new_p):
                    st.error("❌ Password weak! Must have 6+ chars, 1 Capital, and 1 Special Character.")
                elif new_u and new_p and new_email:
                    conn = get_db_connection()
                    try:
                        table = "users" if new_role == "Passenger" else "drivers"
                        wallet = 5000.0 if new_role == "Passenger" else 0.0

                        if new_role == "Passenger":
                            conn.execute(
                                f"INSERT INTO {table} (username, password, wallet, city, email) VALUES (?, ?, ?, ?, ?)",
                                (new_u, new_p, wallet, new_city, new_email))
                        else:
                            conn.execute(
                                f"INSERT INTO {table} (username, password, wallet, rating, rides_done) VALUES (?, ?, ?, ?, ?)",
                                (new_u, new_p, wallet, 5.0, 0))

                        conn.commit()
                        st.success("Created! Go to Login.")
                    except:
                        st.error("Username taken.")
                    finally:
                        conn.close()
                else:
                    st.error("All fields required.")


# --- 5. PASSENGER DASHBOARD ---
def passenger_dashboard(user):
    st.sidebar.title(f"👤 {user['username']}")
    st.sidebar.metric("Wallet", f"₹{user['wallet']:.2f}")

    weather = get_weather_data()
    st.sidebar.divider()
    st.sidebar.metric("Temperature", f"{weather['temp']}°C")
    st.sidebar.markdown(f"## 🌤️ {weather['condition']}")
    if weather['is_rain']: st.sidebar.error("🌧️ RAIN SURGE ACTIVE!")

    if st.sidebar.button("Logout"):
        st.session_state.current_user = None
        st.rerun()

    # --- TABS ---
    tab_book, tab_share, tab_history, tab_profile = st.tabs(["🚖 Book Ride", "🧩 Join Pool", "📜 History", "⚙️ Profile"])

    # --- TAB A: BOOK RIDE ---
    with tab_book:
        if 'active_ride_id' not in st.session_state: st.session_state.active_ride_id = None

        conn = get_db_connection()
        active_ride = None
        if st.session_state.active_ride_id:
            active_ride = conn.execute("SELECT * FROM rides WHERE id=?", (st.session_state.active_ride_id,)).fetchone()
        conn.close()

        if not active_ride:
            st.subheader("Plan your trip")
            c1, c2 = st.columns(2)
            with c1:
                p_in = st.selectbox("Pickup", ["Select..."] + list(AHMEDABAD_LOCATIONS.keys()))
                pickup = p_in if p_in != "Select..." else st.text_input("Or type Pickup", "Kalupur Railway Station")
            with c2:
                d_in = st.selectbox("Drop", ["Select..."] + list(AHMEDABAD_LOCATIONS.keys()))
                drop = d_in if d_in != "Select..." else st.text_input("Or type Drop", "SVP Airport")

            # --- NEW: PASSENGER COUNT ---
            c3, c4 = st.columns(2)
            with c3:
                num_passengers = st.number_input("Passengers", min_value=1, max_value=4, value=1)
            with c4:
                is_pool = st.checkbox("🧩 Share Cab (Pool) - Save 30%")

            if st.button("Calculate Fare"):
                p_coords = AHMEDABAD_LOCATIONS.get(pickup, (23.0225, 72.5714))
                d_coords = AHMEDABAD_LOCATIONS.get(drop, (23.0734, 72.6266))

                dist = ((p_coords[0] - d_coords[0]) ** 2 + (p_coords[1] - d_coords[1]) ** 2) ** 0.5 * 111
                dist = max(2.0, round(dist, 2))

                base_fare = 40 + (dist * 12)
                multiplier = 1.0
                if weather['is_rain']: multiplier += 0.5
                if datetime.now().hour >= 22 or datetime.now().hour < 6: multiplier += 0.25

                final_price = base_fare * multiplier
                if is_pool: final_price *= 0.7

                st.session_state.temp_booking = {
                    "pickup": pickup, "drop": drop, "price": round(final_price),
                    "p_c": p_coords, "d_c": d_coords, "pool": is_pool,
                    "num": num_passengers
                }

            if 'temp_booking' in st.session_state:
                tb = st.session_state.temp_booking
                st.write("---")
                m = folium.Map(location=tb['p_c'], zoom_start=12)
                folium.Marker(tb['p_c'], popup="Pickup", icon=folium.Icon(color="green")).add_to(m)
                folium.Marker(tb['d_c'], popup="Drop", icon=folium.Icon(color="red")).add_to(m)
                folium.PolyLine([tb['p_c'], tb['d_c']], color="blue").add_to(m)
                st_folium(m, height=250, use_container_width=True)

                st.metric("Total Fare", f"₹{tb['price']}")
                if st.button("Confirm Booking"):
                    if user['wallet'] >= tb['price']:
                        ride_id = str(uuid.uuid4())[:8]
                        ride_otp = str(random.randint(1000, 9999))
                        conn = get_db_connection()
                        conn.execute(
                            "INSERT INTO rides (id, passenger, driver, pickup, drop_loc, price, status, created_at, type, ride_otp, num_passengers) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (ride_id, user['username'], None, tb['pickup'], tb['drop'],
                             tb['price'], "Pending", str(datetime.now()),
                             "Shared" if tb['pool'] else "Private", ride_otp, tb['num']))
                        conn.commit()
                        conn.close()
                        st.session_state.active_ride_id = ride_id
                        del st.session_state.temp_booking
                        st.rerun()
                    else:
                        st.error("Insufficient Funds!")
        else:
            # --- ACTIVE RIDE STATUS ---
            st.info(f"Ride Status: **{active_ride['status']}**")

            if active_ride['status'] == 'Pending':
                st.spinner("Finding driver...")
                if st.button("Refresh"): st.rerun()
            elif active_ride['status'] == 'Accepted':
                st.success(f"Driver {active_ride['driver']} is arriving!")
                st.warning(f"🔑 OTP: **{active_ride['ride_otp']}**")

                r_dict = dict(active_ride)
                if r_dict.get('passenger2'):
                    st.info(f"👯 Co-Passenger: {r_dict['passenger2']}")

                if st.button("Refresh"): st.rerun()
            elif active_ride['status'] == 'In Progress':
                st.info("Enjoy your ride!")
                st.progress(50)
                if st.button("Refresh"): st.rerun()
            elif active_ride['status'] == 'Cancelled':
                st.error("❌ Driver cancelled the ride. Money refunded.")
                if st.button("Book New Ride"):
                    st.session_state.active_ride_id = None
                    st.rerun()

    # --- TAB B: LIVE SHARING SECTION ---
    with tab_share:
        st.subheader("🧩 Join a Shared Ride")
        st.write("Join an existing ride to save money and reduce traffic!")

        c_ref, c_spacer = st.columns([1, 4])
        if c_ref.button("🔄 Refresh List"):
            st.rerun()

        conn = get_db_connection()
        shared_rides = conn.execute("""
            SELECT * FROM rides 
            WHERE type='Shared' 
            AND status IN ('Pending', 'Accepted') 
            AND (passenger2 IS NULL OR passenger2 = '')
            AND passenger != ?
        """, (user['username'],)).fetchall()
        conn.close()

        if not shared_rides:
            st.info("No shared rides available nearby right now. Try booking your own!")
        else:
            for ride in shared_rides:
                with st.expander(f"🚗 Ride from {ride['pickup']} to {ride['drop_loc']}"):
                    c1, c2, c3 = st.columns(3)
                    c1.write(f"**Host:** {ride['passenger']}")
                    c1.write(f"**Status:** {ride['status']}")
                    c2.metric("Price", f"₹{ride['price']}")

                    if c3.button("Book Seat", key=f"join_{ride['id']}"):
                        if user['wallet'] >= ride['price']:
                            conn = get_db_connection()
                            conn.execute("UPDATE rides SET passenger2=? WHERE id=?", (user['username'], ride['id']))
                            conn.execute("UPDATE users SET wallet = wallet - ? WHERE username=?",
                                         (ride['price'], user['username']))
                            conn.commit()
                            conn.close()

                            st.balloons()
                            st.success(f"Successfully joined {ride['passenger']}'s ride!")
                            time.sleep(2)
                            st.session_state.active_ride_id = ride['id']
                            st.rerun()
                        else:
                            st.error("Insufficient Funds")

    with tab_history:
        conn = get_db_connection()
        hist = conn.execute(
            "SELECT created_at, pickup, drop_loc, price, driver, status FROM rides WHERE passenger=? OR passenger2=? ORDER BY created_at DESC",
            (user['username'], user['username'])).fetchall()
        conn.close()
        if hist:
            st.dataframe(pd.DataFrame(hist, columns=["Date", "From", "To", "Cost", "Driver", "Status"]))
        else:
            st.info("No rides yet.")

    with tab_profile:
        st.header("My Profile")
        col_img, col_info = st.columns([1, 3])
        with col_img:
            st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=120)
        with col_info:
            st.subheader(f"@{user['username']}")
            st.write(f"📧 **Email:** {user['email'] if user['email'] else 'Not Set'}")
            st.write(f"📍 **City:** {user['city']}")
            st.write(f"💰 **Wallet:** ₹{user['wallet']:.2f}")

        st.divider()
        st.subheader("Edit Details")
        with st.form("edit_prof"):
            new_email = st.text_input("Update Email", value=user['email'] if user['email'] else "")
            new_city = st.text_input("Update City", value=user['city'])
            new_pass = st.text_input("New Password (Leave blank to keep current)", type="password")

            if st.form_submit_button("Save Changes"):
                conn = get_db_connection()
                if new_pass:
                    conn.execute("UPDATE users SET city=?, email=?, password=? WHERE username=?",
                                 (new_city, new_email, new_pass, user['username']))
                else:
                    conn.execute("UPDATE users SET city=?, email=? WHERE username=?",
                                 (new_city, new_email, user['username']))
                conn.commit()
                conn.close()
                st.success("Profile Updated! Please re-login.")
                time.sleep(1.5)
                st.session_state.current_user = None
                st.rerun()


# --- 6. DRIVER DASHBOARD (FIXED) ---
def driver_dashboard(driver):
    st.sidebar.title(f"🚖 {driver['username']}")
    st.sidebar.metric("Earnings", f"₹{driver['wallet']:.2f}")
    if st.sidebar.button("Logout"):
        st.session_state.current_user = None
        st.rerun()

    conn = get_db_connection()
    # Fetch active job
    my_job = conn.execute("SELECT * FROM rides WHERE driver=? AND status IN ('Accepted', 'In Progress')",
                          (driver['username'],)).fetchone()

    if my_job:
        st.subheader("⚠️ Current Job")

        # Convert to dictionary for easy access
        job_dict = dict(my_job)

        # --- 1. JOB DETAILS CARD ---
        st.info(f"📍 Route: {job_dict['pickup']} ➝ {job_dict['drop_loc']}")

        # Display Passenger Info
        p_info = f"{job_dict['passenger']}"
        if job_dict.get('num_passengers'):
            p_info += f" ({job_dict['num_passengers']} people)"
        else:
            p_info += " (1 person)"

        st.write(f"👤 **Passenger:** {p_info}")
        if job_dict.get('passenger2'):
            st.write(f"👯 **Co-Passenger:** {job_dict['passenger2']}")

        st.write(f"💰 **Earnings:** ₹{job_dict['price']}")
        st.divider()

        # --- 2. ACTION BUTTONS ---

        # [CANCEL BUTTON] - Placed here to be visible immediately
        col_cancel, col_action = st.columns([1, 2])

        with col_cancel:
            if st.button("🚫 Cancel Ride", key="cancel_ride_btn", type="secondary"):
                # Logic: Refund everyone and mark as Cancelled
                conn.execute("UPDATE rides SET status='Cancelled', driver=NULL WHERE id=?", (job_dict['id'],))

                # Refund Passenger 1
                conn.execute("UPDATE users SET wallet = wallet + ? WHERE username=?",
                             (job_dict['price'], job_dict['passenger']))

                # Refund Passenger 2 (if any)
                if job_dict.get('passenger2'):
                    conn.execute("UPDATE users SET wallet = wallet + ? WHERE username=?",
                                 (job_dict['price'], job_dict['passenger2']))

                conn.commit()
                st.warning("Ride Cancelled. Refund processed.")
                time.sleep(2)
                st.rerun()

        with col_action:
            # STATUS: ACCEPTED -> START TRIP
            if job_dict['status'] == 'Accepted':
                otp = st.text_input("Enter Passenger OTP:", key="otp_input")
                if st.button("▶️ Start Trip", type="primary"):
                    if otp == job_dict['ride_otp']:
                        conn.execute("UPDATE rides SET status='In Progress' WHERE id=?", (job_dict['id'],))
                        conn.commit()
                        st.success("OTP Verified! Driving...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Wrong OTP")

            # STATUS: IN PROGRESS -> END TRIP
            elif job_dict['status'] == 'In Progress':
                if st.button("🏁 Complete Trip", type="primary"):
                    conn.execute("UPDATE rides SET status='Completed' WHERE id=?", (job_dict['id'],))

                    # Calculate Cuts
                    driver_cut = job_dict['price'] * 0.8
                    plat_cut = job_dict['price'] * 0.2

                    # Add Money to Driver
                    if job_dict.get('passenger2'):
                        driver_cut += (job_dict['price'] * 0.8)  # Double fare for pool

                    conn.execute("UPDATE drivers SET wallet = wallet + ?, rides_done = rides_done + 1 WHERE username=?",
                                 (driver_cut, driver['username']))
                    conn.execute("UPDATE platform SET total_earnings = total_earnings + ? WHERE id=1", (plat_cut,))

                    conn.commit()
                    st.balloons()
                    st.success(f"Trip Done! Earned ₹{driver_cut}")
                    time.sleep(2)
                    st.rerun()

    else:
        # --- JOB FEED (If no active ride) ---
        st.subheader("📡 Job Feed")
        pending = conn.execute("SELECT * FROM rides WHERE status='Pending'").fetchall()

        if not pending:
            st.info("No active requests nearby.")
            if st.button("Refresh Feed"): st.rerun()
        else:
            for r in pending:
                r_dict = dict(r)
                p_count = f"({r_dict.get('num_passengers', 1)} ppl)"

                with st.expander(f"📍 {r['pickup']} ➝ {r['drop_loc']} | ₹{r['price']}"):
                    st.write(f"👤 **Passenger:** {r['passenger']} {p_count}")
                    if r['type'] == 'Shared': st.caption("🧩 Shared Ride")

                    if st.button("✅ Accept Ride", key=f"accept_{r['id']}"):
                        conn.execute("UPDATE rides SET status='Accepted', driver=? WHERE id=?",
                                     (driver['username'], r['id']))
                        conn.commit()
                        st.success("Accepted! Check 'Current Job'.")
                        time.sleep(1)
                        st.rerun()
    conn.close()
# --- 7. ADMIN DASHBOARD ---
def admin_dashboard():
    st.title("🛡️ Admin Panel")
    if st.sidebar.button("Logout"):
        st.session_state.current_user = None
        st.rerun()

    conn = get_db_connection()
    earnings = conn.execute("SELECT total_earnings FROM platform WHERE id=1").fetchone()[0]
    u_count = conn.execute("SELECT count(*) FROM users").fetchone()[0]
    d_count = conn.execute("SELECT count(*) FROM drivers").fetchone()[0]

    # KPIs
    k1, k2, k3 = st.columns(3)
    k1.metric("Platform Profit", f"₹{earnings:.2f}")
    k2.metric("Total Passengers", u_count)
    k3.metric("Total Drivers", d_count)

    st.divider()

    st.subheader("📊 Visual Analytics")
    g1, g2 = st.columns(2)
    with g1:
        st.caption("Top Earning Drivers")
        d_data = conn.execute("SELECT username, wallet FROM drivers ORDER BY wallet DESC LIMIT 5").fetchall()
        if d_data:
            df_d = pd.DataFrame(d_data, columns=["Driver", "Earnings"]).set_index("Driver")
            st.bar_chart(df_d)
        else:
            st.info("No driver data yet.")

    with g2:
        st.caption("Ride Status")
        s_data = conn.execute("SELECT status, count(*) FROM rides GROUP BY status").fetchall()
        if s_data:
            df_s = pd.DataFrame(s_data, columns=["Status", "Count"]).set_index("Status")
            st.bar_chart(df_s)
        else:
            st.info("No rides yet.")

    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Users")
        users = conn.execute("SELECT username, city, wallet, email FROM users").fetchall()
        st.dataframe(pd.DataFrame(users, columns=["User", "City", "Wallet", "Email"]))

    with c2:
        st.subheader("Drivers")
        drivers = conn.execute("SELECT username, rating, rides_done, wallet FROM drivers").fetchall()
        st.dataframe(pd.DataFrame(drivers, columns=["Driver", "Rating", "Rides", "Earnings"]))

    conn.close()


# --- 8. MAIN ENTRY ---
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

if st.session_state.current_user:
    role = st.session_state.user_role
    if role == "Passenger":
        passenger_dashboard(st.session_state.current_user)
    elif role == "Driver":
        driver_dashboard(st.session_state.current_user)
    elif role == "Admin":
        admin_dashboard()
else:
    auth_system()

