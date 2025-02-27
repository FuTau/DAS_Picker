import numpy as np
from src.utils import template_match
import pytest
from scipy import signal
from scipy.signal import find_peaks


# 测试数据生成函数
@pytest.fixture
def sample_data():
    # 生成示例模板和数据
    template = np.array([0, 1, 2, 3, 4, 5],dtype=np.float64)
    data = np.array([0, 0, 1, 2, 3, 4, 5, 4, 3, 2, 1, 0],dtype=np.float64)
    dt = 0.1  # 采样间隔
    return template, data, dt


# 测试函数
def test_template_match_max(sample_data):
    template, data, dt = sample_data
    correlation, correct_t = template_match(template, data, dt, type="max")

    # 检查返回值的类型
    assert isinstance(correlation, np.ndarray), "correlation 应该是一个 numpy 数组"
    assert isinstance(correct_t, float), "correct_t 应该是一个浮点数"

    # 检查相关系数的范围
    assert np.abs(np.max(correlation)-1) <= 1e-10, "相关系数计算错误"

    # 检查时间偏移是否合理
    assert np.isclose(correct_t, (np.argmax(correlation) - len(template) / 2) * dt), "时间偏移计算错误"
