# Codex Handoff

## 椤圭洰鍚嶇О涓庡綋鍓嶇増鏈?
- 椤圭洰锛歮eizhaiseek-platform
- 褰撳墠鐗堟湰锛歮eizhaiseek v1.7.2
- 鐗堟湰鍚嶇О锛氭櫤鑳戒綋钃濆浘鍙戝竷闂幆涓庡彲瑙嗗寲閰嶇疆澧炲己
- 浠撳簱锛歨ttps://github.com/zhuge1hao/seek-platform.git
- 鏈湴璺緞锛歚E:\USE\codexhome\agents-cowork\meizhaiseek-platform`
- 褰撳墠鍒嗘敮锛歚main`
- 鏈€杩戞彁浜わ細`89723b6 feat: complete blueprint release and visual editing flow`
- 宸叉帹閫侊細`origin/main`
- 褰撳墠鏈嶅姟锛歚start-dev.ps1` 宸插惎鍔紝API `http://127.0.0.1:8000`锛學eb `http://localhost:3000`
- 褰撳墠鏈窡韪枃浠讹細`ARCHITECTURE_EVALUATION_REPORT.md`锛屼笉瑕佽鎻愪氦銆?
## 褰撳墠椤圭洰鐩爣

meizhaiseek-platform 鏄潰鍚戠數鍟嗙粡钀ュ満鏅殑鏈湴杞婚噺 AI 宸ヤ綔鍙般€傚綋鍓嶉樁娈电洰鏍囨槸鍦ㄤ笉鐮村潖鏃㈡湁鐧诲綍閴存潈銆佹潈闄愩€丏ataset銆丆onnector銆丏ebug Payload銆丵A/RAG銆佸弻 SQLite 鍜岃棰戞媶瑙ｉ摼璺殑鍓嶆彁涓嬶紝鎶?Agent Blueprint 绋冲畾涓虹幇鏈?Agent Registry銆乄orkflow銆丆onnector 涔嬩笂鐨勭鐞嗘弿杩板眰銆?
Blueprint 鍙弿杩般€佹牎楠屻€佹祴璇曘€佸彂甯冨拰鍥炴粴鐜版湁鑳藉姏锛屼笉鎵ц浠绘剰 Python銆乻hell 鎴栧姩鎬佸伐浣滄祦銆傝棰戞媶瑙ｆ櫤鑳戒綋 `bp_video_script_breakdown` 鏄涓€浠芥寮?published 钃濆浘锛屼粛浣跨敤鐜版湁 `video_script_workflow`銆乣video_script_agent` Connector 鍜?`video_breakdown` renderer銆?
## 鎶€鏈爤涓庡惎鍔ㄦ柟寮?
- 鍓嶇锛歂ext.js 14 App Router銆丷eact 18銆乀ypeScript銆乀ailwind CSS銆丼WR銆乴ucide-react銆?- 鍚庣锛欶astAPI銆乁vicorn銆丳ydantic銆佹爣鍑嗗簱 sqlite3銆乺equests銆?- 瀛樺偍锛欰PP SQLite 涓?RAG SQLite 鍒嗙銆?- AI 瀵硅瘽锛欴eepSeek OpenAI-compatible Chat Completions锛屾湰鍦?BGE embedding銆?- 瑙嗛 Agent锛氬钩鍙板悗绔€氳繃 Connector 璋冪敤鏈湴 8001 `/health` 鍜?`/run`銆?
涓€閿惎鍔細

```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform
.\start-dev.ps1
```

鍗曠嫭鍚姩鍚庣锛?
```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform\apps\api
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

鍗曠嫭鍚姩鍓嶇锛?
```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform\apps\web
$env:NEXT_PUBLIC_API_BASE_URL='http://localhost:8000'
npm.cmd run dev -- -p 3000
```

甯歌楠岃瘉锛?
```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform
python -m compileall apps/api
python -m unittest discover -s apps/api/tests
python -m pytest apps/api/tests
cd apps\web
$env:NEXT_PUBLIC_API_BASE_URL='http://localhost:8000'
npm.cmd run build
```

Smoke锛?
```powershell
cd E:\USE\codexhome\agents-cowork\meizhaiseek-platform
$env:SMOKE_ADMIN_USERNAME='admin'
$env:SMOKE_ADMIN_PASSWORD='<local-password>'
python apps/api/scripts/smoke_minimal.py
```

## 鍏抽敭鐩綍缁撴瀯

