# Codex Handoff

## 椤圭洰鍚嶇О涓庡綋鍓嶇増鏈?
- 椤圭洰锛歚meizhaiseek-platform`
- 褰撳墠鐗堟湰锛歚meizhaiseek v1.6.4`
- 鐗堟湰鍚嶇О锛氭灦鏋勮瘎浼?P1-P3 浼樺寲涓庡伐绋嬭鑼冭ˉ榻?- 椤圭洰璺緞锛歚E:\USE\codexhome\agents-cowork\meizhaiseek-platform`
- GitHub锛歚https://github.com/zhuge1hao/seek-platform.git`
- 褰撳墠鍒嗘敮锛歚main`
- 鏈€杩戞彁浜わ細鏈疆鎻愪氦 `chore: optimize architecture P1-P3 items`

## 褰撳墠椤圭洰鐩爣

meizhaiseek 鏄潰鍚戠數鍟嗙粡钀ュ叏閾捐矾鐨?AI 骞冲彴銆傚綋鍓嶇洰鏍囨槸鍦ㄤ笉鐮村潖宸叉湁閴存潈銆丷AG銆丏ataset銆丆onnector銆丏ebug Payload銆佸悗鍙扮鐞嗚兘鍔涚殑鍓嶆彁涓嬶紝缁х画绋冲畾 `/chat` 娴佸紡闂瓟銆乣/agent` 鏅鸿兘浣撲换鍔°€佽棰戞媶瑙ｆ櫤鑳戒綋銆丄PP SQLite 杩愯鏁版嵁瀛樺偍鍜?RAG SQLite 鐭ヨ瘑搴撹竟鐣屻€?
## 鎶€鏈爤涓庡惎鍔ㄦ柟寮?
- 鍓嶇锛歂ext.js 14 App Router銆丷eact 18銆乀ypeScript銆乀ailwind CSS銆乴ucide-react銆?- 鍚庣锛欶astAPI銆乁vicorn銆丳ydantic銆乺equests銆佹爣鍑嗗簱 `sqlite3`銆?- AI 闂瓟锛欴eepSeek OpenAI-compatible Chat Completions锛屾敮鎸侀潪娴佸紡鍜?SSE 娴佸紡銆?- Embedding锛氭湰鍦?`bge-small-zh`锛岄€氳繃 `sentence-transformers` 鎳掑姞杞姐€?- 涓诲瓨鍌細APP SQLite锛岃矾寰?`apps/api/runtime/app/meizhaiseek.sqlite3`銆?- RAG 瀛樺偍锛氱嫭绔?SQLite锛岃矾寰?`apps/api/runtime/rag/rag.sqlite3`銆?- 鏈湴瑙嗛 agent锛氶粯璁?`http://127.0.0.1:8001`锛屽钩鍙颁笉鑳戒吉閫犳垚鍔熴€?
鍚姩锛?
```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform
.\start-dev.ps1
```

鏍￠獙锛?
```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform
python -m compileall apps/api

cd apps\web
$env:NEXT_PUBLIC_API_BASE_URL='http://localhost:8000'
npm.cmd run build
```

## 鍏抽敭鐩綍缁撴瀯

```text
apps/api/
  main.py
  routers/
    agent_runs.py
    conversations.py
    qa_chat.py
    qa_knowledge.py
    admin_runtime.py
  services/
    app_sqlite.py
    app_sqlite_migrations.py
    json_to_sqlite_migrator.py
    task_store.py
    conversation_store.py
    qa_conversation_store.py
    dataset_store.py
    service_events.py
    video_agent_status_service.py
  workflows/
    video_script_workflow.py
  runtime/              # 鏈湴杩愯鏁版嵁锛屼笉鎻愪氦 Git
apps/web/src/
  app/
    agent/page.tsx
    chat/page.tsx
  components/
    VideoScriptAgentPanel.tsx
    VideoBreakdownResultPanel.tsx
    AgentRunStatus.tsx
    ConversationPanel.tsx
  hooks/
    useAgentRunPolling.ts
  lib/
    api.ts
    perf.ts
docs/
  API.md
  PRD.md
  TODO.md
  STORAGE_SQLITE.md
  CODEX_HANDOFF.md
  NEXT_TASKS.md
  CHANGELOG_CONTEXT.md
AGENTS.md
```

