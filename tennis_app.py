import streamlit as st
import requests
import pandas as pd

st.set_page_config(layout="wide")
st.title("🎾 Live Tennis Global Strategy Engine")

K = "932206dd22mshf288a41328bab03p12d137jsn9b24ebdfb34c"
H = "odds-api-io-real-time-sports-betting-odds-api.p.rapidapi.com"

# Extracted standalone parsing function to eliminate nested try indentation bugs
def parse_odds(odata, id_map):
    rows = []
    for item in odata:
        if not item: continue
        mid = str(item.get('id', ''))
        meta = id_map.get(mid, {"L": "TOUR", "M": "MATCH"})
        
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
                
            r = [mid, meta["L"], meta["M"], name, price, alt]
            rows.append(r)
    return rows

sport_key = st.sidebar.text_input("Sport Key", value="tennis")
status_key = st.sidebar.text_input("Status Key", value="live")
league_filter = st.sidebar.text_input("League Filter", value="")

if st.button("🚀 Scan All Live Courts", type="primary"):
    hd = {"X-RapidAPI-Key": K, "X-RapidAPI-Host": H, "Content-Type": "application/json"}
    
    try:
        # STEP 1: Fetch Events
        u1 = f"https://{H}/v2/events"
        p1 = {"status": status_key, "sport": sport_key}
        if league_filter.strip():
            p1["league"] = league_filter.strip()
            
        res = requests.get(u1, headers=hd, params=p1)
        
        if res.status_code == 404:
            st.info("No live matches found right now.")
            st.stop()
            
        data = res.json()
        if not data:
            st.info("Empty match array from server.")
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
            st.warning("No active IDs found.")
            st.stop()
            
        # STEP 2: Bulk Retrieve Odds
        u2 = f"https://{H}/v2/odds/multi"
        p2 = {"bookmakers": "FanDuel", "eventIds": ",".join(id_list)}
        ores = requests.get(u2, headers=hd, params=p2)
        odata = ores.json()
        
        # STEP 3: Run Decoupled Parser Function
        rows = parse_odds(odata, id_map)
        
        if rows:
            cols = ["ID", "Tour", "Matchup", "Selection", "Odds", "Status"]
            df = pd.DataFrame(rows, columns=cols)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No FanDuel Moneyline options open for active tennis matches.")
            
    except Exception as e:
        st.error(f"Crash: {str(e)}")
