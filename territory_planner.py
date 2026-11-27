import streamlit as st
import pandas as pd
import numpy as np
import json
import folium
from streamlit_folium import st_folium
from copy import deepcopy
import base64
from math import radians, sin, cos, sqrt, atan2
from io import BytesIO

st.set_page_config(page_title="CH Territory Alignment", layout="wide", initial_sidebar_state="collapsed")

with open("flag.png", "rb") as f:
    flag_b64 = base64.b64encode(f.read()).decode()
with open("opella_logo.jpg", "rb") as f:
    opella_b64 = base64.b64encode(f.read()).decode()

st.markdown(f"""
<style>
    .stApp {{ background-color: #F7EFE6; }}
    h1, h2, h3 {{ color: #042B0B !important; font-family: 'Inter', sans-serif; }}
    p, span, label, div {{ color: #3D553E; }}
    [data-testid="stSidebar"] {{ display: none; }}
    section[data-testid="stSidebar"] {{ display: none; }}
    .block-container {{ padding-top: 5rem; max-width: 100%; }}
    header[data-testid="stHeader"] {{ background: #F7EFE6 !important; height: 0px !important; min-height: 0px !important; visibility: hidden; }}
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    .stButton > button {{ background-color: #042B0B; color: #FFFFFF; border: none; border-radius: 50px; font-weight: 800; padding: 8px 24px; font-size: 14px; letter-spacing: 0.3px; }}
    .stButton > button:hover {{ background-color: #0a4a1a; color: #FFFFFF; }}
    .stSelectbox label, .stMultiSelect label, .stNumberInput label {{ color: #042B0B !important; font-weight: 600; }}
    hr {{ border-color: #042B0B !important; opacity: 0.2; }}
    span[data-baseweb="tag"] {{ background-color: #3D553E !important; color: #FFFFFF !important; }}
    span[data-baseweb="tag"] svg {{ fill: #FFFFFF !important; }}
    span[data-baseweb="tag"] span {{ color: #FFFFFF !important; }}
    [data-testid="stExpander"] {{ background-color: #F0E8DC; border-radius: 12px; }}
    div[data-baseweb="select"] > div {{ border-color: #042B0B !important; border-radius: 50px !important; }}
    div[data-baseweb="input"] {{ border-color: #042B0B !important; border-radius: 50px !important; }}
    .stCheckbox label span {{ color: #3D553E !important; }}
    .opella-title {{ display: flex; align-items: center; gap: 16px; margin-bottom: 1rem; padding: 12px 0; }}
    .opella-title img {{ height: 72px; width: 72px; border-radius: 50%; }}
    .opella-title h1 {{ color: #042B0B !important; font-size: 2.8rem; font-weight: 800; margin: 0; letter-spacing: -0.5px; background: none; -webkit-text-fill-color: #042B0B; }}
    .freq-table-wrap {{ overflow-x: auto; }}
    .freq-table-wrap table td:first-child {{ position: sticky; left: 0; background: #F7EFE6; z-index: 1; }}
</style>
<div style="display:flex; justify-content:space-between; align-items:center;">
<div class="opella-title">
    <img src="data:image/png;base64,{flag_b64}" alt="CH">
    <h1>CH Territory Alignment</h1>
</div>
<img src="data:image/jpeg;base64,{opella_b64}" alt="Opella" style="height:50px;">
</div>
""", unsafe_allow_html=True)

TERRITORY_COLORS = {
    "GE-JU-NE": "#2d6a4f", "VD-VS-FR": "#52796f", "IT-CH": "#588157",
    "BS-BL-BE": "#a7c4a0", "ZG CITY-AG": "#b5b682", "ZH-EAST-CH": "#6b705c",
}
REP_TO_TERRITORY = {
    "Florence": "GE-JU-NE", "Eléonore": "VD-VS-FR", "Alessia": "IT-CH",
    "Michaela": "BS-BL-BE", "Luis": "ZG CITY-AG", "Sarina": "ZH-EAST-CH",
}
TERRITORY_TO_REP = {v: k for k, v in REP_TO_TERRITORY.items()}
WORKING_DAYS = 205
REP_CAPACITY = {
    "Alessia":  {"visits_day": 1.4, "capacity": 287},
    "Eléonore": {"visits_day": 7,   "capacity": 1435},
    "Florence": {"visits_day": 7,   "capacity": 1435},
    "Luis":     {"visits_day": 7.5, "capacity": 1538},
    "Michaela": {"visits_day": 7,   "capacity": 1435},
    "Sarina":   {"visits_day": 5.2, "capacity": 1066},
}
REP_HOME = {
    "Florence":  {"lat": 46.938, "lng": 6.837, "address": "Chez-le-Bart, 2025"},
    "Luis":      {"lat": 47.354, "lng": 8.762, "address": "Wermatswil, 8615"},
    "Eléonore":  {"lat": 46.559, "lng": 6.629, "address": "Le Mont-sur-Lausanne, 1052"},
    "Michaela":  {"lat": 47.189, "lng": 7.711, "address": "Herzogenbuchsee, 3360"},
    "Alessia":   {"lat": 46.064, "lng": 8.935, "address": "Curio, 6986"},
    "Sarina":    {"lat": 47.187, "lng": 8.837, "address": "Altendorf, 8852"},
}
CVM_CATEGORIES = ["Build", "Defend", "Gain", "Maintain"]
HDR_BG = "#042B0B"

# Language groups
TERRITORY_LANGUAGE = {
    "BS-BL-BE": "German", "ZG CITY-AG": "German", "ZH-EAST-CH": "German",
    "GE-JU-NE": "French", "VD-VS-FR": "French",
    "IT-CH": "Italian",
}
LANGUAGE_TERRITORIES = {
    "German": ["BS-BL-BE", "ZG CITY-AG", "ZH-EAST-CH"],
    "French": ["GE-JU-NE", "VD-VS-FR"],
    "Italian": ["IT-CH"],
}
REP_LANGUAGE = {rep: TERRITORY_LANGUAGE.get(terr, "Unknown") for rep, terr in REP_TO_TERRITORY.items()}

def get_color(t): return TERRITORY_COLORS.get(t, "#999999")
def haversine_km(lat1, lng1, lat2, lng2):
    R = 6371; dlat = radians(lat2-lat1); dlng = radians(lng2-lng1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlng/2)**2
    return R*2*atan2(sqrt(a), sqrt(1-a))
def dc(val):
    if val > 0: return "color:#27ae60;font-weight:bold;"
    elif val < 0: return "color:#e74c3c;font-weight:bold;"
    return ""

@st.cache_data
def load_geojson():
    with open("blocks.geojson") as f: return json.load(f)
def load_csv(p): return pd.read_csv(p)

geojson_data = load_geojson()
block_df_original = load_csv("block_data.csv")
block_rep_kpis = load_csv("block_rep_kpis.csv")
rep_baseline = load_csv("rep_baseline.csv")
block_rep_cvm = load_csv("block_rep_cvm.csv")
rep_baseline_cvm = load_csv("rep_baseline_cvm.csv")
block_rep_tp = load_csv("block_rep_tp.csv")
rep_baseline_tp = load_csv("rep_baseline_tp.csv")
pharmacy_detail = load_csv("pharmacy_detail.csv")
# Normalize column names for backward compatibility
pharmacy_detail.rename(columns={"NAME":"Name","ORT":"Ort"}, inplace=True, errors="ignore")
block_centroids = load_csv("block_centroids.csv")

# Initialize scenario state early
if "activated_observe_eans" not in st.session_state:
    st.session_state.activated_observe_eans = set()
if "activated_obs_freq" not in st.session_state:
    st.session_state.activated_obs_freq = 4
if "loaded_scenario_results" not in st.session_state:
    st.session_state.loaded_scenario_results = None

# Session state
for key, val in [("assignments", dict(zip(block_df_original["Block_APO"], block_df_original["territory"]))),
    ("custom_territories", {}), ("tp_explicit", {c: False for c in CVM_CATEGORIES}),
    ("selected_blocks_list", []), ("saved_scenarios", {}), ("undo_stack", [])]:
    if key not in st.session_state: st.session_state[key] = val

TERRITORY_COLORS.update(st.session_state.custom_territories)
assignments = st.session_state.assignments
block_df = block_df_original.copy()
block_df["territory"] = block_df["Block_APO"].map(assignments)
all_territories = sorted(set(assignments.values()) | set(st.session_state.custom_territories.keys()))
original_territories = sorted([t for t in all_territories if t in TERRITORY_TO_REP])
custom_territories_list = sorted([t for t in all_territories if t not in TERRITORY_TO_REP])
sorted_territories = original_territories + custom_territories_list
selected_blocks = st.session_state.selected_blocks_list

# KPIs
original_assignments = dict(zip(block_df_original["Block_APO"], block_df_original["territory"]))
moved_blocks = {b: t for b, t in assignments.items() if t != original_assignments.get(b)}
geo_summary = block_df.groupby("territory").agg(Blocks=("Block_APO","count"), PLZ=("plz_count","sum")).reset_index()
kpi_cols = ["pharmacies","visited_pharmacies","top_pharmacies","total_visits","total_sales"]
visited_cvms_set = {"Build","Defend","Gain","Maintain"}

if st.session_state.loaded_scenario_results:
    # Scenario loaded: use the exact results from the scenario
    _sr = st.session_state.loaded_scenario_results
    _terr_map = {"Florence":"GE-JU-NE","Eléonore":"VD-VS-FR","Alessia":"IT-CH",
                 "Michaela":"BS-BL-BE","Luis":"ZG CITY-AG","Sarina":"ZH-EAST-CH","NewRep":"NEW-REP"}
    kpi_per_territory = {}
    for rn, rd in _sr.items():
        t = _terr_map.get(rn, rn)
        kpi_per_territory[t] = {
            "pharmacies": float(rd.get("pharmacies", 0)),
            "visited_pharmacies": float(rd.get("visited", 0)),
            "top_pharmacies": 0.0,
            "total_visits": float(rd.get("visits", 0)),
            "total_sales": float(rd.get("sales", 0)),
        }
    for t in all_territories:
        if t not in kpi_per_territory: kpi_per_territory[t] = {c: 0.0 for c in kpi_cols}
    # Fill top_pharmacies from pharmacy_detail
    _block_terr = dict(zip(block_df["Block_APO"], block_df["territory"]))
    for t in all_territories:
        t_pharma = pharmacy_detail[pharmacy_detail["Block_APO"].map(_block_terr) == t]
        kpi_per_territory[t]["top_pharmacies"] = float(t_pharma["Top_Priority"].sum()) if len(t_pharma) > 0 else 0.0
else:
    # Normal mode: use baseline CSVs with moved-block adjustments
    kpi_per_territory = {}
    for _, row in rep_baseline.iterrows():
        kpi_per_territory[row["territory"]] = {c: float(row[c]) for c in kpi_cols}
    for t in all_territories:
        if t not in kpi_per_territory: kpi_per_territory[t] = {c: 0.0 for c in kpi_cols}
    for bid, nt in moved_blocks.items():
        for _, row in block_rep_kpis[block_rep_kpis["Block_APO"]==bid].iterrows():
            rt = REP_TO_TERRITORY.get(row["Sales_Rep"],"")
            if rt in kpi_per_territory:
                for c in kpi_cols: kpi_per_territory[rt][c] -= float(row[c])
            for c in kpi_cols: kpi_per_territory[nt][c] += float(row[c])

