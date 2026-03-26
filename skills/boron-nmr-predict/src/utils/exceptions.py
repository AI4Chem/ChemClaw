"""自定义异常类"""


class InvalidSMILESError(Exception):
    """无效的 SMILES 异常"""
    pass


class PredictionError(Exception):
    """预测过程中的异常"""
    pass


class DatabaseError(Exception):
    """数据库操作异常"""
    pass


class ValidationError(Exception):
    """输入验证异常"""
    pass