```text
apps/web/src/app                 # 椤甸潰璺敱
apps/web/src/components          # Agent銆丆hat銆丏ataset銆丄dmin銆丅lueprint UI
apps/web/src/hooks               # SWR hooks銆丼SE/polling hooks
apps/web/src/lib                 # API client銆乹ueryKeys銆乤uth銆乤gent types
apps/api/routers                 # FastAPI routers
apps/api/services                # 瀛樺偍銆侀壌鏉冦€佷换鍔°€丆onnector銆丵A/RAG銆丅lueprint
apps/api/workflows               # Agent workflow锛屽惈 video_script_workflow
apps/api/tests                   # unittest/pytest 鍏煎娴嬭瘯
apps/api/scripts/smoke_minimal.py
apps/api/runtime                 # 鏈湴杩愯鏁版嵁锛屼笉鎻愪氦
apps/api/uploads                 # 涓婁紶鏂囦欢锛屼笉鎻愪氦
docs                             # 浜ゆ帴銆丄PI銆佹祴璇曘€佹灦鏋勪笂涓嬫枃
```

## 宸插畬鎴愮増鏈褰?
### v1.7.2锛氭櫤鑳戒綋钃濆浘鍙戝竷闂幆涓庡彲瑙嗗寲閰嶇疆澧炲己

- 鏂板 `agent_blueprint_test_runs` 鍜?`agent_blueprint_validation_results`锛屾瘡娆￠獙璇佸拰娴嬭瘯閮藉彲杩芥函銆?- 鏂板钃濆浘 diff銆乺elease gate銆乮nput preview銆乺esult preview 鏈嶅姟涓?API銆?- 鍙戝竷鎺ュ彛鍚庣閲嶆柊鎵ц鍙戝竷闂ㄧ锛涙棤褰撳墠鐗堟湰鏈夋晥楠岃瘉銆佹棤娴嬭瘯璁板綍銆佹祴璇曞け璐ャ€佺増鏈笉鍖归厤閮戒細闃绘鍙戝竷銆?- 鍙戝竷 warning 闇€瑕?`confirm_warnings=true`锛宱perator/viewer 涓嶈兘鍙戝竷銆?- 鍥炴粴鍓嶆牎楠岀洰鏍囧巻鍙?published 鐗堟湰锛岀敓鎴?diff 鎽樿骞跺啓 release/audit銆?- 钃濆浘绠＄悊椤靛鍔犵粨鏋勫寲缂栬緫鍣ㄣ€侀獙璇佸巻鍙层€佹祴璇曡繍琛屽巻鍙层€佺増鏈?diff銆佸彂甯冮棬绂佸拰棰勮锛涢珮绾?JSON 妯″紡淇濈暀銆?- `/api/agents` 鍜?`/agent` 杞婚噺灞曠ず published 钃濆浘鐗堟湰銆佹柟娉曡鎽樿銆佽緭鍑烘憳瑕佸拰鏈€杩戞祴璇曠姸鎬侊紝涓嶈繑鍥?Prompt 鎴栧畬鏁存墽琛岄厤缃€?- 鐗堟湰灞曠ず鏇存柊涓?`meizhaiseek v1.7.2`锛屾ā鍨嬪悕缁х画 `meizhaiseek 2.0`銆?- 宸查€氳繃 compileall銆乽nittest銆乸ytest銆亀eb build銆乻moke_minimal銆?
### v1.7锛氭櫤鑳戒綋钃濆浘涓庢柟娉曡閰嶇疆涓績

- 鏂板 Agent Blueprint SQLite 琛ㄣ€乻tore銆乻ervice銆乿alidator銆乮mport/export銆乻eed service銆?- 鏂板 `/api/agent-blueprints` CRUD銆乿ersions銆乿alidate銆乸ublish銆乺ollback銆乧lone銆乨isable/enable/deprecate銆乼est-cases銆乺eleases銆乪xport/import銆?- 鍚庡彴鏂板鈥滄櫤鑳戒綋钃濆浘鈥濈鐞嗛〉銆?- `/api/agents` 澧炲姞钃濆浘鍏宠仈瀛楁锛屾棤钃濆浘鏅鸿兘浣撴樉绀?`unmanaged`銆?- `POST /api/agent-runs` 浠呭湪鍏宠仈钃濆浘 disabled/deprecated 鏃舵嫆缁濇柊浠诲姟銆?- 瑙嗛鎷嗚В鏅鸿兘浣?seeded 涓?`bp_video_script_breakdown` published 钃濆浘銆?
### v1.6.5锛氭灦鏋勮瘎浼?P1-P3 浜岃疆浼樺寲

