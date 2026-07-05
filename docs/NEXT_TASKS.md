# Next Tasks

褰撳墠鐗堟湰锛歮eizhaiseek v1.7.2

褰撳墠鍘熷垯锛氬厛鍥炲綊鐪熷疄閾捐矾锛屽啀鍋?UI 澧炲己銆備笉瑕佺敤鍓嶇鐘舵€佹浛浠ｅ悗绔换鍔°€佷細璇濄€佺粨鏋滃拰閿欒鎸佷箙鍖栥€?
## P0锛氬畧浣?`/agent` 鐪熷疄浠诲姟閾捐矾

### P0.1 鎻愪氦浠诲姟鍚庡乏渚ц亰澶╄褰曞繀椤绘柊澧炲苟鎸佷箙淇濆瓨

鐩爣锛?
- 鐢ㄦ埛鍦?`/agent` 鏅鸿兘浣撶晫闈㈡彁浜や换鍔″悗锛屽悗绔繀椤诲垱寤烘垨鏇存柊 Agent Conversation銆?- 宸︿晶鑱婂ぉ璁板綍蹇呴』鏂板鐪熷疄浼氳瘽銆?- 浼氳瘽銆佹秷鎭€乺un 蹇呴』鍐欏叆 APP SQLite銆?- localStorage 鍙兘淇濆瓨 active id锛屼笉鑳戒繚瀛樺畬鏁?messages 鍏呭綋浜嬪疄鏉ユ簮銆?
娑夊強鏂囦欢锛?
- `apps/web/src/app/agent/page.tsx`
- `apps/web/src/components/AgentWorkspace.tsx`
- `apps/web/src/hooks/useAgentConversations.ts`
- `apps/api/routers/agent_runs.py`
- `apps/api/routers/conversations.py`
- `apps/api/services/conversation_store.py`
- `apps/api/services/task_store.py`
- `apps/api/services/service_events.py`

楠屾敹鏍囧噯锛?
- `POST /api/agent-runs` 杩斿洖鐪熷疄 `run_id` 鍜?`conversation_id`銆?- `GET /api/conversations` 绔嬪嵆鑳界湅鍒版柊浼氳瘽銆?- SQLite `agent_conversations`銆乣agent_messages`銆乣agent_runs` 鍧囨湁瀵瑰簲璁板綍銆?- 鍒锋柊椤甸潰鍚庡乏渚ц褰曚粛瀛樺湪銆?- 鐢ㄦ埛 A 涓嶈兘鐪嬪埌鐢ㄦ埛 B 鐨勪細璇濄€?
### P0.2 鍒囨崲璺敱鍐嶅洖鏉ワ紝浠诲姟鍜岃亰澶╀笉鑳芥秷澶?
鐩爣锛?
- 浠?`/agent` 鍒囧埌 `/chat`銆佸悗鍙版垨鍏朵粬璺敱锛屽啀鍥?`/agent`锛岃兘鎭㈠ active conversation銆乵essages銆乴atest run銆乻tatus銆乺esult/error銆?- 鍒锋柊椤甸潰涔熻兘鎭㈠銆?- running run 鎭㈠鍚庣户缁?SSE锛孲SE 澶辫触鍐?polling銆?
娑夊強鏂囦欢锛?
- `apps/web/src/app/agent/page.tsx`
- `apps/web/src/components/AgentWorkspace.tsx`
- `apps/web/src/hooks/useAgentRunEvents.ts`
- `apps/web/src/hooks/useAgentRunPolling.ts`
- `apps/api/services/conversation_store.py`
- `apps/api/services/task_store.py`

楠屾敹鏍囧噯锛?
- 鎭㈠浼樺厛绾э細URL `conversation_id` -> localStorage active id -> 鍚庣鏈€杩戜細璇?-> 绌虹姸鎬併€?- running run 鎭㈠鍚庣户缁洿鏂扮姸鎬併€?- completed/failed/cancelled 涓嶉噸澶嶈疆璇€?- 浼氳瘽涓嶅瓨鍦ㄣ€佸凡褰掓。鎴栨棤鏉冮檺鏃朵笉鐧藉睆锛屾樉绀虹┖鐘舵€佸苟娓呯悊鏃犳晥 active id銆?- 蹇€熷垏鎹細璇濇椂鏈€缁堟樉绀烘渶鍚庝竴娆￠€夋嫨鐨勪細璇濄€?
### P0.3 鑴氭湰/瑙嗛鎷嗚В鏅鸿兘浣撴彁浜ゅ悗蹇呴』鐪熷疄鎵ц

