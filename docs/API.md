## v1.6.5 Runtime And Agent Run Events

- GET /api/admin/runtime/health：version 返回 v1.6.5，新增 legacy_json_fallback_enabled，默认 false。
- GET /api/agent-runs/{run_id}/events：登录后订阅自己的 run 状态 SSE。
- SSE 格式：event: status/completed/failed/cancelled/heartbeat，data 为 run summary JSON。
- 前端优先使用 SSE；连接失败后回退 /api/agent-runs/{run_id}/summary polling。

# meizhaiseek API 鏂囨。

鏈枃妗ｄ负 UTF-8 缂栫爜锛岃褰?meizhaiseek v1.6.4 鐨勪富瑕佸悗绔帴鍙ｃ€傞櫎 `/health` 鍜岀櫥褰曟帴鍙ｅ锛屼笟鍔℃帴鍙ｉ粯璁ら渶瑕?`Authorization: Bearer <token>`銆?
## 鍩虹鍋ュ悍

- `GET /health`锛氬叕寮€鍋ュ悍妫€鏌ワ紝杩斿洖 `{"status":"ok","service":"meizhaiseek-api"}`銆?- `GET /api/admin/runtime/health`锛氱鐞嗗憳杩愯鏃跺仴搴锋鏌ワ紝杩斿洖鏈嶅姟鍚嶃€佺増鏈?`v1.6.4`銆侀厤缃姸鎬佸拰 warnings銆倂1.6.3 璧?warnings 浼氬寘鍚粯璁ゅ紑鍙?secret銆侀粯璁ゅ垵濮嬬鐞嗗憳瀵嗙爜銆乺untime 鐢熸垚 secret 绛夊畨鍏ㄩ厤缃彁绀恒€?
## 璁よ瘉涓庣敤鎴风鐞?
- `POST /api/auth/login`锛氱敤鎴峰悕瀵嗙爜鐧诲綍锛岃繑鍥?token銆佽繃鏈熸椂闂村拰褰撳墠鐢ㄦ埛淇℃伅銆?- `POST /api/auth/logout`锛氳褰曢€€鍑哄璁℃棩蹇椼€?- `GET /api/auth/me`锛氭牎楠?token銆佺敤鎴峰惎鐢ㄧ姸鎬佸拰 `auth_version`銆?- `POST /api/auth/change-password`锛氬綋鍓嶇敤鎴蜂慨鏀瑰瘑鐮侊紝鎴愬姛鍚庨€掑 `auth_version`銆?- `GET /api/admin/users`锛氱鐞嗗憳鏌ヨ鐢ㄦ埛銆?- `POST /api/admin/users`锛氱鐞嗗憳鍒涘缓 admin/operator/viewer 鐢ㄦ埛銆?- `GET /api/admin/users/{user_id}`锛氱鐞嗗憳璇诲彇鍗曚釜鐢ㄦ埛銆?- `POST /api/admin/users/{user_id}`锛氱鐞嗗憳鏇存柊瑙掕壊銆佸惎鐢ㄧ姸鎬佸拰澶囨敞銆?- `POST /api/admin/users/{user_id}/enable`锛氬惎鐢ㄧ敤鎴枫€?- `POST /api/admin/users/{user_id}/disable`锛氱鐢ㄧ敤鎴凤紱绂佹绂佺敤褰撳墠绠＄悊鍛樻垨鏈€鍚庝竴涓惎鐢?admin銆?- `POST /api/admin/users/{user_id}/reset-password`锛氶噸缃瘑鐮佸苟閫掑 `auth_version`銆?- `GET /api/admin/users/{user_id}/agent-runs`锛氭煡鐪嬫寚瀹氱敤鎴蜂换鍔°€?- `GET /api/admin/agent-runs`锛氱鐞嗗憳璺ㄧ敤鎴锋煡璇换鍔°€?
## 鏅鸿兘浣撻厤缃笌鎶€鑳芥ā鏉?
- `GET /api/agents`锛氳繑鍥炲墠绔?22 涓櫤鑳戒綋娉ㄥ唽淇℃伅銆?- `GET /api/agent-configs`锛氳繑鍥炲墠绔櫤鑳戒綋閰嶇疆銆?- `GET /api/agent-configs/{agent_type}`锛氳繑鍥炲崟涓櫤鑳戒綋閰嶇疆銆?- `POST /api/agent-configs/{agent_type}`锛氶儴鍒嗘洿鏂版櫤鑳戒綋閰嶇疆銆?- `GET /api/skills`锛氳繑鍥炴妧鑳藉垪琛ㄣ€?- `GET /api/skills/templates`锛氭寜鍙€?`agent_type` 杩斿洖鎶€鑳芥ā鏉裤€?- `GET /api/skills/templates/{skill_id}`锛氳繑鍥炲崟涓妧鑳芥ā鏉裤€?- `POST /api/skills/templates`锛氭柊澧炴垨鏇存柊鎶€鑳芥ā鏉裤€?- `DELETE /api/skills/templates/{skill_id}`锛氳蒋鍒犻櫎鎶€鑳芥ā鏉裤€?
## 鏂囦欢涓?Artifact