- 鎵╁ぇ SWR 璇诲彇灞傝鐩栥€?- 鏂板鏍稿績 unittest 鍜?GitHub Actions/Docker 鍩虹銆?- legacy JSON fallback 榛樿鍏抽棴锛宺untime health 鏄剧ず鐘舵€併€?- 鏂板 SQLite async wrapper 绗竴闃舵銆?- 鏂板 Agent Run SSE events锛屽墠绔け璐ュ洖閫€ polling銆?- 澧炲己 video-agent E2E smoke銆?- 淇瑙嗛缁撴灉 tab 闂睆鍜岄暱鏂囨湰鏌ョ湅銆?
### v1.6.4锛氳棰戞媶瑙ｆ櫤鑳戒綋鐪熷疄鎴愬姛閾捐矾楠屾敹涓庝骇鐗╅棴鐜?
- 榛樿 Connector 鎸囧悜鏈湴 8001銆?- 骞冲彴 payload 鏄犲皠涓烘湰鍦拌棰?Agent `/run` payload銆?- 鐪熷疄璋冪敤 8001锛屼笉浼€?completed銆?- 鏍囧噯鍖?result_json锛岃鍙?shot_report锛岀櫥璁?Excel/JSON/鍥剧墖/folder_manifest artifacts銆?- Debug Payload 淇濆瓨鐪熷疄 request/response/error銆?
## 褰撳墠姝ｅ湪澶勭悊鐨勯棶棰?
鏈疆鍙仛涓婁笅鏂囦氦鎺ュ寘钀界洏锛屼笉缁х画鍐欐柊鍔熻兘銆?
涓嬩竴绐楀彛鏈€浼樺厛浠诲姟浠嶆槸 `/agent` 鍥炲綊锛?
1. 鍦?`/agent` 鏅鸿兘浣撶晫闈㈡墽琛屼换鍔″悗锛屽乏渚ц亰澶╄褰曞繀椤绘柊澧炲苟鎸佷箙淇濆瓨銆?2. 鍒囨崲鍒板叾浠栬矾鐢卞啀鍥炴潵锛屼换鍔″拰鑱婂ぉ涓嶈兘娑堝け銆?3. 鑴氭湰/瑙嗛鎷嗚В鏅鸿兘浣撴彁浜ゅ悗蹇呴』鐪熷疄璋冪敤鍚庣鍜?local agent锛屼笉鍏佽鍙垱寤?UI 鐘舵€併€?4. 浠诲姟鐘舵€併€佺粨鏋溿€侀敊璇俊鎭繀椤诲洖鏄惧埌瀵瑰簲鑱婂ぉ璁板綍銆?
## 鏈€杩戜竴娆＄敤鎴锋槑纭姹?
鈥滆浣犱负褰撳墠椤圭洰鐢熸垚涓€涓柊绐楀彛鍙户缁帴鎵嬬殑涓婁笅鏂囦氦鎺ュ寘銆備笉瑕佺户缁啓鏂板姛鑳斤紝鍏堝彧鍋氭€荤粨鍜岃惤鐩樸€傗€?
## 宸茬粡鏀硅繃鐨勫叧閿枃浠?
v1.7.2 鍏抽敭浠ｇ爜锛?
- `apps/api/services/app_sqlite_migrations.py`
- `apps/api/services/app_sqlite.py`
- `apps/api/services/agent_blueprint_store.py`
- `apps/api/services/agent_blueprint_service.py`
- `apps/api/services/agent_blueprint_validator.py`
- `apps/api/services/agent_blueprint_diff_service.py`
- `apps/api/services/agent_blueprint_release_gate.py`
- `apps/api/services/agent_blueprint_preview_service.py`
- `apps/api/routers/agent_blueprints.py`
- `apps/api/routers/agents.py`
- `apps/api/routers/admin_runtime.py`
- `apps/api/scripts/smoke_minimal.py`
- `apps/web/src/components/AgentBlueprintPanel.tsx`
- `apps/web/src/components/AgentBlueprintEditor.tsx`
- `apps/web/src/components/AgentWorkspace.tsx`
- `apps/web/src/lib/api.ts`
- `apps/web/src/lib/queryKeys.ts`
- `apps/web/src/hooks/useAgentBlueprints.ts`
- `apps/web/src/lib/agents.ts`

