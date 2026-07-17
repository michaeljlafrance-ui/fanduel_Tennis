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

if st.button("🔄 Scan Live Tennis Courts", type="primary"):
    try:
        # STEP 1: Fetch Live Tennis Events
        u1 = f"https://{H}/v2/events"
        p1 = {"status": "live", "sport": "tennis"}
        res = requests.get(u1, headers=hd, params=p1)
        
        if res.status_code == 404:
            st.info("No active live tennis matches right now.")
            st.stop()
            
        data = res.json()
        if not data:
            st.info("No live tennis events found on the feed.")
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
            st.warning("No active match IDs recovered.")
            st.stop()
            
        # STEP 2: Bulk Fetch Live Odds (Looking for H2H/Moneyline)
        u2 = f"https://{H}/v2/odds/multi"
        p2 = {"bookmakers": "FanDuel", "eventIds": ",".join(id_list)}
        ores = requests.get(u2, headers=hd, params=p2)
        
        if ores.status_code != 200:
            st.error("Odds database pipeline offline.")
            st.stop()
            
        odata = ores.json()
        rows = []
        
        # STEP 3: Parse Out Value Deviations
        for item in odata:
            if not item or 'bookmakers' not in item:
                continue
            mid = str(item.get('id', item.get('eventId', '')))
            meta = id_map.get(mid, {"L": "ATP", "M": "LIVE MATCH"})
            
            bm = item['bookmakers']
            fd = bm.get('fanduel') or bm.get('FanDuel')
            if not fd:
                continue
                
            # Target the head-to-head match winner market
            mkts = fd.get('markets') or fd.get('h2h') or []
            mkt = mkts[0] if isinstance(mkts, list) else mkts
            if not mkt or 'outcomes' not in mkt:
                continue
                
            for out in mkt['outcomes']:
                price = out.get('price') or out.get('odds') or 0
                name = out.get('name', 'Player')
                
                # Check for specific high-probability value entry windows
                # An elite player crossing near flat/plus money live
                alt = "NORMAL"
                if price >= -130 and price <= 120:
                    alt = "🎯 RECOVERY TRIGGER: High-Value Spot"
                    
                r = []
                r.append(mid)
                r.append(meta["L"].upper())
                r.append(meta["M"].upper())
                r.append(name.upper())
                r.append(price)
                r.append(alt)
                rows.append(r)
                
        if rows:
            cols = ["ID", "Tour", "Matchup", "Selection", "Live Odds", "Alert Status"]
            df = pd.DataFrame(rows, columns=cols)
            
            # Style the high-win-rate alerts cleanly
            def highlight(v):
                return 'background-color: #d4edda; color: #155724; font-weight: bold;' if 'TRIGGER' in str(v) else ''
            
            sdf = df.style.map(highlight, subset=['Alert Status'])
            st.dataframe(sdf, use_container_width=True, hide_index=True)
        else:
            st.info("No active lines open on FanDuel for these events.")
            
    except Exception as e:
        st.error(f"Engine Exception: {str(e)}")