## 宸插畬鎴愮増鏈褰?
### v1.5.7锛氭枃妗ｄ贡鐮佷慨澶嶄笌 SQLite 瀛樺偍搴曞骇杩佺Щ

- 淇骞堕噸鍐?`docs/API.md`銆乣docs/PRD.md` 涓?UTF-8銆?- 鏂板 APP SQLite 鍒濆鍖栥€佽縼绉诲拰 health銆?- 鏂板 JSON 鍒?SQLite 骞傜瓑杩佺Щ銆?- users銆乤udit_logs銆丵A conversation銆丄gent conversation銆乤gent_runs銆乧onnectors銆乨ebug_payloads銆乫iles銆乤rtifacts 杩佸叆 APP SQLite銆?- RAG SQLite 淇濇寔鐙珛锛屽彧淇濆瓨 documents/chunks/embedding銆?
### v1.5.8锛氬瓨鍌ㄦ€ц兘浼樺寲涓?Dataset SQLite 缁熶竴

- QA conversation 甯歌鍐欏叆鏀逛负澧為噺 upsert/update/insert銆?- Agent conversation 甯歌鍐欏叆鏀逛负澧為噺 upsert/update/insert銆?- bulk replace 浠呬繚鐣欑粰 legacy migration銆?- Dataset metadata 浠?`datasets.json` 杩佸叆 APP SQLite銆?- 鏂板 `datasets`銆乣dataset_files`銆乣dataset_jobs`銆?- Dataset 鏂囦欢鏈綋浠嶅湪纾佺洏锛屼笉杩涘叆 SQLite銆?- 鏂板 `service_events`锛岃В闄?`task_store` 涓?`conversation_store` 鐨勫嚱鏁板唴寤惰繜 import銆?
### v1.6锛氳棰戞媶瑙ｆ櫤鑳戒綋鐢熶骇鍖?
- 鏂板 `GET /api/agents/video-script/status`銆?- 鍓嶇鏂板瑙嗛鎷嗚В杩炴帴鐘舵€併€佹彁浜ゅ墠棰勬銆侀珮绾у弬鏁板拰澶辫触鎻愮ず銆?- 瑙嗛鎷嗚В workflow 鏍囧噯鍖?steps銆?- 缁撴瀯鍖?result_json锛歴ummary銆乼imeline銆乻ubtitles銆乻elling_points銆乸roof_frames銆乹uality_warnings銆乫iles銆?- 杈撳嚭鏂囦欢鐧昏鍒?artifacts锛屾敮鎸佸畨鍏ㄤ笅杞姐€?- Debug Payload 淇濆瓨 request/response/error銆?- 8001 鏈惎鍔ㄦ椂浠诲姟鐪熷疄 failed锛屼笉浼€犳垚鍔熴€?
### v1.6.1锛欰I 鏅鸿兘浣撲細璇濆垏鎹㈠崱姝讳慨澶?
- `/agent?conversation_id=` 鍒囨崲澧炲姞 AbortController銆?- 杩囨湡璇锋眰閫氳繃 request sequence 蹇界暐銆?- 鐐瑰嚮褰撳墠浼氳瘽涓嶉噸澶嶈姹傘€?- URL 鍚屾浣跨敤 `window.history.replaceState`锛岄伩鍏?App Router 鍚岃矾鐢?query 閲嶈浇銆?- 杞娓呯悊琛ュ己銆?- 澶?JSON 鏂囨湰鎴柇锛岄伩鍏嶉粯璁ゆ拺鐖嗛〉闈€?
### v1.6.2锛欰I 鏅鸿兘浣撻〉闈㈠崱椤挎繁搴︿紭鍖?
- 鍚庣鏂板 `GET /api/agent-runs/{run_id}/summary`銆?- 鍚庣鏂板 `GET /api/agent-runs/{run_id}/result`銆?- conversation detail 榛樿杩斿洖杞婚噺鎽樿锛屽ぇ result/debug payload 涓嶉粯璁よ繑鍥炪€?- 鍓嶇鏂板 `markPerf` 寮€鍙戞€ц兘鎺㈤拡銆?- 鍓嶇鏂板 `useAgentRunPolling`锛岀粺涓€ active run 杞銆?- GenericAgentPanel銆乂ideoScriptAgentPanel銆丄gentRunStatus 涓嶅啀鍚勮嚜 setInterval銆?- VideoBreakdownResultPanel 鏀逛负 memo + tabs + 鈥滃姞杞芥洿澶氣€濄€?- Debug Payload 鍜屽畬鏁?result 鏀逛负鎸夐渶鍔犺浇銆?- 鏂囨。鏂板 `docs/AGENT_PERFORMANCE_NOTES.md`銆?
### v1.6.4锛氭灦鏋勮瘎浼?P1-P3 浼樺寲涓庡伐绋嬭鑼冭ˉ榻?
- 鍓嶇鏂板 SWR/query hooks 鍩虹灞傦紝浣庨闄╂帴鍏?`/agent`銆乣/chat` 浼氳瘽鍒楄〃鍜屽悗鍙?鐭ヨ瘑搴撹鍙栧満鏅€?- DeepSeek 闈炴祦寮忛棶绛旀柊澧?`async_generate_answer` / `async_ask`锛屼繚鐣欏悓姝ュ吋瀹逛笌绋冲畾 SSE銆?- 鏂板 `apps/api/scripts/smoke_minimal.py` 鍜?`docs/SMOKE_TESTS.md`銆?- 鏍圭洰褰曘€丄PI銆乄eb 鍘嗗彶鏃ュ織褰掓。鍒?`apps/api/runtime/logs/archive/`銆?- `docs/*.bak-v1.5.7` 绉诲埌 `docs/archive/legacy_bak_v1.5.7/`銆?- 鏂板 `security_config_service.py`锛屾敮鎸佺己澶?secret 鏃剁敓鎴?`generated_secrets.json`锛宺untime health 杈撳嚭瀹夊叏 warning銆?- 琛ラ綈 Docker Compose銆丏ockerfile 鍜?GitHub Actions CI銆?
## 褰撳墠姝ｅ湪澶勭悊鐨勯棶棰?
鏈疆鍙鐞嗏€滄柊绐楀彛浜ゆ帴鍖呪€濊惤鐩橈紝涓嶇户缁啓鏂板姛鑳姐€傚綋鍓嶇敤鎴烽噸鏂版寚瀹氱殑 P0 鏄洖褰?`/agent` 浠诲姟鍜岃亰澶╂寔涔呭寲閾捐矾锛?
1. 鍦?`/agent` 鏅鸿兘浣撶晫闈㈡墽琛屼换鍔″悗锛屽乏渚ц亰澶╄褰曞繀椤绘柊澧炲苟鎸佷箙淇濆瓨銆?2. 鍒囨崲鍒板叾浠栬矾鐢卞啀鍥炴潵锛屼换鍔?鑱婂ぉ涓嶈兘娑堝け銆?3. 鑴氭湰鎷嗚В鏅鸿兘浣撳繀椤诲湪鎻愪氦浠诲姟鍚庣湡瀹炴墽琛岋紝鑰屼笉鏄彧鍒涘缓 UI 鐘舵€併€?4. 浠诲姟鐘舵€併€佺粨鏋溿€侀敊璇俊鎭鑳藉洖鏄惧埌瀵瑰簲鑱婂ぉ璁板綍銆?
娉ㄦ剰锛歷1.6.2 宸插仛鎬ц兘浼樺寲锛屼絾涓嬩竴绐楀彛浠嶅簲鎸?P0 鍋氱湡瀹炲洖褰掞紝涓嶈鍙浉淇?UI銆?
## 鏈€杩戜竴娆＄敤鎴锋槑纭姹?
鐢ㄦ埛瑕佹眰鐢熸垚涓€涓柊绐楀彛鍙户缁帴鎵嬬殑涓婁笅鏂囦氦鎺ュ寘锛屽彧鍋氭€荤粨鍜岃惤鐩橈紝鏇存柊锛?
- `docs/CODEX_HANDOFF.md`
- `docs/NEXT_TASKS.md`
- `docs/CHANGELOG_CONTEXT.md`
- `AGENTS.md`

