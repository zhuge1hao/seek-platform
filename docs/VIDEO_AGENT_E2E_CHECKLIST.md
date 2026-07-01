## v1.6.5 E2E Checklist Update

- 运行 python apps/api/scripts/smoke_minimal.py --video-agent-e2e --require-video-agent。
- 检查 video status connected、run completed、summary/result/artifacts、assistant completed message、artifact download URL。

# 瑙嗛鎷嗚В Agent E2E 楠屾敹娓呭崟

## 鍓嶇疆鏉′欢
- 涓诲钩鍙?API 鍦?`http://127.0.0.1:8000` 杩愯銆?- 鍓嶇鍦?`http://127.0.0.1:3000` 杩愯銆?- 鏈湴瑙嗛 Agent 宸插惎鍔細
  ```powershell
  cd E:\USE\codexhome\fenge
  .\start_agent_8001.bat
  ```
- 娴嬭瘯瑙嗛瀛樺湪锛歚E:\USE\codexhome\fenge\videos\test\1.mp4`

## 鎵嬪伐楠屾敹
- 鎵撳紑 `/agent`锛岄€夋嫨瑙嗛鎷嗚В鏅鸿兘浣撱€?- 鐐瑰嚮鈥滄祴璇曡繛鎺モ€濓紝纭鐘舵€佷负 connected锛宍model_version` 涓?`shot_cutting_agent_v2_19_reference_balanced_fast_proof`銆?- 鐐瑰嚮鈥滀娇鐢ㄦ祴璇曡棰戔€濓紝纭濉叆锛?  - `video_file=E:\USE\codexhome\fenge\videos\test\1.mp4`
  - `output_dir=E:\USE\codexhome\fenge\output\test`
  - `subtitle_region=bottom`
  - `ocr_workers=6`
  - `mode=shot_text_excel`
- 鎵撳紑 Payload 棰勮锛岀‘璁ゆ渶缁?request 鍙湁鏈湴 Agent 鏀寔鐨勫瓧娈碉細`mode`銆乣video_file`銆乣output_dir`銆乣subtitle_region`銆乣ocr_workers`銆?- 鎻愪氦浠诲姟骞剁瓑寰?completed銆?- 纭缁撴灉闈㈡澘鏄剧ず raw shot count銆乵odel optimized shots銆丒xcel columns/images銆丒xcel path銆乻hot_report path銆?- 纭 Artifact 鍒楄〃鍖呭惈 Excel銆乻hot_report銆乣folder_manifest.json`锛屽浘鐗囧瀛樺湪鍙瑙堛€?- 鍒锋柊椤甸潰銆佸垏鎹㈣矾鐢卞啀鍥炴潵锛宺un 缁撴灉鍜?artifacts 鑳芥仮澶嶃€?
## 鑷姩 smoke
榛樿 smoke 涓嶄緷璧?8001锛?```powershell
python apps/api/scripts/smoke_minimal.py
```

鐪熷疄瑙嗛 E2E锛?```powershell
python apps/api/scripts/smoke_minimal.py --video-agent-e2e --require-video-agent
```

濡傛灉鍙紶 `--video-agent-e2e` 涓?8001 涓嶅彲杈撅紝瑙嗛 E2E 搴旀樉绀?SKIP锛涘鏋滃悓鏃朵紶 `--require-video-agent`锛屽垯搴?FAIL銆?
## 楠屾敹鏍囧噯
- `GET /health` 杩斿洖 `{"status":"ok","service":"meizhaiseek-api"}`銆?- `/api/admin/runtime/health` 杩斿洖 `version=v1.6.4`銆?- `/api/agents/video-script/status` 8001 鍙揪鏃朵负 connected锛屼笉鍙揪鏃朵负 disconnected 涓斾笉杩斿洖 500銆?- completed 浠诲姟鍐欏叆 APP SQLite锛歛gent run銆乧onversation銆乤ssistant message銆乨ebug payload銆乤rtifacts銆?- 澶辫触浠诲姟淇濈暀鐪熷疄 error锛屼笉浼€犳垚鎴愬姛銆?
