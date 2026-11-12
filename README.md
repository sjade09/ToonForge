# ToonForge — 웹툰 독서 관리 웹사이트

세련된 대시보드형 Streamlit 웹앱입니다.

## 포함 기능
- 대시보드: 전체 기록, 작품 수, 이번 달 기록, 평균 별점
- 월간 독서 캘린더: 날짜별 작품 및 회차 표시
- 감상평 관리: 검색, 수정, 삭제
- 취향 진단
- 로컬에서는 SQLite(`toonforge.db`)에 저장
- 공개 배포에서는 Supabase PostgreSQL을 연결해 영구 저장 가능
- `APP_PASSWORD`를 설정하면 공개 URL에서도 비밀번호로 접근 제한 가능

## 1) 내 컴퓨터에서 실행

Python 3.10 이상 권장.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속.

## 2) 공개 웹사이트 배포 (GitHub + Streamlit Community Cloud)

1. GitHub에서 새 저장소(repository)를 만듭니다.
2. `app.py`, `requirements.txt`, `supabase_schema.sql`을 저장소에 업로드합니다.
3. https://share.streamlit.io/ 에서 GitHub 계정으로 로그인합니다.
4. **Create app**을 누르고 저장소, 브랜치(`main`), 파일 경로(`app.py`)를 선택합니다.
5. Deploy를 누르면 공개 URL이 생성됩니다.

### 데이터 영구 저장을 위한 Supabase 설정 (권장)

Streamlit Cloud의 로컬 파일은 재배포/재시작 시 유지된다고 보장할 수 없습니다. 공개 배포에서는 Supabase를 연결하세요.

1. https://supabase.com/ 에서 프로젝트를 생성합니다.
2. Supabase의 **SQL Editor**에서 `supabase_schema.sql` 내용을 실행합니다.
3. Project Settings → API에서 Project URL과 `service_role` 키를 확인합니다.
4. Streamlit Cloud 앱의 **Settings → Secrets**에 아래 내용을 입력합니다.

```toml
SUPABASE_URL = "https://YOUR-PROJECT.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "YOUR_SERVICE_ROLE_KEY"
APP_PASSWORD = "여기에_충분히_긴_접속_비밀번호"
```

5. 저장 후 앱이 재시작되면 Supabase에 기록이 저장됩니다.

**보안 주의**
- `service_role` 키는 관리자 권한 키입니다. GitHub 코드, 화면, 사용자에게 절대 공개하지 말고 Streamlit Secrets에만 저장하세요.
- `APP_PASSWORD`는 공유 접속 비밀번호입니다. URL은 공개되더라도 비밀번호 없이는 앱 내용을 볼 수 있게 설정할 수 있습니다.
- 이 버전은 하나의 공유 비밀번호를 쓰는 소규모 개인/프로젝트용입니다. 사용자별 계정과 개인별 데이터 분리가 필요하면 Supabase Auth를 추가해야 합니다.
- 비밀번호를 설정하지 않으면 누구나 앱과 저장된 기록에 접근할 수 있습니다.
- Supabase 키를 설정하지 않으면 SQLite 로컬 모드로 동작합니다. 공개 배포에서 SQLite 파일을 영구 저장소로 간주하지 마세요.

## 파일 구성

```text
ToonForge/
├── app.py
├── requirements.txt
├── supabase_schema.sql
└── README.md
```
