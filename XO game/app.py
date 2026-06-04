import streamlit as st
import random

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="Real-time XO Game", page_icon="❌", layout="centered")

st.markdown("""
    <style>
    .stButton>button {
        font-size: 24px !important;
        font-weight: bold;
        height: 80px;
        width: 100%;
    }
    .win-text { font-size: 30px; font-weight: bold; color: #2ecc71; text-align: center; }
    .turn-text { font-size: 20px; font-weight: bold; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# --- GLOBAL LIVE GAME STORAGE ---
# Streamlit clears local memory per user, so we use a global memory dictionary 
# to sync player boards across different computers in real-time.
if "global_rooms" not in st.experimental_singleton:
    st.experimental_singleton.global_rooms = {}

rooms = st.experimental_singleton.global_rooms

# --- ROOM MANAGEMENT & URL ROUTING ---
query_params = st.query_params

# Get or create room ID from URL query parameters
if "room" in query_params:
    room_id = query_params["room"]
else:
    # Generate a random 6-character room code if none exists
    room_id = "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ23456789", k=6))
    st.query_params["room"] = room_id

# Initialize the room state in global shared memory if it's new
if room_id not in rooms:
    rooms[room_id] = {
        "board": [""] * 9,
        "turn": "X",
        "players_connected": 0,
        "winner": None,
        "is_draw": False
    }

game = rooms[room_id]

# --- LOCAL USER SESSION SETUP ---
# Assign player identities (First to join is X, second is O)
if "my_role" not in st.session_state:
    if game["players_connected"] == 0:
        st.session_state.my_role = "X"
        game["players_connected"] += 1
    elif game["players_connected"] == 1:
        st.session_state.my_role = "O"
        game["players_connected"] += 1
    else:
        st.session_state.my_role = "Spectator"

# --- GAME LOGIC FUNCTIONS ---
def check_winner(board):
    win_combinations = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
        [0, 4, 8], [2, 4, 6]              # Diagonals
    ]
    for combo in win_combinations:
        if board[combo[0]] == board[combo[1]] == board[combo[2]] != "":
            return board[combo[0]]
    if "" not in board:
        return "Draw"
    return None

def handle_click(index):
    # Only allow moves if it's the player's turn, slot is empty, and game isn't over
    if (game["turn"] == st.session_state.my_role and 
        game["board"][index] == "" and 
        not game["winner"] and not game["is_draw"]):
        
        game["board"][index] = st.session_state.my_role
        
        # Check game conclusion status
        result = check_winner(game["board"])
        if result == "Draw":
            game["is_draw"] = True
        elif result:
            game["winner"] = result
        else:
            # Swap turn
            game["turn"] = "O" if game["turn"] == "X" else "X"

def reset_game():
    game["board"] = [""] * 9
    game["turn"] = "X"
    game["winner"] = None
    game["is_draw"] = False

# --- UI LAYOUT ---
st.title("❌ Multi-Player XO ⭕")
st.caption(f"Lobby Code: **{room_id}** | Your Role: **Player {st.session_state.my_role}**")

# Share Link UI
share_url = f"https://share.streamlit.io/your-username/your-repo/main/app.py?room={room_id}" 
# Note: Streamlit will automatically map domain names on local/cloud deployment.
st.text_input("📋 Copy this link and send it to your friend:", value=st.page_link)

st.write("---")

# Display Status Text
if game["winner"]:
    st.markdown(f'<p class="win-text">🎉 Player {game["winner"]} Wins! 🎉</p>', unsafe_allowed_html=True)
elif game["is_draw"]:
    st.markdown('<p class="win-text">🤝 It\'s a Tie Draw! 🤝</p>', unsafe_allowed_html=True)
else:
    if game["turn"] == st.session_state.my_role:
        st.markdown('<p class="turn-text" style="color:#3498db;">🟢 Your Turn!</p>', unsafe_allowed_html=True)
    else:
        st.markdown(f'<p class="turn-text" style="color:#e67e22;">⏳ Waiting for Player {game["turn"]}...</p>', unsafe_allowed_html=True)

# Render 3x3 Grid
board_container = st.container()
with board_container:
    for row in range(3):
        cols = st.columns(3)
        for col in range(3):
            idx = row * 3 + col
            label = game["board"][idx]
            # Use styling depending on filled state
            button_label = label if label != "" else " "
            
            # Action button for grid cell
            cols[col].button(
                button_label, 
                key=f"btn_{idx}", 
                on_click=handle_click, 
                args=(idx,)
            )

st.write("---")

# Refresh and Restart Controls
col_ctrl1, col_ctrl2 = st.columns(2)
with col_ctrl1:
    if st.button("🔄 Refresh Screen"):
        st.rerun() # Forces streamlit to sync state updates from the global dictionary
with col_ctrl2:
    if st.button("🧹 Clear & Play Again"):
        reset_game()
        st.rerun()