骞惰緭鍑烘枃浠舵憳瑕佸拰鍙鍒剁殑鏂扮獥鍙ｅ惎鍔ㄦ彁绀鸿瘝銆?
## 宸茬粡鏀硅繃鐨勫叧閿枃浠?
鍚庣锛?
- `apps/api/main.py`
- `apps/api/routers/admin_runtime.py`
- `apps/api/routers/agent_runs.py`
- `apps/api/routers/agents.py`
- `apps/api/routers/artifacts.py`
- `apps/api/routers/conversations.py`
- `apps/api/routers/datasets.py`
- `apps/api/routers/qa_chat.py`
- `apps/api/routers/qa_knowledge.py`
- `apps/api/services/app_sqlite.py`
- `apps/api/services/app_sqlite_migrations.py`
- `apps/api/services/json_to_sqlite_migrator.py`
- `apps/api/services/task_store.py`
- `apps/api/services/conversation_store.py`
- `apps/api/services/qa_conversation_store.py`
- `apps/api/services/dataset_store.py`
- `apps/api/services/service_events.py`
- `apps/api/services/video_agent_status_service.py`
- `apps/api/workflows/video_script_workflow.py`

鍓嶇锛?
- `apps/web/src/app/agent/page.tsx`
- `apps/web/src/app/chat/page.tsx`
- `apps/web/src/lib/api.ts`
- `apps/web/src/lib/perf.ts`
- `apps/web/src/hooks/useAgentRunPolling.ts`
- `apps/web/src/components/GenericAgentPanel.tsx`
- `apps/web/src/components/VideoScriptAgentPanel.tsx`
- `apps/web/src/components/AgentRunStatus.tsx`
- `apps/web/src/components/ConversationPanel.tsx`
- `apps/web/src/components/VideoBreakdownResultPanel.tsx`
- `apps/web/src/components/RuntimeHealthPanel.tsx`
- `apps/web/src/components/KnowledgeBasePanel.tsx`
- `apps/web/src/components/DatasetPanel.tsx`
- `apps/web/src/components/AdminConsolePanel.tsx`

