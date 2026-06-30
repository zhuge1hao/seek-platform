import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from services import audit_log_service, data_cleaning_service, dataset_store, field_mapping_service, file_store
from services.auth_service import require_operator_or_admin, require_viewer_or_above


router = APIRouter()


class DatasetCreateRequest(BaseModel):
    file_id: str = Field(..., min_length=1)
    name: str | None = None


class FieldMappingRequest(BaseModel):
    mapping: dict[str, str]
    template_name: str | None = None
    save_as_template: bool = False


class CleaningRequest(BaseModel):
    rules: dict[str, Any] = Field(default_factory=dict)


def _dataset_or_404(dataset_id: str, user: dict[str, Any]) -> dict[str, Any]:
    dataset = dataset_store.get_dataset(dataset_id, user["user_id"], include_all_users=user.get("role") == "admin")
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在。")
    return dataset


@router.post("/datasets/from-file")
def create_from_file(payload: DatasetCreateRequest, request: Request, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    record = file_store.get_file_record(payload.file_id, user["user_id"], include_all_users=user.get("role") == "admin", include_legacy=False)
    if not record:
        raise HTTPException(status_code=404, detail="文件不存在或无权访问。")
    if user.get("role") != "admin" and record.get("user_id") != user["user_id"]:
        raise HTTPException(status_code=403, detail="当前账号无权访问该文件。")
    try:
        result = dataset_store.create_dataset(record.get("user_id") or user["user_id"], record, payload.name)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    audit_log_service.write_log("dataset.create", "success", user, result["dataset_id"], {"file_id": payload.file_id}, audit_log_service.client_ip(request))
    return result


@router.get("/datasets")
def list_datasets(status: str | None = None, limit: int = 50, include_all_users: bool = False, user_id: str | None = None, user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    if (include_all_users or user_id) and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="当前账号无权限执行此操作。")
    if user_id:
        items = dataset_store.list_datasets(user_id, status, limit)
    elif include_all_users and user.get("role") == "admin":
        items = dataset_store.list_all_datasets(status, limit)
    else:
        items = dataset_store.list_datasets(user["user_id"], status, limit)
    return {"datasets": items}


@router.get("/datasets/mapping-templates")
def mapping_templates(user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    return {"templates": field_mapping_service.list_mapping_templates(user["user_id"])}


@router.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: str, user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    return _dataset_or_404(dataset_id, user)


@router.get("/datasets/{dataset_id}/preview")
def get_preview(dataset_id: str, user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    return dataset_store.get_preview(_dataset_or_404(dataset_id, user))


@router.post("/datasets/{dataset_id}/field-mapping")
def save_mapping(dataset_id: str, payload: FieldMappingRequest, request: Request, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    dataset = _dataset_or_404(dataset_id, user)
    if user.get("role") != "admin" and dataset["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="当前账号无权修改该数据集。")
    preview = dataset_store.get_preview(dataset)
    try:
        mapping = field_mapping_service.validate_mapping(payload.mapping, preview.get("columns") or [])
        path = dataset_store.dataset_dir(dataset["user_id"], dataset_id) / "mapping" / "field_mapping.json"
        field_mapping_service.write_json(path, {"dataset_id": dataset_id, "mapping": mapping})
        template = field_mapping_service.save_mapping_template(user["user_id"], payload.template_name or "", mapping) if payload.save_as_template else None
        dataset_store.update_dataset(dataset_id, dataset["user_id"], {"status": "mapped", "field_mapping": mapping})
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    audit_log_service.write_log("dataset.field_mapping.save", "success", user, dataset_id, {"save_as_template": payload.save_as_template}, audit_log_service.client_ip(request))
    return {"status": "success", "dataset_id": dataset_id, "mapping_path": str(path), "mapping": mapping, "template": template}


@router.get("/datasets/{dataset_id}/field-mapping")
def get_mapping(dataset_id: str, user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    dataset = _dataset_or_404(dataset_id, user)
    path = dataset_store.dataset_dir(dataset["user_id"], dataset_id) / "mapping" / "field_mapping.json"
    if not path.exists():
        return {"dataset_id": dataset_id, "mapping": {}, "suggested_mapping": dataset_store.get_preview(dataset).get("suggested_mapping", {})}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail=f"字段映射读取失败：{exc}") from exc


@router.post("/datasets/{dataset_id}/clean")
def clean_dataset(dataset_id: str, payload: CleaningRequest, request: Request, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    dataset = _dataset_or_404(dataset_id, user)
    if user.get("role") != "admin" and dataset["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="当前账号无权清洗该数据集。")
    mapping_path = dataset_store.dataset_dir(dataset["user_id"], dataset_id) / "mapping" / "field_mapping.json"
    if not mapping_path.exists():
        raise HTTPException(status_code=400, detail="请先保存字段映射后再执行清洗。")
    try:
        mapping = json.loads(mapping_path.read_text(encoding="utf-8")).get("mapping", {})
        result = data_cleaning_service.clean_dataset(dataset, mapping, payload.rules)
    except Exception as exc:
        dataset_store.update_dataset(dataset_id, dataset["user_id"], {"status": "failed"})
        raise HTTPException(status_code=400, detail=f"数据清洗失败：{exc}") from exc
    audit_log_service.write_log("dataset.clean", "success", user, dataset_id, {"rules": payload.rules, "profile": result["profile"]}, audit_log_service.client_ip(request))
    return result


@router.get("/datasets/{dataset_id}/profile")
def get_profile(dataset_id: str, user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    return dataset_store.read_json_file(_dataset_or_404(dataset_id, user), "cleaned/data_profile.json")


@router.get("/datasets/{dataset_id}/files")
def get_files(dataset_id: str, user: dict[str, Any] = Depends(require_viewer_or_above)) -> dict[str, Any]:
    return {"files": dataset_store.dataset_files(_dataset_or_404(dataset_id, user))}


@router.delete("/datasets/{dataset_id}")
def delete_dataset(dataset_id: str, request: Request, user: dict[str, Any] = Depends(require_operator_or_admin)) -> dict[str, Any]:
    dataset = _dataset_or_404(dataset_id, user)
    if user.get("role") != "admin" and dataset["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="当前账号无权删除该数据集。")
    updated = dataset_store.update_dataset(dataset_id, dataset["user_id"], {"status": "deleted"})
    audit_log_service.write_log("dataset.delete", "success", user, dataset_id, {}, audit_log_service.client_ip(request))
    return {"status": "success", "dataset": updated}
