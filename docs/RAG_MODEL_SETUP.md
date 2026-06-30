# bge-small-zh 模型放置说明

默认路径：

```text
./models/bge-small-zh
```

目录结构示例：

```text
models/
└─ bge-small-zh/
   ├─ config.json
   ├─ tokenizer.json
   ├─ tokenizer_config.json
   ├─ vocab.txt
   ├─ pytorch_model.bin 或 model.safetensors
   └─ modules.json
```

`.env` 配置：

```text
BGE_SMALL_ZH_MODEL_PATH=./models/bge-small-zh
```

常见错误：

- 模型目录不存在：请将模型放到默认路径，或修改 `BGE_SMALL_ZH_MODEL_PATH`。
- sentence-transformers 未安装：请安装后端依赖。
- 模型文件缺失：请确认目录内包含配置、tokenizer 和权重文件。
- embedding 维度异常：请确认模型目录是 bge-small-zh。
- SQLite chunk 数为 0：请先上传 txt/md/docx 并完成入库。
- DeepSeek API Key 未配置：请在 `.env` 中设置 `DEEPSEEK_API_KEY`。

验证步骤：

1. 打开 `/chat`。
2. 点击“知识库”。
3. 查看模型状态。
4. 点击“测试 Embedding”。
5. 上传 txt/md/docx。
6. 点击“测试检索”。
7. 发送 AI 对话问题并查看 sources。
