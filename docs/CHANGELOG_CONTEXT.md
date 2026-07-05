# Changelog Context

## 褰撳墠鐘舵€?
- 褰撳墠鐗堟湰锛歮eizhaiseek v1.7.2
- 褰撳墠鍒嗘敮锛歚main`
- 鏈€杩戞彁浜わ細`89723b6 feat: complete blueprint release and visual editing flow`
- 宸叉帹閫侊細`origin/main`
- 鏈湴鏈嶅姟锛欰PI `http://127.0.0.1:8000`锛學eb `http://localhost:3000`
- 褰撳墠鏈窡韪枃浠讹細`ARCHITECTURE_EVALUATION_REPORT.md`锛屼笉瑕佽鎻愪氦銆?
## v1.7.2锛氭櫤鑳戒綋钃濆浘鍙戝竷闂幆涓庡彲瑙嗗寲閰嶇疆澧炲己

瀹屾垚鍐呭锛?
- 鏂板 `agent_blueprint_test_runs`锛屾瘡娆¤摑鍥炬祴璇曢兘鏈夌嫭绔嬪巻鍙茶褰曘€?- 鏂板 `agent_blueprint_validation_results`锛屾瘡娆¤摑鍥鹃獙璇侀兘鏈夊巻鍙茶褰曘€?- 鏂板钃濆浘鐗堟湰 diff 鏈嶅姟鍜?API锛屽拷鐣?JSON key 椤哄簭鍙樺寲锛屾敮鎸佹寜瀛楁/姝ラ/section 瀵规瘮銆?- 鏂板鍙戝竷璐ㄩ噺闂ㄧ锛屽彂甯冨墠妫€鏌ュ綋鍓嶇増鏈€侀獙璇佺粨鏋溿€佹祴璇曡褰曘€丆onnector銆乄orkflow銆丷enderer銆丳rompt 鍙橀噺鍜?schema銆?- 鍙戝竷 warning 闇€瑕?`confirm_warnings=true`锛沚locking error 鐩存帴闃绘鍙戝竷銆?- 钃濆浘娴嬭瘯杩愯缁х画澶嶇敤鐪熷疄 Agent Run锛屼笉浼€犻€氳繃銆?- 鍥炴粴鍓嶆牎楠屽巻鍙?published 鐗堟湰骞惰褰?diff 鎽樿銆?- 鏂板杈撳叆鍗忚棰勮鍜岀粨鏋滅粨鏋勯瑙堬紝鍙睍绀虹粨鏋勶紝涓嶆墽琛屼换鍔°€佷笉璇诲彇鏈湴鏂囦欢銆?- 鍚庡彴钃濆浘椤靛鍔犵粨鏋勫寲缂栬緫鍣ㄣ€侀獙璇佸巻鍙层€佹祴璇曡繍琛屽巻鍙层€乨iff銆乺elease gate銆乸review銆?- `/api/agents` 澧炲姞杞婚噺钃濆浘鎽樿瀛楁锛屼笉杩斿洖瀹屾暣 Prompt銆乵ethodology 鎴?execution config銆?- `/agent` 閽堝 published 钃濆浘鏄剧ず鐗堟湰銆佹柟娉曡鎽樿銆佽緭鍑烘憳瑕佸拰鏈€杩戞祴璇曠姸鎬併€?- runtime health 鍜屽墠绔睍绀哄崌绾т负 `meizhaiseek v1.7.2`锛屾ā鍨嬪悕缁х画 `meizhaiseek 2.0`銆?- 宸查€氳繃锛?  - `python -m compileall apps/api`
  - `python -m unittest discover -s apps/api/tests`
  - `python -m pytest apps/api/tests`
  - `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm.cmd run build`
  - `python apps/api/scripts/smoke_minimal.py`锛堝甫鏈湴 smoke admin 鍑嵁锛?
鍏抽敭鎻愪氦锛?
- `89723b6 feat: complete blueprint release and visual editing flow`

## v1.7锛氭櫤鑳戒綋钃濆浘涓庢柟娉曡閰嶇疆涓績

