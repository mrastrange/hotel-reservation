from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
import secrets
import string
import smtplib

# Send mail notification for reservations
def mailit(data, a_d):
    try:
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login("nairmessmailssn@gmail.com", "jqdv cehm ddpg ppyd")
        if a_d == 1:
            message = ("NAIR MESS INC\n\nYour reservation has been accepted"
                       "\n\nYour unique reservation id is " + data["reservation_id"] +
                       "\n\nName: " + data["name"] +
                       "\n\nSeats required: " + str(data["party_size"]) +
                       "\n\nPhone number: " + data["phone"] +
                       "\n\nSpecial comments: " + data["special_comments"] +
                       "\n\n" + str(data["email_id"]))
        elif a_d == 0:
            message = ("NAIR MESS INC\n\nYour reservation has been declined"
                       "\n\nYour unique reservation id is " + data["reservation_id"] +
                       "\n\nName: " + data["name"] +
                       "\n\nSeats required: " + str(data["party_size"]) +
                       "\n\nPhone number: " + data["phone"] +
                       "\n\nSpecial comments: " + data["special_comments"] +
                       "\n\n" + str(data["email_id"]))
        s.sendmail("nairmessmailssn@gmail.com", str(data["email_id"]), message)
        s.quit()
    except:
        pass

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Load users data
if os.path.exists('users.json'):
    with open('users.json') as f:
        users = json.load(f)
else:
    users = {
        "admin": {
            "username": "a",
            "password": "a"
        },
        "customers": []
    }

# Linked List
class Node:
    def __init__(self, data=None):
        self.data = data
        self.next = None

class LinkedList:
    def __init__(self):
        self.head = None
    
    def append(self, data):
        new_node = Node(data)
        if not self.head:
            self.head = new_node
            return
        last_node = self.head
        while last_node.next:
            last_node = last_node.next
        last_node.next = new_node
    
    def pop(self):
        if not self.head:
            return None
        if not self.head.next:
            popped_node = self.head
            self.head = None
            return popped_node.data
        second_last = self.head
        while second_last.next.next:
            second_last = second_last.next
        popped_node = second_last.next
        second_last.next = None
        return popped_node.data
    
    def remove(self, data):
        head = self.head
        if head is not None:
            if head.data == data:
                self.head = head.next
                head = None
                return
        while head is not None:
            if head.data == data:
                break
            prev = head
            head = head.next
        if head == None:
            return
        prev.next = head.next
        head = None
    
    def __iter__(self):
        node = self.head
        while node is not None:
            yield node.data
            node = node.next
    
    def clear(self):
        self.head = None

# LinkedList to store reservation requests
reservation_queue = LinkedList()

# Maximum number of tables
MAX_TABLES = 10

# List to keep track of reserved tables
reserved_tables = []

# Route to homepage based on the role
@app.route('/')
def index():
    if 'username' in session:
        if session['role'] == 'admin':
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('customer'))
    return redirect(url_for('login'))

# Load users from JSON file
def load_users():
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'customers': [], 'admin': {'username': 'admin', 'password': 'admin'}}

# Save users to JSON file
def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f)

# Route for new user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    users = load_users()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        for customer in users['customers']:
            if customer['username'] == username:
                return 'Username already exists'
        users['customers'].append({'username': username, 'password': password})
        save_users(users)
        return redirect(url_for('login'))
    return render_template('register.html')

# Route for existing user/admin login
@app.route('/login', methods=['GET', 'POST'])
def login():
    users = load_users()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        for customer in users['customers']:
                if username == "admin" and password == "admin123":
                       session['username'] = username
                       session['role'] = 'admin'
                       return redirect(url_for('admin'))
                elif username == customer['username'] and password == customer['password']:
                       session['username'] = username
                       session['role'] = 'customer'
                       return redirect(url_for('customer'))
        else:
            return 'Invalid role'
    return render_template('login.html')

# Route for logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))

