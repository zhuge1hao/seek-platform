# TODO

## v1.6.4 已完成目标
- 主平台 Connector 默认配置到 `http://127.0.0.1:8001`
- `/health` 状态识别 `shot_cutting_agent_v2_19_reference_balanced_fast_proof`
- `shot_text_excel` Payload Adapter
- `video_file`/`output_dir`/`subtitle_region`/`ocr_workers` 参数支持
- 使用测试视频按钮
- Payload 预览显示真实 `/run` payload
- 真实 POST `/run` 调用
- completed response 处理
- result normalizer 映射 raw shot count / optimized shots / Excel columns/images
- shot_report JSON 解析
- Excel artifact 自动登记
- shot_report artifact 自动登记
- output_dir 安全扫描和 `folder_manifest.json`
- VideoBreakdownResultPanel 展示真实 completed summary
- Debug Payload request/response/error 记录
- `smoke_minimal.py` 增加 `--video-agent-e2e`
- `docs/VIDEO_AGENT_E2E_CHECKLIST.md` 更新

## v1.6.4 宸插畬鎴愮洰鏍?
- 寮曞叆 SWR 鍩虹鏁版嵁鑾峰彇灞?- 鏂板 queryKeys 鍜岃鍙栧瀷 hooks
- RuntimeHealth / Conversation / Knowledge 绛変綆椋庨櫓鎺ュ彛鎺ュ叆 SWR
- DeepSeek async_generate_answer 鍏煎灞?- 淇濈暀 DeepSeek 鍚屾璋冪敤鍏煎
- 鏂板鏈€灏?smoke 娴嬭瘯鑴氭湰
- 鏂板 docs/SMOKE_TESTS.md
- 鏍圭洰褰曟棩蹇楄縼绉诲埌 runtime/logs
- .bak-v1.5.7 鏂囨。澶囦唤绉诲姩鍒?docs/archive
- 鏂板 security_config_service
- AUTH_TOKEN_SECRET 缂哄け鏃剁敓鎴愬紡鍒濆鍖?- 榛樿 secret / 榛樿鍒濆瀵嗙爜 health warning
- docker-compose 閰嶇疆琛ラ綈
- GitHub Actions CI
- 鏈湴楠岃瘉閫氳繃
- GitHub commit/push

