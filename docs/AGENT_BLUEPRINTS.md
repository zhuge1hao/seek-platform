# Agent Blueprints

## 浣滅敤

Agent Blueprint 鏄?v1.7 鏂板鐨勬櫤鑳戒綋鏂规硶璁洪厤缃腑蹇冦€傚畠缁熶竴鎻忚堪鏅鸿兘浣撶殑鍩烘湰淇℃伅銆佺敓鍛藉懆鏈熴€佽緭鍏ュ崗璁€佹柟娉曡姝ラ銆丳rompt 妯℃澘銆佹墽琛岀粦瀹氥€佽緭鍑哄崗璁€佺粨鏋?UI銆佹祴璇曠敤渚嬨€侀獙鏀惰鍒欍€佺増鏈巻鍙层€佸彂甯冦€佸洖婊氥€佸鍒跺拰瀵煎叆瀵煎嚭銆?
钃濆浘鍙弿杩扮幇鏈夎兘鍔涳紝涓嶅湪 v1.7 涓噸鍐欑幇鏈夎繍琛岄摼璺€?
## Blueprint 涓?Registry

Agent Registry 浠嶇劧鏄繍琛屾椂鏅鸿兘浣撴敞鍐屾潵婧愩€傛病鏈夎摑鍥剧殑鏅鸿兘浣撲笉浼氭秷澶憋紝`/api/agents` 浼氳繑鍥?`blueprint_status=unmanaged`銆?
Blueprint 涓?Registry 琛ュ厖鏂规硶璁恒€佺増鏈€佽緭鍏ヨ緭鍑恒€佹祴璇曞拰鍙戝竷淇℃伅銆俤raft 鎴?testing 钃濆浘涓嶄細璁╂湭瀹屾垚鏅鸿兘浣撹嚜鍔ㄥ彉鎴愭寮忓彲鐢ㄣ€?
## Blueprint 涓?Workflow

Workflow 浠嶇敱鍚庣浠ｇ爜鎵ц锛屼緥濡傝棰戞媶瑙ｇ户缁娇鐢?`video_script_workflow`銆傝摑鍥剧殑 methodology steps 鐢ㄤ簬鎻忚堪銆佹牎楠屽拰楠屾敹锛屼笉浼氬姩鎬佹墽琛屼换鎰?JSON Python锛屼篃涓嶄細鍏佽閰嶇疆浠绘剰 shell 鍛戒护銆?
## 鐢熷懡鍛ㄦ湡鐘舵€?
- `draft`: 鑽夌锛屽彲缂栬緫銆佸鍒躲€佸垹闄ゆ湭鍙戝竷鑽夌銆?- `testing`: 娴嬭瘯涓紝鍙繍琛屾祴璇曠敤渚嬶紝浣嗕笉鑷姩瀵规櫘閫氱敤鎴峰紑鏀俱€?- `published`: 宸插彂甯冿紝鍙綔涓烘寮忚摑鍥惧睍绀恒€?- `disabled`: 宸插仠鐢紝淇濈暀鍘嗗彶鏁版嵁锛屽叧鑱旀櫤鑳戒綋鎷掔粷鏂颁换鍔°€?- `deprecated`: 宸插簾寮冿紝鍙淇濈暀锛屼笉鍏佽鏂板缓浠诲姟銆?
宸插彂甯冪増鏈笉鐩存帴瑕嗙洊銆備慨鏀瑰凡鍙戝竷钃濆浘蹇呴』鍒涘缓鏂扮増鏈紱鍥炴粴浼氬鍒剁洰鏍囧巻鍙插彂甯冪増鏈负鏂扮増鏈苟鍐?release 璁板綍銆?
## 鏁版嵁缁撴瀯

APP SQLite 鏂板锛?
- `agent_blueprints`
- `agent_blueprint_versions`
- `agent_blueprint_test_cases`
- `agent_blueprint_releases`