- `POST /api/files/video/upload`锛氳棰戣剼鏈媶瑙ｅ揩鎹蜂笂浼狅紝鏀寔 `.mp4`銆乣.mov`銆乣.webm`銆乣.mkv`銆?- `POST /api/files/upload`锛氶€氱敤鏂囦欢涓婁紶锛屾敮鎸佽〃鏍笺€佹枃鏈€佸浘鐗囧拰甯歌瑙嗛鏍煎紡銆?- `GET /api/files?extensions=xlsx,xls,csv&limit=50`锛氬垪鍑哄綋鍓嶇敤鎴蜂笂浼犳枃浠躲€?- `GET /api/files/{file_id}/preview`锛氳鍙栨枃浠堕瑙堛€?- `GET /api/artifacts/download?path=...`锛氫笅杞藉畨鍏ㄧ洰褰曞唴缁撴灉鏂囦欢锛屾寜鐢ㄦ埛褰掑睘鏍￠獙銆?
## AI 瀵硅瘽

- `GET /api/qa/health`锛氳繑鍥?QA 鑳藉姏杞婚噺鍋ュ悍鐘舵€侊紝涓嶈繑鍥?DeepSeek API Key銆?- `GET /api/qa/conversations`锛氳繑鍥炲綋鍓嶇敤鎴?AI 瀵硅瘽浜岀骇鏍忚褰曘€?- `GET /api/qa/conversations/{conversation_id}`锛氳繑鍥炲綋鍓嶇敤鎴峰崟鏉?AI 瀵硅瘽鍜?messages銆?- `POST /api/qa/conversations`锛氬垱寤虹┖ QA 瀵硅瘽銆?- `POST /api/qa/conversations/{conversation_id}/archive`锛氳蒋褰掓。褰撳墠鐢ㄦ埛 QA 瀵硅瘽銆?- `POST /api/qa/chat`锛氶潪娴佸紡闂瓟銆傝姹傚寘鍚?`conversation_id`銆乣question`銆乣use_rag`銆乣top_k`锛岃繑鍥?`answer`銆乣sources`銆乣warnings`銆乣conversation_id`銆乣message_id`銆乣model`銆?- `POST /api/qa/chat/stream`锛歋SE 娴佸紡闂瓟銆備簨浠跺寘鎷?`start`銆乣retrieval_start`銆乣sources`銆乣delta`銆乣done`銆乣error`銆傞潪娴佸紡 `/api/qa/chat` 淇濈暀涓?fallback銆?
`POST /api/qa/chat` 璇锋眰绀轰緥锛?
```json
{
  "conversation_id": null,
  "question": "鎬庝箞鎵撶垎娆撅紵",
  "use_rag": true,
  "top_k": 5
}
```

鎴愬姛杩斿洖绀轰緥锛?
```json
{
  "conversation_id": "qa_conv_xxx",
  "message_id": "msg_xxx",
  "answer": "鍥炵瓟鍐呭",
  "sources": [],
  "warnings": [],
  "model": "deepseek-v4-flash"
}
```