## v1.6.2 宸插畬鎴愮洰鏍?
- `/agent` 浼氳瘽鍒囨崲娣卞害鎬ц兘浼樺寲
- 澧炲姞鍓嶇寮€鍙戠幆澧冩€ц兘鎺㈤拡
- conversation detail payload 杞婚噺鍖?- 澶?`result_json` 寤惰繜鍔犺浇
- Debug Payload 寤惰繜鍔犺浇
- Artifact 鍐呭鎳掑姞杞?- Agent run polling 缁熶竴涓哄崟涓€ hook
- 绉婚櫎閲嶅 `setInterval`
- 蹇€熷垏鎹細璇濊繃鏈熻姹傚拷鐣?- `listConversations` 鍒锋柊鍑忓皯
- `VideoBreakdownResultPanel` Tab 鍖?鎶樺彔鍖?- timeline/subtitle/proof_frames 鍒嗘娓叉煋
- 澶?JSON 榛樿涓嶇洿鎺ユ覆鏌?- React.memo 涓庤交閲忔淳鐢熸暟鎹紭鍖?- 澶?payload 涓嶅啀闃诲棣栧睆鍒囨崲
- `/agent` 蹇€熻繛缁偣鍑荤ǔ瀹氭€ч獙璇?
## v1.6.1 宸插畬鎴愮洰鏍?
- 淇 `/agent?conversation_id=` 鍒囨崲鍗℃
- 淇 URL 鍜?activeConversationId 鍚屾姝诲惊鐜?- 澧炲姞 conversation detail 璇锋眰 AbortController
- 澧炲姞杩囨湡璇锋眰蹇界暐鏈哄埗
- 淇 run polling 閲嶅鍒涘缓闂
- 鍒囨崲浼氳瘽鏃舵竻鐞嗘棫 polling
- 澶?payload 榛樿鎶樺彔/鎴柇锛岄伩鍏嶉樆濉炴覆鏌?- 鍒犻櫎鎸夐挳闃绘浜嬩欢鍐掓场
- conversation 涓嶅瓨鍦ㄦ椂娓呯悊 URL 鍜?localStorage
- `/agent` 椤甸潰鍒囨崲绋冲畾鎬ч獙璇?
## v1.6 宸插畬鎴愮洰鏍?
- 瑙嗛鎷嗚В鏅鸿兘浣撶敓浜у寲
- 鏈湴瑙嗛 Agent 鐘舵€佹娴?- 8001 杩炴帴棰勬
- 瑙嗛鎷嗚В涓撶敤杈撳叆鍖?- 鎷嗚В妯″紡閫夋嫨
- 楂樼骇鍙傛暟 workflow_options_json
- video_script_workflow steps 鏍囧噯鍖?- 瑙嗛鎷嗚В缁撴瀯鍖?result_json
- VideoBreakdownResultPanel
- 浠诲姟姒傝灞曠ず
- 鎵ц姝ラ灞曠ず
- 闀滃ご鏃堕棿杞村睍绀?- 瀛楀箷 OCR 灞曠ず
- 鍗栫偣璇嗗埆灞曠ず
- 瑙嗚璇佹槑甯у睍绀?- 璐ㄩ噺璀﹀憡灞曠ず
- 杈撳嚭鏂囦欢绠＄悊
- Artifact 棰勮涓庝笅杞?- Debug Payload 澧炲己
- 澶辫触鎻愮ず浼樺寲
- 浠诲姟鐘舵€佷細璇濆洖鍐?- SQLite 鎸佷箙鍖栭獙璇?## v1.5.8 宸插畬鎴愮洰鏍?- qa_conversation_store 澧為噺 upsert
- conversation_store 澧為噺 upsert
- bulk replace 浠呬繚鐣欑粰 migration
- Dataset metadata 杩佸叆 APP SQLite
- datasets 琛?- dataset_files 琛?- dataset_jobs 琛?- datasets.json legacy 杩佺Щ
- storage health 澧炲姞 dataset 琛ㄧ粺璁?- service_events 杞婚噺浜嬩欢閽╁瓙
- task_store 绉婚櫎瀵?conversation_store 鐨勫嚱鏁板唴寤惰繜 import
- run updated 浜嬩欢鍚屾 conversation
- 鐜版湁 API 杩斿洖缁撴瀯淇濇寔涓嶅彉
- 鐢ㄦ埛闅旂楠岃瘉
- Dataset 鍔熻兘楠岃瘉
## v1.5.7 宸插畬鎴愮洰鏍?
- API.md 涔辩爜淇
- PRD.md 涔辩爜淇
- APP SQLite 鍒濆鍖?- APP SQLite migrations
- JSON legacy backup
- JSON to SQLite migrator
- 鐢ㄦ埛璐﹀彿杩佺Щ
- 瀹¤鏃ュ織杩佺Щ
- QA conversation 杩佺Щ
- agent conversation 杩佺Щ
- agent runs 杩佺Щ
- connector/debug payload/files/artifacts metadata 杩佺Щ
- SQLite storage health API
- JSON store 鏇挎崲涓?SQLite store
- 鐢ㄦ埛闅旂楠岃瘉
- 鏉冮檺楠岃瘉

## v1.5.6 宸插畬鎴愮洰鏍?
- DeepSeek stream_answer
- QA stream service
- POST /api/qa/chat/stream
- SSE event 鏍煎紡
- start/retrieval_start/sources/delta/done/error 浜嬩欢
- 鍓嶇 ReadableStream 瑙ｆ瀽
- /chat 娴佸紡娓叉煋
- 鍋滄鐢熸垚
- 澶嶅埗鍥炵瓟
- 閲嶆柊鐢熸垚
- sources 鎶樺彔灞曠ず
- warnings/error 浼樺寲
- 娴佸紡瀹屾垚鍚庢寔涔呭寲 assistant message
- 娴佸紡澶辫触鍚庢寔涔呭寲 failed message
- 闈炴祦寮?fallback

## v1.5.5 宸插畬鎴愮洰鏍?
- /api/qa/model-status
- /api/qa/test-embedding
- /api/qa/test-retrieval
- /api/qa/diagnose
- qa_model_diagnostic_service
- qa_embedding_service 鐘舵€佹娴嬪寮?- KnowledgeBasePanel 妯″瀷鐘舵€佸尯
- Embedding 娴嬭瘯鎸夐挳
- RAG 妫€绱㈡祴璇曟寜閽?- 鐭ヨ瘑搴撹瘖鏂寜閽?- 璇婃柇 checks 灞曠ず
- RAG_MODEL_SETUP.md
- 妯″瀷缂哄け娓呮櫚鎻愮ず
- DeepSeek 鏈厤缃竻鏅版彁绀?- SQLite RAG 鐘舵€佸睍绀?
## 鍚庣画璁″垝

- v1.6锛氳棰戞媶瑙ｆ櫤鑳戒綋鐢熶骇鍖?- v1.7锛氭櫤鑳戒綋钃濆浘涓庢柟娉曡閰嶇疆涓績
- v1.8锛氬弬鑰冮」鐩媶瑙ｅ姪鎵?
