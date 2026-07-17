import streamlit as st
import requests
import pandas as pd

st.set_page_config(layout="wide")
st.title("🎾 Live Tennis Global Strategy Engine")

K = "932206dd22mshf288a41328bab03p12d137jsn9b24ebdfb34c"
H = "odds-api-io-real-time-sports-betting-odds-api.p.rapidapi.com"

hd = {
    "X-RapidAPI-Key": K,
    "X-RapidAPI-Host": H,
    "Content-Type": "application/json"
}

# Sidebar configuration allowing global or filtered views
sport_key = st.sidebar.text_input("Sport Key", value="tennis")
status_key = st.sidebar.text_input("Status Key", value="live")
league_filter = st.sidebar.text_input("League Filter (Leave blank for ALL)", value="")

if st.button("🚀 Scan All Live Courts", type="primary"):
    with st.spinner("Sweeping global tennis feeds..."):
        try:
            # STEP 1: Fetch Events cleanly without locking into one tournament
            u1 = f"https://{H}/v2/events"
            p1 = {"status": status_key, "sport": sport_key}
            
            # Dynamically inject league filter only if you type one in
            if league_filter.strip():
                p1["league"] = league_filter.strip()
                
            res = requests.get(u1, headers=hd, params=p1)
            
            if res.status_code == 404:
                st.info("No live matches matching these settings are currently publishing data.")
                st.stop()
                
            if res.status_code != 200:
                st.error(f"API Connection Error: {res.status_code}")
                st.stop()
                
            data = res.json()
            if not data:
                st.info("Empty match array returned from the server.")
                st.stop()
                
            id_map = {}
            id_list = []
            for ev in data:
                if ev and 'id' in ev:
                    eid = str(ev['id'])
                    id_list.append(eid)
                    id_map[eid] = {
                        "L": ev.get("league", "TENNIS"),
                        "M": f"{ev.get('away')} vs {ev.get('home')}"
                    }
                    
            if not id_list:
                st.warning("No active IDs to scan.")
                st.stop()
                
            # STEP 2: Bulk Retrieve Odds for all discovered fixtures
            u2 = f"https://{H}/v2/odds/multi"
            p2 = {"bookmakers": "FanDuel", "eventIds": ",".join(id_list)}
            ores = requests.get(u2, headers=hd, params=p2)
            odata = ores.json()
            rows = []
            
            # STEP 3: Flat-Line Value Parser
            for item in odata:
                if not item: continue
                mid = str(item.get('id', ''))
                meta = id_map.get(mid, {"L": "TOUR", "M": "MATCH"})
                
                bm = item.get('bookmakers', {})
                fd = bm.get('fanduel') or bm.get('FanDuel')
                if not fd: continue
                
                mkts = fd.get('markets', [])
                if not mkts: continue
                mkt = mkts