## AI 瀵硅瘽鐭ヨ瘑搴?
- `POST /api/qa/knowledge/upload`锛歛dmin/operator 涓婁紶 txt銆乵d銆乨ocx 骞跺叆搴撱€?- `GET /api/qa/knowledge/documents`锛氬綋鍓嶇敤鎴风煡璇嗗簱鏂囨。鍒楄〃銆?- `GET /api/qa/knowledge/documents/{doc_id}`锛氭枃妗ｈ鎯呭拰鏈€澶?10 鏉?chunk preview銆?- `DELETE /api/qa/knowledge/documents/{doc_id}`锛歛dmin/operator 鍒犻櫎鑷繁鐨勬枃妗ｅ強 chunks銆?- `POST /api/qa/knowledge/documents/{doc_id}/reindex`锛歛dmin/operator 閲嶆柊绱㈠紩鏂囨。銆?- `GET /api/qa/knowledge/stats`锛氬綋鍓嶇敤鎴风煡璇嗗簱缁熻銆?
涓婁紶鎴愬姛杩斿洖绀轰緥锛?
```json
{
  "doc_id": "doc_xxx",
  "title": "鏂囨。鏍囬",
  "status": "ready",
  "chunk_count": 12,
  "message": "鏂囨。鍏ュ簱瀹屾垚"
}
```

## RAG 涓庢ā鍨嬭瘖鏂?
- `GET /api/qa/model-status?include_load_check=false`锛氭煡鐪?bge-small-zh 璺緞銆丼QLite RAG銆丏eepSeek 閰嶇疆鐘舵€侊紱admin/operator/viewer 鍙敤锛屼笉杩斿洖 API Key銆?- `POST /api/qa/test-embedding`锛歛dmin/operator 娴嬭瘯 embedding锛岃繑鍥炵淮搴﹀拰 preview銆?- `POST /api/qa/test-retrieval`锛歛dmin/operator 娴嬭瘯褰撳墠鐢ㄦ埛 RAG 妫€绱紝涓嶈皟鐢?DeepSeek銆?- `POST /api/qa/diagnose`锛歛dmin/operator 杩斿洖缁煎悎璇婃柇 summary 鍜?checks銆?
## AI 鏅鸿兘浣撲細璇濅笌浠诲姟

