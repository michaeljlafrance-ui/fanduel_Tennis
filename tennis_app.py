import streamlit as st
import requests
import pandas as pd

st.set_page_config(layout="wide")
st.title("🎾 Live Tennis Engine")

K = "932206dd22mshf288a41328bab03p12d137jsn9b24ebdfb34c"
H = "odds-api-io-real-time-sports-betting-odds-api.p.rapidapi.com"

hd = {
    "X-RapidAPI-Key": K,
    "X-RapidAPI-Host": H,
    "Content-Type": "application/json"
}

# Pre-populated sidebar values set up to conform to standard server constraints
sport_key = st.sidebar.text_input("Sport Target Key", value="tennis")
status_key = st.sidebar.text_input("Status Target Key", value="pending,live")
league_key = st.sidebar.text_input("League Target Key", value="atp-gstaad")

if st.button("🚀 Run Scan", type="primary"):
    try:
        # STEP 1: Fetch Events
        u1 = f"https://{H}/v2/events"
        p1 = {
            "status": status_key, 
            "sport": sport_key,
            "league": league_key
        }
        res = requests.get(u1, headers=hd, params=p1)
        
        # Friendly catch if the specific league string isn't trading at this millisecond
        if res.status_code == 404:
            st.info(f"The league string '{league_key}' is not actively publishing live data right now.")
            st.write("Try updating the sidebar to 'atp' or clear the field to scan broad categories.")
            st.stop()
            
        if res.status_code != 200:
            st.error(f"API Connection Error: {res.status_code}")
            st.code(res.text)
            st.stop()
            
        data = res.json()
        if not data:
            st.info("No games matching search parameters.")
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
            st.warning("No structural game IDs parsed.")
            st.stop()
            
        # STEP 2: Bulk Odds
        u2 = f"https://{H}/v2/odds/multi"
        p2 = {"bookmakers": "FanDuel", "eventIds": ",".join(id_list)}
        ores = requests.get(u2, headers=hd, params=p2)
        odata = ores.json()
        rows = []
        
        # STEP 3: Pure Flat Short-Line Parser
        for item in odata:
            if not item: continue
            mid = str(item.get('id', ''))
            meta = id_map.get(mid, {"L": "ATP", "M": "MATCH"})
            
            bm = item.get('bookmakers', {})
            fd = bm.get('fanduel') or bm.get('FanDuel')
            if not fd: continue
            
            mkts = fd.get('markets', [])
            if not mkts: continue
            mkt = mkts[0] if isinstance(mkts, list) else mkts
            outcomes = mkt.get('outcomes', [])
            
            for out in outcomes:
                price = out.get('price', 0)
                name = out.get('name', 'Player')
                
                alt = "NORMAL"
                if price >= -130 and price <= 120:
                    alt = "🎯 TRIGGER"
                    
                r = []
                r.append(mid)
                r.append(meta["L"])
                r.append(meta["M"])
                r.append(name)
                r.append(price)
                r.append(alt)
                rows.append(r)
                
        if rows:
            cols = ["ID", "Tour", "Matchup", "Selection", "Odds", "Status"]
            df = pd.DataFrame(rows, columns=cols)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No FanDuel Moneyline options open for these matches currently.")
            
    except Exception as e:
        st.error(f"Crash: {str(e)}")
