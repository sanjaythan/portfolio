
import re
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

import mysql.connector
from mysql.connector import Error
import streamlit as st


# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Hotel & Restaurant Management",
    page_icon="🏨",
    layout="wide"
)

st.title("🏨 Centralized Hotel & Restaurant Management System")
st.caption(
    "Review 3 Prototype — "
    "SANJAY THANDEESWARAN (25BCE2759) & "
    "MONISH KUMAR T O (25BCE2819)"
)


# =========================================================
# 2. DATABASE CONNECTION SETTINGS
# =========================================================

with st.sidebar:
    st.header("🔑 Database Connection")

    db_host = st.text_input("MySQL Host", value="localhost")
    db_user = st.text_input("MySQL User", value="root")
    db_pwd = st.text_input("MySQL Password", type="password")
    db_name = st.text_input("Database Name", value="HRMS")

    connect_btn = st.button(
        "Initialize / Test Database",
        type="primary",
        use_container_width=True
    )

    st.caption(
        "Enter your local MySQL credentials. "
        "The database and required tables will be created if permitted."
    )


# =========================================================
# 3. DATABASE CONNECTION HELPERS
# =========================================================

def validate_database_name(name):
    """Allow only simple SQL database identifiers."""
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", name):
        raise ValueError(
            "Database name must start with a letter and contain "
            "only letters, numbers, and underscores."
        )


def server_connection():
    """Connect to MySQL without selecting a database."""
    return mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_pwd,
        connection_timeout=5
    )


def get_connection():
    """Connect to the selected application database."""
    return mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_pwd,
        database=db_name,
        connection_timeout=5
    )


def close_db(conn=None, cursor=None):
    """Close database resources safely."""
    if cursor is not None:
        try:
            cursor.close()
        except Error:
            pass

    if conn is not None:
        try:
            if conn.is_connected():
                conn.close()
        except Error:
            pass


# =========================================================
# 4. CREATE DATABASE TABLES AND VIEW
# =========================================================