鏂囨。/閰嶇疆锛?
- `.gitignore`
- `.env.example`
- `AGENTS.md`
- `docs/API.md`
- `docs/PRD.md`
- `docs/TODO.md`
- `docs/STORAGE_SQLITE.md`
- `docs/VIDEO_AGENT_SETUP.md`
- `docs/AGENT_PERFORMANCE_NOTES.md`
- `docs/CODEX_HANDOFF.md`
- `docs/NEXT_TASKS.md`
- `docs/CHANGELOG_CONTEXT.md`

## 鏁版嵁搴?API/鍓嶇鐘舵€?
- `/health` 淇濇寔 `{"status":"ok","service":"meizhaiseek-api"}`銆?- `/api/admin/runtime/health` 褰撳墠搴旇繑鍥?`version = v1.6.4`銆?- `/api/admin/storage/health` 杩斿洖 APP SQLite 琛ㄧ粺璁″拰 legacy JSON 鐘舵€併€?- `GET /api/agent-runs/{run_id}/summary` 鐢ㄤ簬杞婚噺杞銆?- `GET /api/agent-runs/{run_id}/result` 鐢ㄤ簬鎸夐渶璇诲彇瀹屾暣 result銆?- `GET /api/conversations/{conversation_id}` 淇濇寔 wire shape锛屼絾澶у瓧娈佃繑鍥?preview/summary銆?- `/chat` 娴佸紡闂瓟涓嶅簲琚悗缁敼鍔ㄥ奖鍝嶃€?- `/agent` 椤甸潰杞缁熶竴鍦?`useAgentRunPolling.ts`锛屽瓙缁勪欢涓嶅簲鍐嶅垱寤鸿嚜宸辩殑 interval銆?- Dataset metadata 涓诲瓨鍌ㄦ槸 APP SQLite锛涙枃浠舵湰浣撲粛鍦ㄧ鐩樸€?- Debug Payload 璇︽儏涓嶅湪浼氳瘽鍒囨崲鏃堕粯璁ゅ姞杞姐€?
## 宸茬煡 bug / 椋庨櫓