鐩爣锛?
- `/agent` 椤甸潰鍙皟鐢ㄥ钩鍙板悗绔?`POST /api/agent-runs`銆?- 鍚庣鎸?`agent_type=video_script_breakdown` 杩涘叆 `video_script_workflow`銆?- 8001 鏈惎鍔ㄦ椂浠诲姟鐪熷疄 failed銆?- 8001 鍙揪鏃剁湡瀹?POST `/run`锛屼繚瀛?Debug Payload銆乺esult_json 鍜?artifacts銆?
娑夊強鏂囦欢锛?
- `apps/web/src/components/VideoScriptAgentPanel.tsx`
- `apps/api/routers/agent_runs.py`
- `apps/api/workflows/video_script_workflow.py`
- `apps/api/services/video_agent_payload_builder.py`
- `apps/api/services/local_agent_client.py`
- `apps/api/services/video_breakdown_result_normalizer.py`
- `apps/api/services/artifact_service.py`
- `apps/api/scripts/smoke_minimal.py`

楠屾敹鏍囧噯锛?
- Payload 鍖呭惈 `video_file`銆乣output_dir`銆乣mode`銆乣subtitle_region`銆乣ocr_workers`銆?- `standard` / `shot_text_excel` 鏈€缁堟槧灏勫埌鏈湴 Agent 鍙帴鍙楁ā寮忋€?- 8001 涓嶅彲杈炬椂 run.status 涓?`failed`锛岄敊璇俊鎭竻妤氥€?- 8001 鍙揪鏃?run 鐪熷疄 running/completed锛宺esult_json 鍜?artifacts 鎸佷箙鍖栥€?- Debug Payload request 鏄湡瀹炲彂缁?8001 鐨?`/run` payload銆?
### P0.4 浠诲姟鐘舵€併€佺粨鏋溿€侀敊璇繀椤诲洖鏄惧埌瀵瑰簲鑱婂ぉ璁板綍

鐩爣锛?
- `running/completed/failed/cancelled` 閫氳繃 `service_events` 鍚屾鍒板搴?conversation 鐨?assistant message銆?- completed 鏄剧ず summary銆乤rtifact銆乨ownload URL銆?- failed 鏄剧ず娓呮櫚閿欒銆?- retry 杩藉姞鏂?user/assistant messages 鍜屾柊 run id锛屼笉瑕嗙洊鏃?run銆?
娑夊強鏂囦欢锛?
- `apps/api/services/service_events.py`
- `apps/api/services/conversation_store.py`
- `apps/api/services/task_store.py`
- `apps/web/src/components/AgentWorkspace.tsx`
- `apps/web/src/components/AgentRunStatus.tsx`
- `apps/web/src/components/VideoBreakdownResultPanel.tsx`

楠屾敹鏍囧噯锛?
- running 鐘舵€佽兘鍦ㄨ亰澶╄褰曚腑鐪嬪埌浠诲姟杩涜涓€?- completed 鍚庡搴?assistant message 鏄剧ず缁撴灉鎽樿銆?- failed 鍚庡搴?assistant message 鏄剧ず閿欒鎽樿銆?- cancelled 鍚庢樉绀轰换鍔″凡鍙栨秷銆?- 澶氫細璇濄€佸 run 骞跺瓨鏃剁姸鎬佷笉涓茬嚎銆?
## P1锛氳摑鍥惧彂甯冮棴鐜洖褰?
### P1.1 瑙嗛鎷嗚В Blueprint 淇濇寔鐪熷疄鏍锋澘

鐩爣锛?
- `bp_video_script_breakdown` 淇濇寔 `published`銆?- 缁х画缁戝畾 `video_script_workflow`銆乣video_script_agent`銆乣video_breakdown`銆?- 钃濆浘娴嬭瘯浠嶅鐢ㄧ湡瀹?Agent Run銆?
娑夊強鏂囦欢锛?
- `apps/api/services/agent_blueprint_seed_service.py`
- `apps/api/services/agent_blueprint_service.py`
- `apps/api/services/agent_blueprint_release_gate.py`
- `apps/api/routers/agent_blueprints.py`
- `apps/web/src/components/AgentBlueprintPanel.tsx`

楠屾敹鏍囧噯锛?
- 钃濆浘瀛樺湪涓旂姸鎬佷负 `published`銆?- 8001 涓嶅彲杈炬椂钃濆浘娴嬭瘯鐪熷疄 failed锛宼est_run 璁板綍閿欒銆?- 8001 鍙揪鏃惰摑鍥炬祴璇曠敓鎴愮湡瀹?`agent_run_id` 鍜?artifacts銆?- release gate 涓嶅厑璁告棤楠岃瘉銆佹棤娴嬭瘯銆佹祴璇曞け璐ユ垨鐗堟湰涓嶅尮閰嶇殑鍙戝竷銆?
### P1.2 淇濇寔鏋勫缓銆佹祴璇曞拰 smoke 鍙繍琛?
鐩爣锛?
- 鍚庣 compileall銆乽nittest銆乸ytest 閫氳繃銆?- 鍓嶇 build 閫氳繃銆?- smoke 缂哄嚟鎹椂娓呮櫚澶辫触锛屽甫鍑嵁鏃堕€氳繃銆?
娑夊強鏂囦欢锛?
- `apps/api/tests/*`
- `apps/api/scripts/smoke_minimal.py`
- `apps/web/src/**/*`
- `docs/TESTING.md`