v1.7.2 娴嬭瘯锛?
- `apps/api/tests/test_agent_blueprint_diff.py`
- `apps/api/tests/test_agent_blueprint_release_gate.py`
- `apps/api/tests/test_agent_blueprint_test_runs.py`
- `apps/api/tests/test_agent_blueprint_validation_history.py`
- `apps/api/tests/test_agent_blueprint_preview.py`
- `apps/api/tests/test_agent_blueprint_publish_flow.py`
- 鏃㈡湁钃濆浘/API/Agent Run 娴嬭瘯涔熷凡鏇存柊銆?
鏂囨。锛?
- `README.md`
- `AGENTS.md`
- `docs/CODEX_HANDOFF.md`
- `docs/NEXT_TASKS.md`
- `docs/CHANGELOG_CONTEXT.md`
- `docs/AGENT_BLUEPRINTS.md`
- `docs/API.md`
- `docs/PRD.md`
- `docs/TODO.md`
- `docs/TESTING.md`
- `docs/STORAGE_SQLITE.md`

## 鏁版嵁搴?API/鍓嶇鐘舵€?
鏁版嵁搴擄細

- APP SQLite 鏂板锛?  - `agent_blueprints`
  - `agent_blueprint_versions`
  - `agent_blueprint_test_cases`
  - `agent_blueprint_releases`
  - `agent_blueprint_test_runs`
  - `agent_blueprint_validation_results`
- `app_sqlite.health_check()` 绾冲叆钃濆浘琛ㄨ鏁般€?- RAG SQLite 浠嶅彧璐熻矗鐭ヨ瘑搴撴枃妗ｃ€乧hunks銆乪mbedding銆?
API锛?
- `/health` 杩斿洖 `{"status":"ok","service":"meizhaiseek-api"}`銆?- 鐧诲綍鍚?`/api/admin/runtime/health` 杩斿洖 `version=v1.7.2`銆?- `/api/agent-blueprints` 鏀寔 v1.7/v1.7.2 钃濆浘 API銆?- `/api/agents` 杩斿洖杞婚噺钃濆浘瀛楁锛屼笉娉勯湶瀹屾暣 Prompt銆乵ethodology 鎴?execution config銆?- `/api/agents/video-script/status` 鍦?8001 涓嶅彲杈炬椂杩斿洖 disconnected锛屼笉搴?500銆?- `/api/agent-runs/{run_id}/events` 缁х画鎻愪緵 SSE锛屽墠绔け璐ュ悗 polling fallback銆?
鍓嶇锛?
- 鐗堟湰灞曠ず锛歚meizhaiseek v1.7.2`銆?- 妯″瀷灞曠ず锛歚meizhaiseek 2.0`銆?- 宸︿晶涓诲鑸繚鐣欌€滅編瀹匓I鈥濃€滀竾鑳界編铏锯€濄€?- 鍚庡彴宸叉湁鈥滄櫤鑳戒綋钃濆浘鈥濋〉闈€?- `/agent` 宸插睍绀?published 钃濆浘杞婚噺鎽樿锛屼絾涓嶆敼鍙樼幇鏈変换鍔℃墽琛岄€昏緫銆?
## 宸茬煡 bug / 椋庨櫓

- `smoke_minimal.py` 缂?admin 鍑嵁浼氬け璐ワ紝杩欐槸淇濇姢鏈哄埗锛涗笉瑕佹敼鎴愰粯璁ら€氳繃銆?- 8001 鏈惎鍔ㄦ椂瑙嗛鎷嗚В浠诲姟搴旂湡瀹?failed锛涗笉瑕佷负浜?UI 濂界湅浼€犳垚鍔熴€?- 鏍圭洰褰?`ARCHITECTURE_EVALUATION_REPORT.md` 鏄湭璺熻釜鏂囦欢锛涢櫎闈炵敤鎴锋槑纭姹傦紝鍚﹀垯涓嶈鎻愪氦銆?- `start-dev.ps1` 浼氬啓 `apps/api/runtime/logs/api-dev.log` 鍜?`web-dev.log`锛宺untime/logs 涓嶆彁浜ゃ€?- 钃濆浘 UI 宸叉槸绱у噾鍙敤瀹炵幇锛屼笉鏄畬鏁磋〃鍗曟瀯寤哄櫒锛涘悗缁寮鸿鍏堝畧浣忓悗绔湡瀹炵姸鎬併€?
## 涓嶈兘鐮村潖鐨勫姛鑳?
- v1.2 鐧诲綍閴存潈銆佽鑹叉潈闄愩€佺敤鎴烽殧绂汇€?- v1.3 Connector銆丳ayload Preview銆丏ebug Replay銆?- v1.4 绠＄悊鍛樸€佸璁°€佹潈闄愩€丼afeDrawer銆?- v1.5 Dataset銆佸瓧娈垫槧灏勩€佹竻娲椼€佸鍑恒€佸畨鍏ㄤ笅杞姐€?- v1.5.2-v1.5.6 QA/RAG銆佺煡璇嗗簱銆佽瘖鏂€佹祦寮忛棶绛斻€?- v1.5.7 APP SQLite 杩佺Щ鍜?APP/RAG SQLite 鍒嗙銆?- v1.5.8 conversation 澧為噺 upsert銆丏ataset SQLite銆乻ervice_events銆?- v1.6+ 瑙嗛鎷嗚В鐪熷疄鎵ц銆乺esult normalizer銆乤rtifact銆丏ebug Payload銆?- v1.7+ Blueprint 鎻忚堪灞傘€佽棰戞媶瑙?published 钃濆浘銆佸彂甯?鍥炴粴/娴嬭瘯/瀵煎叆瀵煎嚭銆?- `/agent` 浼氳瘽鎸佷箙鍖栥€佽矾鐢辨仮澶嶃€佸彇娑堛€侀噸璇曘€佷笅杞姐€?- `/chat` 娴佸紡闂瓟銆?
## 涓嬩竴绐楀彛蹇呴』浼樺厛璇诲彇鐨勬枃浠?
1. `AGENTS.md`
2. `docs/CODEX_HANDOFF.md`
3. `docs/NEXT_TASKS.md`
4. `docs/CHANGELOG_CONTEXT.md`
5. `docs/API.md`
6. `docs/PRD.md`
7. `docs/STORAGE_SQLITE.md`
8. `docs/AGENT_BLUEPRINTS.md`
9. `docs/TESTING.md`
10. `apps/web/src/app/agent/page.tsx`
11. `apps/web/src/components/AgentWorkspace.tsx`
12. `apps/api/routers/agent_runs.py`
13. `apps/api/services/conversation_store.py`
14. `apps/api/services/task_store.py`
15. `apps/api/services/service_events.py`
16. `apps/api/workflows/video_script_workflow.py`

