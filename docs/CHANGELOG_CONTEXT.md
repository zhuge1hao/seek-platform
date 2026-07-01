# Changelog Context

鏈枃浠惰褰曡法 Codex 绐楀彛鐨勫彉鏇翠笂涓嬫枃锛屼笉鏇夸唬姝ｅ紡 release notes銆傚綋鍓嶄粨搴撳凡鍒濆鍖?Git锛屽苟宸叉帹閫佸埌 `https://github.com/zhuge1hao/seek-platform.git`銆傜户缁帴鎵嬩粛搴斿厛璇荤鐩樻枃浠跺拰鏈枃浠讹紝涓嶈鍙緷璧栧巻鍙插璇濄€?
## 褰撳墠鐘舵€佹憳瑕?
- 褰撳墠鐗堟湰锛歚meizhaiseek v1.6.4`
- `/health`锛歚{"status":"ok","service":"meizhaiseek-api"}`
- `/api/admin/runtime/health`锛氬簲杩斿洖 `version = v1.6.4`
- APP SQLite锛歚apps/api/runtime/app/meizhaiseek.sqlite3`
- RAG SQLite锛歚apps/api/runtime/rag/rag.sqlite3`
- GitHub锛歚https://github.com/zhuge1hao/seek-platform.git`
- 鏈€杩戞彁浜わ細鏈疆鎻愪氦 `chore: optimize architecture P1-P3 items`
- 杩愯鏁版嵁銆佹ā鍨嬨€佷笂浼犳枃浠躲€佹棩蹇楀潎琚?`.gitignore` 鎺掗櫎锛屼笉鍦?GitHub銆?
## 鐗堟湰鑴夌粶

### v1.5.2锛欰I 瀵硅瘽棣栧睆闂瓟鍔熻兘

- 鏂板鐪熷疄 `/chat` 闂瓟閾捐矾銆?- 鍚庣浣跨敤 FastAPI QA API銆?- 鏈湴 `bge-small-zh` 璐熻矗涓枃鍚戦噺鍖栥€?- RAG SQLite 瀛樺偍 documents/chunks/embedding銆?- DeepSeek 闈炴祦寮忓洖绛斻€?- QA 浼氳瘽鎸夌敤鎴锋寔涔呭寲銆?
### v1.5.3锛欰I 瀵硅瘽鐭ヨ瘑搴撳叆搴撲笌 RAG 绠＄悊涓績

- 鏂板 txt/md/docx 鏂囨。涓婁紶銆?- 鏂囨湰瑙ｆ瀽銆佹竻娲椼€乧hunk 鍒囧垎銆?- 浣跨敤 bge-small-zh 鐢熸垚 embedding銆?- 鍐欏叆 RAG SQLite銆?- 鏂板鐭ヨ瘑搴撳垪琛ㄣ€佽鎯呫€佸垹闄ゃ€侀噸鏂扮储寮曘€乻tats銆?- `/chat` sources 鍙睍绀哄叆搴撴枃妗ｆ潵婧愩€?
### v1.5.4锛氫細璇濇爮浜や簰浼樺寲鐗?
- `/chat` 鍜?`/agent` 浜岀骇浼氳瘽鏍忔敮鎸佹敹缂?灞曞紑銆?- QA conversation 鏀寔 archive銆?- Agent conversation 澶嶇敤 archive銆?- 鍒犻櫎浜屾纭銆?- 鏀剁缉鐘舵€佸啓鍏?localStorage銆?
### v1.5.5锛氭湰鍦版ā鍨嬬姸鎬佷笌 RAG 鍙敤鎬ц瘖鏂?
- 鏂板 `/api/qa/model-status`銆?- 鏂板 `/api/qa/test-embedding`銆?- 鏂板 `/api/qa/test-retrieval`銆?- 鏂板 `/api/qa/diagnose`銆?- KnowledgeBasePanel 灞曠ず妯″瀷銆丷AG銆丏eepSeek 鐘舵€併€?- 鏂板 `docs/RAG_MODEL_SETUP.md`銆?
### v1.5.6锛欰I 瀵硅瘽娴佸紡杈撳嚭涓庡洖绛斾綋楠屼紭鍖?
- DeepSeek client 鏂板 streaming銆?- 鏂板 `qa_stream_service.py`銆?- 鏂板 `POST /api/qa/chat/stream`銆?- 鍓嶇鐢?`fetch + ReadableStream` 瑙ｆ瀽 SSE銆?- 鏀寔鍋滄鐢熸垚銆佸鍒跺洖绛斻€侀噸鏂扮敓鎴愩€?- 瀹屾垚/澶辫触/鍋滄閮芥寔涔呭寲 assistant message銆?- 闈炴祦寮?`/api/qa/chat` 淇濈暀 fallback銆?
### v1.5.7锛氭枃妗ｄ贡鐮佷慨澶嶄笌 SQLite 瀛樺偍搴曞骇杩佺Щ