瀹屾垚鍐呭锛?
- 鏂板 `agent_blueprints`銆乣agent_blueprint_versions`銆乣agent_blueprint_test_cases`銆乣agent_blueprint_releases`銆?- 鏂板钃濆浘 store銆乻ervice銆乿alidator銆乮mport/export銆乻eed service銆?- 鏂板 `/api/agent-blueprints` CRUD銆乿ersions銆乿alidate銆乸ublish銆乺ollback銆乧lone銆乨isable/enable/deprecate銆乼est-cases銆乺eleases銆乪xport/import API銆?- `/api/agents` 杩斿洖钃濆浘鍏宠仈瀛楁锛屾棤钃濆浘鏅鸿兘浣撲繚鎸?`unmanaged`銆?- `POST /api/agent-runs` 浠呭湪鍏宠仈钃濆浘涓?disabled/deprecated 鏃舵嫆缁濇柊浠诲姟銆?- 瑙嗛鎷嗚В鏅鸿兘浣?seeded 涓虹涓€浠?published 钃濆浘锛岀户缁粦瀹?`video_script_workflow`銆乣video_script_agent` 鍜?`video_breakdown` renderer銆?- 鍚庡彴绠＄悊鏂板鈥滄櫤鑳戒綋钃濆浘鈥濆叆鍙ｏ紝鏀寔鍒楄〃銆佽鎯呫€丣SON 缂栬緫銆侀獙璇併€佹祴璇曘€佸彂甯冦€佸洖婊氥€佸鍒躲€佸鍏ュ鍑恒€?- 鏂板鑷姩鍖栨祴璇曡鐩?store銆乻ervice銆乿alidator銆乮mport/export銆丄PI 鏉冮檺銆?
鍏抽敭鎻愪氦锛?
- `bb01356 feat: add agent blueprint center`

## v1.6.5锛氭灦鏋勮瘎浼?P1-P3 浜岃疆浼樺寲銆佸洖褰掓祴璇曚笌鏈嶅姟鍚姩

瀹屾垚鍐呭锛?
- 鎵╁ぇ SWR 璇诲彇灞傝鐩栵紝鏂板澶氫釜璇诲彇鍨?hooks銆?- 鏂板鏍稿績 unittest锛岃鐩?auth銆乧onversation銆乼ask_store銆乤gent-runs API銆乿ideo normalizer銆?- `APP_LEGACY_JSON_FALLBACK=false` 榛樿鍏抽棴銆?- runtime health 澧炲姞 `legacy_json_fallback_enabled`銆?- 鏂板 Docker production compose銆?- 鏂板 SQLite async wrapper 绗竴闃舵銆?- 鏂板 Agent Run SSE events 鎺ュ彛锛屽墠绔け璐ュ洖閫€ polling銆?- 澧炲己 video-agent E2E smoke銆?- 淇瑙嗛缁撴灉 tab 闂睆銆?- 淇瑙嗛缁撴灉闀挎枃鏈埅鏂煡鐪嬩綋楠屻€?- 淇 active docs 鍜?README 涔辩爜銆?
鍏抽敭鎻愪氦锛?
- `5c0fc25 chore: address architecture P1-P3 follow-up items`
- `412b68e fix: reveal long video result text`
- `db35e66 fix: prevent video result tab flicker`
- `845b4bc fix: keep next dev assets stable during build`
- `dd1a9e9 fix: restore UI docs encoding`

## v1.6.4锛氳棰戞媶瑙ｆ櫤鑳戒綋鐪熷疄鎴愬姛閾捐矾楠屾敹涓庝骇鐗╅棴鐜?
瀹屾垚鍐呭锛?
- 榛樿 Connector 淇鍒版湰鍦?8001銆?- `GET /api/agents/video-script/status` 璇锋眰 `/health`锛岃繑鍥?connected/disconnected锛屼笉鍙揪涓?500銆?- 鏂板瑙嗛 Agent payload builder锛屾妸骞冲彴瀛楁鏄犲皠涓烘湰鍦?`/run` payload銆?- 鐪熷疄 POST `/run`锛屼笉浼€?completed銆?- 鏍囧噯鍖?result_json.summary锛屽吋瀹?raw shot count銆乷ptimized shots銆丒xcel columns/images銆丒xcel path銆乻hot report path銆?- 璇诲彇 shot_report JSON锛屾彁鍙?timeline 鍜?proof frames銆?- 鏀堕泦 Excel銆丣SON銆乀XT銆丮D銆丳NG銆丣PG銆乄EBP artifacts銆?- 鐢熸垚 folder_manifest锛宎rtifact metadata 鍐欏叆 APP SQLite銆?- 鍓嶇缁撴灉闈㈡澘灞曠ず completed summary銆乻teps銆乼abs銆佽緭鍑烘枃浠躲€?- Debug Payload 淇濆瓨鐪熷疄 request/response/error銆?- smoke 澧炲姞 `--video-agent-e2e` 鍜?`--require-video-agent`銆?
## v1.6.3锛氭灦鏋勮瘎浼?P1-P3 浼樺寲涓庡伐绋嬭鑼冭ˉ榻?
瀹屾垚鍐呭锛?
- 寮曞叆 SWR 鍩虹鏁版嵁灞傘€?- DeepSeek 闈炴祦寮忚皟鐢ㄥ鍔?`async_generate_answer` wrapper銆?- 鏂板 smoke 鑴氭湰鍜?docs銆?- 鏃ュ織鐩綍娌荤悊銆?- 鍘嗗彶 `.bak-v1.5.7` 鏂囨。褰掓。銆?- 鏂板瀹夊叏閰嶇疆鐢熸垚寮忓垵濮嬪寲銆?- 琛ュ厖 Docker Compose 鍜?GitHub Actions CI銆?
## v1.6.2锛欰I 鏅鸿兘浣撻〉闈㈠崱椤挎繁搴︿紭鍖?
瀹屾垚鍐呭锛?
- 鎷嗗垎 run summary/result銆?- 澶?result/debug payload 寤惰繜鍔犺浇銆?- 蹇€熷垏鎹?conversation 杩囨湡璇锋眰蹇界暐銆?- `/agent` 鍗曚竴 run polling 杈圭晫銆?
## v1.6.1锛欰I 鏅鸿兘浣撲細璇濆垏鎹㈢ǔ瀹氭€т慨澶?
瀹屾垚鍐呭锛?
- `/agent?conversation_id=` 鍒囨崲澧炲姞 AbortController銆?- URL 涓?activeConversationId 鍚屾淇銆?- 鍒囨崲璺敱鍜屽埛鏂版仮澶嶄細璇濄€?
## v1.6锛氳棰戞媶瑙ｆ櫤鑳戒綋鐢熶骇鍖?
瀹屾垚鍐呭锛?
- 鏂板瑙嗛鎷嗚В鏅鸿兘浣撲笓鐢ㄩ潰鏉裤€?- 鏂板 local agent status check銆?- 瑙嗛浠诲姟鏍囧噯 steps銆乺esult_json銆乤rtifact銆丏ebug Payload銆?- 8001 涓嶅彲杈炬椂浠诲姟鐪熷疄 failed銆?
## v1.5.8锛氬瓨鍌ㄦ€ц兘浼樺寲涓?Dataset SQLite 缁熶竴