- 鐢ㄦ埛浠嶈姹備紭鍏堝洖褰?`/agent` 鎵ц浠诲姟鍚庡乏渚т細璇濇寔涔呭寲銆佽矾鐢辨仮澶嶅拰鐘舵€佸洖鍐欙紝璇存槑鐪熷疄浣跨敤涓繖鏉￠摼璺粛闇€閲嶇偣楠岃瘉銆?- 8001 local agent 鏄閮ㄦ湇鍔°€傛湭鍚姩鏃?failed 鏄纭涓猴紱涓嶈涓轰簡楠屾敹浼€犳垚 completed銆?- `NEXT_PUBLIC_API_BASE_URL` 鍦ㄥ墠绔?build 鏃跺浐鍖栵紝鏋勫缓鍓嶅繀椤昏涓?`http://localhost:8000`銆?- runtime銆丼QLite銆乽ploads銆乵odels銆乴ogs 閮借 `.gitignore` 鎺掗櫎锛孏itHub 涓嶅寘鍚湰鍦拌繍琛屾暟鎹€?- 鏂囨。澶囦唤鏂囦欢 `docs/API.md.bak-v1.5.7`銆乣docs/PRD.md.bak-v1.5.7` 鍙兘淇濈暀鍘嗗彶涔辩爜锛屼粎鐢ㄤ簬杩芥函銆?
## 涓嶈兘鐮村潖鐨勫姛鑳?
- v1.2 鐧诲綍閴存潈銆乣auth_version`銆佺敤鎴烽殧绂汇€乤dmin/operator/viewer 鏉冮檺銆?- v1.3 Connector銆丳ayload Preview銆丏ebug Payload銆丷eplay銆?- v1.4 绠＄悊鍛樿处鍙风鐞嗐€佸璁℃棩蹇椼€佹潈闄愩€丼afeDrawer/婊氬姩淇銆?- v1.5 Dataset銆佸瓧娈垫槧灏勩€佹竻娲椼€佸鍑恒€佸畨鍏ㄤ笅杞姐€?- v1.5.2 QA 棣栧睆闂瓟鍜?QA conversation銆?- v1.5.3 鐭ヨ瘑搴撲笂浼犮€佸垹闄ゃ€侀噸鏂扮储寮曘€丷AG sources銆?- v1.5.4 浜岀骇浼氳瘽鏍忔敹缂?灞曞紑銆佷細璇濆綊妗ｅ垹闄ゃ€?- v1.5.5 妯″瀷鐘舵€併€丒mbedding 娴嬭瘯銆丷AG 妫€绱㈡祴璇曘€佺煡璇嗗簱璇婃柇銆?- v1.5.6 QA 娴佸紡杈撳嚭銆佸仠姝㈢敓鎴愩€侀潪娴佸紡 fallback銆?- v1.5.7 APP SQLite 涓?RAG SQLite 鍒嗙銆?- v1.5.8 conversation 澧為噺 upsert銆丏ataset SQLite銆乻ervice_events銆?- v1.6 瑙嗛鎷嗚В杩炴帴棰勬銆佺湡瀹炴墽琛屻€佺粨鏋勫寲缁撴灉銆乤rtifact 涓嬭浇銆?- v1.6.2 `/agent` 杞婚噺 payload銆佸崟涓€杞銆佸欢杩熷姞杞藉拰鍒嗘娓叉煋銆?
## 涓嬩竴绐楀彛蹇呴』浼樺厛璇诲彇鐨勬枃浠?
1. `AGENTS.md`
2. `docs/CODEX_HANDOFF.md`
3. `docs/NEXT_TASKS.md`
4. `docs/CHANGELOG_CONTEXT.md`
5. `docs/API.md`
6. `docs/PRD.md`
7. `docs/STORAGE_SQLITE.md`
8. `docs/AGENT_PERFORMANCE_NOTES.md`
9. `apps/api/main.py`
10. `apps/api/routers/agent_runs.py`
11. `apps/api/routers/conversations.py`
12. `apps/api/services/task_store.py`
13. `apps/api/services/conversation_store.py`
14. `apps/api/services/service_events.py`
15. `apps/api/workflows/video_script_workflow.py`
16. `apps/web/src/app/agent/page.tsx`
17. `apps/web/src/lib/api.ts`
18. `apps/web/src/hooks/useAgentRunPolling.ts`
19. `apps/web/src/components/VideoScriptAgentPanel.tsx`
20. `apps/web/src/components/AgentRunStatus.tsx`