- 淇 `docs/API.md`銆乣docs/PRD.md` 涔辩爜銆?- 鏂板 `docs/STORAGE_SQLITE.md`銆?- 鏂板 APP SQLite 鍒濆鍖栧拰 migrations銆?- 鏂板 JSON 鍒?SQLite 骞傜瓑杩佺Щ銆?- 鏂板 `GET /api/admin/storage/health`銆?- 鏂板 `POST /api/admin/storage/migrate-json`銆?- 涓诲啓鍏?store 鍒囨崲鍒?APP SQLite锛?  - users
  - audit_logs
  - qa_conversations / qa_messages
  - agent_conversations / agent_messages
  - agent_runs
  - local_agent_connectors
  - debug_payloads
  - files metadata
  - artifacts metadata
- RAG SQLite 淇濇寔鐙珛銆?
### v1.5.8锛氬瓨鍌ㄦ€ц兘浼樺寲涓?Dataset SQLite 缁熶竴

- `qa_conversation_store.py` 甯歌鍐欏叆鍙栨秷 DELETE + 鍏ㄩ噺 INSERT銆?- `conversation_store.py` 甯歌鍐欏叆鍙栨秷 DELETE + 鍏ㄩ噺 INSERT銆?- bulk replace 鍑芥暟鍙繚鐣欑粰 legacy migration銆?- Dataset metadata 杩佸叆 APP SQLite銆?- 鏂板 `datasets`銆乣dataset_files`銆乣dataset_jobs`銆?- `datasets.json` 鍙綔涓鸿縼绉绘簮鍜?fallback read銆?- Dataset 鏂囦欢鏈綋缁х画淇濆瓨鍦ㄧ鐩樸€?- 鏂板 `service_events.py`銆?- `task_store.py` 閫氳繃 run updated event 鍚屾 conversation锛屼笉鍐嶅嚱鏁板唴 import `conversation_store`銆?
### v1.6锛氳棰戞媶瑙ｆ櫤鑳戒綋鐢熶骇鍖?
- 瑙嗛鎷嗚В鎴愪负绗竴涓寮忎笟鍔℃櫤鑳戒綋鏍锋澘銆?- 鏂板 `GET /api/agents/video-script/status`銆?- 鍚庣妫€娴?`video_script_agent` local connector锛屽墠绔笉鐩磋繛 8001銆?- 鍓嶇鏂板杩炴帴鐘舵€佸崱鐗囥€佹祴璇曡繛鎺ャ€佹彁浜ゅ墠棰勬銆?- 鏀寔鎷嗚В妯″紡鍜岄珮绾у弬鏁板啓鍏?`workflow_options_json`銆?- `video_script_workflow` 鏍囧噯鍖?steps銆?- `result_json` 褰掍竴鍖栦负 summary銆乼imeline銆乻ubtitles銆乻elling_points銆乸roof_frames銆乹uality_warnings銆乫iles銆?- 杈撳嚭鏂囦欢鐧昏 artifacts銆?- Artifact 涓嬭浇鍋氱敤鎴锋墍鏈夋潈鍜屽畨鍏ㄨ矾寰勬牎楠屻€?- Debug Payload 淇濆瓨 request/response/error銆?- 8001 涓嶅彲杈炬椂 run 鐪熷疄 failed銆?
### v1.6.1锛欰I 鏅鸿兘浣撲細璇濆垏鎹㈢ǔ瀹氭€т慨澶?
- `/agent?conversation_id=` detail 璇锋眰鏀寔 AbortController銆?- requestSeq 蹇界暐杩囨湡鍝嶅簲銆?- 鐐瑰嚮褰撳墠浼氳瘽鐩存帴 return銆?- URL 鍚屾浣跨敤鍘熺敓 `window.history.replaceState`銆?- 鍒囨崲浼氳瘽鏃舵竻鐞嗘棫 polling銆?- 澶?JSON 鏂囨湰榛樿鎴柇銆?- 鍒犻櫎鎸夐挳闃绘浜嬩欢鍐掓场銆?- conversation 涓嶅瓨鍦ㄦ椂娓呯悊 URL 鍜?localStorage銆?
### v1.6.2锛欰I 鏅鸿兘浣撻〉闈㈠崱椤挎繁搴︿紭鍖?
- 鍚庣 payload 杞婚噺鍖栥€?- 鏂板 `GET /api/agent-runs/{run_id}/summary`銆?- 鏂板 `GET /api/agent-runs/{run_id}/result`銆?- `/api/conversations/{conversation_id}` 榛樿杩斿洖 conversation + message 鎽樿 + run summary銆?- 鏂板 `apps/web/src/lib/perf.ts`锛屽紑鍙戠幆澧冭€楁椂鎺㈤拡銆?- 鏂板 `apps/web/src/hooks/useAgentRunPolling.ts`锛岀粺涓€ `/agent` active run 杞銆?- 瀛愮粍浠剁Щ闄ら噸澶?setInterval銆?- `VideoBreakdownResultPanel` 鏀逛负 memo + tabs + load more銆?- Debug Payload 涓嶅湪浼氳瘽鍒囨崲鏃堕粯璁ゅ姞杞姐€?- Artifact 鍐呭涓嶅湪鍒囨崲浼氳瘽鏃舵壒閲忓姞杞姐€?- 鏂板 `docs/AGENT_PERFORMANCE_NOTES.md`銆?- 宸叉帹閫?GitHub 棣栦釜 commit锛歚dc88a86`銆?
### v1.6.4锛氭灦鏋勮瘎浼?P1-P3 浼樺寲涓庡伐绋嬭鑼冭ˉ榻?
- 寮曞叆 SWR 鍩虹鏁版嵁鑾峰彇灞傚拰璇诲彇鍨?hooks銆?- `/agent`銆乣/chat` 浼氳瘽鍒楄〃鍙婂悗鍙?鐭ヨ瘑搴撲綆椋庨櫓璇诲彇鍦烘櫙鎺ュ叆 SWR銆?- DeepSeek 闈炴祦寮忛棶绛旀柊澧?async wrapper锛屼繚鐣欏悓姝ュ拰 SSE 娴佸紡鍏煎銆?- 鏂板鏈€灏?smoke 鑴氭湰涓?`docs/SMOKE_TESTS.md`銆?- 鏍圭洰褰曞拰鍓嶇/API 鏁ｈ惤鏃ュ織褰掓。鍒?`apps/api/runtime/logs/archive/`銆?- `docs/*.bak-v1.5.7` 褰掓。鍒?`docs/archive/legacy_bak_v1.5.7/`銆?- 鏂板 runtime secret 鐢熸垚寮忓垵濮嬪寲鍜?runtime health 瀹夊叏 warning銆?- 琛ラ綈 Docker Compose銆丏ockerfile 鍜?GitHub Actions 鏈€灏?CI銆?
## 鏈€杩戦獙璇佽褰?
鏈€杩戜竴杞?v1.6.4 寮€鍙戝凡閫氳繃锛?
- `python -m compileall apps/api`
- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm.cmd run build`
- `/health` 杩斿洖 `meizhaiseek-api`
- `/api/admin/runtime/health` 杩斿洖 `v1.6.4`
- summary/result endpoints 鍩虹 smoke
- 绂佹璇嶆壂鎻忓湪 `apps docs` 鑼冨洿鏃犲懡涓?- 瀵艰埅浠嶆樉绀衡€滅編瀹匓I鈥濃€滀竾鑳界編铏锯€?
鏈疆浜ゆ帴鍖呭彧鏀规枃妗ｏ紝鏈噸璺戞瀯寤恒€?
## 褰撳墠椋庨櫓

- 鐢ㄦ埛鍐嶆鏄庣‘ P0 鏄?`/agent` 浠诲姟鎵ц鍚庣殑浼氳瘽鎸佷箙鍖栥€佽矾鐢辨仮澶嶃€佺湡瀹炴墽琛屽拰鐘舵€佸洖鍐欙紝闇€瑕佷笅涓€绐楀彛浼樺厛鐪熷疄楠岃瘉銆?- 8001 local agent 涓嶅睘浜庡钩鍙板唴缃湇鍔★紝鏈惎鍔ㄦ椂 failed 鏄纭涓恒€?- GitHub 涓嶅寘鍚?runtime 鏁版嵁锛涙柊鏈哄櫒鎷変粨搴撳悗闇€瑕佹寜 `.env.example` 鍜屾枃妗ｅ噯澶囪繍琛岀幆澧冦€?- `docs/API.md.bak-v1.5.7`銆乣docs/PRD.md.bak-v1.5.7` 鍙兘淇濈暀鍘嗗彶涔辩爜锛屾寮忛槄璇讳互褰撳墠 docs 涓哄噯銆?
## 鍚庣画鏈€閲嶈妫€鏌ョ偣

1. `/agent` 鏂颁换鍔℃槸鍚﹀啓鍏?`agent_conversations`銆乣agent_messages`銆乣agent_runs`銆?2. `/agent` 鍒囪矾鐢?鍒锋柊鍚庢槸鍚︽仮澶?conversation 鍜?latest run銆?3. 瑙嗛鑴氭湰浠诲姟鏄惁鐪熷疄杩涘叆鍚庣 orchestrator/workflow銆?4. local agent 8001 涓嶅彲杈炬椂鏄惁鐪熷疄 failed 骞跺洖鍐?assistant message銆?5. run updated event handler 鏄惁浠嶇敓鏁堛€?6. `/agent` 鏄惁浠嶅彧鏈夊崟涓€ summary polling銆?7. storage health 鏄惁鎸佺画杩斿洖 SQLite 琛ㄨ鏁般€?
