import mysql.connector
from mysql.connector import Error
from getpass import getpass
import datetime

# ---------- DB CONFIG ----------
DB_CONFIG = {
    "host": "localhost",
    "user": "aero_user",      # change
    "password": "aero_pass",  # change
    "database": "aeronavigator"
}

# ---------- DB HELPERS ----------
def get_conn():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print("DB error:", e)
        return None

def execute(query, params=()):
    conn = get_conn()
    if not conn: return False
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    cur.close()
    conn.close()
    return True

def query_all(query, params=()):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def query_one(query, params=()):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute(query, params)
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

# ---------- USER FUNCTIONS ----------
def register():
    print("\n--- Register ---")
    name = input("Name: ").strip()
    email = input("Email: ").strip().lower()
    pwd = getpass("Password: ")
    exists = query_one("SELECT id FROM users WHERE email=%s", (email,))
    if exists:
        print("❌ Email already registered.")
        return
    execute("INSERT INTO users (name,email,password_hash,is_admin) VALUES (%s,%s,%s,0)", (name,email,pwd))
    print("✅ Registered successfully!")

def login():
    print("\n--- Login ---")
    email = input("Email: ").strip().lower()
    pwd = getpass("Password: ")
    user = query_one("SELECT * FROM users WHERE email=%s AND password_hash=%s", (email,pwd))
    if not user:
        print("❌ Invalid credentials")
        return None
    print(f"✅ Welcome {user['name']}!")
    return user

# ---------- FLIGHT FUNCTIONS ----------
def view_flights():
    flights = query_all("SELECT * FROM flights ORDER BY departure_time LIMIT 20")
    if not flights:
        print("No flights found.")
        return
    print("\n--- Flights ---")
    for f in flights:
        print(f"{f['id']}: {f['flight_number']} {f['origin']} → {f['destination']} at {f['departure_time']} | Seats {f['seats_available']} | ₹{f['price']}")

def search_flights():
    frm = input("From: ").strip()
    to = input("To: ").strip()
    date = input("Date (YYYY-MM-DD, optional): ").strip()
    q = "SELECT * FROM flights WHERE origin LIKE %s AND destination LIKE %s"
    params = [f"%{frm}%", f"%{to}%"]
    if date:
        try:
            d = datetime.datetime.strptime(date, "%Y-%m-%d")
            q += " AND departure_time BETWEEN %s AND %s"
            params.extend([d, d + datetime.timedelta(days=1)])
        except:
            print("⚠ Invalid date format, ignoring.")
    flights = query_all(q, tuple(params))
    if not flights:
        print("❌ No matching flights")
        return
    print("\n--- Search Results ---")
    for f in flights:
        print(f"{f['id']}: {f['flight_number']} {f['origin']} → {f['destination']} at {f['departure_time']} | Seats {f['seats_available']} | ₹{f['price']}")

def book_flight(user):
    fid = int(input("Enter flight ID to book: "))
    seats = int(input("Seats: "))
    f = query_one("SELECT * FROM flights WHERE id=%s", (fid,))
    if not f:
        print("❌ Flight not found")
        return
    if f['seats_available'] < seats:
        print("❌ Not enough seats available")
        return
    execute("INSERT INTO bookings (user_id,flight_id,seats,booked_at) VALUES (%s,%s,%s,%s)",
            (user['id'], fid, seats, datetime.datetime.now()))
    execute("UPDATE flights SET seats_available=seats_available-%s WHERE id=%s", (seats, fid))
    print("✅ Booking successful!")

def my_bookings(user):
    rows = query_all("""
      SELECT b.id,f.flight_number,f.origin,f.destination,f.departure_time,b.seats,f.price
      FROM bookings b JOIN flights f ON b.flight_id=f.id
      WHERE b.user_id=%s ORDER BY b.booked_at DESC
    """,(user['id'],))
    if not rows:
        print("No bookings yet.")
        return
    print("\n--- My Bookings ---")
    for b in rows:
        print(f"{b['id']}: {b['flight_number']} {b['origin']}→{b['destination']} | {b['seats']} seats | Total ₹{b['price']*b['seats']}")

# ---------- ADMIN ----------
def admin_add_flight():
    fn = input("Flight number: ")
    origin = input("Origin: ")
    dest = input("Destination: ")
    dt = input("Departure (YYYY-MM-DD HH:MM): ")
    seats = int(input("Seats: "))
    price = float(input("Price: "))
    try:
        dep = datetime.datetime.strptime(dt,"%Y-%m-%d %H:%M")
    except:
        print("❌ Invalid datetime format")
        return
    execute("INSERT INTO flights (flight_number,origin,destination,departure_time,seats_available,price) VALUES (%s,%s,%s,%s,%s,%s)",
            (fn,origin,dest,dep,seats,price))
    print("✅ Flight added.")

# ---------- MAIN MENU ----------
def main():
    user=None
    while True:
        if not user:
            print("\n==== AeroNavigator ====")
            print("1. Register\n2. Login\n0. Exit")
            ch=input("Choice: ")
            if ch=='1': register()
            elif ch=='2': user=login()
            elif ch=='0': break
        else:
            print(f"\n==== Menu (Logged in as {user['name']}) ====")
            print("1. View Flights\n2. Search Flights\n3. Book Flight\n4. My Bookings")
            if user['is_admin']==1:
                print("5. Add Flight (Admin)")
            print("6. Logout\n0. Exit")
            ch=input("Choice: ")
            if ch=='1': view_flights()
            elif ch=='2': search_flights()
            elif ch=='3': book_flight(user)
            elif ch=='4': my_bookings(user)
            elif ch=='5' and user['is_admin']==1: admin_add_flight()
            elif ch=='6': user=None
            elif ch=='0': break

if __name__=="__main__":
    main()
