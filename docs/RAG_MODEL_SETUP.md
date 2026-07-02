# RAG Model Setup

## 本地模型

知识库 embedding 默认使用本地 `bge-small-zh`。模型路径由后端配置读取，`GET /api/qa/model-status` 会返回模型路径、是否存在、是否可加载、RAG SQLite 状态和 DeepSeek 配置状态。

## 不可用时的表现

- `/chat` 可继续使用非 RAG 问答。
- RAG 检索会返回清晰 warning。
- 诊断接口不会打印 API Key。

## 建议验证

```powershell
python -m compileall apps/api
python apps/api/scripts/smoke_minimal.py
```

如需验证知识库能力，可在前端知识库面板上传 txt、md 或 docx 文档后查看 stats、model status 和 retrieval test。
