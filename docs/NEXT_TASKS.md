# Next Tasks

褰撳墠鐗堟湰锛歚meizhaiseek v1.6.4`

鏈枃浠跺彧鎻忚堪涓嬩竴绐楀彛浼樺厛绾с€備笉瑕佹妸鍓嶇 UI 鐘舵€佸綋浣滃悗绔垚鍔燂紱鎵€鏈?P0 閮藉繀椤昏惤鍒扮湡瀹?API銆丼QLite 鎸佷箙鍖栧拰浼氳瘽鍥炲啓銆?
## P0锛氬洖褰掑苟淇 `/agent` 浠诲姟鎵ц銆佷細璇濇寔涔呭寲鍜岀姸鎬佸洖鍐?
### P0.1 鎵ц浠诲姟鍚庡乏渚ц亰澶╄褰曞繀椤绘柊澧炲苟鎸佷箙淇濆瓨

鐩爣锛?
- 鐢ㄦ埛鍦?`/agent` 鏅鸿兘浣撶晫闈㈡彁浜や换鍔″悗锛屽悗绔繀椤诲垱寤烘垨鏇存柊 agent conversation銆?- 宸︿晶浼氳瘽鏍忓繀椤诲嚭鐜扮湡瀹炶褰曘€?- 浼氳瘽蹇呴』鍐欏叆 APP SQLite锛屼笉鍏佽鍙瓨鍦ㄥ墠绔?state 鎴?localStorage銆?- 鐢ㄦ埛闅旂蹇呴』鎸?`user_id` 鐢熸晥銆?
娑夊強鏂囦欢锛?
- `apps/api/routers/agent_runs.py`
- `apps/api/routers/conversations.py`
- `apps/api/services/task_store.py`
- `apps/api/services/conversation_store.py`
- `apps/api/services/service_events.py`
- `apps/web/src/app/agent/page.tsx`
- `apps/web/src/components/ConversationPanel.tsx`
- `apps/web/src/lib/api.ts`

楠屾敹鏍囧噯锛?
- `POST /api/agent-runs` 杩斿洖 `run_id` 鍜?`conversation_id`銆?- `GET /api/conversations` 鑳界湅鍒版柊浼氳瘽銆?- SQLite `agent_conversations` / `agent_messages` / `agent_runs` 鏈夊搴旇褰曘€?- 鍒锋柊椤甸潰鍚庤褰曚粛瀛樺湪銆?- 鐢ㄦ埛 A 涓嶈兘鐪嬪埌鐢ㄦ埛 B 鐨勪細璇濄€?
### P0.2 鍒囨崲璺敱鍐嶅洖鏉ヤ换鍔?鑱婂ぉ涓嶈兘娑堝け

鐩爣锛?
- 浠?`/agent` 鍒囧埌 `/chat`銆乣/board` 鎴栧叾浠栬矾鐢憋紝鍐嶅洖 `/agent`锛屾仮澶?active conversation銆乵essages銆乴atest run銆乻tatus銆乺esult preview銆?- 鍒锋柊椤甸潰涔熻兘鎭㈠銆?- localStorage 鍙繚瀛?active conversation id锛屼笉淇濆瓨瀹屾暣 messages銆?
娑夊強鏂囦欢锛?
- `apps/web/src/app/agent/page.tsx`
- `apps/web/src/hooks/useAgentRunPolling.ts`
- `apps/web/src/components/AgentRunStatus.tsx`
- `apps/web/src/components/GenericAgentPanel.tsx`
- `apps/web/src/components/VideoScriptAgentPanel.tsx`
- `apps/web/src/lib/api.ts`
- `apps/api/routers/conversations.py`

楠屾敹鏍囧噯锛?
- 鎭㈠浼樺厛绾э細URL `conversation_id` -> `localStorage.meizhaiseek_active_conversation_id` -> 绌虹姸鎬併€?- running run 鎭㈠鍚庣户缁疆璇€?- completed/failed/cancelled 涓嶅啀杞銆?- 涓嶅瓨鍦ㄦ垨宸插綊妗?conversation 涓嶇櫧灞忥紝鏄剧ず涓枃绌虹姸鎬佸苟娓呯悊鏃犳晥 active id銆?- 蹇€熷垏鎹細璇濇渶缁堟樉绀烘渶鍚庝竴娆＄偣鍑荤殑浼氳瘽銆?
### P0.3 鑴氭湰鎷嗚В鏅鸿兘浣撴彁浜ゅ悗蹇呴』鐪熷疄鎵ц鍚庣浠诲姟