鐗堟湰鍐呭瀛楁浣跨敤 JSON 淇濆瓨锛歚input_schema_json`銆乣methodology_json`銆乣prompt_config_json`銆乣execution_config_json`銆乣output_schema_json`銆乣result_ui_config_json`銆乣acceptance_rules_json`銆?
## 杈撳叆鍗忚

`input_schema` 鎻忚堪琛ㄥ崟瀛楁锛屾敮鎸?`text`銆乣textarea`銆乣number`銆乣boolean`銆乣select`銆乣multi_select`銆乣file`銆乣image`銆乣video`銆乣excel`銆乣word`銆乣local_path`銆乣dataset`銆乣knowledge_base`銆?
鏂囦欢鍜屾湰鍦拌矾寰勫瓧娈靛彧鎻忚堪杈撳叆锛屼笉鎺堜簣浠绘剰绯荤粺璺緞璇诲彇鏉冮檺銆?
## 鏂规硶璁烘楠?
`methodology.steps` 鍙弿杩版楠?ID銆佸悕绉般€侀『搴忋€佽緭鍏ヨ緭鍑哄瓧娈点€乻kill銆丆onnector銆佽秴鏃躲€佸け璐ョ瓥鐣ュ拰楠屾敹瑙勫垯銆傚け璐ョ瓥鐣ユ敮鎸?`stop`銆乣continue`銆乣retry`銆乣skip`銆?
鍓嶇浣跨敤涓婄Щ銆佷笅绉绘垨 JSON 缂栬緫缁存姢椤哄簭锛屾湰鐗堜笉寮曞叆鎷栨嫿鐢诲竷銆?
## Prompt 鐗堟湰

Prompt 閰嶇疆璺熼殢 blueprint version銆傚彂甯冪増鏈笉鍙洿鎺ョ紪杈戯紱鏀瑰姩瑕佸垱寤烘柊鐗堟湰銆俈alidator 鏀寔 `{var}` 鍜?`{{ var }}` 鍙橀噺寮曠敤鏍￠獙锛屾湭瀹氫箟鍙橀噺涓?error锛屽畾涔変絾鏈娇鐢ㄤ负 warning銆?
Prompt 鍜屽鍏ュ鍑洪兘涓嶅厑璁镐繚瀛?`password`銆乣token`銆乣api_key`銆乣apikey`銆乣secret` 绛夋晱鎰熷瓧娈点€?
## 鎵ц缁戝畾

`execution_config.execution_type` 鏀寔 `internal`銆乣http_connector`銆乣cli_connector`銆乣mock`銆傚彂甯冨墠浼氭牎楠?Agent Registry銆乄orkflow銆丆onnector 鍜?renderer銆侰onnector 涓嶅瓨鍦ㄦ垨鍋滅敤銆乄orkflow 涓嶅瓨鍦ㄣ€佹湭鐭?renderer 閮戒細闃绘鍙戝竷銆?
CLI Connector 蹇呴』澶嶇敤鐜版湁瀹夊叏鏈哄埗锛岃摑鍥炬湰韬笉淇濆瓨鍙墽琛屽懡浠ゆā鏉裤€?
## 杈撳嚭鍗忚涓庣粨鏋?UI