楠屾敹鏍囧噯锛?
- `python -m compileall apps/api` 閫氳繃銆?- `python -m unittest discover -s apps/api/tests` 閫氳繃銆?- `python -m pytest apps/api/tests` 閫氳繃銆?- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm.cmd run build` 閫氳繃銆?- `python apps/api/scripts/smoke_minimal.py` 甯︽湰鍦?admin 鍑嵁鏃堕€氳繃銆?
## P2锛氬伐绋嬫不鐞嗕笌鏂囨。

### P2.1 鏈窡韪枃浠朵笌杩愯鏁版嵁娌荤悊

鐩爣锛?
- 涓嶆彁浜?`.env`銆乺untime DB銆乬enerated secrets銆乴ogs銆乽ploads銆乵odels銆乶ode_modules銆乣.next`銆佽棰戣緭鍑恒€?- 鏍圭洰褰?`ARCHITECTURE_EVALUATION_REPORT.md` 鑻ュ彧鏄弬鑰冭祫鏂欙紝涓嶆彁浜ゃ€?- 鏃ュ織缁х画鍐欏叆 `apps/api/runtime/logs/`銆?
娑夊強鏂囦欢锛?
- `.gitignore`
- `start-dev.ps1`
- `apps/api/runtime/logs/`
- `ARCHITECTURE_EVALUATION_REPORT.md`

楠屾敹鏍囧噯锛?
- `git status --short` 涓嶅嚭鐜版晱鎰熸垨杩愯鏁版嵁銆?- 闇€瑕佹彁浜ゆ椂鍙?stage 鏈鐩稿叧鏂囦欢锛屼笉浣跨敤鏃犺剳 `git add .`銆?- 闈炵┖鏃ュ織濡傞渶娌荤悊锛屽厛褰掓。锛屼笉鐩存帴鍒犻櫎銆?
### P2.2 鏂囨。涓庣増鏈繚鎸佷竴鑷?
鐩爣锛?
- 褰撳墠鏂囨。淇濇寔 UTF-8 鍙銆?- 鏂囨。銆佸墠绔睍绀哄拰 runtime health 鍧囦负 `meizhaiseek v1.7.2`銆?- 鏂扮獥鍙ｅ彲浠ュ彧闈犱氦鎺ユ枃妗ｆ帴鎵嬨€?
娑夊強鏂囦欢锛?
- `AGENTS.md`
- `docs/CODEX_HANDOFF.md`
- `docs/NEXT_TASKS.md`
- `docs/CHANGELOG_CONTEXT.md`
- `docs/API.md`
- `docs/PRD.md`
- `docs/AGENT_BLUEPRINTS.md`
- `README.md`

楠屾敹鏍囧噯锛?
- `/api/admin/runtime/health` 杩斿洖 `version=v1.7.2`銆?- 鍓嶇鏄剧ず `meizhaiseek v1.7.2` 鍜?`meizhaiseek 2.0`銆?- 绂佺敤璇嶆壂鎻忔棤鍛戒腑銆?- 鏂囨。涓嶆妸 archive 閲岀殑鏃у唴瀹瑰綋褰撳墠浜嬪疄銆?
## 鍚庣画璺嚎

- v1.8锛氬弬鑰冮」鐩媶瑙ｄ笌钃濆浘鐢熸垚鍔╂墜銆?- v1.8.1锛氳摑鍥句汉宸ュ鏌ュ拰淇娴佺▼銆?- v1.9锛氬熀浜庤摑鍥惧疄鐜伴涓潪瑙嗛涓氬姟鏅鸿兘浣撱€?- v2.0锛氬鏅鸿兘浣撳伐浣滄祦缂栨帓銆?
## meizhaiseek v1.7.2

v1.7.2 focuses on architecture stabilization after the 2026-07-03 evaluation: Blueprint release E2E coverage, wider auth/conversation/task tests, Blueprint Store splitting, legacy JSON fallback retirement diagnostics, production Docker build/start, Agent Run SSE tests, async SQLite read wrappers, frontend API module compatibility split, methodology drag ordering, Registry/Blueprint reconciliation, and the Agent Run Event Hub. Existing Agent, Workflow, Connector, APP SQLite, RAG SQLite, Dataset, QA/RAG, Debug Payload, and video breakdown execution models are unchanged.