def initialize_database():
    validate_database_name(db_name)

    conn = None
    cursor = None

    try:
        conn = server_connection()
        cursor = conn.cursor()

        # Database name has been validated above.
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{db_name}`"
        )

        close_db(conn, cursor)
        conn = get_connection()
        cursor = conn.cursor()

        statements = [
            """
            CREATE TABLE IF NOT EXISTS Guest (
                Guest_ID INT AUTO_INCREMENT PRIMARY KEY,
                Guest_Name VARCHAR(100) NOT NULL,
                Phone VARCHAR(20) NOT NULL,
                Email VARCHAR(120),
                Address TEXT
            ) ENGINE=InnoDB
            """,

            """
            CREATE TABLE IF NOT EXISTS Room (
                Room_ID INT AUTO_INCREMENT PRIMARY KEY,
                Room_Number VARCHAR(20) NOT NULL UNIQUE,
                Room_Type VARCHAR(40) NOT NULL,
                Price_Per_Night DECIMAL(10,2) NOT NULL,
                Status ENUM(
                    'Available', 'Occupied', 'Maintenance'
                ) NOT NULL DEFAULT 'Available',
                CHECK (Price_Per_Night >= 0)
            ) ENGINE=InnoDB
            """,

            """
            CREATE TABLE IF NOT EXISTS Reservation (
                Reservation_ID INT AUTO_INCREMENT PRIMARY KEY,
                Guest_ID INT NOT NULL,
                Room_ID INT NOT NULL,
                Check_In_Date DATE NOT NULL,
                Check_Out_Date DATE NOT NULL,
                Number_of_Guests INT NOT NULL DEFAULT 1,
                Reservation_Status ENUM(
                    'Confirmed', 'Cancelled', 'Completed'
                ) NOT NULL DEFAULT 'Confirmed',
                Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_reservation_guest
                    FOREIGN KEY (Guest_ID)
                    REFERENCES Guest(Guest_ID),
                CONSTRAINT fk_reservation_room
                    FOREIGN KEY (Room_ID)
                    REFERENCES Room(Room_ID),
                CHECK (Check_Out_Date > Check_In_Date),
                CHECK (Number_of_Guests >= 1)
            ) ENGINE=InnoDB
            """,

            """
            CREATE TABLE IF NOT EXISTS Restaurant (
                Restaurant_ID INT AUTO_INCREMENT PRIMARY KEY,
                Restaurant_Name VARCHAR(100) NOT NULL,
                Location VARCHAR(150),
                Contact_Number VARCHAR(20)
            ) ENGINE=InnoDB
            """,

            """
            CREATE TABLE IF NOT EXISTS Menu_Item (
                Item_ID INT AUTO_INCREMENT PRIMARY KEY,
                Restaurant_ID INT NOT NULL,
                Item_Name VARCHAR(100) NOT NULL,
                Category VARCHAR(50),
                Price DECIMAL(10,2) NOT NULL,
                Availability ENUM(
                    'Available', 'Unavailable'
                ) NOT NULL DEFAULT 'Available',
                FOREIGN KEY (Restaurant_ID)
                    REFERENCES Restaurant(Restaurant_ID),
                CHECK (Price >= 0)
            ) ENGINE=InnoDB
            """,

            """
            CREATE TABLE IF NOT EXISTS Food_Order (
                Order_ID INT AUTO_INCREMENT PRIMARY KEY,
                Guest_ID INT NOT NULL,
                Restaurant_ID INT NOT NULL,
                Order_Date DATE NOT NULL,
                Order_Time TIME NOT NULL,
                Order_Status ENUM(
                    'Pending', 'Preparing',
                    'Completed', 'Cancelled'
                ) NOT NULL DEFAULT 'Pending',
                Total_Amount DECIMAL(10,2) NOT NULL DEFAULT 0,
                FOREIGN KEY (Guest_ID)
                    REFERENCES Guest(Guest_ID),
                FOREIGN KEY (Restaurant_ID)
                    REFERENCES Restaurant(Restaurant_ID),
                CHECK (Total_Amount >= 0)
            ) ENGINE=InnoDB
            """,

            """
            CREATE TABLE IF NOT EXISTS Order_Item (
                Order_Item_ID INT AUTO_INCREMENT PRIMARY KEY,
                Order_ID INT NOT NULL,
                Item_ID INT NOT NULL,
                Quantity INT NOT NULL,
                Unit_Price DECIMAL(10,2) NOT NULL,
                Subtotal DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (Order_ID)
                    REFERENCES Food_Order(Order_ID),
                FOREIGN KEY (Item_ID)
                    REFERENCES Menu_Item(Item_ID),
                CHECK (Quantity >= 1),
                CHECK (Unit_Price >= 0),
                CHECK (Subtotal >= 0)
            ) ENGINE=InnoDB
            """,

            """
            CREATE TABLE IF NOT EXISTS Payment (
                Payment_ID INT AUTO_INCREMENT PRIMARY KEY,
                Guest_ID INT NOT NULL,
                Reservation_ID INT NULL,
                Payment_Date DATE NOT NULL,
                Amount DECIMAL(10,2) NOT NULL,
                Payment_Method ENUM(
                    'Cash', 'Card', 'UPI', 'Bank Transfer'
                ) NOT NULL DEFAULT 'Cash',
                Payment_Status ENUM(
                    'Paid', 'Pending', 'Refunded'
                ) NOT NULL DEFAULT 'Paid',
                FOREIGN KEY (Guest_ID)
                    REFERENCES Guest(Guest_ID),
                FOREIGN KEY (Reservation_ID)
                    REFERENCES Reservation(Reservation_ID),
                CHECK (Amount >= 0)
            ) ENGINE=InnoDB
            """,

            """
            CREATE TABLE IF NOT EXISTS Staff (
                Staff_ID INT AUTO_INCREMENT PRIMARY KEY,
                Name VARCHAR(100) NOT NULL,
                Role VARCHAR(50) NOT NULL,
                Phone VARCHAR(20),
                Email VARCHAR(120)
            ) ENGINE=InnoDB
            """,

            """
            CREATE TABLE IF NOT EXISTS Service_Request (
                Service_ID INT AUTO_INCREMENT PRIMARY KEY,
                Guest_ID INT NOT NULL,
                Staff_ID INT NULL,
                Service_Type VARCHAR(100) NOT NULL,
                Request_Date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                Status ENUM(
                    'Pending', 'In Progress', 'Completed'
                ) NOT NULL DEFAULT 'Pending',
                FOREIGN KEY (Guest_ID)
                    REFERENCES Guest(Guest_ID),
                FOREIGN KEY (Staff_ID)
                    REFERENCES Staff(Staff_ID)
            ) ENGINE=InnoDB
            """
        ]

        for statement in statements:
            cursor.execute(statement)

        # View for reservation and payment summaries.
        cursor.execute("DROP VIEW IF EXISTS View_Active_Billing_Summary")

        cursor.execute(
            """
            CREATE VIEW View_Active_Billing_Summary AS
            SELECT
                r.Reservation_ID,
                g.Guest_ID,
                g.Guest_Name,
                rm.Room_Number,
                r.Check_In_Date,
                r.Check_Out_Date,
                r.Reservation_Status,
                COALESCE(SUM(
                    CASE
                        WHEN p.Payment_Status = 'Paid'
                        THEN p.Amount
                        ELSE 0
                    END
                ), 0) AS Amount_Paid
            FROM Reservation r
            JOIN Guest g ON r.Guest_ID = g.Guest_ID
            JOIN Room rm ON r.Room_ID = rm.Room_ID
            LEFT JOIN Payment p
                ON r.Reservation_ID = p.Reservation_ID
            WHERE r.Reservation_Status = 'Confirmed'
            GROUP BY
                r.Reservation_ID,
                g.Guest_ID,
                g.Guest_Name,
                rm.Room_Number,
                r.Check_In_Date,
                r.Check_Out_Date,
                r.Reservation_Status
            """
        )

        conn.commit()
        return True, "Database and tables initialized successfully."

    except (Error, ValueError) as err:
        if conn is not None:
            try:
                conn.rollback()
            except Error:
                pass

        return False, str(err)

    finally:
        close_db(conn, cursor)


# Initialize the database when the sidebar button is clicked.
if connect_btn:
    success, message = initialize_database()

    if success:
        st.session_state["db_ready"] = True
        st.sidebar.success(message)
    else:
        st.session_state["db_ready"] = False
        st.sidebar.error(message)


# =========================================================
# 5. DATABASE STATUS
# =========================================================

if "db_ready" not in st.session_state:
    st.session_state["db_ready"] = False

if st.session_state["db_ready"]:
    st.sidebar.success("Database initialized in this session.")
else:
    st.info(
        "👈 Enter your MySQL credentials in the sidebar and click "
        "**Initialize / Test Database** to begin."
    )


# =========================================================
# 6. REUSABLE DATABASE QUERY HELPERS
# =========================================================

def fetch_all(sql, params=()):
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params)
        return cursor.fetchall()

    finally:
        close_db(conn, cursor)


def execute_write(sql, params=()):
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()

        return cursor.lastrowid, cursor.rowcount

    except Error:
        if conn is not None:
            conn.rollback()
        raise

    finally:
        close_db(conn, cursor)


def money(value):
    return Decimal(str(value)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


def valid_phone(phone):
    digits = re.sub(r"\D", "", phone)
    return len(digits) == 10


# =========================================================
# 7. MODULE SELECTION
# =========================================================

module = st.selectbox(
    "Select Module",
    [
        "1. Guest Management (CRUD)",
        "2. Room Availability & Search",
        "3. Food Orders & Subtotal",
        "4. Advanced SQL Analytics & Views",
        "5. Test Cases & Validation"
    ]
)


# =========================================================
# MODULE 1: GUEST CRUD
# =========================================================

if module == "1. Guest Management (CRUD)":
    st.header("👤 Guest Management Operations")

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Add Guest",
            "View / Search Guests",
            "Update Guest",
            "Delete Guest"
        ]
    )

    with tab1:
        st.subheader("Register New Guest")

        with st.form("add_guest_form"):
            name = st.text_input("Full Name *")
            phone = st.text_input("Phone Number (10 digits) *")
            email = st.text_input("Email Address")
            address = st.text_area("Postal Address")

            submitted = st.form_submit_button("Save Guest")

        if submitted:
            if not name.strip():
                st.error("Guest name is required.")
            elif not valid_phone(phone):
                st.error("Enter a valid 10-digit phone number.")
            elif email.strip() and not re.fullmatch(
                r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()
            ):
                st.error("Enter a valid email address.")
            else:
                try:
                    guest_id, _ = execute_write(
                        """
                        INSERT INTO Guest
                            (Guest_Name, Phone, Email, Address)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            name.strip(),
                            phone.strip(),
                            email.strip() or None,
                            address.strip() or None
                        )
                    )

                    st.success(
                        f"Guest registered successfully! Guest ID: {guest_id}"
                    )

                except Error as err:
                    st.error(f"Database Error: {err}")

    with tab2:
        st.subheader("Search and Retrieve Guests")

        search_term = st.text_input(
            "Search by guest name or phone number"
        )

        if st.button("Search Guests"):
            try:
                if search_term.strip():
                    rows = fetch_all(
                        """
                        SELECT *
                        FROM Guest
                        WHERE Guest_Name LIKE %s OR Phone LIKE %s
                        ORDER BY Guest_ID DESC
                        """,
                        (
                            f"%{search_term.strip()}%",
                            f"%{search_term.strip()}%"
                        )
                    )
                else:
                    rows = fetch_all(
                        "SELECT * FROM Guest ORDER BY Guest_ID DESC"
                    )

                if rows:
                    st.dataframe(rows, use_container_width=True)
                else:
                    st.info("No guests found.")

            except Error as err:
                st.error(f"Database Error: {err}")

    with tab3:
        st.subheader("Update Guest Details")

        with st.form("update_guest_form"):
            gid_update = st.number_input(
                "Guest ID",
                min_value=1,
                step=1,
                key="update_guest_id"
            )

            new_name = st.text_input("New Guest Name")
            new_phone = st.text_input("New Phone Number")
            new_email = st.text_input("New Email Address")

            update_btn = st.form_submit_button("Update Guest")

        if update_btn:
            if not new_name.strip():
                st.error("Guest name cannot be empty.")
            elif not valid_phone(new_phone):
                st.error("Enter a valid 10-digit phone number.")
            elif new_email.strip() and not re.fullmatch(
                r"[^@\s]+@[^@\s]+\.[^@\s]+", new_email.strip()
            ):
                st.error("Enter a valid email address.")
            else:
                try:
                    _, affected = execute_write(
                        """
                        UPDATE Guest
                        SET Guest_Name = %s, Phone = %s, Email = %s
                        WHERE Guest_ID = %s
                        """,
                        (
                            new_name.strip(),
                            new_phone.strip(),
                            new_email.strip() or None,
                            gid_update
                        )
                    )

                    if affected:
                        st.success("Guest record updated successfully.")
                    else:
                        st.warning(
                            "No record changed. Check the ID or values."
                        )

                except Error as err:
                    st.error(f"Database Error: {err}")

    with tab4:
        st.subheader("Delete Guest Record")

        st.warning(
            "A guest with related reservations, orders, payments, "
            "or service requests cannot be deleted until those records "
            "are handled."
        )

        with st.form("delete_guest_form"):
            gid_del = st.number_input(
                "Guest ID to Delete",
                min_value=1,
                step=1,
                key="delete_guest_id"
            )

            confirm_delete = st.checkbox(
                "I confirm that I want to delete this guest."
            )

            delete_btn = st.form_submit_button("Delete Guest")

        if delete_btn:
            if not confirm_delete:
                st.error("Confirm the deletion first.")
            else:
                try:
                    _, affected = execute_write(
                        "DELETE FROM Guest WHERE Guest_ID = %s",
                        (gid_del,)
                    )

                    if affected:
                        st.success("Guest deleted successfully.")
                    else:
                        st.warning("Guest ID not found.")

                except Error as err:
                    st.error(
                        "Guest could not be deleted. Related records "
                        f"may exist. Database message: {err}"
                    )


# =========================================================
# MODULE 2: ROOM SEARCH AND AVAILABILITY
# =========================================================

elif module == "2. Room Availability & Search":
    st.header("🛏️ Room Availability & Search")

    tab1, tab2 = st.tabs(["Room Inventory", "Date-Based Availability"])

    with tab1:
        status_filter = st.selectbox(
            "Filter by Room Status",
            ["All", "Available", "Occupied", "Maintenance"]
        )

        if st.button("Load Rooms"):
            try:
                if status_filter == "All":
                    rooms = fetch_all(
                        "SELECT * FROM Room ORDER BY Price_Per_Night ASC"
                    )
                else:
                    rooms = fetch_all(
                        """
                        SELECT *
                        FROM Room
                        WHERE Status = %s
                        ORDER BY Price_Per_Night ASC
                        """,
                        (status_filter,)
                    )

                if rooms:
                    st.dataframe(rooms, use_container_width=True)
                else:
                    st.info("No rooms found. Add room records in MySQL.")

            except Error as err:
                st.error(f"Database Error: {err}")

    with tab2:
        st.subheader("Check Room Availability for Dates")

        today = date.today()

        col1, col2 = st.columns(2)

        with col1:
            check_in = st.date_input(
                "Check-in Date",
                value=today,
                min_value=today,
                key="room_check_in"
            )

        with col2:
            check_out = st.date_input(
                "Check-out Date",
                value=today + timedelta(days=1),
                min_value=today + timedelta(days=1),
                key="room_check_out"
            )

        if st.button("Find Available Rooms"):
            if check_out <= check_in:
                st.error("Check-out must be after check-in.")
            else:
                try:
                    rooms = fetch_all(
                        """
                        SELECT rm.*
                        FROM Room rm
                        WHERE rm.Status = 'Available'
                          AND NOT EXISTS (
                              SELECT 1
                              FROM Reservation r
                              WHERE r.Room_ID = rm.Room_ID
                                AND r.Reservation_Status = 'Confirmed'
                                AND r.Check_In_Date < %s
                                AND r.Check_Out_Date > %s
                          )
                        ORDER BY rm.Price_Per_Night ASC
                        """,
                        (check_out, check_in)
                    )

                    if rooms:
                        st.success(
                            f"Found {len(rooms)} room(s) for "
                            f"{check_in} to {check_out}."
                        )
                        st.dataframe(rooms, use_container_width=True)
                    else:
                        st.info(
                            "No rooms match the selected dates. "
                            "Check the room status and reservations."
                        )

                except Error as err:
                    st.error(f"Database Error: {err}")


# =========================================================
# MODULE 3: FOOD ORDER AND SUBTOTAL
# =========================================================

elif module == "3. Food Orders & Subtotal":
    st.header("🍽️ Food Orders & Automatic Subtotal")

    st.caption(
        "Place an order containing one menu item. "
        "The schema supports multiple Order_Item records per order."
    )

    try:
        guests = fetch_all(
            "SELECT Guest_ID, Guest_Name FROM Guest ORDER BY Guest_Name"
        )
        restaurants = fetch_all(
            """
            SELECT Restaurant_ID, Restaurant_Name
            FROM Restaurant
            ORDER BY Restaurant_Name
            """
        )

        if not guests:
            st.warning("Add at least one guest before placing an order.")

        elif not restaurants:
            st.warning(
                "Add a restaurant and its menu items in MySQL first."
            )

        else:
            guest_options = {
                f"{g['Guest_Name']} (ID: {g['Guest_ID']})": g["Guest_ID"]
                for g in guests
            }

            restaurant_options = {
                f"{r['Restaurant_Name']} (ID: {r['Restaurant_ID']})":
                r["Restaurant_ID"]
                for r in restaurants
            }

            with st.form("order_form"):
                selected_guest = st.selectbox(
                    "Select Guest",
                    list(guest_options.keys())
                )

                selected_restaurant = st.selectbox(
                    "Select Restaurant",
                    list(restaurant_options.keys())
                )

                item_id = st.number_input(
                    "Menu Item ID",
                    min_value=1,
                    step=1
                )

                qty = st.number_input(
                    "Quantity",
                    min_value=1,
                    max_value=100,
                    step=1
                )

                order_btn = st.form_submit_button("Submit Order")

            if order_btn:
                guest_id = guest_options[selected_guest]
                restaurant_id = restaurant_options[selected_restaurant]

                conn = None
                cursor = None

                try:
                    conn = get_connection()
                    cursor = conn.cursor(dictionary=True)

                    # Verify that the item belongs to this restaurant.
                    cursor.execute(
                        """
                        SELECT Item_ID, Item_Name, Price, Availability
                        FROM Menu_Item
                        WHERE Item_ID = %s
                          AND Restaurant_ID = %s
                        """,
                        (item_id, restaurant_id)
                    )

                    dish = cursor.fetchone()

                    if not dish:
                        st.error(
                            "The menu item does not exist in the "
                            "selected restaurant."
                        )

                    elif dish["Availability"] != "Available":
                        st.error("This menu item is unavailable.")

                    else:
                        unit_price = money(dish["Price"])
                        subtotal = money(unit_price * int(qty))

                        # Create order and its item atomically.
                        cursor.execute(
                            """
                            INSERT INTO Food_Order (
                                Guest_ID, Restaurant_ID,
                                Order_Date, Order_Time,
                                Order_Status, Total_Amount
                            )
                            VALUES (
                                %s, %s, %s, CURTIME(),
                                'Completed', %s
                            )
                            """,
                            (
                                guest_id,
                                restaurant_id,
                                date.today(),
                                subtotal
                            )
                        )

                        new_order_id = cursor.lastrowid

                        cursor.execute(
                            """
                            INSERT INTO Order_Item (
                                Order_ID, Item_ID, Quantity,
                                Unit_Price, Subtotal
                            )
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (
                                new_order_id,
                                item_id,
                                int(qty),
                                unit_price,
                                subtotal
                            )
                        )

                        conn.commit()

                        st.success(
                            f"Order #{new_order_id} placed successfully!"
                        )

                        st.write(f"**Item:** {dish['Item_Name']}")
                        st.write(f"**Quantity:** {qty}")
                        st.write(f"**Unit price:** ₹{unit_price:.2f}")
                        st.write(f"**Subtotal:** ₹{subtotal:.2f}")

                except Error as err:
                    if conn is not None:
                        conn.rollback()

                    st.error(f"Order transaction failed: {err}")

                finally:
                    close_db(conn, cursor)

    except Error as err:
        st.error(f"Unable to load guests or restaurants: {err}")

    st.divider()
    st.subheader("Recent Food Orders")

    if st.button("Load Food Order History"):
        try:
            orders = fetch_all(
                """
                SELECT
                    fo.Order_ID,
                    g.Guest_Name,
                    r.Restaurant_Name,
                    fo.Order_Date,
                    fo.Order_Time,
                    fo.Order_Status,
                    fo.Total_Amount
                FROM Food_Order fo
                JOIN Guest g ON fo.Guest_ID = g.Guest_ID
                JOIN Restaurant r
                    ON fo.Restaurant_ID = r.Restaurant_ID
                ORDER BY fo.Order_ID DESC
                """
            )

            if orders:
                st.dataframe(orders, use_container_width=True)
            else:
                st.info("No food orders have been recorded.")

        except Error as err:
            st.error(f"Database Error: {err}")


# =========================================================
# MODULE 4: ADVANCED SQL ANALYTICS AND VIEWS
# =========================================================

elif module == "4. Advanced SQL Analytics & Views":
    st.header("📊 Advanced SQL Analytics & Views")

    query_choice = st.selectbox(
        "Select Analytical Report",
        [
            "1. JOIN & Aggregate: Total Spend per Guest",
            "2. GROUP BY & HAVING: Categories with Average Price > ₹100",
            "3. Subquery: Guests with Above-Average Order Value",
            "4. View: Active Billing Summary",
            "5. JOIN: Most Ordered Menu Items",
            "6. Aggregate: Total Revenue by Restaurant",
            "7. Subquery: Rooms Priced Above Average"
        ]
    )

    query_map = {
        "1": """
            SELECT
                g.Guest_ID,
                g.Guest_Name,
                COUNT(p.Payment_ID) AS Total_Payments,
                COALESCE(SUM(
                    CASE
                        WHEN p.Payment_Status = 'Paid'
                        THEN p.Amount ELSE 0
                    END
                ), 0) AS Total_Spent
            FROM Guest g
            LEFT JOIN Payment p ON g.Guest_ID = p.Guest_ID
            GROUP BY g.Guest_ID, g.Guest_Name
            ORDER BY Total_Spent DESC
        """,

        "2": """
            SELECT
                Category,
                COUNT(*) AS Total_Items,
                AVG(Price) AS Average_Price
            FROM Menu_Item
            GROUP BY Category
            HAVING AVG(Price) > 100.00
        """,

        "3": """
            SELECT DISTINCT
                g.Guest_ID,
                g.Guest_Name,
                g.Email,
                g.Phone
            FROM Guest g
            JOIN Food_Order fo ON g.Guest_ID = fo.Guest_ID
            WHERE fo.Total_Amount > (
                SELECT AVG(Total_Amount)
                FROM Food_Order
                WHERE Order_Status <> 'Cancelled'
            )
        """,

        "4": """
            SELECT *
            FROM View_Active_Billing_Summary
            ORDER BY Check_In_Date
        """,

        "5": """
            SELECT
                mi.Item_ID,
                mi.Item_Name,
                SUM(oi.Quantity) AS Total_Quantity_Ordered,
                SUM(oi.Subtotal) AS Total_Sales
            FROM Menu_Item mi
            JOIN Order_Item oi ON mi.Item_ID = oi.Item_ID
            JOIN Food_Order fo ON oi.Order_ID = fo.Order_ID
            WHERE fo.Order_Status <> 'Cancelled'
            GROUP BY mi.Item_ID, mi.Item_Name
            ORDER BY Total_Quantity_Ordered DESC
        """,

        "6": """
            SELECT
                r.Restaurant_ID,
                r.Restaurant_Name,
                COUNT(fo.Order_ID) AS Number_of_Orders,
                COALESCE(SUM(
                    CASE
                        WHEN fo.Order_Status <> 'Cancelled'
                        THEN fo.Total_Amount ELSE 0
                    END
                ), 0) AS Total_Revenue
            FROM Restaurant r
            LEFT JOIN Food_Order fo
                ON r.Restaurant_ID = fo.Restaurant_ID
            GROUP BY r.Restaurant_ID, r.Restaurant_Name
            ORDER BY Total_Revenue DESC
        """,

        "7": """
            SELECT Room_ID, Room_Number, Room_Type, Price_Per_Night
            FROM Room
            WHERE Price_Per_Night > (
                SELECT AVG(Price_Per_Night) FROM Room
            )
            ORDER BY Price_Per_Night DESC
        """
    }

    if st.button("Execute Query", type="primary"):
        query_key = query_choice.split(".")[0]
        sql = query_map[query_key]

        st.subheader("SQL Query")
        st.code(sql.strip(), language="sql")

        try:
            results = fetch_all(sql)

            if results:
                st.success(f"Query executed. {len(results)} row(s) returned.")
                st.dataframe(results, use_container_width=True)
            else:
                st.info(
                    "Query executed successfully, but no rows were returned."
                )

        except Error as err:
            st.error(f"Query Execution Error: {err}")

    st.info(
        "Note: the billing view contains confirmed reservations and "
        "their recorded paid amounts. It is not a complete restaurant "
        "billing report."
    )


# =========================================================
# MODULE 5: TEST CASES AND VALIDATION
# =========================================================

elif module == "5. Test Cases & Validation":
    st.header("🧪 Review 3 Test Case Verification Matrix")

    test_cases = [
        {
            "Test ID": "TC-01",
            "Module": "Guest CRUD",
            "Input Data": "Empty name / invalid phone",
            "Expected Output": "Input rejected",
            "Verification": "UI validation implemented"
        },
        {
            "Test ID": "TC-02",
            "Module": "Reservation",
            "Input Data": "Check-out before check-in",
            "Expected Output": "Invalid date range rejected",
            "Verification": "Database CHECK constraint; test manually"
        },
        {
            "Test ID": "TC-03",
            "Module": "Food Order",
            "Input Data": "Unavailable menu item",
            "Expected Output": "Order rejected",
            "Verification": "Application availability check"
        },
        {
            "Test ID": "TC-04",
            "Module": "Subtotal",
            "Input Data": "Quantity=2, Price=250.00",
            "Expected Output": "Subtotal=500.00",
            "Verification": "Decimal subtotal calculation"
        },
        {
            "Test ID": "TC-05",
            "Module": "Guest Delete",
            "Input Data": "Delete guest with related records",
            "Expected Output": "Foreign-key restriction enforced",
            "Verification": "Database test required"
        },
        {
            "Test ID": "TC-06",
            "Module": "Room Availability",
            "Input Data": "Overlapping confirmed reservation",
            "Expected Output": "Room excluded for those dates",
            "Verification": "Date-based query implemented"
        },
        {
            "Test ID": "TC-07",
            "Module": "Order Transaction",
            "Input Data": "Order item insert fails",
            "Expected Output": "Order transaction rolled back",
            "Verification": "Rollback implemented"
        },
        {
            "Test ID": "TC-08",
            "Module": "SQL Analytics",
            "Input Data": "Execute aggregate and subquery reports",
            "Expected Output": "Query results displayed",
            "Verification": "Run against populated database"
        }
    ]

    st.dataframe(
        test_cases,
        use_container_width=True,
        hide_index=True
    )

    st.warning(
        "These are test definitions, not proof that every test passed. "
        "Run each test against your MySQL database and record the actual "
        "result before presenting the final test report."
    )

    st.subheader("Quick Validation: Subtotal Calculator")

    col1, col2 = st.columns(2)

    with col1:
        test_price = st.number_input(
            "Unit Price (₹)",
            min_value=0.0,
            value=250.0,
            step=10.0,
            key="test_price"
        )

    with col2:
        test_qty = st.number_input(
            "Quantity",
            min_value=1,
            value=2,
            step=1,
            key="test_qty"
        )

    test_subtotal = money(Decimal(str(test_price)) * int(test_qty))

    st.metric("Calculated Subtotal", f"₹{test_subtotal:.2f}")

    if st.button("Verify Subtotal"):
        expected = money(Decimal("500.00"))

        if (
            money(Decimal(str(test_price))) == Decimal("250.00")
            and int(test_qty) == 2
            and test_subtotal == expected
        ):
            st.success("TC-04 passed: subtotal equals ₹500.00.")
        else:
            st.info(
                "Calculation completed. Use Price=250 and Quantity=2 "
                "to verify the expected ₹500.00 example."
            )


# =========================================================
# 8. FOOTER
# =========================================================

st.divider()
st.caption(
    "Hotel and Restaurant Management System | "
    "Database Systems Project | Streamlit + MySQL"
)
