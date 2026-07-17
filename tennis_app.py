import streamlit as st
import requests
import pandas as pd

st.set_page_config(layout="wide")
st.title("🎾 Live Tennis Favorite-Recovery Engine")

K = "932206dd22mshf288a41328bab03p12d137jsn9b24ebdfb34c"
H = "odds-api-io-real-time-sports-betting-odds-api.p.rapidapi.com"

hd = {
    "X-RapidAPI-Key": K,
    "X-RapidAPI-Host": H,
    "Content-Type": "application/json"
}

mode = st.sidebar.selectbox("Select Target Scan Mode", ["Scan Active Courts", "Raw Server Text Diagnostic"])

if st.button("🚀 Execution Command", type="primary"):
    try:
        if mode == "Raw Server Text Diagnostic":
            # Testing direct text responses to see exact system routes without crash risk
            u_diag = f"https://{H}/v2/events"
            r_diag = requests.get(u_diag, headers=hd, params={"status": "live", "sport": "Tennis"})
            st.write(f"### Server HTTP Status: {r_diag.status_code}")
            st.write("### Raw Response Body:")
            st.code(r_diag.text)
            st.stop()
            
        # STEP 1: Fetch Live Tennis Events (Using strict Enum capitalization 'Tennis')
        u1 = f"https://{H}/v2/events"
        p1 = {"status": "live", "sport": "Tennis"}
        res = requests.get(u1, headers=hd, params=p1)
        
        # Safe catch for zero live trading markets
        if res.status_code == 404:
            st.info("No live tennis matches are currently publishing data on this network route.")
            st.stop()
            
        if res.status_code != 200:
            st.error(f"API Connection Error: {res.status_code}")
            st.code(res.text)
            st.stop()
            
        data = res.json()
        if not data:
            st.info("No active tennis lines discovered in the current feed.")
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
            st.warning("No live matchup structures available to track.")
            st.stop()
            
        # STEP 2: Bulk Retrieve Odds
        u2 = f"https://{H}/v2/odds/multi"
        p2 = {"bookmakers": "FanDuel", "eventIds": ",".join(id_list)}
        ores = requests.get(u2, headers=hd, params=p2)
        
        if ores.status_code != 200:
            st.error("Odds pipeline down.")
            st.stop()
            
        odata = ores.json()
        rows = []
        
        # STEP 3: Parse Out Premium Value Targets
        for item in odata:
            if not item or 'bookmakers' not in item:
                continue
            mid = str(item.get('id', item.get('eventId', '')))
            meta = id_map.get(mid, {"L": "ATP/WTA", "M": "LIVE MATCH"})
            
            bm = item['bookmakers']
            fd = bm.get('fanduel') or bm.get('FanDuel')
            if not fd:
                continue
                
            mkts = fd.get('markets') or fd.
