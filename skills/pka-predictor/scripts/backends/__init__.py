"""
pKa Predictor Backends

预测后端模块
"""

# Custom 后端总是可用
from .custom_backend import (
    CustomBackend,
    predict_pka_custom,
)

# UniPKA 后端需要额外依赖，延迟导入
try:
    from .unipka_backend import (
        UniPKABackend,
        predict_pka_unipka,
    )
    UNIPKA_AVAILABLE = True
except ImportError as e:
    UNIPKA_AVAILABLE = False
    UniPKABackend = None
    predict_pka_unipka = None
    # 仅在真正使用时才报错
    def predict_pka_unipka(*args, **kwargs):
        raise ImportError(f"UniPKA 后端需要额外依赖：{e}")

__all__ = [
    'CustomBackend',
    'predict_pka_custom',
    'UniPKABackend',
    'predict_pka_unipka',
    'UNIPKA_AVAILABLE',
]
