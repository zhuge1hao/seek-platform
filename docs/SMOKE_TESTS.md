## v1.6.5 Smoke Updates

- smoke_minimal.py 继续默认不依赖 8001。
- --video-agent-e2e 支持 VIDEO_AGENT_BASE_URL、VIDEO_AGENT_TEST_VIDEO、VIDEO_AGENT_TEST_OUTPUT_DIR。
- --require-video-agent 会在 8001 不可达时返回失败。

# Smoke Tests

## 鍚姩鏈嶅姟

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform
.\start-dev.ps1
```

榛樿鍚庣涓?`http://127.0.0.1:8000`锛屽墠绔负 `http://localhost:3000`銆?
## 杩愯

```powershell
$env:API_BASE_URL='http://127.0.0.1:8000'
$env:SMOKE_ADMIN_USERNAME='admin'
$env:SMOKE_ADMIN_PASSWORD='<鏈湴绠＄悊鍛樺瘑鐮?'
python apps/api/scripts/smoke_minimal.py
```

鏈缃?`SMOKE_ADMIN_USERNAME` / `SMOKE_ADMIN_PASSWORD` 鏃讹紝鑴氭湰浼氳鍙?`.env` 涓殑 `MEIZHAISEEK_ADMIN_USERNAME` / `MEIZHAISEEK_ADMIN_INITIAL_PASSWORD`銆傝鍙栦笉鍒板瘑鐮佷細鐩存帴 FAIL锛屼笉浼氳鎶ラ€氳繃銆?
## 瑕嗙洊鑼冨洿

- `GET /health`
- 绠＄悊鍛樼櫥褰?- `GET /api/admin/runtime/health`
- `GET /api/conversations`
- `POST /api/agent-runs`
- `GET /api/agent-runs/{run_id}/summary`
- `GET /api/conversations/{conversation_id}`
- SQLite `agent_runs`銆乣agent_conversations`銆乣agent_messages` 钀借〃妫€鏌?- `GET /api/admin/storage/health`
- `GET /api/qa/model-status`

8001 鏈湴瑙嗛 Agent 鏈惎鍔ㄦ椂锛宻moke 浼氶獙璇佷换鍔＄湡瀹炶繘鍏?`failed`锛屼笉浼氫吉閫犳垚鎴愬姛銆?
## 甯歌澶辫触

- 鍚庣鏈惎鍔細纭 8000 绔彛鍜?`API_BASE_URL`銆?- 鐧诲綍澶辫触锛氱‘璁ゆ湰鍦?`.env` 鎴?smoke 鐜鍙橀噺涓殑绠＄悊鍛樿处鍙峰瘑鐮併€?- runtime version 涓嶅尮閰嶏細纭鍚庣宸查噸鍚苟鍔犺浇褰撳墠浠ｇ爜銆?- 8001 宸插惎鍔細smoke 涓嶈姹?failed锛屽彧妫€鏌ヤ换鍔℃湁鐪熷疄鍚庣鐘舵€併€?
## GitHub Actions

褰撳墠 smoke 闇€瑕佹湰鍦拌繍琛屼腑鐨?API 鏈嶅姟鍜岀鐞嗗憳璐﹀彿锛屼笉鍦?CI 寮哄埗鎵ц銆侰I 鍙墽琛?`compileall` 鍜屽墠绔?build锛岄伩鍏嶄緷璧?DeepSeek銆丅GE 妯″瀷鎴?8001 local agent銆?
