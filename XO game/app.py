import streamlit as st
import random
import time
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="Real-time XO Game with Robot", page_icon="🤖", layout="centered")

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
    .score-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center; font-size: 18px; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

# --- AUTOMATIC BACKGROUND REFRESH ---
# Silently refreshes the script every 2 seconds (2000ms) so players see real-time updates 
# without clicking a refresh button.
st_autorefresh(interval=2000, key="datarefresh")

# --- GLOBAL LIVE GAME STORAGE ---
@st.cache_resource
def get_global_rooms():
    return {}

rooms = get_global_rooms()

# --- ROOM MANAGEMENT & URL ROUTING ---
query_params = st.query_params

if "room" in query_params:
    room_id = query_params["room"]
else:
    room_id = "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ23456789", k=6))
    st.query_params["room"] = room_id

# Initialize global room if it doesn't exist
if room_id not in rooms:
    rooms[room_id] = {
        "board": [""] * 9,
        "turn": "X",
        "players_connected": 0,
        "winner": None,
        "is_draw": False,
        "game_mode": "Friend", # "Friend" or "Robot"
        "max_rounds": 3,       # 3 or 5 rounds
        "scores": {"X": 0, "O": 0, "Draws": 0},
        "current_round": 1,
        "series_winner": None
    }

game = rooms[room_id]

# --- LOCAL USER SESSION SETUP ---
if "my_role" not in st.session_state:
    if game["players_connected"] == 0:
        st.session_state.my_role = "X"
        game["players_connected"] += 1
    elif game["players_connected"] == 1 and game["game_mode"] == "Friend":
        st.session_state.my_role = "O"
        game["players_connected"] += 1
    else:
        st.session_state.my_role = "Spectator"

# --- ROBOT INTELLIGENCE (AI MOVE) ---
def get_robot_move(board):
    empty_indices = [i for i, val in enumerate(board) if val == ""]
    if empty_indices:
        return random.choice(empty_indices)
    return None

# --- GAME LOGIC ---
def check_winner(board):
    win_combinations = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],
        [0, 3, 6], [1, 4, 7], [2, 5, 8],
        [0, 4, 8], [2, 4, 6]
    ]
    for combo in win_combinations:
        if board[combo[0]] == board[combo[1]] == board[combo[2]] != "":
            return board[combo[0]]
    if "" not in board:
        return "Draw"
    return None