`output_schema.sections` 鍙弿杩?`summary`銆乣steps`銆乣text`銆乣table`銆乣metrics`銆乣timeline`銆乣subtitles`銆乣selling_points`銆乣images`銆乣proof_frames`銆乣warnings`銆乣recommendations`銆乣artifacts`銆乣raw_preview`銆?
`result_ui_config.renderer` 鍙厑璁稿钩鍙版敞鍐屽€硷細`generic_text`銆乣generic_structured`銆乣video_breakdown`銆乣table_report`銆乣dataset_report`銆傛湭鐭?renderer 鏍￠獙澶辫触锛涙湭瀹炵幇 renderer 鍙畨鍏ㄩ檷绾у埌閫氱敤缁撴瀯鍖栧睍绀恒€?
## 娴嬭瘯鍜屽彂甯?
娴嬭瘯鐢ㄤ緥淇濆瓨杈撳叆銆佹湡鏈涚姸鎬併€佹湡鏈涚粨鏋滆鍒欍€佹湡鏈?artifact 鍜屾渶澶ц€楁椂銆傝繍琛屾祴璇曚細澶嶇敤鐜版湁 Agent Run API锛岀敓鎴愮湡瀹?`run_id`锛屽苟鍦?run 缁堟€佸悗鎶?PASS/FAIL銆侀敊璇拰鎽樿鍐欏洖 `last_result_json`銆?
鍙戝竷浠?admin 鍙墽琛屻€俹perator 鍙垱寤鸿崏绋裤€佸垱寤虹増鏈€佽繍琛屾祴璇曘€佸鍒跺拰瀵煎嚭銆倂iewer 鍙兘鏌ョ湅宸插彂甯冭摑鍥惧拰宸插彂甯冪増鏈紝涓嶈兘鏌ョ湅鏈彂甯?Prompt锛屼篃涓嶈兘杩愯娴嬭瘯銆?
## 澶嶅埗銆佸鍏ュ拰瀵煎嚭

瀵煎嚭鏍煎紡鍖呭惈 `format_version`銆乣platform`銆乣exported_at`銆乣blueprint`銆乣version`銆乣test_cases`銆傚鍑轰細閫掑綊鑴辨晱鏁忔劅瀛楁銆?
瀵煎叆蹇呴』鍏?preview銆傛寮忓鍏ラ粯璁ゅ湪 `blueprint_id` 鍐茬獊鏃跺垱寤烘柊 ID锛涗篃鍙綔涓虹洰鏍囪摑鍥炬柊鐗堟湰瀵煎叆锛屼絾涓嶈兘瑕嗙洊宸插彂甯冪増鏈€傚鍒惰摑鍥鹃粯璁ょ敓鎴?draft锛屾竻绌?`published_version_id`銆?
## 瑙嗛鎷嗚В鏍锋澘

v1.7 鑷姩骞傜瓑鍒涘缓 `bp_video_script_breakdown`锛岀粦瀹氾細

- `agent_id`: `video_script_breakdown`
- `workflow_type`: `video_script_workflow`
- `connector_id`: `video_script_agent`
- `renderer`: `video_breakdown`
- 鐘舵€侊細`published`

璇ヨ摑鍥惧彧鎻忚堪鐜版湁瑙嗛鎷嗚В閾捐矾锛屼笉淇敼鏈湴 8001 Agent锛屼笉澶嶅埗鏈湴 Agent 鍐呴儴 Prompt锛屼笉閲嶅啓 `video_script_workflow`銆?
## 瀹夊叏瑙勫垯

- 涓嶄繚瀛?token銆乸assword銆乤pi key銆乻ecret銆?- 涓嶅厑璁搁€氳繃钃濆浘鎵ц浠绘剰 shell銆?- 涓嶅厑璁稿姩鎬佹墽琛屼换鎰?JSON Python銆?- viewer 涓嶅彲鏌ョ湅鏈彂甯?Prompt銆?- 鎵€鏈夊啓鎿嶄綔鎸夎鑹叉潈闄愭帶鍒跺苟鍐欏璁℃棩蹇椼€?- disabled/deprecated 鍏宠仈钃濆浘浼氶樆姝㈡柊 Agent Run銆?
## 甯歌闂

### 钃濆浘浼氭浛浠?Agent Registry 鍚楋紵

涓嶄細銆俁egistry 浠嶇劧鍐冲畾杩愯鏃舵湁鍝簺鏅鸿兘浣擄紝钃濆浘鏄弿杩般€佹不鐞嗐€佹祴璇曞拰鍙戝竷灞傘€?
### draft 钃濆浘浼氬奖鍝嶇幇鏈夋櫤鑳戒綋杩愯鍚楋紵