- `GET /api/conversations`锛氬綋鍓嶇敤鎴?AI 鏅鸿兘浣撲細璇濆垪琛ㄣ€?- `GET /api/conversations/{conversation_id}`锛氫細璇濊鎯呫€乴atest run 鍜?runs銆?- `POST /api/conversations`锛氬垱寤烘櫤鑳戒綋浼氳瘽銆?- `POST /api/conversations/{conversation_id}/rename`锛氶噸鍛藉悕浼氳瘽銆?- `POST /api/conversations/{conversation_id}/archive`锛氳蒋褰掓。浼氳瘽銆?- `POST /api/agent-runs`锛氭彁浜ゆ櫤鑳戒綋浠诲姟锛岃繑鍥?`run_id`銆乣conversation_id`銆乣status`銆?- `GET /api/agent-runs`锛氬綋鍓嶇敤鎴蜂换鍔″垪琛ㄣ€?- `GET /api/agent-runs/{run_id}`锛氭煡璇换鍔＄姸鎬併€佽繘搴︺€佹棩蹇椼€佺粨鏋滃拰閿欒銆?- `POST /api/agent-runs/{run_id}/cancel`锛氬彇娑?running 浠诲姟銆?- `POST /api/agent-runs/{run_id}/retry`锛氬熀浜庡師 payload 鍒涘缓閲嶈瘯浠诲姟銆?- `POST /api/agent-runs/preview-payload`锛氭寜鏅鸿兘浣撻厤缃瑙堟渶缁?Payload锛屼笉鍒涘缓浠诲姟銆?
`POST /api/agent-runs` 鏀寔 `selected_skill_ids`銆乣link`銆乣file_ids`銆乣dataset_ids`銆乣image_paths`銆乣video_path`銆乣video_url`銆乣session_id` 鍜?`workflow_options`銆?
## Local Agent Connector 涓?Debug Payload

- `GET /api/agent-connectors`锛氬垪鍑鸿繛鎺ュ櫒銆?- `GET /api/agent-connectors/{connector_id}`锛氳鍙栬繛鎺ュ櫒銆?- `POST /api/agent-connectors`锛氬垱寤鸿繛鎺ュ櫒銆?- `POST /api/agent-connectors/{connector_id}`锛氭洿鏂拌繛鎺ュ櫒銆?- `DELETE /api/agent-connectors/{connector_id}`锛氳蒋绂佺敤杩炴帴鍣ㄣ€?- `POST /api/agent-connectors/{connector_id}/test`锛氭祴璇?mock銆丠TTP銆丆LI 杩炴帴銆?- `POST /api/agent-connectors/{connector_id}/preview-payload`锛氭寜杩炴帴鍣ㄩ瑙?Payload銆?- `GET /api/admin/debug-payloads`锛氱鐞嗗憳鏌ヨ鑱旇皟璁板綍銆?- `GET /api/admin/debug-payloads/{run_id}`锛氳鍙?request銆乺esponse銆乪rror銆?- `POST /api/admin/debug-payloads/{run_id}/replay`锛氶噸鏀句繚瀛樼殑 request銆?
## Dataset 鏁版嵁娓呮礂

- `POST /api/datasets/from-file`锛氬熀浜庡綋鍓嶇敤鎴风殑 `file_id` 鍒涘缓 Dataset銆?- `GET /api/datasets`锛氭煡璇㈠綋鍓嶇敤鎴?Dataset锛沘dmin 鍙寜鍙傛暟鏌ョ湅鍏ㄩ儴鎴栨寚瀹氱敤鎴枫€?- `GET /api/datasets/mapping-templates`锛氳鍙栧綋鍓嶇敤鎴峰彲澶嶇敤瀛楁鏄犲皠妯℃澘銆?- `GET /api/datasets/{dataset_id}`锛氳鍙?Dataset 鍏冩暟鎹€?- `GET /api/datasets/{dataset_id}/preview`锛氳鍙栭瑙堣鍜屽瓧娈佃瘑鍒粨鏋溿€?- `POST /api/datasets/{dataset_id}/field-mapping`锛氫繚瀛樺瓧娈垫槧灏勩€?- `GET /api/datasets/{dataset_id}/field-mapping`锛氳鍙栧瓧娈垫槧灏勩€?- `POST /api/datasets/{dataset_id}/clean`锛氭墽琛屽悓姝ユ竻娲楀苟鐢熸垚 Excel銆乸rofile 鍜?metrics 鏂囦欢銆?- `GET /api/datasets/{dataset_id}/profile`锛氳鍙栨竻娲楃敾鍍忋€?- `GET /api/datasets/{dataset_id}/files`锛氳鍙栫粨鏋滄枃浠躲€?- `DELETE /api/datasets/{dataset_id}`锛氳蒋鍒犻櫎 Dataset銆?
## 鍚庡彴杩愮淮

- `GET /api/admin/runtime/configs/status`锛氭鏌?agent_configs銆乻kill_templates銆乫iles銆?- `POST /api/admin/runtime/configs/backup`锛氬浠?runtime configs銆?- `POST /api/admin/runtime/configs/repair`锛氫慨澶?runtime configs銆?- `POST /api/admin/runtime/configs/reset`锛氶噸缃粯璁ら厤缃€?- `GET /api/admin/runtime/configs/export`锛氬鍑洪厤缃€?- `POST /api/admin/runtime/cache/clear`锛氭竻鐞嗗彲娓呯悊缂撳瓨銆?- `GET /api/admin/agent-runs/stats`锛氫换鍔＄粺璁°€?- `POST /api/admin/agent-runs/repair-stale`锛氫慨澶嶈秴鏃?running 浠诲姟銆?- `POST /api/admin/agent-runs/cleanup`锛氭竻鐞嗗巻鍙蹭换鍔°€?- `GET /api/admin/audit-logs`锛氭煡璇㈠璁℃棩蹇椼€?- `GET /api/admin/audit-logs/export`锛氬鍑哄璁℃棩蹇?CSV 鎴?JSONL銆?
## v1.5.7 APP SQLite 瀛樺偍

- `GET /api/admin/storage/health`锛氫粎 admin锛岃繑鍥?APP SQLite 璺緞銆佽〃璁℃暟銆丣SON 杩佺Щ鐘舵€併€?- `POST /api/admin/storage/migrate-json`锛氫粎 admin锛屾墜鍔ㄨЕ鍙戞棫 JSON 澶囦唤鍜屽箓绛夎縼绉汇€?
APP SQLite 榛樿璺緞涓?`apps/api/runtime/app/meizhaiseek.sqlite3`銆俁AG SQLite 浠嶄负 `apps/api/runtime/rag/rag.sqlite3`锛屼袱鑰呯嫭绔嬬鐞嗐€?
## v1.5.8 瀛樺偍鎬ц兘浼樺寲涓?Dataset SQLite 缁熶竴

- v1.5.8 娌℃湁鏂板涓氬姟鎺ュ彛锛屼富瑕佹槸搴曞眰瀛樺偍涓庢€ц兘浼樺寲锛岀幇鏈?API 杩斿洖缁撴瀯淇濇寔鍏煎銆?- Dataset API 搴曞眰 metadata 宸茶縼鍏?APP SQLite锛汦xcel銆佸浘鐗囥€佹竻娲楃粨鏋滅瓑鏂囦欢鏈綋浠嶄繚瀛樺湪纾佺洏銆?- `GET /api/admin/storage/health` 鐨?`tables` 杩斿洖鏂板 `datasets`銆乣dataset_files`銆乣dataset_jobs` 缁熻锛沗legacy_json` 杩斿洖鏂板 Dataset migration 鐘舵€佸拰 warnings銆?## v1.6 瑙嗛鎷嗚В鏅鸿兘浣撶敓浜у寲

