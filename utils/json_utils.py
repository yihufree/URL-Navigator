import json
import logging

logger = logging.getLogger(__name__)

# 改为始终使用简化的验证逻辑，不再尝试导入jsonschema
HAS_JSONSCHEMA = False

# 书签数据的JSON验证模式
BOOKMARK_SCHEMA = {
    "type": "object",
    "patternProperties": {
        "^.+$": {
            "oneOf": [
                {
                    "type": "object",
                    "required": ["type", "url", "name"],
                    "properties": {
                        "type": {"enum": ["url"]},
                        "url": {"type": "string"},
                        "name": {"type": "string"},
                        "icon": {"type": "string"}
                    },
                    "additionalProperties": False
                },
                {
                    "type": "object",
                    "required": ["type", "children"],
                    "properties": {
                        "type": {"enum": ["folder"]},
                        "children": {"$ref": "#"}
                    },
                    "additionalProperties": False
                }
            ]
        }
    }
}

def validate_json_schema(data, schema=None):
    """
    验证JSON数据是否符合指定的模式
    
    Args:
        data: JSON数据对象
        schema: JSON Schema 模式定义，如果为 None 则使用默认的书签模式
        
    Returns:
        (is_valid, message) 元组:
        - is_valid: 布尔值，表示验证是否通过
        - message: 如果验证失败，包含错误消息；如果成功，为空字符串
    """
    if schema is None:
        schema = BOOKMARK_SCHEMA
        
    # 始终使用简化的验证
    return _simple_validate(data)

def _simple_validate(data):
    """
    简化版验证
    
    Args:
        data: 要验证的数据
        
    Returns:
        (is_valid, message) 元组
    """
    if not isinstance(data, dict):
        return False, "数据必须是字典类型"
    
    try:
        for key, item in data.items():
            if not isinstance(item, dict):
                return False, f"项目 '{key}' 必须是字典类型"
                
            if "type" not in item:
                return False, f"项目 '{key}' 缺少 'type' 字段"
                
            if item["type"] == "url":
                # 验证 URL 项目
                if "url" not in item:
                    return False, f"URL 项目 '{key}' 缺少 'url' 字段"
                if "name" not in item:
                    return False, f"URL 项目 '{key}' 缺少 'name' 字段"
            elif item["type"] == "folder":
                # 验证文件夹项目
                if "children" not in item:
                    return False, f"文件夹 '{key}' 缺少 'children' 字段"
                if not isinstance(item["children"], dict):
                    return False, f"文件夹 '{key}' 的 'children' 必须是字典类型"
                
                # 递归验证子项目
                is_valid, message = _simple_validate(item["children"])
                if not is_valid:
                    return False, f"文件夹 '{key}' 的子项目: {message}"
            else:
                return False, f"项目 '{key}' 的 type 值 '{item['type']}' 无效，必须是 'url' 或 'folder'"
        
        return True, ""
    except Exception as e:
        logger.error(f"简化验证过程发生错误: {e}")
        return False, f"验证过程发生错误: {str(e)}"

def safe_json_load(content, default_value=None):
    """
    安全地解析JSON字符串
    
    Args:
        content: JSON字符串
        default_value: 解析失败时返回的默认值
        
    Returns:
        (success, data, message) 元组:
        - success: 布尔值，表示解析是否成功
        - data: 如果成功，包含解析后的JSON对象；如果失败，为default_value
        - message: 如果解析失败，包含错误消息；如果成功，为空字符串
    """
    try:
        # 尝试解析JSON
        data = json.loads(content)
        return True, data, ""
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析错误: {e}")
        return False, default_value, f"JSON解析错误: {str(e)}"
    except Exception as e:
        logger.error(f"解析过程发生错误: {e}")
        return False, default_value, f"解析过程发生错误: {str(e)}"
        
def safe_json_dump(data):
    """
    安全地将对象序列化为JSON字符串
    
    Args:
        data: 要序列化的对象
        
    Returns:
        (success, json_string, message) 元组:
        - success: 布尔值，表示序列化是否成功
        - json_string: 如果成功，包含JSON字符串；如果失败，为空字符串
        - message: 如果序列化失败，包含错误消息；如果成功，为空字符串
    """
    try:
        # 尝试序列化为JSON
        json_string = json.dumps(data, ensure_ascii=False, indent=2)
        return True, json_string, ""
    except TypeError as e:
        logger.error(f"类型错误，无法序列化为JSON: {e}")
        return False, "", f"类型错误，无法序列化为JSON: {str(e)}"
    except Exception as e:
        logger.error(f"序列化过程发生错误: {e}")
        return False, "", f"序列化过程发生错误: {str(e)}" 