def update_scores(result):
    if result == "Draw":
        game["scores"]["Draws"] += 1
    else:
        game["scores"][result] += 1
    
    # Check if someone has secured the series
    target_wins = (game["max_rounds"] // 2) + 1
    if game["scores"]["X"] >= target_wins:
        game["series_winner"] = "X"
    elif game["scores"]["O"] >= target_wins:
        game["series_winner"] = "O"
    elif (game["scores"]["X"] + game["scores"]["O"] + game["scores"]["Draws"]) >= game["max_rounds"]:
        # If all rounds are played out and no one has absolute majority wins
        if game["scores"]["X"] > game["scores"]["O"]:
            game["series_winner"] = "X"
        elif game["scores"]["O"] > game["scores"]["X"]:
            game["series_winner"] = "O"
        else:
            game["series_winner"] = "Tie"

def handle_click(index):
    if game["series_winner"]:
        return

    # Check validity of turn
    if (game["turn"] == st.session_state.my_role and 
        game["board"][index] == "" and 
        not game["winner"] and not game["is_draw"]):
        
        # Player Move
        game["board"][index] = st.session_state.my_role
        
        # Evaluate Move
        result = check_winner(game["board"])
        if result:
            process_game_end(result)
        else:
            game["turn"] = "O"
            
            # Trigger Robot immediate response if mode matches
            if game["game_mode"] == "Robot":
                st.rerun() # Forces turn swap rendering quickly before bot picks

def process_game_end(result):
    if result == "Draw":
        game["is_draw"] = True
    else:
        game["winner"] = result
    update_scores(result)

def advance_round():
    if not game["series_winner"]:
        game["current_round"] += 1
    game["board"] = [""] * 9
    game["turn"] = "X"
    game["winner"] = None
    game["is_draw"] = False

def reset_entire_series():
    game["board"] = [""] * 9
    game["turn"] = "X"
    game["winner"] = None
    game["is_draw"] = False
    game["scores"] = {"X": 0, "O": 0, "Draws": 0}
    game["current_round"] = 1
    game["series_winner"] = None

# --- RUN ROBOT TURN AUTOMATICALLY ---
if (game["game_mode"] == "Robot" and 
    game["turn"] == "O" and 
    not game["winner"] and not game["is_draw"] and 
    not game["series_winner"]):
    
    bot_idx = get_robot_move(game["board"])
    if bot_idx is not None:
        time.sleep(0.4) # Slight delay so it feels realistic
        game["board"][bot_idx] = "O"
        result = check_winner(game["board"])
        if result:
            process_game_end(result)
        else:
            game["turn"] = "X"
    st.rerun()

# --- SIDEBAR: GAME CONTROLS & SETUP ---
with st.sidebar:
    st.header("⚙️ Game Setup")
    
    # Mode selection is locked once game begins to protect cross-room states
    moves_made = any(cell != "" for cell in game["board"]) or game["current_round"] > 1
    
    mode = st.radio("Opponent Mode:", ["Vs Friend", "Vs Robot (AI)"], disabled=moves_made)
    game["game_mode"] = "Robot" if "Robot" in mode else "Friend"
    
    rounds = st.selectbox("Series Strategy:", [3, 5], index=0 if game["max_rounds"]==3 else 1, disabled=moves_made)
    game["max_rounds"] = rounds

    st.write("---")
    if st.button("🚨 Reset Whole Series", use_container_width=True):
        reset_entire_series()
        st.rerun()

# --- UI LAYOUT ---
st.title("🤖 Real-Time Multi-Round XO Game ❌⭕")

# Display Live Scoreboards
col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    st.markdown(f'<div class="score-box">❌ Player X<br><span style="font-size:24px;">{game["scores"]["X"]}</span></div>', unsafe_allowed_html=True)
with col_s2:
    st.markdown(f'<div class="score-box">🤝 Draws<br><span style="font-size:24px;">{game["scores"]["Draws"]}</span></div>', unsafe_allowed_html=True)
with col_s3:
    opp_name = "Robot 🤖" if game["game_mode"] == "Robot" else "Player O ⭕"
    st.markdown(f'<div class="score-box">⭕ {opp_name}<br><span style="font-size:24px;">{game["scores"]["O"]}</span></div>', unsafe_allowed_html=True)

st.write("")
st.caption(f"Lobby Code: **{room_id}** | Your Role: **Player {st.session_state.my_role}** | Mode: **Best of {game['max_rounds']} (Round {game['current_round']})**")

# Generated URL Sharing Link 
if game["game_mode"] == "Friend":
    base_url = "https://xo-game-share.streamlit.app/"
    st.text_input("📋 Send this link to your friend:", value=f"{base_url}?room={room_id}")

st.write("---")

# Series Winner Announcement
if game["series_winner"]:
    if game["series_winner"] == "Tie":
        st.markdown('<p class="win-text">🏆 The entire series ended in a overall Tie! 🏆</p>', unsafe_allowed_html=True)
    else:
        winner_label = "Robot 🤖" if (game["series_winner"] == "O" and game["game_mode"] == "Robot") else f"Player {game['series_winner']}"
        st.markdown(f'<p class="win-text">🏆 {winner_label} WINS THE SERIES! 🏆</p>', unsafe_allowed_html=True)
# Individual Turn/Round State Announcement
elif game["winner"]:
    round_win_lbl = "Robot 🤖" if (game["winner"] == "O" and game["game_mode"] == "Robot") else f"Player {game['winner']}"
    st.success(f"🎉 {round_win_lbl} won Round {game['current_round']}!")
    st.button("➡️ Advance to Next Round", on_click=advance_round, use_container_width=True)
elif game["is_draw"]:
    st.warning(f"🤝 Round {game['current_round']} is a Draw!")
    st.button("➡️ Advance to Next Round", on_click=advance_round, use_container_width=True)
else:
    if game["turn"] == st.session_state.my_role:
        st.markdown('<p class="turn-text" style="color:#3498db;">🟢 Your Turn!</p>', unsafe_allowed_html=True)
    else:
        opp_turn_lbl = "Robot" if game["game_mode"] == "Robot" else f"Player {game['turn']}"
        st.markdown(f'<p class="turn-text" style="color:#e67e22;">⏳ Waiting for {opp_turn_lbl}...</p>', unsafe_allowed_html=True)

# Render Grid
for row in range(3):
    cols = st.columns(3)
    for col in range(3):
        idx = row * 3 + col
        label = game["board"][idx]
        btn_label = label if label != "" else " "
        
        # Disabled buttons if series over, round over, or not your turn
        is_disabled = (
            label != "" or 
            game["winner"] is not None or 
            game["is_draw"] or 
            game["series_winner"] is not None or 
            game["turn"] != st.session_state.my_role
        )
        
        cols[col].button(
            btn_label, 
            key=f"btn_{idx}", 
            on_click=handle_click, 
            args=(idx,),
            disabled=is_disabled
        )
