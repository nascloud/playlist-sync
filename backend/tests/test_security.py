import pytest
from core.security import encrypt_token, decrypt_token

def test_encrypt_decrypt_token():
    """测试令牌加密和解密"""
    # 保存原始密钥
    from core.config import settings
    original_key = settings.SECRET_KEY
    
    try:
        # 设置测试密钥
        import os
        os.environ["SECRET_KEY"] = "test-secret-key"
        # 重新加载配置
        import importlib
        import core.config
        importlib.reload(core.config)
        from core.config import settings
        
        # 测试加密和解密
        original_token = "test_plex_token_12345"
        encrypted = encrypt_token(original_token)
        decrypted = decrypt_token(encrypted)
        
        assert decrypted == original_token
    finally:
        # 恢复原始密钥
        os.environ["SECRET_KEY"] = original_key
        importlib.reload(core.config)

def test_encrypt_decrypt_empty_token():
    """测试空令牌的加密和解密"""
    from core.config import settings
    original_key = settings.SECRET_KEY
    
    try:
        import os
        os.environ["SECRET_KEY"] = "test-secret-key"
        import importlib
        import core.config
        importlib.reload(core.config)
        from core.config import settings
        
        original_token = ""
        encrypted = encrypt_token(original_token)
        decrypted = decrypt_token(encrypted)
        
        assert decrypted == original_token
    finally:
        os.environ["SECRET_KEY"] = original_key
        importlib.reload(core.config)