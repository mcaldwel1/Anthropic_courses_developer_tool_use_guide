# Modified TechNova assistant with additional functionality, error handling,
# input validation, and a postgres database connection 

from dotenv import load_dotenv, dotenv_values
from anthropic import Anthropic
import pg8000
import json
import re
import getpass
import os 

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# getpass authentication method 
client = Anthropic(
    api_key = getpass.getpass("Enter your Anthropic API Key:")
)

try:
    db_connection = pg8000.connect(
        host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD, port=DB_PORT
    )

    cursor = db_connection.cursor()

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
        return(f"There is no user {key} of value: {value}")

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
            # For now, we're just changing the status to 'cancelled' because the exercise 
            # doesn't call for an insert/delete orders function
            if "Processing" in order[0]:
                order[0][order[0].index("Processing")] = "Cancelled"
                return "Cancelled the order"
            else:
                return "Order has already shipped.  Can't cancel it."
        return "Can't find that order!"

    def update_info(mode, old, new):
        query = f"SELECT {mode} FROM customers WHERE {mode} = '{old}';"
        cursor.execute(query)
        rec = cursor.fetchall()
        if rec:
            # added duplicate handling 
            
            query2 = f"SELECT {mode} FROM customers WHERE {mode} IN ('{new}');"
            cursor.execute(query2)
            duplicate = cursor.fetchall()

            # regex patterns to ensure valid phone and email formatting 

            pattern1 = r"^[a-zA-Z0-9_.-]+@[a-zA-Z0-9-]+\..+$"
            pattern2 = r"[0-9]+\-[0-9]+\-[0-9]+$"
            if(not(re.match(pattern1, new) or re.match(pattern2, new))):
                return(f"error invalid format for {mode}")
            elif(duplicate):
                return(f"error: that {mode} already exists")
            else:
                query3 = f"UPDATE customers \
                    SET {mode} = '{new}' \
                    WHERE {mode} = '{old}'; \
                    COMMIT;"
                cursor.execute(query3)

                query4 = "SELECT * FROM customers;"
                cursor.execute(query4)
                rec2 = cursor.fetchall()
                print(rec2)
        else:
            return(f"No user with that {mode}")
        return 0

    tools = [
        {
            "name": "get_user_info",
            "description": "Looks up a user by email, phone, or username and finds their order history.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "enum": ["email", "phone", "username"],
                        "description": "The attribute to search for a user by (email, phone, or username)."
                    },
                    "value": {
                        "type": "string",
                        "description": "The value to match for the specified attribute."
                    }
                },
                "required": ["key", "value"]
            }
        },
        {
            "name": "get_order_by_id",
            "description": "Retrieves the details of a specific order based on the order ID. Returns the order ID, product name, quantity, price, and order status.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The unique identifier for the order."
                    }
                },
                "required": ["order_id"]
            }
        },
        {
            "name": "get_customer_orders",
            "description": "Retrieves the list of orders belonging to a user based on a user's customer id.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "The customer_id belonging to the user"
                    }
                },
                "required": ["customer_id"]
            }
        },
        {
            "name": "cancel_order",
            "description": "Cancels an order based on a provided order_id.  Only orders that are 'processing' can be cancelled",
            "input_schema": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order_id pertaining to a particular order"
                    }
                },
                "required": ["order_id"]
            }
        },
        {
            "name": "update_info",
            "description": "Updates the user's current email or phone number with the new email or number entered",
            "input_schema": {
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "description": "the category that the user wants to change (email or phone)"
                    },
                    "old": {
                        "type": "string",
                        "description": "the user's current email or phone number"
                    },
                    "new": {
                        "type": "string",
                        "description": "the user's new email or phone number"
                    }
                },
                "required": ["phone_number", "new_phone_number"]
            }
        }
    ]

    def process_tool_call(tool_name, tool_input):
        if tool_name == "get_user_info":
            return get_user_info(tool_input["key"], tool_input["value"])
        elif tool_name == "get_order_by_id":
            return get_order_by_id(tool_input["order_id"])
        elif tool_name == "get_customer_orders":
            return get_customer_orders(tool_input["customer_id"])
        elif tool_name == "cancel_order":
            return cancel_order(tool_input["order_id"])
        elif tool_name == "update_info":
            return update_info(tool_input["mode"], tool_input["old"], tool_input["new"])

    def extract_reply(text):
        pattern = r'<reply>(.*?)</reply>'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1)
        else:
            return text

    def simple_chat():
        user_message = input("\nUser: ")
        messages = [{"role": "user", "content": user_message}]

        system_prompt = """
        You are a customer support chat bot for an online retailer called TechNova. 
        Your job is to help users look up their account, orders, and cancel orders.
        Be helpful and brief in your responses.
        You have access to a set of tools, but only use them when needed.  
        If you do not have enough information to use a tool correctly, ask a user follow up questions to get the required inputs.
        If a required tool input is not given by the user, ask the user for more information.
        Do not call any of the tools unless you have the required data from a user. 
        Only use inputs that the user provides. Do not assume inputs.

        In each conversational turn, you will begin by thinking about your response. 
        Once you're done, you will write a user-facing response. 
        It's important to place all user-facing conversational responses in <reply></reply> XML tags to make them easy to parse.
        """

        while True:
            if(messages[-1].get("role") == "assistant"):
                user_message = input("\nUser: ")
                messages.append({"role": "user", "content": user_message})

            response = client.messages.create(
                model = "claude-3-haiku-20240307",
                system = system_prompt,
                messages = messages,
                tools = tools,
                max_tokens = 1000
            )

            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "tool_use":
                tool_use = response.content[-1]
                tool_name = tool_use.name
                tool_input = tool_use.input
                print(f"======Claude wants to use the {tool_name} tool======")

                tool_result = process_tool_call(tool_name, tool_input)

                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use.id,
                                "content": str(tool_result),
                            }
                        ],
                    },
                )
            else: 
                print("\nTechNova Support: ")
                model_reply = extract_reply(response.content[0].text)
                print(model_reply)
    
    while(True):
        try:
            simple_chat()
        except:
            print('program exited')
            break

except Exception as e:
    print(e)

finally:
    if db_connection:
        cursor.close()
        db_connection.close()