- `GET /api/agents/video-script/status`锛氱櫥褰曠敤鎴峰彲鏌ョ湅鏈湴瑙嗛鎷嗚В Agent 杩炴帴鐘舵€併€傝繑鍥?`connected/disconnected/mock/disabled`銆乣base_url`銆乣reachable`銆乣latency_ms`銆佷腑鏂囨彁绀哄拰鍚姩寤鸿锛涙湰鍦?8001 涓嶅彲杈炬椂涓嶈繑鍥?500銆?- `POST /api/agent-runs`锛歚agent_type=video_script_breakdown` 鏃舵敮鎸?`mode`銆乣video_path`銆乣video_url`銆乣session_id` 鍜?`workflow_options`銆傛帹鑽?mode 涓?`standard_breakdown`銆乣no_subtitle_breakdown`銆乣fast_breakdown`銆乣quality_check`銆?- `workflow_options_json`锛氫繚瀛?OCR銆侀煶棰戣浆鍐欍€丒xcel/JSON/keyframes 杈撳嚭銆佽川閲忔鏌ャ€丏ebug Payload銆佽緭鍑虹洰褰曞拰鍥哄畾 session_id 绛夎棰戞媶瑙ｅ弬鏁般€?- `result_json`锛氳棰戞媶瑙ｇ粨鏋滃寘鍚?`summary`銆乣timeline`銆乣subtitles`銆乣selling_points`銆乣proof_frames`銆乣quality_warnings`銆乣files`銆乣steps`锛涚己澶卞瓧娈典互绌烘暟缁勬垨 null 鍏煎銆?- Artifact 涓嬭浇锛氫繚鐣?`/api/artifacts/download?path=...`锛屽苟鏂板 run-scoped 涓嬭浇 `/api/agent-runs/{run_id}/artifacts/{artifact_id}/download`锛屼笅杞藉墠鏍￠獙鐢ㄦ埛銆乺un銆乤rtifact 褰掑睘鍜屽畨鍏ㄨ矾寰勩€?## v1.6.2 Performance

v1.6.2 鏂板 `GET /api/agent-runs/{run_id}/summary` 鍜?`GET /api/agent-runs/{run_id}/result`銆俙summary` 鐢ㄤ簬 `/agent` 椤甸潰杞婚噺杞锛岃繑鍥炰换鍔＄姸鎬併€佽繘搴︺€佹楠ゆ憳瑕併€乤rtifact 璁℃暟鍜?result preview锛沗result` 鐢ㄤ簬鐢ㄦ埛灞曞紑瀹屾暣缁撴灉鏃舵寜闇€璇诲彇瀹屾暣 `result_json`銆俙GET /api/conversations/{conversation_id}` 淇濇寔鍘?wire shape锛屼絾鍏朵腑 run/message 澶у瓧娈甸粯璁よ繑鍥?preview锛孌ebug Payload 浠嶈蛋鍚庡彴璇︽儏鎺ュ彛銆?
## v1.6.4 Engineering