total_sales_all = sum(k["total_sales"] for k in kpi_per_territory.values())
summary_rows = []
for t in all_territories:
    geo = geo_summary[geo_summary["territory"]==t]
    bl = int(geo["Blocks"].values[0]) if len(geo)>0 else 0
    pl = int(geo["PLZ"].values[0]) if len(geo)>0 else 0
    k = kpi_per_territory.get(t,{c:0 for c in kpi_cols})
    ph = int(round(k["pharmacies"])); vi = int(round(k["visited_pharmacies"]))
    summary_rows.append({"territory":t,"Blocks":bl,"PLZ":pl,"Pharmacies":ph,"Visited":vi,
        "Top_Pharma":int(round(k["top_pharmacies"])),"Visits":int(round(k["total_visits"])),"Sales":k["total_sales"],
        "Coverage":round(vi/ph*100,1) if ph>0 else 0,"Visits_Day":round(k["total_visits"]/WORKING_DAYS,1),
        "Avg_Sales":int(round(k["total_sales"]/ph)) if ph>0 else 0,
        "Sales_Share":round(k["total_sales"]/total_sales_all*100,1) if total_sales_all>0 else 0})
summary = pd.DataFrame(summary_rows).sort_values("territory")

# Legend
legend_cols = st.columns(len(all_territories))
for i, t in enumerate(sorted_territories):
    c = get_color(t); cnt = sum(1 for v in assignments.values() if v==t); r = TERRITORY_TO_REP.get(t,t)
    legend_cols[i].markdown(f'<div style="background:{c};color:white;padding:14px 8px;border-radius:6px;text-align:center;"><strong style="font-size:18px;">{t}</strong><br><span style="font-size:17px;font-weight:600;color:white;">{r}</span><br><span style="font-size:14px;opacity:0.9;color:white;">{cnt} blocks</span></div>', unsafe_allow_html=True)