鐩爣锛?
- 瑙嗛鑴氭湰鎷嗚В鎻愪氦鍚庡彧璋冪敤骞冲彴鍚庣 `POST /api/agent-runs`銆?- 鍚庣鏍规嵁 `agent_type=video_script_breakdown` 杩涘叆 `video_script_workflow`銆?- 8001 鏈惎鍔ㄦ椂浠诲姟鐪熷疄 failed锛屼笉浼€犳垚 completed銆?- 鐪熷疄 local agent 瀛樺湪鏃讹紝淇濆瓨 request/response Debug Payload 鍜?artifacts銆?
娑夊強鏂囦欢锛?
- `apps/web/src/components/VideoScriptAgentPanel.tsx`
- `apps/api/routers/agent_runs.py`
- `apps/api/services/orchestrator.py`
- `apps/api/workflows/video_script_workflow.py`
- `apps/api/services/local_agent_client.py`
- `apps/api/services/video_agent_status_service.py`
- `apps/api/services/debug_payload_service.py`
- `apps/api/services/artifact_service.py`

楠屾敹鏍囧噯锛?
- payload 淇濈暀 `agent_type=video_script_breakdown`銆乵ode銆亀orkflow_options銆乿ideo_path/video_url銆?- 榛樿 session id 缁х画娌跨敤 `019dd824-f4bb-7273-8ac3-6e19b195ff82`銆?- 8001 涓嶅彲杈炬椂 run.status 涓?`failed`锛岄敊璇唴瀹瑰寘鍚棤娉曡繛鎺ユ湰鍦拌棰?Agent銆?- failed run 鍐欏叆 APP SQLite銆?- 濡傛灉 8001 鍙揪锛宺un 鑳借繘鍏?running/completed锛宺esult_json 鍜?artifacts_json 鎸佷箙鍖栥€?
### P0.4 浠诲姟鐘舵€併€佺粨鏋溿€侀敊璇俊鎭洖鏄惧埌瀵瑰簲鑱婂ぉ璁板綍

鐩爣锛?
- `running/completed/failed/cancelled` 閫氳繃 `service_events` 鍚屾鍒板搴?conversation 鐨?assistant message銆?- completed 鏄剧ず summary銆乫iles銆乨ownload URL銆?- failed 鏄剧ず娓呮櫚涓枃閿欒銆?- retry 杩藉姞鏂?user/assistant messages 鍜屾柊 run ID锛屼笉瑕嗙洊鏃?run銆?
娑夊強鏂囦欢锛?
- `apps/api/services/task_store.py`
- `apps/api/services/conversation_store.py`
- `apps/api/services/service_events.py`
- `apps/api/routers/agent_runs.py`
- `apps/web/src/app/agent/page.tsx`
- `apps/web/src/components/AgentRunStatus.tsx`
- `apps/web/src/components/ConversationMessages.tsx`

楠屾敹鏍囧噯锛?
- running 鐘舵€佽兘鍦ㄨ亰澶╄褰曚腑鐪嬪埌浠诲姟杩涜涓€?- completed 鍚庡搴?assistant message 鏄剧ず缁撴灉鎽樿銆?- failed 鍚庡搴?assistant message 鏄剧ず閿欒鎽樿銆?- cancelled 鍚庢樉绀轰换鍔″凡鍙栨秷銆?- 澶氫細璇濄€佸 run 骞跺瓨鏃剁姸鎬佷笉涓茬嚎銆?
## P1锛歷1.6.2 鎬ц兘閾捐矾鍥炲綊

### P1.1 纭 `/agent` 浠嶅彧鏈夊崟涓€ run polling

鐩爣锛?
- 椤甸潰鍚屼竴鏃堕棿鍙湁 `useAgentRunPolling.ts` 璐熻矗 active run 杞銆?- 瀛愮粍浠朵笉鍐嶅垱寤?`setInterval`銆?
娑夊強鏂囦欢锛?
- `apps/web/src/hooks/useAgentRunPolling.ts`
- `apps/web/src/app/agent/page.tsx`
- `apps/web/src/components/GenericAgentPanel.tsx`
- `apps/web/src/components/VideoScriptAgentPanel.tsx`
- `apps/web/src/components/AgentRunStatus.tsx`