涓嶄細銆傛棤钃濆浘銆乨raft銆乼esting 閮戒笉鏀瑰彉鏃㈡湁 Registry/Workflow 鍙繍琛屾€с€傚彧鏈?disabled 鎴?deprecated 鐨勫叧鑱旇摑鍥句細鎷掔粷鏂颁换鍔°€?
### 瑙嗛鎷嗚В鏄惁鏀规垚鍔ㄦ€佸伐浣滄祦锛?
娌℃湁銆傝棰戞媶瑙ｄ粛浣跨敤绋冲畾鐨?`video_script_workflow`銆乣video_agent_payload_builder`銆乣video_breakdown_result_normalizer`銆?001 Connector 鍜?`VideoBreakdownResultPanel`銆?
## v1.7.2 鍙戝竷闂幆

v1.7.2 澧炲姞琛ㄥ崟妯″紡鍜岄珮绾?JSON 妯″紡銆傝〃鍗曟ā寮忚鐩栬緭鍏ュ崗璁€佹柟娉曡姝ラ銆丳rompt銆佹墽琛岄厤缃€佽緭鍑哄崗璁拰楠屾敹瑙勫垯锛涢珮绾?JSON 妯″紡缁х画鐢ㄤ簬鎵归噺缂栬緫銆?
姣忔楠岃瘉閮戒細鍐欏叆 `agent_blueprint_validation_results`锛屾瘡娆¤繍琛屾祴璇曢兘浼氬啓鍏?`agent_blueprint_test_runs`銆傚彂甯冮棬绂佽姹傚綋鍓嶇増鏈瓨鍦ㄦ湁鏁堥獙璇併€佸惎鐢ㄦ祴璇曠敤渚嬪拰鏈€杩戜竴娆￠€氳繃鐨勬祴璇曡繍琛岋紱warning 闇€瑕佺鐞嗗憳纭锛宐locking error 浼氶樆姝㈠彂甯冦€?
鐗堟湰宸紓鎺ュ彛鏀寔褰撳墠鑽夌涓庡凡鍙戝竷鐗堟湰銆佸巻鍙茬増鏈箣闂淬€佸洖婊氱洰鏍囦笌褰撳墠鍙戝竷鐗堟湰涔嬮棿鐨勫姣斻€傝緭鍏ラ瑙堝拰缁撴灉棰勮鍙睍绀虹粨鏋勶紝涓嶆彁浜や换鍔°€佷笉璇诲彇鏈湴鏂囦欢銆?
瑙嗛鎷嗚В钃濆浘浠嶆槸 `bp_video_script_breakdown`锛岀户缁粦瀹?`video_script_workflow`銆乣video_script_agent` 鍜?`video_breakdown` renderer銆傝摑鍥惧彧鎻忚堪鐜版湁閾捐矾锛屼笉淇敼鏈湴 8001 Agent锛屼篃涓嶅鍒舵湰鍦?Agent 鍐呴儴 Prompt銆?

## meizhaiseek v1.7.2

v1.7.2 focuses on architecture stabilization after the 2026-07-03 evaluation: Blueprint release E2E coverage, wider auth/conversation/task tests, Blueprint Store splitting, legacy JSON fallback retirement diagnostics, production Docker build/start, Agent Run SSE tests, async SQLite read wrappers, frontend API module compatibility split, methodology drag ordering, Registry/Blueprint reconciliation, and the Agent Run Event Hub. Existing Agent, Workflow, Connector, APP SQLite, RAG SQLite, Dataset, QA/RAG, Debug Payload, and video breakdown execution models are unchanged.

## meizhaiseek v1.8

Blueprint remains a configuration and governance layer over existing Agent Registry, Workflow, Connector, and Renderer capabilities. v1.8 may enqueue Blueprint test runs through the shared task queue, but it does not execute arbitrary code from Blueprint JSON. Runtime health exposes queue/event/storage status so release gates can be diagnosed without leaking prompts or secrets.