# MAP + KPIs
col_map, col_kpi = st.columns([3,1])
with col_map:
    m = folium.Map(location=[46.8,8.2], zoom_start=8, tiles="CartoDB positron")
    gc = deepcopy(geojson_data)
    for f in gc["features"]:
        bid = f["properties"]["Block_APO"]; f["properties"]["Territory"] = assignments.get(bid,"Unknown")
    def sf(feature):
        t = feature["properties"].get("Territory","Unknown"); bid = feature["properties"]["Block_APO"]; sel = bid in selected_blocks
        return {"fillColor":get_color(t),"color":"#ff0000" if sel else "#333333","weight":3 if sel else 0.8,"fillOpacity":0.7 if not sel else 0.9}
    folium.GeoJson(gc,style_function=sf,tooltip=folium.GeoJsonTooltip(fields=["Block_APO","Territory"],aliases=["Block:","Territory:"],style="font-size:14px;font-weight:bold;")).add_to(m)
    from shapely.geometry import shape
    for f in gc["features"]:
        cen = shape(f["geometry"]).centroid; bid = f["properties"]["Block_APO"]; t = assignments.get(bid,"Unknown"); lc = get_color(t)
        folium.Marker(location=[cen.y,cen.x],icon=folium.DivIcon(html=f'<div style="font-size:9px;font-weight:bold;color:{lc};text-shadow:1px 1px 1px white,-1px -1px 1px white,1px -1px 1px white,-1px 1px 1px white;white-space:nowrap;">{bid}</div>',icon_size=(50,15),icon_anchor=(25,7))).add_to(m)
    for rn, h in REP_HOME.items():
        folium.Marker(location=[h["lat"],h["lng"]],icon=folium.Icon(color="darkgreen",icon="home",prefix="fa"),tooltip=f"🏠 {rn} — {h['address']}").add_to(m)
    # Show proposed new rep location from loaded scenario only
    if st.session_state.get("wi_loaded_scenario"):
        sc = st.session_state["wi_loaded_scenario"]
        folium.Marker(
            location=[sc["new_lat"], sc["new_lng"]],
            icon=folium.Icon(color="orange", icon="star", prefix="fa"),
            tooltip=f"⭐ {sc['name']} — NewRep ({sc['coverage']}% coverage)",
        ).add_to(m)
    st_folium(m, width=None, height=600, returned_objects=[])

    # Controls below map
    ctrl1, ctrl2, ctrl3 = st.columns(3)
    with ctrl1:
        st.markdown('<p style="color:#042B0B;font-weight:800;font-size:16px;">Add New Territory</p>', unsafe_allow_html=True)
        nn = st.text_input("Name",key="new_terr_input",label_visibility="collapsed",placeholder="Territory name")
        nc = st.color_picker("Color","#e07b39")
        if st.button("Add Territory") and nn and nn not in all_territories:
            st.session_state.custom_territories[nn] = nc; st.rerun()
    with ctrl2:
        st.markdown('<p style="color:#042B0B;font-weight:800;font-size:16px;">Move Blocks</p>', unsafe_allow_html=True)
        src = st.selectbox("From territory:",options=["All"]+all_territories)
        avail = sorted(assignments.keys()) if src=="All" else sorted([b for b,t in assignments.items() if t==src])
        ns = st.multiselect("Select blocks:",options=avail,default=st.session_state.selected_blocks_list,format_func=lambda x:f"{x} ({assignments[x]})")
        st.session_state.selected_blocks_list = ns
        tgt = st.selectbox("Move to:",options=all_territories)
        if ns:
            # Preview with pharmacy count
            pv = {}
            for t in all_territories:
                s = summary[summary["territory"]==t]
                pv[t] = {"Visits":int(s["Visits"].values[0]) if len(s)>0 else 0, "Pharmacies":int(s["Pharmacies"].values[0]) if len(s)>0 else 0}
            for b in ns:
                for _, row in block_rep_kpis[block_rep_kpis["Block_APO"]==b].iterrows():
                    rt = REP_TO_TERRITORY.get(row["Sales_Rep"],"")
                    if rt in pv: pv[rt]["Visits"]-=int(row["total_visits"]); pv[rt]["Pharmacies"]-=int(row["pharmacies"])
                    if tgt in pv: pv[tgt]["Visits"]+=int(row["total_visits"]); pv[tgt]["Pharmacies"]+=int(row["pharmacies"])
            pvh = '<div style="font-size:12px;background:#e8f0e8;padding:8px;border-radius:4px;margin-top:8px;"><strong>Preview after move:</strong><br>'
            for t in sorted_territories:
                if t in pv:
                    sb = summary[summary["territory"]==t]
                    vb = int(sb["Visits"].values[0]) if len(sb)>0 else 0; va = pv[t]["Visits"]; dv = va-vb
                    pb = int(sb["Pharmacies"].values[0]) if len(sb)>0 else 0; pa = pv[t]["Pharmacies"]; dp = pa-pb
                    if dv!=0 or dp!=0:
                        vc = "#27ae60" if dv>0 else "#e74c3c"; pc = "#27ae60" if dp>0 else "#e74c3c"
                        pvh += f'{t}: {vb}→{va} visits (<span style="color:{vc}">{dv:+d}</span>) · {pb}→{pa} ph. (<span style="color:{pc}">{dp:+d}</span>)<br>'
            pvh += '</div>'; st.markdown(pvh, unsafe_allow_html=True)
            # Language warning
            tgt_lang = TERRITORY_LANGUAGE.get(tgt, "Unknown")
            lang_warnings = []
            for b in ns:
                orig_terr = original_assignments.get(b, "")
                block_lang = TERRITORY_LANGUAGE.get(orig_terr, "Unknown")
                if block_lang != tgt_lang and tgt_lang != "Unknown" and block_lang != "Unknown":
                    lang_warnings.append(f"Block {b} ({block_lang}) → {tgt} ({tgt_lang})")
            if lang_warnings:
                whtml = '<div style="font-size:12px;background:#fff3cd;padding:8px;border-radius:4px;margin-top:4px;border-left:4px solid #ffc107;">⚠️ <strong>Language group mismatch:</strong><br>'
                for w in lang_warnings[:5]: whtml += f'{w}<br>'
                if len(lang_warnings) > 5: whtml += f'... and {len(lang_warnings)-5} more'
                whtml += '</div>'; st.markdown(whtml, unsafe_allow_html=True)
        if st.button("Apply Reassignment",type="primary") and ns:
            st.session_state.undo_stack.append(dict(st.session_state.assignments))
            for b in ns: st.session_state.assignments[b] = tgt
            st.session_state.selected_blocks_list = []; st.rerun()
    with ctrl3:
        st.markdown('<p style="color:#042B0B;font-weight:800;font-size:16px;">Actions</p>', unsafe_allow_html=True)
        a1,a2 = st.columns(2)
        with a1:
            if st.button("Undo"):
                if st.session_state.undo_stack: st.session_state.assignments=st.session_state.undo_stack.pop(); st.session_state.selected_blocks_list=[]; st.rerun()
                else: st.info("Nothing to undo")
        with a2:
            if st.button("Reset All"):
                st.session_state.assignments=dict(zip(block_df_original["Block_APO"],block_df_original["territory"])); st.session_state.selected_blocks_list=[]; st.session_state.undo_stack=[]; st.session_state.custom_territories={}; st.session_state["wi_run"]=False; st.session_state["wi_scenarios"]=[]; st.session_state["wi_loaded_scenario"]=None; st.session_state.activated_observe_eans=set(); st.session_state.activated_obs_freq=4; st.session_state.loaded_scenario_results=None; st.rerun()
        st.divider()
        edf = pd.DataFrame([{"Block_APO":b,"Territory":t} for b,t in assignments.items()]).sort_values("Block_APO")
        st.download_button("Assignments CSV",edf.to_csv(index=False),"territory_assignments.csv","text/csv")
        def build_excel():
            o = BytesIO()
            with pd.ExcelWriter(o,engine="openpyxl") as w:
                summary.to_excel(w,sheet_name="Territory KPIs",index=False); edf.to_excel(w,sheet_name="Block Assignments",index=False)
                pc = pharmacy_detail.copy(); pc["current_territory"]=pc["Block_APO"].map(dict(zip(block_df["Block_APO"],block_df["territory"])))
                pc.to_excel(w,sheet_name="Pharmacy Detail",index=False)
                obs = pc[pc["CVM_clean"]=="Observe"]
                sort_col = "YTD2026" if "YTD2026" in obs.columns else ("FY2025" if "FY2025" in obs.columns else None)
                if sort_col: obs = obs.sort_values(sort_col, ascending=False)
                obs.to_excel(w,sheet_name="Observe",index=False)
            return o.getvalue()
        st.download_button("Full Excel Report",build_excel(),"territory_report.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with col_kpi:
    st.markdown('<h3 style="color:#042B0B;font-weight:800;">Territory KPIs</h3>', unsafe_allow_html=True)
    # Capacity chart
    st.markdown('<p style="color:#042B0B;font-weight:700;font-size:14px;">Visit Capacity</p>', unsafe_allow_html=True)
    ch = '<div style="margin-bottom:16px;">'
    for _,row in summary.iterrows():
        t=row["territory"]; r=TERRITORY_TO_REP.get(t,t); rc=REP_CAPACITY.get(r,{"capacity":1435})
        cp=round(row["Visits"]/rc["capacity"]*100,1) if rc["capacity"]>0 else 0
        bw=min(cp,120); bc="#e74c3c" if cp>100 else get_color(t)
        ch+=f'<div style="margin-bottom:4px;font-size:12px;"><span style="display:inline-block;width:90px;">{t[:8]}</span><div style="display:inline-block;width:calc(100% - 140px);height:14px;background:#ddd;border-radius:3px;vertical-align:middle;"><div style="width:{bw}%;height:100%;background:{bc};border-radius:3px;"></div></div><span style="font-size:11px;margin-left:4px;">{cp}%</span></div>'
    ch+='</div>'; st.markdown(ch, unsafe_allow_html=True)
    for _,row in summary.iterrows():
        c=get_color(row["territory"]); r=TERRITORY_TO_REP.get(row["territory"],row["territory"])
        rc=REP_CAPACITY.get(r,{"visits_day":7,"capacity":1435}); cp=round(row["Visits"]/rc["capacity"]*100,1) if rc["capacity"]>0 else 0
        with st.expander(f'{row["territory"]} — {r} | {row["Pharmacies"]} ph. | {row["Sales"]:,.0f}',expanded=False):
            st.markdown(f'<div style="border-left:6px solid {c};padding-left:12px;"><span style="color:#042B0B;">•</span> Blocks: {row["Blocks"]} · PLZ: {row["PLZ"]}<br><span style="color:#042B0B;">•</span> Pharmacies: {row["Pharmacies"]} · Visited: {row["Visited"]} · Coverage: {row["Coverage"]}%<br><span style="color:#042B0B;">•</span> Top Priority Pharmacies: {int(row["Top_Pharma"])}<br><span style="color:#042B0B;">•</span> Visits: {int(row["Visits"])} · V/Day: {row["Visits_Day"]} (vs. {rc["visits_day"]})<br><span style="color:#042B0B;">•</span> Visit Capacity: {cp}% (of {rc["capacity"]})<br><span style="color:#042B0B;">•</span> Net Sales YTD 2026: {row["Sales"]:,.0f} · Avg: {row["Avg_Sales"]:,}</div>', unsafe_allow_html=True)
    st.divider()
    st.markdown(f'**Total: {len(all_territories)} territories · {len(assignments)} blocks**<br>**{summary["Pharmacies"].sum()} ph. · {int(summary["Visits"].sum())} visits · {summary["Sales"].sum():,.0f}**', unsafe_allow_html=True)


# Pharma data for tables
pharma_current = pharmacy_detail.copy()
if st.session_state.loaded_scenario_results:
    _table_terr_map = dict(zip(block_df_original["Block_APO"], block_df_original["territory"]))
else:
    _table_terr_map = dict(zip(block_df["Block_APO"], block_df["territory"]))
pharma_current["current_territory"]=pharma_current["Block_APO"].map(_table_terr_map)
visited_cvms = ["Build","Defend","Gain","Maintain"]

# TOTAL PER CVM
st.divider()
st.markdown('<h3 style="color:#042B0B;font-weight:800;">Total per CVM</h3>', unsafe_allow_html=True)
cfr = st.multiselect("Filter by Sales Rep:",options=["All"]+sorted(pharmacy_detail["Sales_Rep"].unique().tolist()),default=["All"],key="cvm_rep_filter")
pf = pharma_current if "All" in cfr or not cfr else pharma_current[pharma_current["Sales_Rep"].isin(cfr)]
CVM_COLS = CVM_CATEGORIES+["Observe","Total"]
tpa=len(pf); tva=int(pf["Planned_Visits"].sum()); tsa=pf["YTD2026"].sum()
ctd={}
for cvm in CVM_COLS:
    ss = pf if cvm=="Total" else pf[pf["CVM_clean"]==cvm]
    np2=len(ss); nt=int(ss["Top_Priority"].sum()); tv=int(ss["Planned_Visits"].sum())
    vpd=round(tv/WORKING_DAYS,1); ts=ss["YTD2026"].sum(); avs=round(ts/np2,0) if np2>0 else 0
    sp=round(np2/tpa*100,1) if tpa>0 else 0; sv=round(tv/tva*100,1) if tva>0 else 0; ss2=round(ts/tsa*100,1) if tsa>0 else 0
    nv=ss[ss["CVM_clean"].isin(visited_cvms)].shape[0]; cov=round(nv/np2*100,1) if np2>0 else 0
    ctd[cvm]={"Number of Pharmacies":np2,"Share of Pharmacies %":sp,"Top Priority Pharmacies*":nt,"Visits":tv,"Visits/Day":vpd,"Share of Visits %":sv,"Net Sales YTD 2026":f"{ts:,.0f}","Avg Sales/Pharmacy":f"{avs:,.0f}","Share in Total Sales %":ss2}
ch2=f'<table style="width:100%;border-collapse:collapse;font-size:15px;"><tr style="background:{HDR_BG};color:#F7EFE6;"><th style="padding:8px;text-align:left;">Metric</th>'
for cvm in CVM_COLS: ch2+=f'<th style="padding:8px;text-align:center;">{cvm}</th>'
ch2+='</tr>'
for mt in ctd["Build"].keys():
    ch2+=f'<tr style="border-bottom:1px solid #eee;"><td style="padding:6px;font-weight:bold;">{mt}</td>'
    for cvm in CVM_COLS:
        s="font-weight:bold;" if cvm=="Total" else ""; ch2+=f'<td style="padding:6px;text-align:center;{s}">{ctd[cvm][mt]}</td>'
    ch2+='</tr>'
ch2+='</table>'; st.markdown(ch2, unsafe_allow_html=True)
st.markdown('<p style="font-size:12px;color:#6D7F6E;margin-top:4px;">*Pharmacies that generated 50% of Net Sales YTD 2026</p>', unsafe_allow_html=True)

# VISIT FREQUENCY SCENARIO
st.divider()
st.markdown('<h3 style="color:#042B0B;font-weight:800;">Visit Frequency Scenario</h3>', unsafe_allow_html=True)
fc1,fc2 = st.columns([1,3])
with fc1:
    st.markdown("**Adjust visit frequency overrides (visits/year):**")
    st.markdown('<span style="font-size:12px;color:#6D7F6E;">Each pharmacy keeps its individual planned visits as baseline. Activate TP or Sales-based overrides to change specific pharmacies.</span>', unsafe_allow_html=True)

    # Global sales threshold
    sales_threshold = st.number_input("Sales threshold (≥):", min_value=0, max_value=500000, value=10000, step=1000, key="sales_thresh")

    CVM_WITH_OBS = CVM_CATEGORIES + ["Observe"]
    tp_freq = {}; tp_active = {}; sales_freq = {}; sales_active = {}

    # Header
    st.markdown(
        '<div style="display:grid;grid-template-columns:1.2fr 0.3fr 1fr 0.3fr 1fr;gap:4px;font-size:13px;font-weight:bold;padding:4px 0;">'
        '<span style="font-weight:700;">CVM</span><span>★</span><span style="font-weight:700;">TP Freq.</span><span>🔥</span><span style="font-weight:700;">Sales Freq.</span>'
        '</div>', unsafe_allow_html=True)

    for cvm in CVM_WITH_OBS:
        default_override = 8 if cvm not in ("Observe", "Maintain") else (4 if cvm == "Maintain" else 2)
        cols = st.columns([1.2, 0.3, 1, 0.3, 1])
        with cols[0]: st.markdown(f"**{cvm}**")
        with cols[1]: tp_active[cvm] = st.checkbox("", key=f"tp_on_{cvm}", label_visibility="collapsed")
        with cols[2]:
            if tp_active[cvm]:
                tp_freq[cvm] = st.number_input(f"TP_{cvm}", min_value=0, max_value=52, value=default_override, step=1, key=f"tp_freq_{cvm}", label_visibility="collapsed")
            else:
                tp_freq[cvm] = 0
        with cols[3]: sales_active[cvm] = st.checkbox("", key=f"sales_on_{cvm}", label_visibility="collapsed")
        with cols[4]:
            if sales_active[cvm]:
                sales_freq[cvm] = st.number_input(f"S_{cvm}", min_value=0, max_value=52, value=default_override, step=1, key=f"sales_freq_{cvm}", label_visibility="collapsed")
            else:
                sales_freq[cvm] = 0

    if st.button("Reset Frequencies"):
        for cvm in CVM_WITH_OBS:
            st.session_state[f"tp_on_{cvm}"] = False
            st.session_state[f"sales_on_{cvm}"] = False
        st.session_state["sales_thresh"] = 10000
        st.rerun()

def calc_td(bdf, col, bldf):
    r={}
    for _,row in bdf.iterrows():
        t=row.get("territory",""); k=row.get("CVM_clean","__t")
        if t not in r: r[t]={}
        r[t][k]=float(row[col])
    for t in all_territories:
        if t not in r: r[t]={}
    # Only apply block moves if NOT from scenario (scenario only affects map+KPIs)
    if not st.session_state.loaded_scenario_results:
        for bid,nt in moved_blocks.items():
            for _,row in bldf[bldf["Block_APO"]==bid].iterrows():
                rp=row["Sales_Rep"]; k=row.get("CVM_clean","__t"); cnt=float(row["count"]); rt=REP_TO_TERRITORY.get(rp,"")
                if rt in r and k in r.get(rt,{}): r[rt][k]-=cnt
                if nt not in r: r[nt]={}
                r[nt][k]=r[nt].get(k,0)+cnt
    return r

cvm_pt = calc_td(rep_baseline_cvm,"count",block_rep_cvm)
tp_pt = calc_td(rep_baseline_tp,"count",block_rep_tp)

with fc2:
    # Frequency table always uses original 6 territories, never affected by scenarios
    freq_territories = sorted([t for t in TERRITORY_TO_REP.keys()])
    # Baseline data from rep_baseline
    baseline_visits = {}; baseline_pharma = {}; baseline_visited = {}
    for _, row in rep_baseline.iterrows():
        baseline_visits[row["territory"]] = int(row["total_visits"])
        baseline_pharma[row["territory"]] = int(row["pharmacies"])
        baseline_visited[row["territory"]] = int(row["visited_pharmacies"])

    # Compute To Be visits per pharmacy using priority: TP > Sales-based > CVM
    # Map by Sales_Rep → territory (matches baseline CSVs exactly)
    _freq_pharma = pharmacy_detail.copy()
    _freq_pharma["_territory"] = _freq_pharma["Sales_Rep"].map(REP_TO_TERRITORY)

    def calc_to_be_visits(row):
        cvm = row["CVM_clean"]
        is_tp = row.get("Top_Priority", 0) == 1
        sales = row.get("YTD2026", 0)
        pv = row.get("Planned_Visits", 0)

        # Baseline = individual planned visits
        result = pv
        category = cvm

        # Sales-based override (if active and sales >= threshold)
        if sales_active.get(cvm, False) and sales >= sales_threshold:
            result = sales_freq.get(cvm, pv)
            category = f"{cvm}-Sales"

        # Top Priority override (highest priority, if active)
        if is_tp and tp_active.get(cvm, False):
            result = tp_freq.get(cvm, pv)
            category = f"{cvm}-TP"

        return result, category

    _freq_pharma[["_to_be_visits", "_category"]] = _freq_pharma.apply(calc_to_be_visits, axis=1, result_type="expand")

    # Aggregate per territory per CVM - ALL pharmacies in their CVM row
    td = {}
    for t in freq_territories:
        t_ph = _freq_pharma[_freq_pharma["_territory"] == t]
        aiv = baseline_visits.get(t, 0)
        t_pharma_count = baseline_pharma.get(t, 0)
        t_visited_count = baseline_visited.get(t, 0)
        rep_name = TERRITORY_TO_REP.get(t, t)
        rep_cap = REP_CAPACITY.get(rep_name, {"capacity": 1435})["capacity"]

        cd = {}
        tvc = 0; tvv = 0  # total visited count and visits
        for cvm in CVM_WITH_OBS:
            cvm_ph = t_ph[t_ph["CVM_clean"] == cvm]
            cnt = len(cvm_ph)
            vis = int(cvm_ph["_to_be_visits"].sum())
            # TP override delta: compare TP pharmacies' to_be vs individual baseline
            tp_ph = cvm_ph[cvm_ph["Top_Priority"] == 1]
            if tp_active.get(cvm, False):
                tp_base = int(tp_ph["Planned_Visits"].sum())
                tp_delta = int(tp_ph["_to_be_visits"].sum()) - tp_base
            else:
                tp_delta = 0
            # Sales override delta: non-TP pharmacies with sales >= threshold
            if sales_active.get(cvm, False):
                sales_ph = cvm_ph[(cvm_ph["YTD2026"] >= sales_threshold) & (cvm_ph["Top_Priority"] != 1)]
                sales_base = int(sales_ph["Planned_Visits"].sum())
                sales_delta = int(sales_ph["_to_be_visits"].sum()) - sales_base
            else:
                sales_delta = 0

            cd[cvm] = {"count": cnt, "visits": vis, "tp_delta": tp_delta, "sales_delta": sales_delta}
            if cvm != "Observe":
                tvc += cnt; tvv += vis
            elif cvm == "Observe":
                # Observe with visits > 0 count as visited
                obs_visited = len(cvm_ph[cvm_ph["_to_be_visits"] > 0])
                tvc += obs_visited; tvv += vis

        tbv = tvv  # Total = sum of CVM rows
        t_cap_ai = round(aiv / rep_cap * 100, 1) if rep_cap > 0 else 0
        t_cap_tb = round(tbv / rep_cap * 100, 1) if rep_cap > 0 else 0
        t_cov_ai = round(t_visited_count / t_pharma_count * 100, 1) if t_pharma_count > 0 else 0
        t_cov_tb = round(tvc / t_pharma_count * 100, 1) if t_pharma_count > 0 else 0

        td[t] = {"rep": rep_name, "cvm": cd, "tv": {"count": tvc, "visits": tvv},
                 "cov_tb_count": tvc,
                 "ai": aiv, "tb": tbv, "dv": tbv - aiv,
                 "aivpd": round(aiv / WORKING_DAYS, 1), "tbvpd": round(tbv / WORKING_DAYS, 1),
                 "dvpd": round((tbv - aiv) / WORKING_DAYS, 1),
                 "cap_ai": t_cap_ai, "cap_tb": t_cap_tb, "cov_ai": t_cov_ai, "cov_tb": t_cov_tb}

    # Compute total TP and Sales overrides per territory
    for t in freq_territories:
        tp_total = sum(td[t]["cvm"][c]["tp_delta"] for c in CVM_WITH_OBS)
        sales_total = sum(td[t]["cvm"][c]["sales_delta"] for c in CVM_WITH_OBS)
        td[t]["tpo"] = tp_total
        td[t]["sales_o"] = sales_total

    # As Is CVM data from baseline - ALL pharmacies in their CVM row
    _as_is_cvm = {}
    for t in freq_territories:
        t_ph = _freq_pharma[_freq_pharma["_territory"] == t]
        _as_is_cvm[t] = {}
        for cvm in CVM_WITH_OBS:
            cvm_ph = t_ph[t_ph["CVM_clean"] == cvm]
            _as_is_cvm[t][cvm] = {"count": len(cvm_ph), "visits": int(cvm_ph["Planned_Visits"].sum())}

    total_cap = sum(REP_CAPACITY.get(TERRITORY_TO_REP.get(t,""),{"capacity":0})["capacity"] for t in freq_territories)
    total_ai_visits = sum(td[t]["ai"] for t in freq_territories)
    total_tb_visits = sum(td[t]["tb"] for t in freq_territories)

    # Filter by territory
    freq_filter = st.multiselect("Filter by Sales Rep:", options=["All"] + [f"{TERRITORY_TO_REP.get(t,t)} ({t})" for t in freq_territories], default=["All"], key="freq_rep_filter")
    if "All" in freq_filter or not freq_filter:
        show_territories = freq_territories
        show_individual = False
    else:
        show_territories = [t for t in freq_territories if f"{TERRITORY_TO_REP.get(t,t)} ({t})" in freq_filter]
        show_individual = True

    show_total = True

    disp_territories = show_territories if show_individual else []
    html = f'<div class="freq-table-wrap"><table style="width:100%;border-collapse:collapse;font-size:14px;">'
    # Header row 1
    html += f'<tr style="background:{HDR_BG};color:#F7EFE6;"><th rowspan="2" style="padding:8px;text-align:left;min-width:130px;">Metric</th>'
    for t in disp_territories:
        html += f'<th colspan="4" style="padding:6px;text-align:center;border-left:2px solid #0a4a1a;">{t}<br><span style="font-size:11px;">({TERRITORY_TO_REP.get(t,t)})</span></th>'
    if show_total:
        html += f'<th colspan="4" style="padding:6px;text-align:center;border-left:2px solid #0a4a1a;">TOTAL</th>'
    html += '</tr>'
    # Header row 2
    html += f'<tr style="background:#0a4a1a;color:#F7EFE6;">'
    for _ in range(len(disp_territories) + (1 if show_total else 0)):
        html += '<th style="padding:3px;text-align:center;border-left:2px solid #042B0B;font-size:11px;"># Ph.</th>'
        html += '<th style="padding:3px;text-align:center;font-size:11px;">As Is</th>'
        html += '<th style="padding:3px;text-align:center;font-size:11px;">To Be</th>'
        html += '<th style="padding:3px;text-align:center;font-size:11px;">Change</th>'
    html += '</tr>'

    def mk_cells(data_list, bold=False, total_override=None):
        """Generate cells for territories + total. data_list = [(ph, ai, tb), ...]"""
        cells = ""
        s = "font-weight:bold;" if bold else ""
        tot_ph=0;tot_ai=0;tot_tb=0
        for ph,ai,tb in data_list:
            ch=tb-ai; tot_ph+=ph;tot_ai+=ai;tot_tb+=tb
            cs=dc(ch) if ch!=0 else ""
            cells+=f'<td style="padding:3px;text-align:center;border-left:2px solid #eee;{s}">{ph}</td>'
            cells+=f'<td style="padding:3px;text-align:center;{s}">{ai:,}</td>'
            cells+=f'<td style="padding:3px;text-align:center;{s}">{tb:,}</td>'
            cells+=f'<td style="padding:3px;text-align:center;{cs}">{ch:+,}</td>'
        if show_total:
            # Use total_override if provided (covers all territories, not just displayed)
            if total_override:
                tot_ph=sum(d[0] for d in total_override);tot_ai=sum(d[1] for d in total_override);tot_tb=sum(d[2] for d in total_override)
            tch=tot_tb-tot_ai;cs=dc(tch) if tch!=0 else ""
            cells+=f'<td style="padding:3px;text-align:center;border-left:2px solid #eee;font-weight:bold;">{tot_ph}</td>'
            cells+=f'<td style="padding:3px;text-align:center;font-weight:bold;">{tot_ai:,}</td>'
            cells+=f'<td style="padding:3px;text-align:center;font-weight:bold;">{tot_tb:,}</td>'
            cells+=f'<td style="padding:3px;text-align:center;font-weight:bold;{cs}">{tch:+,}</td>'
        return cells

    # CVM rows
    for cvm in CVM_WITH_OBS:
        data = [(_as_is_cvm[t][cvm]["count"], _as_is_cvm[t][cvm]["visits"], td[t]["cvm"][cvm]["visits"]) for t in disp_territories]
        # For total column, use all show_territories
        total_data = [(_as_is_cvm[t][cvm]["count"], _as_is_cvm[t][cvm]["visits"], td[t]["cvm"][cvm]["visits"]) for t in show_territories]
        html += f'<tr style="border-bottom:1px solid #eee;"><td style="padding:4px;font-weight:bold;">{cvm}</td>{mk_cells(data, total_override=total_data)}</tr>'

    # Total
    data_total = [(baseline_pharma.get(t,0), td[t]["ai"], td[t]["tb"]) for t in disp_territories]
    total_all = [(baseline_pharma.get(t,0), td[t]["ai"], td[t]["tb"]) for t in show_territories]
    html += f'<tr style="border-bottom:1px solid #eee;background:#e8f0e8;"><td style="padding:4px;font-weight:bold;">Total</td>{mk_cells(data_total, bold=True, total_override=total_all)}</tr>'

    # TP override (change only)
    for label, key in [("Top Priority", "tpo"), ("Sales-based", "sales_o")]:
        html += f'<tr style="border-bottom:1px solid #eee;background:#fdf6ec;"><td style="padding:4px;font-weight:bold;">{label}</td>'
        tot_ch = 0
        for t in disp_territories:
            ch = td[t][key]; tot_ch += ch; cs = dc(ch) if ch!=0 else ""
            html += f'<td style="padding:3px;text-align:center;border-left:2px solid #eee;" colspan="3"></td>'
            html += f'<td style="padding:3px;text-align:center;{cs}">{ch:+,}</td>'
        # Add non-displayed territories to total
        for t in show_territories:
            if t not in disp_territories: tot_ch += td[t][key]
        if show_total:
            cs = dc(tot_ch) if tot_ch!=0 else ""
            html += f'<td style="padding:3px;text-align:center;border-left:2px solid #eee;" colspan="3"></td>'
            html += f'<td style="padding:3px;text-align:center;font-weight:bold;{cs}">{tot_ch:+,}</td>'
        html += '</tr>'

    # Separator
    html += f'<tr><td colspan="100" style="border-bottom:2px solid {HDR_BG};"></td></tr>'

    # Coverage, Capacity, Visits/Day
    for metric_label, ai_key, tb_key, ai_num_fn, ai_den_fn in [
        ("Coverage", "cov_ai", "cov_tb", lambda t: baseline_visited.get(t,0), lambda t: baseline_pharma.get(t,0)),
        ("Capacity", "cap_ai", "cap_tb", lambda t: td[t]["ai"], lambda t: REP_CAPACITY.get(TERRITORY_TO_REP.get(t,""),{"capacity":1435})["capacity"]),
    ]:
        html += f'<tr style="border-bottom:1px solid #eee;"><td style="padding:4px;font-weight:bold;">{metric_label}</td>'
        tot_ai_n=0;tot_ai_d=0;tot_tb_n=0;tot_tb_d=0
        for t in disp_territories:
            ai_p=td[t][ai_key]; tb_p=td[t][tb_key]; ch=round(tb_p-ai_p,1); cs=dc(ch) if ch!=0 else ""
            tot_ai_n+=ai_num_fn(t);tot_ai_d+=ai_den_fn(t)
            if tb_key=="cov_tb": tot_tb_n+=td[t]["cov_tb_count"]; tot_tb_d+=baseline_pharma.get(t,0)
            else: tot_tb_n+=td[t]["tb"]; tot_tb_d+=ai_den_fn(t)
        for t in show_territories:
            if t not in disp_territories:
                tot_ai_n+=ai_num_fn(t);tot_ai_d+=ai_den_fn(t)
                if tb_key=="cov_tb": tot_tb_n+=td[t]["cov_tb_count"]; tot_tb_d+=baseline_pharma.get(t,0)
                else: tot_tb_n+=td[t]["tb"]; tot_tb_d+=ai_den_fn(t)
        if show_total:
            tot_ai=round(tot_ai_n/tot_ai_d*100,1) if tot_ai_d>0 else 0
            tot_tb=round(tot_tb_n/tot_tb_d*100,1) if tot_tb_d>0 else 0
            tch=round(tot_tb-tot_ai,1);cs=dc(tch) if tch!=0 else ""
            html+=f'<td style="padding:3px;text-align:center;border-left:2px solid #eee;font-weight:bold;" colspan="2">{tot_ai}%</td>'
            html+=f'<td style="padding:3px;text-align:center;font-weight:bold;">{tot_tb}%</td>'
            html+=f'<td style="padding:3px;text-align:center;font-weight:bold;{cs}">{tch:+.1f}%</td>'
        html += '</tr>'

    # Visits/Day
    html += f'<tr style="border-bottom:1px solid #eee;"><td style="padding:4px;font-weight:bold;">Visits/Day</td>'
    tot_ai_vpd=0;tot_tb_vpd=0
    for t in disp_territories:
        ch=td[t]["dvpd"];cs=dc(ch) if ch!=0 else ""
        tot_ai_vpd+=td[t]["aivpd"];tot_tb_vpd+=td[t]["tbvpd"]
        html+=f'<td style="padding:3px;text-align:center;border-left:2px solid #eee;" colspan="2">{td[t]["aivpd"]}</td>'
        html+=f'<td style="padding:3px;text-align:center;">{td[t]["tbvpd"]}</td>'
        html+=f'<td style="padding:3px;text-align:center;{cs}">{ch:+.1f}</td>'
    for t in show_territories:
        if t not in disp_territories: tot_ai_vpd+=td[t]["aivpd"]; tot_tb_vpd+=td[t]["tbvpd"]
    if show_total:
        tch=round(tot_tb_vpd-tot_ai_vpd,1);cs=dc(tch) if tch!=0 else ""
        html+=f'<td style="padding:3px;text-align:center;border-left:2px solid #eee;font-weight:bold;" colspan="2">{round(tot_ai_vpd,1)}</td>'
        html+=f'<td style="padding:3px;text-align:center;font-weight:bold;">{round(tot_tb_vpd,1)}</td>'
        html+=f'<td style="padding:3px;text-align:center;font-weight:bold;{cs}">{tch:+.1f}</td>'
    html += '</tr>'

    html += '</table></div>'
    st.markdown(html, unsafe_allow_html=True)

# DISTANCE CALCULATOR
st.divider()
st.markdown('<h3 style="color:#042B0B;font-weight:800;">Distance Calculator</h3>', unsafe_allow_html=True)
dc1,dc2,dc3 = st.columns([1,1,1])
bc_dict = dict(zip(block_centroids["Block_APO"], zip(block_centroids["lat"],block_centroids["lng"])))
from_options = list(REP_HOME.keys()) + sorted(block_centroids["Block_APO"].tolist())
with dc1:
    fr = st.selectbox("From:", options=from_options, key="dist_from", format_func=lambda x: f"🏠 {x}" if x in REP_HOME else f"Block {x}")
with dc2:
    to = st.selectbox("To:", options=from_options, key="dist_to", format_func=lambda x: f"🏠 {x}" if x in REP_HOME else f"Block {x}")
with dc3:
    def get_coords(x):
        if x in REP_HOME: return REP_HOME[x]["lat"], REP_HOME[x]["lng"]
        if x in bc_dict: return bc_dict[x]
        return None, None
    lat1,lng1 = get_coords(fr); lat2,lng2 = get_coords(to)
    if lat1 and lat2:
        dist = round(haversine_km(lat1,lng1,lat2,lng2),1)
        fr_label = f"🏠 {fr}" if fr in REP_HOME else f"Block {fr}"
        to_label = f"🏠 {to}" if to in REP_HOME else f"Block {to}"
        st.markdown(f'<div style="padding:16px;background:#e8f0e8;border-radius:6px;margin-top:24px;"><strong style="font-size:20px;">{dist} km</strong><br>{fr_label} → {to_label}</div>', unsafe_allow_html=True)

# BLOCK REASSIGNMENT SUGGESTIONS
st.divider()
st.markdown('<h3 style="color:#042B0B;font-weight:800;">Block Reassignment Suggestions</h3>', unsafe_allow_html=True)
st.markdown('<span style="font-size:13px;color:#6D7F6E;">Analyzes each block\'s distance to all rep homes and suggests swaps that reduce travel while keeping capacity balanced (~100%). Only suggests swaps within the same language group.</span>', unsafe_allow_html=True)

# Build block-level data for analysis
_ra_bc = dict(zip(block_centroids["Block_APO"], zip(block_centroids["lat"], block_centroids["lng"])))
_ra_block_visits = {}
_ra_block_sales = {}
_ra_block_pharma = {}
for _, row in block_rep_kpis.iterrows():
    bid = row["Block_APO"]
    _ra_block_visits[bid] = _ra_block_visits.get(bid, 0) + float(row["total_visits"])
    _ra_block_sales[bid] = _ra_block_sales.get(bid, 0) + float(row["total_sales"])
    _ra_block_pharma[bid] = _ra_block_pharma.get(bid, 0) + int(row["pharmacies"])

# Current territory visits/capacity per rep
_ra_rep_visits = {}
for t in original_territories:
    rep = TERRITORY_TO_REP.get(t, t)
    k = kpi_per_territory.get(t, {})
    _ra_rep_visits[rep] = float(k.get("total_visits", 0))

# Compute distance from every block to every rep home
_ra_block_dists = {}
for bid, (blat, blng) in _ra_bc.items():
    _ra_block_dists[bid] = {}
    for rn, h in REP_HOME.items():
        _ra_block_dists[bid][rn] = round(haversine_km(h["lat"], h["lng"], blat, blng), 1)

# Language of each block (from original assignment)
_ra_block_lang = {}
for bid in assignments:
    orig_t = original_assignments.get(bid, assignments.get(bid, ""))
    _ra_block_lang[bid] = TERRITORY_LANGUAGE.get(orig_t, "Unknown")

# Find swap suggestions
_ra_suggestions = []
for bid, cur_terr in assignments.items():
    cur_rep = TERRITORY_TO_REP.get(cur_terr, None)
    if not cur_rep or bid not in _ra_block_dists:
        continue
    cur_dist = _ra_block_dists[bid].get(cur_rep, 999)
    block_lang = _ra_block_lang.get(bid, "Unknown")
    bv = _ra_block_visits.get(bid, 0)
    bs = _ra_block_sales.get(bid, 0)
    bp = _ra_block_pharma.get(bid, 0)

    # Check all reps in the same language group
    for other_rep, other_dist in _ra_block_dists[bid].items():
        if other_rep == cur_rep:
            continue
        other_lang = REP_LANGUAGE.get(other_rep, "Unknown")
        if other_lang != block_lang:
            continue
        # Only suggest if distance saving is meaningful (>15 km closer)
        dist_saving = cur_dist - other_dist
        if dist_saving < 15:
            continue
        # Check capacity impact
        other_terr = REP_TO_TERRITORY.get(other_rep, "")
        cur_rep_cap = REP_CAPACITY.get(cur_rep, {"capacity": 1435})["capacity"]
        other_rep_cap = REP_CAPACITY.get(other_rep, {"capacity": 1435})["capacity"]
        cur_rep_new_v = _ra_rep_visits.get(cur_rep, 0) - bv
        other_rep_new_v = _ra_rep_visits.get(other_rep, 0) + bv
        cur_rep_new_pct = round(cur_rep_new_v / cur_rep_cap * 100, 1) if cur_rep_cap > 0 else 0
        other_rep_new_pct = round(other_rep_new_v / other_rep_cap * 100, 1) if other_rep_cap > 0 else 0
        # Accept if receiving rep stays under 110% and donating rep stays above 70%
        if other_rep_new_pct > 110 or cur_rep_new_pct < 70:
            continue
        # Score: combine distance saving + capacity balance improvement
        cur_pct_before = round(_ra_rep_visits.get(cur_rep, 0) / cur_rep_cap * 100, 1) if cur_rep_cap > 0 else 0
        other_pct_before = round(_ra_rep_visits.get(other_rep, 0) / other_rep_cap * 100, 1) if other_rep_cap > 0 else 0
        # Imbalance = max deviation from 100%
        imb_before = abs(cur_pct_before - 100) + abs(other_pct_before - 100)
        imb_after = abs(cur_rep_new_pct - 100) + abs(other_rep_new_pct - 100)
        balance_gain = imb_before - imb_after
        score = dist_saving * 2 + balance_gain
        _ra_suggestions.append({
            "block": bid, "from_rep": cur_rep, "to_rep": other_rep,
            "from_terr": cur_terr, "to_terr": other_terr,
            "cur_dist": cur_dist, "new_dist": other_dist, "dist_saving": round(dist_saving, 1),
            "from_pct_before": cur_pct_before, "from_pct_after": cur_rep_new_pct,
            "to_pct_before": other_pct_before, "to_pct_after": other_rep_new_pct,
            "balance_gain": round(balance_gain, 1), "score": round(score, 1),
            "visits": int(bv), "sales": round(bs, 0), "pharmacies": int(bp),
            "language": block_lang,
        })

# Sort by score descending
_ra_suggestions.sort(key=lambda x: -x["score"])

# Remove duplicates (if a block appears multiple times, keep best suggestion)
_ra_seen_blocks = set()
_ra_unique = []
for s in _ra_suggestions:
    if s["block"] not in _ra_seen_blocks:
        _ra_unique.append(s)
        _ra_seen_blocks.add(s["block"])

ra_col1, ra_col2 = st.columns([1, 3])
with ra_col1:
    ra_min_saving = st.number_input("Min. distance saving (km):", min_value=5, max_value=100, value=15, step=5, key="ra_min_km")
    ra_lang_filter = st.selectbox("Language group:", options=["All", "German", "French", "Italian"], key="ra_lang")
    ra_show_count = st.number_input("Show top N:", min_value=5, max_value=50, value=20, step=5, key="ra_top_n")

with ra_col2:
    _ra_filtered = [s for s in _ra_unique if s["dist_saving"] >= ra_min_saving]
    if ra_lang_filter != "All":
        _ra_filtered = [s for s in _ra_filtered if s["language"] == ra_lang_filter]
    _ra_display = _ra_filtered[:int(ra_show_count)]

    if _ra_display:
        st.markdown(f"**{len(_ra_filtered)} suggestions found** (showing top {len(_ra_display)} by score)")
        rh = f'<table style="width:100%;border-collapse:collapse;font-size:13px;"><tr style="background:{HDR_BG};color:white;">'
        for col in ["#", "Block", "Lang", "From → To", "Dist Now", "Dist New", "Saving", "Ph.", "Visits", "Sales", "From Cap%", "To Cap%", "Score"]:
            rh += f'<th style="padding:5px;text-align:center;">{col}</th>'
        rh += '</tr>'
        for i, s in enumerate(_ra_display):
            # Color code the capacity changes
            from_arrow = f'{s["from_pct_before"]}→{s["from_pct_after"]}%'
            to_arrow = f'{s["to_pct_before"]}→{s["to_pct_after"]}%'
            from_color = "#27ae60" if abs(s["from_pct_after"]-100) < abs(s["from_pct_before"]-100) else "#e74c3c"
            to_color = "#27ae60" if abs(s["to_pct_after"]-100) < abs(s["to_pct_before"]-100) else "#e74c3c"
            bg = "background:#f8f4ee;" if i % 2 == 0 else ""
            rh += f'<tr style="border-bottom:1px solid #eee;{bg}">'
            rh += f'<td style="padding:4px;text-align:center;">{i+1}</td>'
            rh += f'<td style="padding:4px;text-align:center;font-weight:bold;">{s["block"]}</td>'
            rh += f'<td style="padding:4px;text-align:center;font-size:11px;">{s["language"][:2]}</td>'
            rh += f'<td style="padding:4px;text-align:center;font-size:12px;">{s["from_rep"]}→{s["to_rep"]}</td>'
            rh += f'<td style="padding:4px;text-align:center;">{s["cur_dist"]} km</td>'
            rh += f'<td style="padding:4px;text-align:center;">{s["new_dist"]} km</td>'
            rh += f'<td style="padding:4px;text-align:center;color:#27ae60;font-weight:bold;">−{s["dist_saving"]} km</td>'
            rh += f'<td style="padding:4px;text-align:center;">{s["pharmacies"]}</td>'
            rh += f'<td style="padding:4px;text-align:center;">{s["visits"]}</td>'
            rh += f'<td style="padding:4px;text-align:center;">{s["sales"]:,.0f}</td>'
            rh += f'<td style="padding:4px;text-align:center;"><span style="color:{from_color}">{from_arrow}</span></td>'
            rh += f'<td style="padding:4px;text-align:center;"><span style="color:{to_color}">{to_arrow}</span></td>'
            rh += f'<td style="padding:4px;text-align:center;font-weight:bold;">{s["score"]}</td>'
            rh += '</tr>'
        rh += '</table>'
        st.markdown(rh, unsafe_allow_html=True)

        # Summary by rep pair
        st.markdown("---")
        st.markdown("**Summary by rep pair:**")
        _pair_summary = {}
        for s in _ra_filtered:
            pair = f'{s["from_rep"]} → {s["to_rep"]}'
            if pair not in _pair_summary:
                _pair_summary[pair] = {"count": 0, "total_dist_saving": 0, "total_visits": 0, "total_sales": 0}
            _pair_summary[pair]["count"] += 1
            _pair_summary[pair]["total_dist_saving"] += s["dist_saving"]
            _pair_summary[pair]["total_visits"] += s["visits"]
            _pair_summary[pair]["total_sales"] += s["sales"]
        ps_html = f'<table style="width:100%;border-collapse:collapse;font-size:13px;"><tr style="background:{HDR_BG};color:white;">'
        for col in ["From → To", "Blocks", "Total km Saved", "Visits Moved", "Sales Moved"]:
            ps_html += f'<th style="padding:5px;text-align:center;">{col}</th>'
        ps_html += '</tr>'
        for pair, d in sorted(_pair_summary.items(), key=lambda x: -x[1]["total_dist_saving"]):
            ps_html += f'<tr style="border-bottom:1px solid #eee;"><td style="padding:4px;text-align:center;font-weight:bold;">{pair}</td>'
            ps_html += f'<td style="padding:4px;text-align:center;">{d["count"]}</td>'
            ps_html += f'<td style="padding:4px;text-align:center;color:#27ae60;font-weight:bold;">−{d["total_dist_saving"]:.0f} km</td>'
            ps_html += f'<td style="padding:4px;text-align:center;">{d["total_visits"]}</td>'
            ps_html += f'<td style="padding:4px;text-align:center;">{d["total_sales"]:,.0f}</td></tr>'
        ps_html += '</table>'
        st.markdown(ps_html, unsafe_allow_html=True)

        # Quick-apply top suggestions button
        st.markdown("---")
        ra_apply_n = st.number_input("Apply top N suggestions:", min_value=1, max_value=len(_ra_filtered), value=min(5, len(_ra_filtered)), step=1, key="ra_apply_n")
        if st.button("Apply Selected Reassignments", type="primary", key="ra_apply"):
            st.session_state.undo_stack.append(dict(st.session_state.assignments))
            applied = 0
            # Recompute with running capacity tracking
            _running_visits = dict(_ra_rep_visits)
            for s in _ra_filtered[:int(ra_apply_n)]:
                bid = s["block"]
                from_rep = s["from_rep"]
                to_rep = s["to_rep"]
                to_terr = s["to_terr"]
                bv = s["visits"]
                to_cap = REP_CAPACITY.get(to_rep, {"capacity": 1435})["capacity"]
                from_cap = REP_CAPACITY.get(from_rep, {"capacity": 1435})["capacity"]
                # Re-check capacity with running totals
                if (_running_visits.get(to_rep, 0) + bv) / to_cap <= 1.10 and (_running_visits.get(from_rep, 0) - bv) / from_cap >= 0.70:
                    st.session_state.assignments[bid] = to_terr
                    _running_visits[from_rep] = _running_visits.get(from_rep, 0) - bv
                    _running_visits[to_rep] = _running_visits.get(to_rep, 0) + bv
                    applied += 1
            if applied > 0:
                st.success(f"Applied {applied} reassignments.")
                st.rerun()
            else:
                st.warning("No reassignments could be applied (capacity constraints).")
    else:
        st.info("No reassignment suggestions found with current filters. Try lowering the minimum distance saving.")

# BLOCK DETAILS
st.divider()
st.markdown('<h3 style="color:#042B0B;font-weight:800;">Block Details</h3>', unsafe_allow_html=True)
bm = pharma_current.groupby("Block_APO").agg(territory=("current_territory","first"),plz_count=("PLZ","nunique"),pharmacies=("EAN","count"),
    visited=("CVM_clean",lambda x:x.isin(visited_cvms).sum()),top_pharmacies=("Top_Priority","sum"),visits=("Planned_Visits","sum"),total_sales=("YTD2026","sum")).reset_index()
bm["coverage"]=(bm["visited"]/bm["pharmacies"]*100).round(1); bm["vpd"]=(bm["visits"]/WORKING_DAYS).round(1)
bm["spp"]=(bm["total_sales"]/bm["plz_count"]).round(0); bm["spa"]=(bm["total_sales"]/bm["pharmacies"]).round(0)
bm["ss"]=(bm["total_sales"]/bm["total_sales"].sum()*100).round(2); bm["rep"]=bm["territory"].map(TERRITORY_TO_REP).fillna(bm["territory"])
bm=bm.merge(block_centroids,on="Block_APO",how="left")
def cd2(row):
    h=REP_HOME.get(row.get("rep",""))
    if h and pd.notna(row.get("lat")): return round(haversine_km(h["lat"],h["lng"],row["lat"],row["lng"]),1)
    return None
bm["distance_km"]=bm.apply(cd2,axis=1)
bf1,bf2=st.columns([1,3])
with bf1: btf=st.selectbox("Filter by territory:",options=["All"]+sorted_territories,key="btf")
with bf2:
    fb=bm if btf=="All" else bm[bm["territory"]==btf]
    sb2=st.selectbox("Search block:",options=["Top 10 by Sales"]+sorted(fb["Block_APO"].tolist()),key="bs")
db=fb.nlargest(10,"total_sales") if sb2=="Top 10 by Sales" else bm[bm["Block_APO"]==sb2]
for _,br in db.iterrows():
    ds=f" · 📍 {br['distance_km']} km" if pd.notna(br.get("distance_km")) else ""
    with st.expander(f"Block {br['Block_APO']} — {br['rep']} ({br['territory']}) — {int(br['pharmacies'])} ph. — {br['total_sales']:,.0f} sales{ds}"):
        st.markdown(f"**PLZ:** {int(br['plz_count'])} · **Pharmacies:** {int(br['pharmacies'])} · **Visited:** {int(br['visited'])} · **Coverage:** {br['coverage']}%<br>**Top Pharmacies:** {int(br['top_pharmacies'])} · **Visits:** {int(br['visits'])} · **V/Day:** {br['vpd']}<br>**Net Sales YTD 2026:** {br['total_sales']:,.0f} · **Sales/PLZ:** {br['spp']:,.0f} · **Sales/Pharmacy:** {br['spa']:,.0f} · **Share:** {br['ss']}%", unsafe_allow_html=True)
        bp=pharma_current[pharma_current["Block_APO"]==br["Block_APO"]]
        pm=bp.groupby("PLZ").agg(pharmacies=("EAN","count"),visited=("CVM_clean",lambda x:x.isin(visited_cvms).sum()),top=("Top_Priority","sum"),visits=("Planned_Visits","sum"),sales=("YTD2026","sum")).reset_index()
        pm["coverage"]=(pm["visited"]/pm["pharmacies"]*100).round(1); pm["vpd"]=(pm["visits"]/WORKING_DAYS).round(1); pm=pm.sort_values("sales",ascending=False)
        for _,pr in pm.iterrows():
            with st.expander(f"    PLZ {int(pr['PLZ'])} — {int(pr['pharmacies'])} ph. — {pr['sales']:,.0f} sales"):
                st.markdown(f"**Pharmacies:** {int(pr['pharmacies'])} · **Visited:** {int(pr['visited'])} · **Coverage:** {pr['coverage']}% · **Top:** {int(pr['top'])} · **Visits:** {int(pr['visits'])} · **V/Day:** {pr['vpd']}", unsafe_allow_html=True)
                for _,ph in bp[bp["PLZ"]==pr["PLZ"]].sort_values("YTD2026",ascending=False).iterrows():
                    ts2="⭐ " if ph["Top_Priority"]==1 else ""
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{ts2}**{ph['Name']}** — {ph['CVM_clean']} — {int(ph['Planned_Visits'])} visits — {ph['YTD2026']:,.0f} sales", unsafe_allow_html=True)

# OBSERVE PHARMACIES
st.divider()
st.markdown('<h3 style="color:#042B0B;font-weight:800;">Observe Pharmacies</h3>', unsafe_allow_html=True)
obs=pharma_current[pharma_current["CVM_clean"]=="Observe"].copy().sort_values("YTD2026",ascending=False)
obs["current_territory"]=obs["current_territory"].fillna("Unknown")
no=pharma_current[pharma_current["CVM_clean"]!="Observe"]
pla=no.groupby("PLZ")["YTD2026"].mean().round(0).to_dict()
plc=pharma_current.groupby("PLZ")["EAN"].count().to_dict()
obs["PLZ_Avg_Sales"]=obs["PLZ"].map(pla).fillna(0)
obs["PLZ_Pharma_Count"]=obs["PLZ"].map(plc).fillna(0).astype(int)
st.markdown(f'**{len(obs)} Observe pharmacies** with total sales of **{obs["YTD2026"].sum():,.0f}** — not currently visited.')
to2=obs.head(20)
if len(to2)>0:
    oh=f'<table style="width:100%;border-collapse:collapse;font-size:14px;"><tr style="background:{HDR_BG};color:white;">'
    for c in ["Rank","Name","PLZ","Ort","Block","Territory","Sales Rep","Net Sales YTD 2026","PLZ Avg Sales","PLZ # Pharm."]:
        oh+=f'<th style="padding:6px;text-align:center;">{c}</th>'
    oh+='</tr>'
    for i,(_,r) in enumerate(to2.iterrows()):
        oh+=f'<tr style="border-bottom:1px solid #eee;"><td style="padding:4px;text-align:center;">{i+1}</td><td style="padding:4px;">{r["Name"]}</td><td style="padding:4px;text-align:center;">{int(r["PLZ"])}</td><td style="padding:4px;">{r["Ort"]}</td><td style="padding:4px;text-align:center;">{int(r["Block_APO"])}</td><td style="padding:4px;text-align:center;">{r["current_territory"]}</td><td style="padding:4px;text-align:center;">{r["Sales_Rep"]}</td><td style="padding:4px;text-align:center;">{r["YTD2026"]:,.0f}</td><td style="padding:4px;text-align:center;">{r["PLZ_Avg_Sales"]:,.0f}</td><td style="padding:4px;text-align:center;">{r["PLZ_Pharma_Count"]}</td></tr>'
    oh+='</table>'; st.markdown(oh, unsafe_allow_html=True)

# TERRITORY OPTIMIZATION: ADD 7TH REP
st.divider()
st.markdown('<h3 style="color:#042B0B;font-weight:800;">Territory Optimization: Add New Rep</h3>', unsafe_allow_html=True)
st.markdown("Redistribute all blocks across 7 reps (6 existing + 1 new) to increase coverage while keeping capacity balanced and respecting language groups.")

wi1,wi2=st.columns([1,2])
with wi1:
    total_pharma = len(pharma_current)
    total_visited = pharma_current[pharma_current["CVM_clean"].isin(visited_cvms)].shape[0]
    current_cov = round(total_visited/total_pharma*100,1) if total_pharma>0 else 0
    st.markdown(f"**Current coverage: {current_cov}%** ({total_visited}/{total_pharma})")
    wi_target = st.number_input("Target coverage %:",min_value=50.0,max_value=100.0,value=85.0,step=1.0,key="wi_tgt")
    wi_vpd = st.number_input("New rep V/Day:",min_value=1.0,max_value=15.0,value=7.0,step=0.5,key="wi_vpd")
    wi_max_visits = int(wi_vpd * WORKING_DAYS)
    st.markdown(f"Max visits/year: **{wi_max_visits}**")
    st.markdown("**Visit frequency (all pharmacies):**")
    wh1,wh2,wh3 = st.columns([2,2,2]); wh1.markdown("**CVM**"); wh2.markdown("**Freq.**"); wh3.markdown("**Top Priority**")
    wi_freq = {}; wi_tp_freq = {}
    WI_CVM_LIST = CVM_CATEGORIES + ["Observe"]
    for cvm in WI_CVM_LIST:
        default_f = 4 if cvm != "Observe" else 0
        wlc,wc1,wc2 = st.columns([2,2,2]); wlc.markdown(f"**{cvm}**")
        with wc1: wi_freq[cvm] = st.number_input(f"WI {cvm}",min_value=0,max_value=52,value=default_f,step=1,key=f"wi_freq_{cvm}",label_visibility="collapsed")
        with wc2: wi_tp_freq[cvm] = st.number_input(f"WI TP {cvm}",min_value=0,max_value=52,value=wi_freq[cvm],step=1,key=f"wi_tp_{cvm}",label_visibility="collapsed")
    wi_new_lang = st.selectbox("New rep language:", options=["German", "French", "Italian"], key="wi_lang")
    if st.button("Generate Scenarios", type="primary"):
        st.session_state["wi_run"] = True
    if st.button("Reset Optimization"):
        st.session_state["wi_run"] = False
        st.session_state["wi_scenarios"] = []
        st.session_state["wi_loaded_scenario"] = None
        st.session_state.activated_observe_eans = set()
        st.session_state.activated_obs_freq = 4
        st.session_state.loaded_scenario_results = None
        st.session_state.assignments = dict(zip(block_df_original["Block_APO"], block_df_original["territory"]))
        st.session_state.custom_territories = {}
        st.session_state.undo_stack = []
        st.session_state.selected_blocks_list = []
        st.rerun()
    st.divider()
    st.markdown("""**How it works:**
1. Selects top Observe pharmacies by sales to reach target coverage
2. Recalculates all block visits with new frequencies
3. Finds optimal new rep location within their language region
4. Redistributes ALL blocks among 7 reps within each language group
5. Balances capacity (target: 80-100% for every rep)

**Scenarios:**
- **A: Coverage-focused** \u2014 New rep near highest-value Observe clusters
- **B: Balance-focused** \u2014 New rep near the most overloaded territory
- **C: Geography-focused** \u2014 New rep at geographic center of language region""")

with wi2:
    if st.session_state.get("wi_run", False):
        # Step 1: Select Observe pharmacies to activate
        needed_new_visited = int(np.ceil(wi_target/100*total_pharma)) - total_visited
        needed_new_visited = max(0, needed_new_visited)

        observe_ranked = pharma_current[pharma_current["CVM_clean"]=="Observe"].sort_values("YTD2026", ascending=False)
        activated_observe = observe_ranked.head(needed_new_visited)
        activated_blocks = set(activated_observe["Block_APO"].unique())

        # Step 2: Recalculate block visits with user frequencies
        pc = pharma_current.copy()
        # Mark activated observe pharmacies
        activated_eans = set(activated_observe["EAN"].astype(str))
        def calc_new_visits(row):
            cvm = row["CVM_clean"]
            is_tp = row.get("Top_Priority", 0) == 1
            pv = row.get("Planned_Visits", 0)
            # Observe: only activated ones get visits
            if cvm == "Observe":
                if str(row["EAN"]) in activated_eans:
                    obs_f = wi_freq.get("Observe", 0) if wi_freq.get("Observe", 0) > 0 else pv
                    return obs_f
                return 0
            # Use individual planned visits as baseline, override with WI frequencies
            if cvm in wi_freq:
                result = wi_freq[cvm]
                if is_tp and cvm in wi_tp_freq:
                    result = wi_tp_freq[cvm]
                return result
            return pv
        pc["new_visits"] = pc.apply(calc_new_visits, axis=1)

        # Activated observe count per block
        act_obs_per_block = activated_observe.groupby("Block_APO").size().to_dict()

        bc = block_centroids.copy()
        block_all = pc.groupby("Block_APO").agg(
            total_pharma=("EAN","count"),
            visited_count=("CVM_clean", lambda x: x.isin(visited_cvms).sum()),
            total_visits=("new_visits","sum"),
            total_sales=("YTD2026","sum"),
        ).reset_index()

        block_info = bc.merge(block_all, on="Block_APO", how="left")
        block_info["activated_obs"] = block_info["Block_APO"].map(act_obs_per_block).fillna(0).astype(int)
        block_info["new_visited"] = block_info["visited_count"] + block_info["activated_obs"]
        # Base visits = CVM visits only (no Observe), for block assignment
        pc_no_obs = pc[pc["CVM_clean"] != "Observe"]
        block_base = pc_no_obs.groupby("Block_APO")["new_visits"].sum().to_dict()
        block_info["base_visits"] = block_info["Block_APO"].map(block_base).fillna(0)

        # Block language from original territory
        orig_terr_map = dict(zip(block_df_original["Block_APO"], block_df_original["territory"]))
        block_info["orig_territory"] = block_info["Block_APO"].map(orig_terr_map)
        block_info["language"] = block_info["orig_territory"].map(TERRITORY_LANGUAGE).fillna("Unknown")

        # Distance from each rep home to each block
        all_reps_homes = dict(REP_HOME)
        for rn, h in all_reps_homes.items():
            block_info[f"dist_{rn}"] = block_info.apply(
                lambda r: round(haversine_km(h["lat"],h["lng"],r["lat"],r["lng"]),1) if pd.notna(r["lat"]) else 999, axis=1)

        rep_lang = dict(REP_LANGUAGE)
        rep_lang["NewRep"] = wi_new_lang

        def find_optimal_location(blocks_subset, weight_col):
            if len(blocks_subset) == 0:
                return 46.8, 8.2
            weights = blocks_subset[weight_col].clip(lower=1)
            return (np.average(blocks_subset["lat"], weights=weights),
                    np.average(blocks_subset["lng"], weights=weights))

        rep_caps_local = {r: REP_CAPACITY[r]["capacity"] for r in REP_HOME}
        rep_caps_local["NewRep"] = wi_max_visits

        def run_scenario(name, new_rep_lat, new_rep_lng):
            bi = block_info.copy()
            bi["dist_NewRep"] = bi.apply(
                lambda r: round(haversine_km(new_rep_lat, new_rep_lng, r["lat"], r["lng"]),1) if pd.notna(r["lat"]) else 999, axis=1)

            all_rep_names = list(REP_HOME.keys()) + ["NewRep"]
            rep_caps = {r: REP_CAPACITY[r]["capacity"] for r in REP_HOME}
            rep_caps["NewRep"] = wi_max_visits
            ba = {}

            # STEP A: Assign blocks using base visits (no Observe)
            for lang in ["German", "French", "Italian"]:
                lang_reps = [r for r in all_rep_names if rep_lang.get(r) == lang]
                lang_bl = bi[bi["language"] == lang].copy()
                if not lang_reps or len(lang_bl) == 0: continue

                for r in lang_reps:
                    dc = f"dist_{r}"
                    if dc not in lang_bl.columns: lang_bl[dc] = 999
                lang_bl["min_dist"] = lang_bl[[f"dist_{r}" for r in lang_reps]].min(axis=1)
                lang_bl = lang_bl.sort_values("min_dist")
                rep_used = {r: 0 for r in lang_reps}

                for _, row in lang_bl.iterrows():
                    bid = row["Block_APO"]; bv = row["base_visits"]
                    dists = {r: row[f"dist_{r}"] for r in lang_reps}
                    assigned = False
                    for r in sorted(dists, key=dists.get):
                        if rep_used[r] + bv <= rep_caps[r]:
                            ba[bid] = r; rep_used[r] += bv; assigned = True; break
                    if not assigned:
                        least = min(lang_reps, key=lambda r: rep_used[r]/rep_caps[r] if rep_caps[r]>0 else 999)
                        ba[bid] = least; rep_used[least] += bv

                # Balance: target 80-100% for all reps
                for _i in range(200):
                    pct = {r: rep_used[r]/rep_caps[r] if rep_caps[r]>0 else 0 for r in lang_reps}
                    # Phase 1: fix >100% (critical)
                    over = [r for r in lang_reps if pct[r] > 1.0]
                    # Phase 2: fix imbalance (move from highest to lowest if gap > 20%)
                    if not over:
                        sorted_by_pct = sorted(lang_reps, key=lambda r: pct[r])
                        lowest = sorted_by_pct[0]; highest = sorted_by_pct[-1]
                        if pct[highest] - pct[lowest] < 0.15: break  # close enough
                        if pct[lowest] >= 0.80: break  # everyone above 80%
                        over = [highest]
                    
                    over.sort(key=lambda r: -pct[r]); moved = False
                    for or_r in over:
                        obl = lang_bl[lang_bl["Block_APO"].isin([b for b,r in ba.items() if r==or_r])]
                        obl = obl.sort_values(f"dist_{or_r}", ascending=False)
                        for _, brow in obl.iterrows():
                            bid = brow["Block_APO"]; bv = brow["base_visits"]
                            if bv == 0: continue
                            # Find best receiver: closest to this block, under 100%, and lower pct than donor
                            candidates = [(r, pct[r], brow[f"dist_{r}"]) for r in lang_reps 
                                         if r != or_r and rep_used[r]+bv <= rep_caps[r] and pct[r] < pct[or_r] - 0.05]
                            if not candidates: continue
                            # Prefer lowest capacity %, then closest distance
                            candidates.sort(key=lambda x: (x[1], x[2]))
                            ur_r = candidates[0][0]
                            ba[bid]=ur_r; rep_used[or_r]-=bv; rep_used[ur_r]+=bv; moved=True; break
                        if moved: break
                    if not moved: break

                # Fine-tune geography (only if both reps stay in 80-100%)
                for _i in range(50):
                    imp = False
                    for bid1, r1 in list(ba.items()):
                        if r1 not in lang_reps: continue
                        br1 = lang_bl[lang_bl["Block_APO"]==bid1]
                        if len(br1)==0: continue
                        br1 = br1.iloc[0]
                        for r2 in lang_reps:
                            if r2==r1: continue
                            if br1[f"dist_{r2}"] < br1[f"dist_{r1}"]*0.7:
                                bv = br1["base_visits"]
                                # Both reps must stay within 80-100% after swap
                                if (rep_used[r2]+bv <= rep_caps[r2] and 
                                    rep_used[r1]-bv >= rep_caps[r1]*0.75):
                                    ba[bid1]=r2; rep_used[r1]-=bv; rep_used[r2]+=bv; imp=True; break
                        if imp: break
                    if not imp: break

            # STEP B: Activate Observe pharmacies within remaining capacity (capped at target)
            bi["new_rep"] = bi["Block_APO"].map(ba)
            rep_base = {}
            for rn in all_rep_names:
                rep_base[rn] = int(bi[bi["new_rep"]==rn]["base_visits"].sum())

            target_new = int(np.ceil(wi_target/100*total_pharma)) - total_visited
            target_new = max(0, target_new)
            total_act = 0; rep_act = {r:0 for r in all_rep_names}; blk_act = {}
            obs_freq = wi_freq.get("Observe", 0) if wi_freq.get("Observe", 0) > 0 else wi_freq.get("Build", 4)
            # Collect all Observe candidates sorted by sales globally
            all_obs_list = []
            for rn in all_rep_names:
                remaining = rep_caps[rn] - rep_base[rn]
                if remaining < obs_freq: continue
                rep_bl = bi[bi["new_rep"]==rn]
                r_obs = pharma_current[
                    (pharma_current["Block_APO"].isin(rep_bl["Block_APO"])) &
                    (pharma_current["CVM_clean"]=="Observe")
                ].copy()
                r_obs["_rep"] = rn
                all_obs_list.append(r_obs)
            if all_obs_list:
                all_obs_df = pd.concat(all_obs_list).sort_values("YTD2026", ascending=False)
                rep_remaining = {rn: rep_caps[rn] - rep_base[rn] for rn in all_rep_names}
                for _, orow in all_obs_df.iterrows():
                    if total_act >= target_new: break
                    rn = orow["_rep"]
                    if rep_remaining.get(rn, 0) >= obs_freq:
                        total_act += 1; rep_act[rn] += 1
                        blk_act[orow["Block_APO"]] = blk_act.get(orow["Block_APO"],0)+1
                        rep_remaining[rn] -= obs_freq

            bi["final_activated"] = bi["Block_APO"].map(blk_act).fillna(0).astype(int)
            new_cov = round((total_visited + total_act)/total_pharma*100, 1)

            results = {}
            for rn in all_rep_names:
                rb = bi[bi["new_rep"]==rn]; cap=rep_caps[rn]
                bv=rep_base[rn]; ao=rep_act[rn]; tv=bv+ao*obs_freq
                dc_col = f"dist_{rn}" if rn!="NewRep" else "dist_NewRep"
                nv=int(rb["visited_count"].sum())+ao; np2=int(rb["total_pharma"].sum())
                results[rn] = {
                    "blocks":len(rb),"pharmacies":np2,"visited":nv,"activated_obs":ao,
                    "coverage":round(nv/np2*100,1) if np2>0 else 0,
                    "visits":tv,"capacity":cap,
                    "cap_pct":round(tv/cap*100,1) if cap>0 else 0,
                    "vpd":round(tv/WORKING_DAYS,1),
                    "sales":round(rb["total_sales"].sum(),0),
                    "avg_dist":round(rb[dc_col].mean(),1) if len(rb)>0 else 0,
                    "max_dist":round(rb[dc_col].max(),1) if len(rb)>0 else 0,
                }
            return {"name":name,"new_lat":new_rep_lat,"new_lng":new_rep_lng,
                    "coverage":new_cov,"assignments":ba,"results":results,
                    "total_activated":total_act}

        # Generate 3 scenarios with different new rep locations
        lang_blocks = block_info[block_info["language"] == wi_new_lang]

        # A: Near highest-value Observe clusters in this language
        obs_lang = lang_blocks[lang_blocks["activated_obs"] > 0]
        if len(obs_lang) > 0:
            a_lat, a_lng = find_optimal_location(obs_lang, "total_sales")
        else:
            a_lat, a_lng = find_optimal_location(lang_blocks, "total_sales")

        # B: Near the most overloaded territory in this language
        lang_terrs = LANGUAGE_TERRITORIES.get(wi_new_lang, [])
        lang_summary = summary[summary["territory"].isin(lang_terrs)]
        if len(lang_summary) > 0:
            ol_terr = lang_summary.loc[lang_summary.apply(
                lambda r: r["Visits"]/(REP_CAPACITY.get(TERRITORY_TO_REP.get(r["territory"],""),{"capacity":1435})["capacity"])
                if r["territory"] in TERRITORY_TO_REP else 0, axis=1).idxmax(), "territory"]
            ol_bl = block_info[block_info["orig_territory"]==ol_terr]
            b_lat, b_lng = find_optimal_location(ol_bl, "total_visits")
        else:
            b_lat, b_lng = a_lat, a_lng

        # C: Geographic center of language region
        c_lat, c_lng = find_optimal_location(lang_blocks, "total_pharma")

        scenarios = [
            run_scenario("A: Coverage-focused", a_lat, a_lng),
            run_scenario("B: Balance-focused", b_lat, b_lng),
            run_scenario("C: Geography-focused", c_lat, c_lng),
        ]
        st.session_state["wi_scenarios"] = scenarios

        st.markdown(f"**Target: {wi_target}% coverage.** Algorithm activates Observe pharmacies within each rep's remaining capacity (hard cap: 100%).")
        # Warn about language groups with only 1 rep (can't rebalance)
        for lang in ["German", "French", "Italian"]:
            lang_reps_check = [r for r in (list(REP_HOME.keys()) + ["NewRep"]) if rep_lang.get(r) == lang]
            if len(lang_reps_check) == 1:
                st.markdown(f'<div style="font-size:13px;background:#fff3cd;padding:6px;border-radius:4px;border-left:4px solid #ffc107;">⚠️ **{lang}** has only 1 rep ({lang_reps_check[0]}) — capacity cannot be rebalanced. Consider setting new rep language to {lang}.</div>', unsafe_allow_html=True)

        for sc in scenarios:
            with st.expander(f"{sc['name']} \u2014 Coverage: {sc['coverage']}% \u2014 New rep at ({sc['new_lat']:.2f}, {sc['new_lng']:.2f})"):
                st.markdown(f"**Coverage: {current_cov}% \u2192 {sc['coverage']}%** ({sc.get('total_activated',0)} Observe pharmacies activated)")

                sh = f'<table style="width:100%;border-collapse:collapse;font-size:14px;"><tr style="background:{HDR_BG};color:white;">'
                for col in ["Rep","Lang","Blocks","Ph.","Visited","New Obs","Cov%","Visits","Visits/Day","Cap%","Avg km","Max km","Sales"]:
                    sh += f'<th style="padding:6px;text-align:center;">{col}</th>'
                sh += '</tr>'
                for rn in list(REP_HOME.keys()) + ["NewRep"]:
                    r = sc["results"].get(rn, {})
                    rl = rep_lang.get(rn, "?")
                    bg = "background:#e8f0e8;" if rn=="NewRep" else ""
                    cp = r.get("cap_pct",0)
                    cs2 = "color:#e74c3c;font-weight:bold;" if cp>100 else ("color:#e67e22;" if cp<80 else "")
                    sh += f'<tr style="border-bottom:1px solid #eee;{bg}">'
                    sh += f'<td style="padding:4px;font-weight:bold;">{rn}</td>'
                    sh += f'<td style="padding:4px;text-align:center;font-size:12px;">{rl}</td>'
                    for v in [r.get("blocks",0), r.get("pharmacies",0), r.get("visited",0), r.get("activated_obs",0)]:
                        sh += f'<td style="padding:4px;text-align:center;">{v}</td>'
                    sh += f'<td style="padding:4px;text-align:center;">{r.get("coverage",0)}%</td>'
                    sh += f'<td style="padding:4px;text-align:center;">{r.get("visits",0):,}</td>'
                    sh += f'<td style="padding:4px;text-align:center;">{r.get("vpd",0)}</td>'
                    sh += f'<td style="padding:4px;text-align:center;{cs2}">{cp}%</td>'
                    sh += f'<td style="padding:4px;text-align:center;">{r.get("avg_dist",0)}</td>'
                    sh += f'<td style="padding:4px;text-align:center;">{r.get("max_dist",0)}</td>'
                    sh += f'<td style="padding:4px;text-align:center;">{r.get("sales",0):,.0f}</td></tr>'
                sh += '</table>'
                st.markdown(sh, unsafe_allow_html=True)

                # Block moves summary
                changes_from = {}
                for bid, new_rep in sc["assignments"].items():
                    old_t = original_assignments.get(bid, "")
                    old_r = TERRITORY_TO_REP.get(old_t, old_t)
                    if old_r != new_rep:
                        key = f"{old_r} \u2192 {new_rep}"
                        changes_from[key] = changes_from.get(key, 0) + 1
                if changes_from:
                    st.markdown("**Block moves:**")
                    for mv, cnt in sorted(changes_from.items(), key=lambda x: -x[1]):
                        st.markdown(f"&nbsp;&nbsp;{mv}: {cnt} blocks")

                if st.button(f"Load {sc['name']}", key=f"load_{sc['name']}"):
                    r2t = dict(REP_TO_TERRITORY); r2t["NewRep"] = "NEW-REP"
                    na = {bid: r2t.get(rep, rep) for bid, rep in sc["assignments"].items()}
                    if "NEW-REP" not in st.session_state.custom_territories:
                        st.session_state.custom_territories["NEW-REP"] = "#e07b39"
                    st.session_state.undo_stack.append(dict(st.session_state.assignments))
                    st.session_state.assignments = na
                    st.session_state["wi_loaded_scenario"] = sc
                    # Store scenario results directly for KPI consistency
                    st.session_state.loaded_scenario_results = sc["results"]
                    st.rerun()
    else:
        st.info("Set parameters and click **Generate Scenarios** to see optimization results.")

# SCENARIO MANAGEMENT
st.divider()
st.markdown('<h3 style="color:#042B0B;font-weight:800;">Scenario Management</h3>', unsafe_allow_html=True)
sc1,sc2,sc3=st.columns(3)
with sc1:
    st.markdown("**Save Current Scenario**")
    sn=st.text_input("Scenario name:",key="sc_name",placeholder="e.g. Option A")
    if st.button("Save Scenario") and sn:
        st.session_state.saved_scenarios[sn]={"assignments":dict(st.session_state.assignments),"tp_freq":dict(tp_freq),"sales_freq":dict(sales_freq),"tp_active":dict(tp_active),"sales_active":dict(sales_active),"sales_threshold":sales_threshold,
            "summary":{t:{"Blocks":int(summary[summary["territory"]==t]["Blocks"].values[0]) if len(summary[summary["territory"]==t])>0 else 0,
                "Pharmacies":int(summary[summary["territory"]==t]["Pharmacies"].values[0]) if len(summary[summary["territory"]==t])>0 else 0,
                "Visits":int(summary[summary["territory"]==t]["Visits"].values[0]) if len(summary[summary["territory"]==t])>0 else 0,
                "Sales":float(summary[summary["territory"]==t]["Sales"].values[0]) if len(summary[summary["territory"]==t])>0 else 0} for t in all_territories}}
        st.success(f"Saved '{sn}'")
with sc2:
    st.markdown("**Export / Import**")
    if st.session_state.saved_scenarios:
        es=st.selectbox("Export:",options=list(st.session_state.saved_scenarios.keys()),key="es")
        if st.button("Export JSON"): st.download_button("Download",json.dumps(st.session_state.saved_scenarios[es],indent=2),f"{es}.json","application/json",key="dl_sc")
    up=st.file_uploader("Import (JSON):",type=["json"],key="imp_sc")
    if up:
        try: st.session_state.saved_scenarios[up.name.replace(".json","")]=json.loads(up.read()); st.success(f"Imported '{up.name}'")
        except Exception as e: st.error(f"Error: {e}")
with sc3:
    st.markdown("**Load Scenario**")
    if st.session_state.saved_scenarios:
        ls=st.selectbox("Load:",options=list(st.session_state.saved_scenarios.keys()),key="ls")
        if st.button("Load"):
            sc=st.session_state.saved_scenarios[ls]; st.session_state.assignments={int(k):v for k,v in sc["assignments"].items()}
            CVM_WITH_OBS = CVM_CATEGORIES + ["Observe"]
            for cvm in CVM_WITH_OBS:
                st.session_state[f"tp_freq_{cvm}"]=sc.get("tp_freq",{}).get(cvm,4)
                st.session_state[f"sales_freq_{cvm}"]=sc.get("sales_freq",{}).get(cvm,4)
                st.session_state[f"tp_on_{cvm}"]=sc.get("tp_active",{}).get(cvm,False)
                st.session_state[f"sales_on_{cvm}"]=sc.get("sales_active",{}).get(cvm,False)
            st.session_state["sales_thresh"]=sc.get("sales_threshold",10000)
            st.rerun()
    else: st.info("No saved scenarios yet.")
if len(st.session_state.saved_scenarios)>=2:
    st.markdown("**Compare Scenarios**")
    cs=st.multiselect("Select scenarios:",options=list(st.session_state.saved_scenarios.keys()),key="cs")
    if len(cs)>=2:
        ch3=f'<table style="width:100%;border-collapse:collapse;font-size:14px;"><tr style="background:{HDR_BG};color:white;"><th style="padding:6px;">Territory</th>'
        for s in cs: ch3+=f'<th colspan="3" style="padding:6px;text-align:center;">{s}</th>'
        ch3+='</tr><tr style="background:#e8f0e8;"><td></td>'
        for s in cs: ch3+='<td style="padding:4px;text-align:center;font-weight:bold;">Blocks</td><td style="padding:4px;text-align:center;font-weight:bold;">Visits</td><td style="padding:4px;text-align:center;font-weight:bold;">Sales</td>'
        ch3+='</tr>'
        at2=set()
        for s in cs: at2.update(st.session_state.saved_scenarios[s]["summary"].keys())
        for t in sorted(at2):
            ch3+=f'<tr style="border-bottom:1px solid #eee;"><td style="padding:4px;font-weight:bold;">{t}</td>'
            for s in cs:
                d=st.session_state.saved_scenarios[s]["summary"].get(t,{})
                ch3+=f'<td style="padding:4px;text-align:center;">{d.get("Blocks",0)}</td><td style="padding:4px;text-align:center;">{d.get("Visits",0):,}</td><td style="padding:4px;text-align:center;">{d.get("Sales",0):,.0f}</td>'
            ch3+='</tr>'
        ch3+='</table>'; st.markdown(ch3, unsafe_allow_html=True)