v1.6.4 鏃犳柊澧炰笟鍔?API銆俙GET /api/admin/runtime/health` 鐨?`version` 杩斿洖 `v1.6.4`锛宍warnings` 澧炲姞瀹夊叏閰嶇疆鎻愮ず銆傛柊澧炴湰鍦?smoke 鑴氭湰 `python apps/api/scripts/smoke_minimal.py`锛岀敤浜庨獙璇?`/health`銆佺櫥褰曘€乧onversation銆乤gent run銆丼QLite 鎸佷箙鍖栥€乻torage health 鍜?QA model status銆?
## v1.6.1 Hotfix

v1.6.1 鏃犳柊澧炰笟鍔℃帴鍙ｏ紝涓昏淇 `/agent` 浼氳瘽鍒囨崲绋冲畾鎬с€傜幇鏈?Agent銆佽棰戞媶瑙ｃ€丄rtifact銆丏ebug Payload銆丏ataset銆丷AG 鍜?`/chat` 鎺ュ彛淇濇寔鍏煎銆?

## v1.6.4 Video Agent E2E

### GET /api/agents/video-script/status
返回主平台后端对本地视频拆解 Agent 的健康检查结果。后端请求 Connector 配置中的 `health_path`，默认是 `http://127.0.0.1:8001/health`。

成功示例：
```json
{
  "status": "connected",
  "reachable": true,
  "base_url": "http://127.0.0.1:8001",
  "health_path": "/health",
  "health_status": "ok",
  "service": "shot-cutting-agent",
  "version": "0.1.0",
  "model_version": "shot_cutting_agent_v2_19_reference_balanced_fast_proof",
  "latency_ms": 12
}
```

失败时返回 `status=disconnected`、`reachable=false` 和错误提示，不返回 500。

### POST /api/agent-runs video_script_breakdown
平台请求仍走现有 agent run 接口。`agent_type=video_script_breakdown` 时，平台会把前端输入映射成本地 Agent 原生 `/run` payload。

请求示例：
```json
{
  "agent_type": "video_script_breakdown",
  "mode": "shot_text_excel",
  "video_path": "E:\\USE\\codexhome\\fenge\\videos\\test\\1.mp4",
  "workflow_options": {
    "output_dir": "E:\\USE\\codexhome\\fenge\\output\\test",
    "subtitle_region": "bottom",
    "ocr_workers": 6,
    "keep_debug_payload": true
  }
}
```

发送到 8001 的真实 payload：
```json
{
  "mode": "shot_text_excel",
  "video_file": "E:\\USE\\codexhome\\fenge\\videos\\test\\1.mp4",
  "output_dir": "E:\\USE\\codexhome\\fenge\\output\\test",
  "subtitle_region": "bottom",
  "ocr_workers": 6
}
```

`standard`、`standard_breakdown`、`shot_text_excel` 会映射为 `shot_text_excel`；`mock` 保持 `mock`。平台高级参数会保存在 run/debug 中，但不会把本地 Agent 不支持的字段直接传给 8001。

### result_json.summary
v1.6.4 标准化字段：
- `video_name`
- `video_path`
- `status`
- `raw_shot_count`
- `model_optimized_shot_count`
- `excel_column_count`
- `excel_image_count`
- `artifact_count`
- `excel_path`
- `shot_report_path`
- `execution_mode`

如果 shot_report JSON 可读取，平台会尽量提取 `timeline`、`subtitles`、`proof_frames` 和 `quality_warnings`；读取失败不会让 completed 任务失败，会写入 `normalization_warnings`。

### artifacts 下载/预览
平台会登记 Excel、JSON、TXT、MD、PNG、JPG、JPEG、WEBP，并为 output_dir 生成 `folder_manifest.json`。下载和预览继续使用现有 artifact 接口，校验登录用户、run 归属和安全路径。文件不存在时返回中文错误。

