# meizhaiseek v1.6.5 Notes

- 前端数据层：读取型接口通过 SWR hooks 接入，HTTP 仍统一走 apps/web/src/lib/api.ts。
- 测试：python -m unittest discover -s apps/api/tests；smoke 使用 python apps/api/scripts/smoke_minimal.py。
- Docker 开发：docker compose up --build。
- Docker 生产模式：docker compose -f docker-compose.prod.yml up --build。
- 日志目录：apps/api/runtime/logs/。
- legacy JSON fallback 默认关闭：APP_LEGACY_JSON_FALLBACK=false。
- Docker 内访问本机视频 Agent 使用 http://host.docker.internal:8001。

# meizhaiseek-platform

meizhaiseek-platform 鏄竴涓潰鍚戠數鍟嗙粡钀ュ叏閾捐矾鐨勬湰鍦?AI 宸ヤ綔鍙般€傚綋鍓嶇増鏈负 meizhaiseek v1.6.4锛屽寘鍚?Next.js 鍓嶇銆丗astAPI 鍚庣銆丄PP SQLite銆丷AG SQLite銆丄I 瀵硅瘽銆佹櫤鑳戒綋浠诲姟銆丏ataset銆丆onnector 鍜屽悗鍙扮鐞嗚兘鍔涖€?
## 椤圭洰缁撴瀯

```text
meizhaiseek-platform/
鈹溾攢 apps/
鈹? 鈹溾攢 web/
鈹? 鈹斺攢 api/
鈹溾攢 docs/
鈹? 鈹溾攢 PRD.md
鈹? 鈹溾攢 API.md
鈹? 鈹斺攢 TODO.md
鈹溾攢 README.md
鈹溾攢 .env.example
鈹斺攢 docker-compose.yml
```

## 鍓嶇鍚姩

```bash
cd apps/web
npm install
npm run dev
```

榛樿璁块棶锛?
- 鐧诲綍椤碉細http://localhost:3000/login
- AI 鏅鸿兘浣撻〉锛歨ttp://localhost:3000/agent

## 鍚庣鍚姩

```bash
cd apps/api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

榛樿鎺ュ彛锛?
- 鍋ュ悍妫€鏌ワ細http://localhost:8000/health
- 鏅鸿兘浣撳垪琛細http://localhost:8000/api/agents
- 鎶€鑳藉垪琛細http://localhost:8000/api/skills

## 涓€閿惎鍔?
Windows 涓嬪彲浠ュ湪椤圭洰鏍圭洰褰曞弻鍑伙細

```text
start-dev.bat
```

涔熷彲浠ュ湪 PowerShell 涓繍琛岋細

```powershell
.\start-dev.ps1
```

鑴氭湰浼氬悓鏃跺惎鍔ㄥ墠绔拰鍚庣锛?
- 鍓嶇锛歨ttp://localhost:3000
- 鍚庣锛歨ttp://127.0.0.1:8000
- API 鏂囨。锛歨ttp://127.0.0.1:8000/docs
- 鏃ュ織鐩綍锛歚apps/api/runtime/logs/`

## 鐜鍙橀噺

澶嶅埗 `.env.example` 鍚庢寜鏈湴鐜璋冩暣銆?
```bash
cp .env.example .env
```

鍓嶇璇诲彇 `NEXT_PUBLIC_API_BASE_URL` 璋冪敤鍚庣銆傞粯璁ょ鐞嗗憳鐢辩幆澧冨彉閲忓垵濮嬪寲锛涚敓浜ф垨澶氫汉閮ㄧ讲鍓嶈璁剧疆 `AUTH_TOKEN_SECRET` 鍜?`MEIZHAISEEK_ADMIN_INITIAL_PASSWORD`銆傚鏋滄湭璁剧疆 `AUTH_TOKEN_SECRET`锛屽悗绔細鍦?`apps/api/runtime/app/generated_secrets.json` 鐢熸垚鏈湴 secret锛涜鏂囦欢涓嶅簲鎻愪氦銆?
## Smoke 娴嬭瘯

```powershell
$env:API_BASE_URL='http://127.0.0.1:8000'
$env:SMOKE_ADMIN_USERNAME='admin'
$env:SMOKE_ADMIN_PASSWORD='<鏈湴绠＄悊鍛樺瘑鐮?'
python apps/api/scripts/smoke_minimal.py
```

鏇村璇存槑瑙?`docs/SMOKE_TESTS.md`銆?
## Docker 鍙€夊惎鍔?
Docker 浠呬綔涓烘湰鍦板紑鍙戠殑鍙€夋柟寮忥紝涓嶅紩鍏?MySQL銆丳ostgreSQL銆丷edis銆丮ongoDB 鎴栧閮ㄦ暟鎹簱鏈嶅姟銆?
```bash
docker compose up --build
```

榛樿绔彛锛?
- Web: http://localhost:3000
- API: http://localhost:8000

杩愯鏁版嵁鎸傝浇鍦?`apps/api/runtime/` 鍜?`apps/api/uploads/`銆?

