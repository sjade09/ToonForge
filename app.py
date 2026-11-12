import os
import sqlite3
import calendar
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

try:
    import plotly.express as px
except ImportError:
    px = None

try:
    from supabase import create_client
except ImportError:
    create_client = None


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="ToonForge | Webtoon Studio",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = Path("toonforge.db")
GENRES = ["판타지/액션", "로맨스/드라마", "일상/개그", "스릴러/공포", "미스터리", "기타"]

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');
:root {
  --ink: #20243a; --muted: #777d91; --line: #e8eaf1;
  --purple: #7158d8; --purple-dark: #5941bd; --lavender: #f1efff;
  --surface: #ffffff; --bg: #f7f8fc;
}
html, body, [class*="css"] { font-family: 'DM Sans','Noto Sans KR',sans-serif; }
.stApp { background: var(--bg); color: var(--ink); }
.block-container { max-width: 1440px; padding-top: 2rem; padding-bottom: 3rem; }
[data-testid="stSidebar"] { background: #fff; border-right: 1px solid var(--line); }
[data-testid="stSidebar"] .block-container { padding-top: 1.5rem; }
h1,h2,h3 { color: var(--ink); letter-spacing: -0.035em; }
h1 { font-weight: 800; }
p, label, .stCaption { color: var(--muted); }
div[data-testid="stMetric"] {
  background: white; border: 1px solid var(--line); border-radius: 16px;
  padding: 18px 20px; box-shadow: 0 4px 18px rgba(32,36,58,.035);
}
div[data-testid="stMetricLabel"] { color: #777d91; font-weight: 600; }
div[data-testid="stMetricValue"] { color: #20243a; font-weight: 800; }
.stButton > button, .stFormSubmitButton > button {
  border-radius: 10px; border: 1px solid #dedaf8; font-weight: 700;
  min-height: 2.65rem;
}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
  background: var(--purple); border-color: var(--purple); color: white;
}
.stButton > button[kind="primary"]:hover { background: var(--purple-dark); border-color: var(--purple-dark); }
div[data-testid="stTabs"] button { font-weight: 700; }
div[data-testid="stTabs"] button[aria-selected="true"] { color: var(--purple); }
div[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
.tf-hero {
  background: linear-gradient(115deg,#292c49 0%,#48406f 56%,#7058d8 100%);
  border-radius: 22px; padding: 30px 34px; color: white; margin-bottom: 22px;
  box-shadow: 0 12px 30px rgba(67,57,128,.16);
}
.tf-hero h1 { color: white; font-size: 2.25rem; margin: 0 0 8px 0; }
.tf-hero p { color: #e6e2ff; margin: 0; font-size: 1rem; }
.tf-kicker { color: #c9c1ff; font-size: .75rem; font-weight: 800; letter-spacing: .16em; text-transform: uppercase; }
.tf-panel {
  background: white; border: 1px solid var(--line); border-radius: 16px;
  padding: 18px 20px; margin-bottom: 12px;
}
.tf-day {
  border: 1px solid var(--line); background: white; border-radius: 12px;
  padding: 9px 10px; min-height: 112px;
}
.tf-day.today { border: 1.5px solid var(--purple); background: #faf9ff; }
.tf-day-num { color: var(--ink); font-size: .9rem; font-weight: 800; margin-bottom: 7px; }
.tf-event {
  background: var(--lavender); color: #5941bd; border-radius: 6px;
  padding: 4px 6px; font-size: .70rem; font-weight: 700; margin: 3px 0;
  overflow-wrap: anywhere;
}
.tf-muted { color: #9297a8; font-size: .75rem; }
a { color: var(--purple); }
@media (max-width: 700px) {
  .block-container { padding: 1rem .8rem 2rem .8rem; }
  .tf-hero { padding: 23px 20px; }
  .tf-hero h1 { font-size: 1.7rem; }
  .tf-day { min-height: 82px; padding: 6px 5px; }
  .tf-event { font-size: .62rem; }
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Configuration and data layer
# ---------------------------------------------------------
def get_secret(name, default=""):
    try:
        return st.secrets.get(name, os.getenv(name, default))
    except Exception:
        return os.getenv(name, default)


APP_PASSWORD = get_secret("APP_PASSWORD")
SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_KEY = get_secret("SUPABASE_SERVICE_ROLE_KEY")

@st.cache_resource
def supabase_client():
    if SUPABASE_URL and SUPABASE_KEY and create_client:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    return None

def db_mode():
    return "Supabase" if supabase_client() else "SQLite (로컬)"

def init_sqlite():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                read_date TEXT NOT NULL,
                title TEXT NOT NULL,
                episode TEXT DEFAULT '',
                genre TEXT NOT NULL,
                rating INTEGER NOT NULL,
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()

def get_reviews():
    sb = supabase_client()
    if sb:
        response = sb.table("reviews").select("*").order("read_date", desc=True).execute()
        rows = response.data or []
        return pd.DataFrame(rows, columns=[
            "id", "read_date", "title", "episode", "genre", "rating", "notes", "created_at"
        ])
    init_sqlite()
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query("SELECT * FROM reviews ORDER BY read_date DESC, id DESC", conn)

def add_review(payload):
    sb = supabase_client()
    if sb:
        sb.table("reviews").insert(payload).execute()
    else:
        init_sqlite()
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO reviews (read_date,title,episode,genre,rating,notes,created_at)
                VALUES (?,?,?,?,?,?,?)
            """, tuple(payload[k] for k in [
                "read_date","title","episode","genre","rating","notes","created_at"
            ]))
            conn.commit()

def update_review(review_id, payload):
    sb = supabase_client()
    if sb:
        sb.table("reviews").update(payload).eq("id", review_id).execute()
    else:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                UPDATE reviews SET read_date=?,title=?,episode=?,genre=?,rating=?,notes=?
                WHERE id=?
            """, (
                payload["read_date"], payload["title"], payload["episode"],
                payload["genre"], payload["rating"], payload["notes"], review_id
            ))
            conn.commit()

def delete_review(review_id):
    sb = supabase_client()
    if sb:
        sb.table("reviews").delete().eq("id", review_id).execute()
    else:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DELETE FROM reviews WHERE id=?", (review_id,))
            conn.commit()


# ---------------------------------------------------------
# Optional password gate for a public URL
# ---------------------------------------------------------
if APP_PASSWORD:
    if not st.session_state.get("authenticated", False):
        st.markdown('<div class="tf-hero"><div class="tf-kicker">YOUR CREATIVE READING SPACE</div><h1>ToonForge</h1><p>Read deeply. Study the craft. Build your own stories.</p></div>', unsafe_allow_html=True)
        with st.form("login_form"):
            st.subheader("비공개 접속")
            password = st.text_input("접속 비밀번호", type="password")
            submitted = st.form_submit_button("접속하기", type="primary")
            if submitted:
                if password == APP_PASSWORD:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("비밀번호가 올바르지 않습니다.")
        st.stop()


# ---------------------------------------------------------
# Header and navigation
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("## 🎨 ToonForge")
    st.caption("WEBTOON READING STUDIO")
    page = st.radio(
        "WORKSPACE",
        ["대시보드", "독서 캘린더", "감상평 관리", "취향 진단"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("DATA STORAGE")
    st.markdown(f"**{db_mode()}**")
    if APP_PASSWORD:
        if st.button("로그아웃", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
    st.markdown("---")
    st.caption("ToonForge · Make every panel count.")

st.markdown("""
<div class="tf-hero">
  <div class="tf-kicker">YOUR CREATIVE READING SPACE</div>
  <h1>Read deeply. Create boldly.</h1>
  <p>웹툰을 읽고, 연출을 관찰하고, 나만의 창작 감각을 기록해 보세요.</p>
</div>
""", unsafe_allow_html=True)

try:
    df = get_reviews()
except Exception as e:
    st.error("데이터베이스에 연결하지 못했습니다. Supabase 설정과 테이블을 확인해 주세요.")
    st.exception(e)
    st.stop()

if not df.empty:
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0).astype(int)
    df["read_date"] = pd.to_datetime(df["read_date"], errors="coerce").dt.strftime("%Y-%m-%d")


# ---------------------------------------------------------
# Dashboard
# ---------------------------------------------------------
if page == "대시보드":
    st.subheader("Overview")
    st.caption(f"{date.today().strftime('%Y년 %m월 %d일')} · 나의 독서 활동")

    total = len(df)
    titles = df["title"].nunique() if total else 0
    avg = float(df["rating"].mean()) if total else 0
    this_month = date.today().strftime("%Y-%m")
    month_total = int(df["read_date"].str.startswith(this_month).sum()) if total else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("전체 독서 기록", f"{total:,}개")
    m2.metric("읽은 작품", f"{titles:,}개")
    m3.metric("이번 달 기록", f"{month_total:,}개")
    m4.metric("평균 별점", f"{avg:.1f} / 5" if total else "—")

    left, right = st.columns([1.35, 1])
    with left:
        st.markdown("### 최근 독서 기록")
        if total:
            recent = df.head(6)[["read_date","title","episode","genre","rating"]].copy()
            recent.columns = ["읽은 날짜","작품","회차","장르","별점"]
            recent["별점"] = recent["별점"].map(lambda n: "★" * int(n))
            st.dataframe(recent, use_container_width=True, hide_index=True)
        else:
            st.info("아직 기록이 없어요. 독서 캘린더에서 첫 기록을 추가해 보세요.")
    with right:
        st.markdown("### 장르 분포")
        if total:
            genre_data = df["genre"].value_counts().rename_axis("장르").reset_index(name="기록")
            if px:
                fig = px.pie(genre_data, names="장르", values="기록", hole=.62)
                fig.update_layout(margin=dict(t=10,b=10,l=5,r=5), height=280,
                                  legend_title=None, paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.bar_chart(genre_data, x="장르", y="기록")
        else:
            st.info("기록이 쌓이면 장르 분포를 보여드릴게요.")

    st.markdown("### Quick actions")
    qa, qb = st.columns(2)
    with qa:
        if st.button("＋ 새 독서 기록 작성", type="primary", use_container_width=True):
            st.session_state.quick_add = True
    with qb:
        if st.button("📅 캘린더 열기", use_container_width=True):
            st.session_state["nav_override"] = "독서 캘린더"
            st.rerun()
    if st.session_state.pop("quick_add", False):
        st.markdown("#### 새 기록")
        with st.form("quick_add_form"):
            a,b = st.columns(2)
            with a:
                d = st.date_input("읽은 날짜", value=date.today())
                t = st.text_input("작품 제목")
                ep = st.text_input("읽은 회차", placeholder="예: 12화")
            with b:
                g = st.selectbox("장르", GENRES)
                r = st.slider("별점", 1, 5, 4)
                n = st.text_area("감상 및 연출 스터디 노트")
            if st.form_submit_button("기록 저장", type="primary"):
                if not t.strip():
                    st.warning("작품 제목을 입력해 주세요.")
                else:
                    add_review({
                        "read_date": str(d), "title": t.strip(), "episode": ep.strip(),
                        "genre": g, "rating": r, "notes": n.strip(),
                        "created_at": datetime.now().isoformat(timespec="seconds")
                    })
                    st.success("기록을 저장했어요.")
                    st.rerun()


# ---------------------------------------------------------
# Calendar
# ---------------------------------------------------------
elif page == "독서 캘린더":
    st.subheader("Reading Calendar")
    st.caption("날짜별로 읽은 작품과 회차를 확인하고 기록을 추가하세요.")
    default_month = date.today().replace(day=1)
    chosen = st.date_input("달력 기준 월 선택", value=default_month, key="calendar_month")
    year, month = chosen.year, chosen.month

    month_df = df[df["read_date"].str.startswith(f"{year}-{month:02d}")] if not df.empty else df
    weekdays = ["월","화","수","목","금","토","일"]
    cols = st.columns(7)
    for col, wd in zip(cols, weekdays):
        col.markdown(f"**{wd}**")
    for week in calendar.monthcalendar(year, month):
        cols = st.columns(7)
        for col, day in zip(cols, week):
            with col:
                if day == 0:
                    st.markdown('<div class="tf-day"><span class="tf-muted"> </span></div>', unsafe_allow_html=True)
                else:
                    ds = f"{year:04d}-{month:02d}-{day:02d}"
                    records = month_df[month_df["read_date"] == ds] if not month_df.empty else month_df
                    today_class = " today" if ds == str(date.today()) else ""
                    event_html = "".join(
                        f'<div class="tf-event">{str(row["title"])[:18]}'
                        f'{(" · " + str(row["episode"])) if row["episode"] else ""}</div>'
                        for _, row in records.head(3).iterrows()
                    )
                    more = f'<div class="tf-muted">+{len(records)-3}개 더</div>' if len(records) > 3 else ""
                    st.markdown(
                        f'<div class="tf-day{today_class}"><div class="tf-day-num">{day}</div>'
                        f'{event_html}{more}</div>', unsafe_allow_html=True
                    )
    st.markdown("### 이 달의 기록")
    if not month_df.empty:
        for _, row in month_df.iterrows():
            with st.expander(f'{row["read_date"]} · {row["title"]} · {"★" * int(row["rating"])}'):
                st.write(f'**회차:** {row["episode"] or "미입력"}　 **장르:** {row["genre"]}')
                st.write(row["notes"] or "감상평이 없습니다.")
    else:
        st.info("선택한 달에는 아직 기록이 없습니다.")

    st.divider()
    st.markdown("### ＋ 독서 기록 추가")
    with st.form("calendar_add_form"):
        a,b = st.columns(2)
        with a:
            read_date = st.date_input("읽은 날짜", value=date.today(), key="cal_add_date")
            title = st.text_input("작품 제목", key="cal_add_title")
            episode = st.text_input("읽은 회차", key="cal_add_episode")
        with b:
            genre = st.selectbox("장르", GENRES, key="cal_add_genre")
            rating = st.slider("별점", 1, 5, 4, key="cal_add_rating")
            notes = st.text_area("감상 / 연출 스터디 노트", key="cal_add_notes")
        if st.form_submit_button("기록 저장", type="primary"):
            if not title.strip():
                st.warning("작품 제목을 입력해 주세요.")
            else:
                add_review({
                    "read_date": str(read_date), "title": title.strip(), "episode": episode.strip(),
                    "genre": genre, "rating": rating, "notes": notes.strip(),
                    "created_at": datetime.now().isoformat(timespec="seconds")
                })
                st.success("기록을 저장했어요.")
                st.rerun()


# ---------------------------------------------------------
# Review management
# ---------------------------------------------------------
elif page == "감상평 관리":
    st.subheader("Review Library")
    st.caption("저장한 감상평을 검색하고 수정하거나 삭제할 수 있어.")
    if df.empty:
        st.info("저장된 기록이 없습니다. 캘린더에서 첫 기록을 추가해 보세요.")
    else:
        query = st.text_input("🔎 작품명 또는 감상평 검색", placeholder="검색어 입력")
        filtered = df.copy()
        if query.strip():
            mask = (
                filtered["title"].str.contains(query, case=False, na=False) |
                filtered["notes"].str.contains(query, case=False, na=False)
            )
            filtered = filtered[mask]
        st.caption(f"검색 결과 {len(filtered)}개")
        view = filtered[["id","read_date","title","episode","genre","rating"]].copy()
        view.columns = ["ID","날짜","작품","회차","장르","별점"]
        view["별점"] = view["별점"].map(lambda n: "★" * int(n))
        st.dataframe(view, use_container_width=True, hide_index=True)

        if not filtered.empty:
            labels = {
                f'{row["title"]} · {row["read_date"]} · ID {row["id"]}': int(row["id"])
                for _, row in filtered.iterrows()
            }
            selected_label = st.selectbox("관리할 기록 선택", list(labels.keys()))
            rid = labels[selected_label]
            row = df[df["id"] == rid].iloc[0]

            edit_tab, delete_tab = st.tabs(["기록 수정", "기록 삭제"])
            with edit_tab:
                with st.form("edit_form"):
                    a,b = st.columns(2)
                    with a:
                        ed_date = st.date_input("읽은 날짜", value=date.fromisoformat(row["read_date"]))
                        ed_title = st.text_input("작품 제목", value=row["title"])
                        ed_episode = st.text_input("회차", value=row["episode"] or "")
                    with b:
                        old_genre = row["genre"] if row["genre"] in GENRES else "기타"
                        ed_genre = st.selectbox("장르", GENRES, index=GENRES.index(old_genre))
                        ed_rating = st.slider("별점", 1, 5, int(row["rating"]))
                    ed_notes = st.text_area("감상 / 스터디 노트", value=row["notes"] or "", height=150)
                    if st.form_submit_button("수정 내용 저장", type="primary"):
                        if not ed_title.strip():
                            st.warning("작품 제목을 입력해 주세요.")
                        else:
                            update_review(rid, {
                                "read_date": str(ed_date), "title": ed_title.strip(),
                                "episode": ed_episode.strip(), "genre": ed_genre,
                                "rating": ed_rating, "notes": ed_notes.strip()
                            })
                            st.success("수정 내용을 저장했어요.")
                            st.rerun()
            with delete_tab:
                st.warning(f'**{row["title"]}** 기록을 삭제하면 복구할 수 없습니다.')
                confirm = st.checkbox("이 기록을 삭제하겠습니다.")
                if st.button("선택한 기록 영구 삭제", type="primary", disabled=not confirm):
                    delete_review(rid)
                    st.success("기록을 삭제했어요.")
                    st.rerun()


# ---------------------------------------------------------
# Taste quiz
# ---------------------------------------------------------
elif page == "취향 진단":
    st.subheader("Creative Taste Finder")
    st.caption("선호하는 연출과 이야기 분위기를 바탕으로 창작 방향을 탐색해 보세요.")
    q1 = st.radio("어떤 연출을 선호하나요?", [
        "웅장한 세계관과 역동적인 컷 구성",
        "인물의 감정선과 섬세한 심리 묘사",
        "빠른 전개와 재치 있는 컷 전환"
    ])
    q2 = st.radio("가장 끌리는 이야기 분위기는?", [
        "긴장감 넘치는 미스터리와 모험",
        "설렘과 관계 중심의 감성적인 이야기",
        "유쾌하고 편안한 일상과 코미디"
    ])
    if st.button("나의 취향 분석하기", type="primary"):
        if "웅장한" in q1:
            st.success("추천 연출: 와이드 샷, 깊이감 있는 배경, 역동적인 액션 동선")
            st.info("추천 장르: 판타지 · 액션 · 모험 · 아포칼립스")
        elif "감정선" in q1:
            st.success("추천 연출: 클로즈업, 여백, 시선 처리, 대사 리듬")
            st.info("추천 장르: 드라마 · 로맨스 · 성장 서사")
        else:
            st.success("추천 연출: 짧은 컷 호흡, 타이밍을 살린 리액션, 시각적 반복")
            st.info("추천 장르: 일상 · 개그 · 학원물")
        st.caption(f"분위기 취향: {q2}")


st.divider()
st.caption("TOONFORGE  /  READ DEEPLY. CREATE BOLDLY.")