## 鏂扮獥鍙ｅ惎鍔ㄦ彁绀鸿瘝

璇风户缁帴鎵?`E:\USE\codexhome\agents-cowork\meizhaiseek-platform`銆傚綋鍓嶇増鏈槸 meizhaiseek v1.7.2锛孏itHub 浠撳簱鏄?`https://github.com/zhuge1hao/seek-platform.git`锛屾渶杩戞彁浜ゆ槸 `89723b6 feat: complete blueprint release and visual editing flow`銆傝鍏堝畬鏁磋鍙?`AGENTS.md`銆乣docs/CODEX_HANDOFF.md`銆乣docs/NEXT_TASKS.md`銆乣docs/CHANGELOG_CONTEXT.md`銆乣docs/API.md`銆乣docs/PRD.md`銆乣docs/STORAGE_SQLITE.md`銆乣docs/AGENT_BLUEPRINTS.md`銆乣docs/TESTING.md`锛屽啀璇诲彇鐩稿叧浠ｇ爜锛屼笉瑕佸彧渚濊禆鍘嗗彶瀵硅瘽鎴?Git 鐘舵€併€傚綋鍓嶆渶浼樺厛鍥炲綊 `/agent`锛氫换鍔℃彁浜ゅ悗宸︿晶鑱婂ぉ璁板綍蹇呴』鏂板骞舵寔涔呬繚瀛橈紱鍒囨崲璺敱鍐嶅洖鏉ヤ换鍔″拰鑱婂ぉ涓嶈兘娑堝け锛涜剼鏈?瑙嗛鎷嗚В鏅鸿兘浣撳繀椤荤湡瀹炶皟鐢ㄥ悗绔拰 local agent锛涗换鍔＄姸鎬併€佺粨鏋溿€侀敊璇繀椤诲洖鍐欏埌瀵瑰簲鑱婂ぉ璁板綍銆備笉瑕佺牬鍧?v1.2-v1.7.2 宸叉湁閴存潈銆丆onnector銆丏ebug銆佺鐞嗗憳銆丏ataset銆丵A/RAG銆丼QLite銆佽棰戞媶瑙ｃ€丼SE/polling 鍜?Blueprint 鑳藉姏銆?
## meizhaiseek v1.7.2

v1.7.2 focuses on architecture stabilization after the 2026-07-03 evaluation: Blueprint release E2E coverage, wider auth/conversation/task tests, Blueprint Store splitting, legacy JSON fallback retirement diagnostics, production Docker build/start, Agent Run SSE tests, async SQLite read wrappers, frontend API module compatibility split, methodology drag ordering, Registry/Blueprint reconciliation, and the Agent Run Event Hub. Existing Agent, Workflow, Connector, APP SQLite, RAG SQLite, Dataset, QA/RAG, Debug Payload, and video breakdown execution models are unchanged.