# Route for admin interface to manage reservation
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    global reserved_tables, reservation_queue
    if 'username' in session and session['role'] == 'admin':
        if request.method == 'POST':
            action = request.form.get('action')
            reservation_id = request.form.get('reservation_id')
            if action == 'accept':
                flash('Reservation accepted!', 'success')
            elif action == 'decline':
                flash('Reservation declined!', 'success')
            elif action == 'remove':
                reservation = next((res for res in reserved_tables if res['reservation_id'] == reservation_id), None)
                if reservation:
                    reserved_tables.remove(reservation)
                    flash('Reservation removed!', 'success')
                else:
                    flash('Reservation not found!', 'error')
            elif action == 'accept_next':
                if reservation_queue.head:
                    reservation = reservation_queue.pop()
                    reservation['status'] = 'Reserved'
                    reserved_tables.append(reservation)
                    mailit(reserved_tables[-1], 1)
                    flash('Next reservation processed!', 'success')
                else:
                    flash('No reservations in the queue!', 'error')
            elif action == 'decline_next':
                if reservation_queue.head:
                    reservation = reservation_queue.pop()
                    reservation['status'] = 'Reservation Not Found'
                    mailit(reservation, 0)
                    flash('Next reservation processed!', 'success')
                else:
                    flash('No reservations in the queue!', 'error')
            elif action == 'clear_reservations':
                reserved_tables = []
                for reservation in reservation_queue:
                    reservation['status'] = 'Reservation Not Found'
                flash('All reservations cleared!', 'success')
            elif action == 'clear_one_reservation':
                reserved_tables = reserved_tables[:-1]
                flash('Reservations cleared!', 'success')
        return render_template('admin.html', reservation_queue=reservation_queue, reserved_tables=reserved_tables)
    return redirect(url_for('login'))

# Route to customer interface
@app.route('/customer')
def customer():
    if 'username' in session and session['role'] == 'customer':
        customer_reservations = [res for res in reserved_tables if res['name'] == session['username']]
        return render_template('customer.html', customer_reservations=customer_reservations)
    return redirect(url_for('login'))

# Route to make a reservation
@app.route('/reserve', methods=['GET', 'POST'])
def reserve():
    if 'username' in session and session['role'] == 'customer':
        if request.method == 'POST':
            name = session['username']
            phone = session['username']
            party_size = int(request.form['party_size'])
            email_id = str(request.form['email_id'])
            special_comments = request.form.get('special_comments', '')

            # Generate a unique ID
            reservation_id = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
            datareserve = {'reservation_id': reservation_id, 'name': name, 'party_size': party_size, 'phone': phone, 'email_id': email_id, 'special_comments': special_comments}
            reservation_queue.append(datareserve)
            flash(f'Reservation successful! Your reservation ID is: {reservation_id}\nA mail will be sent if the reservation is accepted or declined', 'success')  # Customer flash message
            return redirect(url_for('reserve'))
        return render_template('reserve.html')
    return redirect(url_for('login'))

# Route to check the status of the reservation
@app.route('/check_status', methods=['GET', 'POST'])
def check_status():
    if 'username' in session and session['role'] == 'customer':
        if request.method == 'POST':
            reservation_id = request.form.get('reservation_id')
            reservation = next((res for res in reserved_tables if res['reservation_id'] == reservation_id), None)
            if reservation:
                reservation['status'] = 'Accepted'
                flash('Reservation found!', 'reservation_status_success')
                return render_template('check_status.html', reservation=reservation)
            else:
                reservation = next((res for res in reservation_queue if res['reservation_id'] == reservation_id), None)
                if reservation:
                    reservation['status'] = 'Pending'
                    flash('Reservation is pending!', 'reservation_status_pending')
                    return render_template('check_status.html', reservation=reservation)
                flash('Reservation not found. Please enter a valid ID.', 'reservation_status_error')
                return render_template('check_status.html')
        return render_template('check_status.html')
    return redirect(url_for('login'))

@flask_app.route('/endpoint', methods=['GET', 'POST'])
def endpoint():
    # Your endpoint logic here
    return 'Hello from Flask endpoint!'

# Embed the Flask app into the Streamlit app
def run_flask_app():
    from werkzeug.middleware.dispatcher import DispatcherMiddleware
    from werkzeug.serving import run_simple

    app = DispatcherMiddleware(flask_app)
    run_simple('localhost', 5000, app)

# Streamlit app logic
def main():
    st.title('Streamlit and Flask Integration')
    if st.button('Start Flask Server'):
        run_flask_app()

if __name__ == '__main__':
    main()