瀹屾垚鍐呭锛?
- QA conversation 鍜?Agent conversation 鏀逛负澧為噺 upsert銆?- Dataset metadata 杩佸叆 APP SQLite銆?- 鏂板 `datasets`銆乣dataset_files`銆乣dataset_jobs`銆?- 鏂板 `service_events`锛岃В闄?task_store 涓?conversation_store 鐨勫惊鐜緷璧栥€?
## v1.5.7锛氭枃妗ｄ贡鐮佷慨澶嶄笌 SQLite 瀛樺偍搴曞骇杩佺Щ

瀹屾垚鍐呭锛?
- 鏂板 APP SQLite 鍒濆鍖栥€佽縼绉诲拰 health銆?- 鐢ㄦ埛銆佸璁°€丵A conversation銆丄gent conversation銆乤gent_runs銆丆onnector銆丏ebug Payload銆乫iles銆乤rtifacts metadata 杩佸叆 APP SQLite銆?- RAG SQLite 缁х画鍙繚瀛?knowledge documents/chunks/embedding銆?
## v1.5.2-v1.5.6锛欰I 瀵硅瘽銆佺煡璇嗗簱涓庢祦寮忛棶绛?
瀹屾垚鍐呭锛?
- AI 瀵硅瘽棣栧睆闂瓟銆?- 鐭ヨ瘑搴撴枃妗ｅ叆搴撲笌 RAG 绠＄悊涓績銆?- 浼氳瘽鏍忎氦浜掍紭鍖栥€?- 鏈湴妯″瀷鐘舵€佷笌 RAG 鍙敤鎬ц瘖鏂€?- `/chat` SSE 娴佸紡杈撳嚭涓庡洖绛斾綋楠屼紭鍖栥€?
## 涓嬩釜绐楀彛娉ㄦ剰

- 绗竴浼樺厛绾т粛鏄?`/agent` 鐪熷疄浠诲姟閾捐矾鍥炲綊锛屼笉瑕佽 UI 琛ㄨ薄楠楄繃鍘汇€?- 8001 涓嶅彲杈炬椂蹇呴』 failed锛?001 鍙揪鏃跺繀椤荤湡瀹?`/run`銆?- Blueprint 鏄弿杩板眰锛屼笉鏄姩鎬佹墽琛屽櫒銆?- smoke 缂?admin 鍑嵁鏃跺け璐ユ槸姝ｅ父淇濇姢锛屼笉瑕佹敼鎴愰粯璁ら€氳繃銆?- 鏈窡韪?`ARCHITECTURE_EVALUATION_REPORT.md` 涓嶈璇彁浜ゃ€?
## meizhaiseek v1.7.2

v1.7.2 focuses on architecture stabilization after the 2026-07-03 evaluation: Blueprint release E2E coverage, wider auth/conversation/task tests, Blueprint Store splitting, legacy JSON fallback retirement diagnostics, production Docker build/start, Agent Run SSE tests, async SQLite read wrappers, frontend API module compatibility split, methodology drag ordering, Registry/Blueprint reconciliation, and the Agent Run Event Hub. Existing Agent, Workflow, Connector, APP SQLite, RAG SQLite, Dataset, QA/RAG, Debug Payload, and video breakdown execution models are unchanged.