楠屾敹鏍囧噯锛?
- `rg "setInterval|polling|pollRun" apps/web/src` 娌℃湁閲嶅杞瀹炵幇銆?- running 杞璇锋眰璧?`/api/agent-runs/{run_id}/summary`銆?- terminal 鐘舵€佸仠姝㈣疆璇€?- 杩炵画澶辫触 3 娆″仠姝㈣疆璇㈠苟鏄剧ず閿欒銆?
### P1.2 纭澶?payload 寤惰繜鍔犺浇

鐩爣锛?
- conversation detail 涓嶉粯璁よ繑鍥炲畬鏁?result/debug payload銆?- VideoBreakdownResultPanel 榛樿鍙覆鏌撴瑙堝拰鎽樿銆?- 瀹屾暣 result 鍙湪鐢ㄦ埛灞曞紑鐩稿叧 tab 鏃舵寜闇€鍔犺浇銆?
娑夊強鏂囦欢锛?
- `apps/api/routers/conversations.py`
- `apps/api/routers/agent_runs.py`
- `apps/api/services/task_store.py`
- `apps/web/src/components/VideoBreakdownResultPanel.tsx`
- `apps/web/src/lib/api.ts`

楠屾敹鏍囧噯锛?
- `GET /api/conversations/{conversation_id}` 杩斿洖 run/message preview锛屼笉杩斿洖瀹屾暣 raw_response/debug payload銆?- `GET /api/agent-runs/{run_id}/summary` 杩斿洖杞婚噺鎽樿銆?- `GET /api/agent-runs/{run_id}/result` 杩斿洖瀹屾暣 result銆?- timeline 棣栧睆涓嶈秴杩?20 鏉★紝subtitles 涓嶈秴杩?30 鏉★紝proof_frames 涓嶈秴杩?20 鏉★紝files 涓嶈秴杩?30 鏉°€?
## P2锛氭枃妗ｃ€丟itHub 鍜屾渶灏?smoke

### P2.1 淇濇寔鏂囨。鍚屾

鐩爣锛?
- 鏂囨。鍜岀湡瀹炵増鏈?v1.6.4 淇濇寔涓€鑷淬€?- 涓嶅啀鍑虹幇涔辩爜浜ゆ帴鏂囨。銆?
娑夊強鏂囦欢锛?
- `AGENTS.md`
- `docs/CODEX_HANDOFF.md`
- `docs/NEXT_TASKS.md`
- `docs/CHANGELOG_CONTEXT.md`
- `docs/API.md`
- `docs/PRD.md`
- `docs/TODO.md`

楠屾敹鏍囧噯锛?
- `docs/CODEX_HANDOFF.md` 鑳借鏂扮獥鍙ｇ洿鎺ユ帴鎵嬨€?- `docs/NEXT_TASKS.md` P0/P1/P2 娓呮櫚銆?- `docs/CHANGELOG_CONTEXT.md` 璁板綍 v1.5.7 鍒?v1.6.4銆?- 绂佹璇嶆壂鎻忔棤鍛戒腑锛氭棫鍝佺墝璇嶃€佹棫涓汉绉板懠銆侀搴﹀睍绀烘枃妗堛€佽瘯鐢?婕旂ず绫绘枃妗堥兘涓嶈兘鍑虹幇銆?
### P2.2 鏈€灏忚嚜鍔ㄥ寲 smoke

鐩爣锛?
- 涓嶅紩鍏ュぇ娴嬭瘯妗嗘灦锛屼繚鐣欐渶灏忓彲閲嶅妫€鏌ャ€?
寤鸿瑕嗙洊锛?
- `/health`
- 鐧诲綍 admin
- `/api/admin/runtime/health`
- `/api/admin/storage/health`
- `/api/conversations`
- `/api/agent-runs/{run_id}/summary`
- `/api/qa/model-status`

楠屾敹鏍囧噯锛?
- `python -m compileall apps/api` 閫氳繃銆?- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm.cmd run build` 閫氳繃銆?- smoke 缁撴灉璁板綍鍒颁氦鎺ヨ鏄庢垨 TODO銆?
### P2.3 GitHub 鍚屾

鐩爣锛?
- 鏈湴鏀瑰姩瀹屾垚骞堕獙璇佸悗鍚屾鍒?GitHub銆?
娑夊強鏂囦欢锛?
- 鍏ㄩ」鐩?Git 鐘舵€併€?
楠屾敹鏍囧噯锛?
- `git status -sb` 娓呮銆?- 涓嶆彁浜?`.env`銆乺untime銆丼QLite銆乽ploads銆乵odels銆乴ogs銆乶ode_modules銆乣.next`銆?- 鎺ㄩ€佸埌 `https://github.com/zhuge1hao/seek-platform.git`銆?
