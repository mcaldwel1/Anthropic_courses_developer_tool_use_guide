import pg8000
from dotenv import load_dotenv
import re
import os

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

try:
    connection = pg8000.connect(
        host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD, port=DB_PORT
    )

    cursor = connection.cursor()

    def get_user_info(key, value):
        bundle = []
        if key in {"email", "phone", "username"}: 
            query1 = f"SELECT * FROM customers WHERE {key} = '{value}';"
            cursor.execute(query1)
            rec = cursor.fetchall()
            bundle.append(rec)
            query2 = f"SELECT * FROM orders WHERE customer_id IN (SELECT id FROM customers WHERE {key} = '{value}')"
            cursor.execute(query2)
            rec2 = cursor.fetchall()
            bundle.append(rec2)
            return bundle
        print(f"There is no user {key} of value: {value}")

    def get_order_by_id(order_id):
        query = f"SELECT * FROM orders WHERE id = {order_id}"
        cursor.execute(query)
        rec = cursor.fetchall()
        if(rec):
            return rec
        else:
            return "Can't find that order!"
    
    def get_customer_orders(customer_id):
        query = f"SELECT * FROM orders WHERE customer_id = {customer_id}"
        cursor.execute(query)
        rec = cursor.fetchall()
        return rec
    
    def cancel_order(order_id):
        order = get_order_by_id(order_id)
        if order:
            if "Processing" in order[0]:
                order[0][order[0].index("Processing")] = "Cancelled"
                return "Cancelled the order"
            else:
                return "Order has already shipped.  Can't cancel it."
        return "Can't find that order!"
    
    def update_info_helper(mode, old, new):
        query = f"SELECT {mode} FROM customers WHERE {mode} = '{old}';"
        cursor.execute(query)
        rec = cursor.fetchall()
        if rec:
            query2 = f"SELECT {mode} FROM customers WHERE {mode} IN ('{new}');"
            cursor.execute(query2)
            duplicate = cursor.fetchall()

            pattern1 = r"^[a-zA-Z0-9_.-]+@[a-zA-Z0-9-]+\..+$"
            pattern2 = r"[0-9]+\-[0-9]+\-[0-9]+$"
            if(not(re.match(pattern1, new) or re.match(pattern2, new))):
                raise ValueError(f"error invalid format for {mode}")
            elif(duplicate):
                 raise ValueError(f"error: that {mode} already exists")
            else:
                query3 = f"UPDATE customers \
                    SET {mode} = '{new}' \
                    WHERE {mode} = '{old}'; \
                    COMMIT;"
                cursor.execute(query3)
        else:
            raise ValueError(f"There is no user with that {mode}")
        return 0
    
    def update_info(mode, old, new):
        caller = update_info_helper(mode, old, new)
        query = "SELECT * FROM customers;"
        cursor.execute(query)
        rec = cursor.fetchall()
        print(rec)
    
    update_info('email', 'priya@candy.com', 'priya@soda.com')

except Exception as e:
    print(e)

finally:
    if connection:
        cursor.close()
        connection.close()

