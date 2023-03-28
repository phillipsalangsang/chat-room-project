from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

# Initialize Flask app

app = Flask(__name__)

# Set secret key for the app
app.config["SECRET_KEY"] = "PhillipLouis"

# Initialize SocketIO instance
socketio = SocketIO(app)

# Initialize dictionary to store rooms and their information
rooms = {}

# Define function to generate unique codes for rooms
def generate_unique_code(length):
    while True:
        
        # Generate a code of specified length
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)

        # Check if the code already exists in the rooms dictionary
        if code not in rooms:
            
            # If the code doesn't exist, return it
            break

    return code

# Define home page route
@app.route("/", methods=["POST", "GET"])
def home():
    
    # Clear session data
    session.clear()
    
    # Check if the request method is POST
    if request.method == "POST":
        
        # Get name and code from form data
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        # Check if name is provided
        if not name:
            
            # If name is not provided, show an error message
            return render_template("home.html", error= "Enter a name.", code=code, name=name)

        # Check if join button is pressed and code is not provided
        if join != False and not code:
            
            # If join button is pressed and code is not provided, show an error message
            return render_template("home.html", error="Enter valid room code.", code=code, name=name)
        
        # Set room to the provided code
        room = code
        
        # If create button is pressed
        if create != False:
            
            # Generate a unique room code
            room = generate_unique_code(4)
            
            # Add the room to the rooms dictionary with members and messages keys
            rooms[room] = {"members": 0, "messages": []}
        
        # If the provided code does not exist in the rooms dictionary
        elif code not in rooms:
            
            # Show an error message
            return render_template("home.html", error="Invalid Room.", code=code, name=name)

        # Set session variables for room and name
        session["room"] = room
        session["name"] = name
        
        # Redirect to room page
        return redirect(url_for("room"))

    # If the request method is GET, show the home page
    return render_template("home.html")

# Define room page route
@app.route("/room")
def room():
    
    # Get room and name from session variables
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        
        # If room or name is not provided, or room does not exist in rooms dictionary, redirect to home page
        return redirect(url_for("home"))

    # Show room page with code and messages for the room
    return render_template("room.html", code=room, messages=rooms[room]["messages"])

# Define function to handle incoming messages
@socketio.on("message")
def message(data):
    
    # Get the name of the chat room from the client's session
    room = session.get("room")
    
    # If the room does not exist in the dictionary, do nothing
    if room not in rooms:
        return
    
    # Create a dictionary with information about the message
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    
    # Send the message to all clients in the room
    send(content, to=room)
    
    # Append the message to the list of messages for the room
    rooms[room]["messages"].append(content)
    
    # Print the message to the server console
    print(f"{session.get('name')} said: {data['data']}")

# Define a function that is called when a client connects to the server
@socketio.on("connect")
def connect(auth):
    
    # Get the name and chat room of the client from their session
    room = session.get("room")
    name = session.get("name")
    
    # If the name or chat room are missing, do nothing
    if not room or not name:
        return
    
    # If the chat room does not exist in the dictionary, leave the room and do nothing
    if room not in rooms:
        leave_room(room)
        return
    
    # Join the chat room and send a message to all clients in the room
    join_room(room)
    send({"name": name, "message": "has entered the room"}, to=room)
    
    # Update the number of members in the room
    rooms[room]["members"] += 1
    
    # Print a message to the server console
    print(f"{name} has joined the room {room}")

# Define a function that is called when a client disconnects from the server
@socketio.on("disconnect")
def disconnect():
    
    # Get the name and chat room of the client from their session
    room = session.get("room")
    name = session.get("name")
    
    # Leave the chat room
    leave_room(room)
    
    # If the chat room exists in the dictionary, update the number of members and remove the room if there are no members left
    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    
    # Send a message to all clients in the room that the client has left
    send({"name": name, "message": "has exited the room"}, to=room)
    
    # Print a message to the server console
    print(f"{name} has exited the room {room}")

# Run the SocketIO server
if __name__ == "__main__":
    socketio.run(app, debug=True)