## 鏂扮獥鍙ｅ惎鍔ㄦ彁绀鸿瘝

```text
璇风户缁帴鎵?E:\USE\codexhome\agents-cowork\meizhaiseek-platform銆傚綋鍓嶇増鏈槸 meizhaiseek v1.6.4锛孏itHub 浠撳簱鏄?https://github.com/zhuge1hao/seek-platform.git锛屼絾璇峰厛璇诲彇纾佺洏浠ｇ爜鍜屾枃妗ｏ紝涓嶈鍙緷璧栧巻鍙插璇濇垨 Git 鐘舵€併€?
绗竴姝ュ畬鏁磋鍙?AGENTS.md銆乨ocs/CODEX_HANDOFF.md銆乨ocs/NEXT_TASKS.md銆乨ocs/CHANGELOG_CONTEXT.md銆乨ocs/API.md銆乨ocs/PRD.md銆乨ocs/STORAGE_SQLITE.md銆乨ocs/AGENT_PERFORMANCE_NOTES.md锛岀劧鍚庢寜 NEXT_TASKS 鐨?P0 鍋氭渶灏忓繀瑕佸鐞嗗拰楠岃瘉銆?
褰撳墠鏈€浼樺厛浠诲姟鏄洖褰?/agent锛?锛夊湪 /agent 鏅鸿兘浣撶晫闈㈡墽琛屼换鍔″悗锛屽乏渚ц亰澶╄褰曞繀椤绘柊澧炲苟鎸佷箙淇濆瓨锛?锛夊垏鎹㈠埌鍏朵粬璺敱鍐嶅洖鏉ワ紝浠诲姟/鑱婂ぉ涓嶈兘娑堝け锛?锛夎剼鏈媶瑙ｆ櫤鑳戒綋蹇呴』鍦ㄦ彁浜や换鍔″悗鐪熷疄鎵ц锛岃€屼笉鏄彧鍒涘缓 UI 鐘舵€侊紱4锛変换鍔＄姸鎬併€佺粨鏋溿€侀敊璇俊鎭鑳藉洖鏄惧埌瀵瑰簲鑱婂ぉ璁板綍銆?
濡傛灉瑙嗛鑴氭湰浠诲姟鎶?local agent 8001 鏃犳硶杩炴帴锛屼笉瑕佷吉閫犳垚鎴愬姛銆傚厛纭 3000/8000 鏄惁鍚姩锛屽啀纭鏄惁瀛樺湪鐪熷疄 local agent 鏈嶅姟骞跺惎鍔?POST http://localhost:8001/api/agent/run銆傝嫢娌℃湁鐪熷疄 local agent锛屽彧鑳芥姤鍛婂閮ㄦ湇鍔＄己澶憋紝骞冲彴鎸夎璁?failed銆?
涓嶈鐮村潖 v1.2 閴存潈闅旂銆乿1.3 Connector/Debug銆乿1.4 绠＄悊鍛?瀹¤/鏉冮檺/婊氬姩銆乿1.5 Dataset銆乿1.5.2-v1.5.6 QA/RAG/娴佸紡闂瓟銆乿1.5.7 APP SQLite 杩佺Щ銆乿1.5.8 澧為噺 upsert/Dataset SQLite/service_events銆乿1.6 瑙嗛鎷嗚В鐢熶骇鍖栥€乿1.6.2 /agent 鎬ц兘浼樺寲銆備慨鏀瑰悗杩愯 python -m compileall apps/api 鍜?apps/web 涓?NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm.cmd run build銆?```
