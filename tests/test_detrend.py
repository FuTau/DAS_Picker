import numpy as np
from src.utils import detrend_2D
import pytest


# 测试数据生成函数，装饰器pytest.fixture定义测试夹具
@pytest.fixture
def sample_data():
    np.random.seed(42)  # 确保测试结果可重复
    data = np.random.rand(3, 10)  # 生成随机数据，3个通道，每个通道10个数据点
    return data


# 测试函数是否正常运行
def test_detrend_2D_runs(sample_data):
    detrended_data = detrend_2D(sample_data)
    assert detrended_data.shape == sample_data.shape, "输出数据形状应与输入相同"


# 测试函数是否正确去趋势
def test_detrend_2D_result(sample_data):
    detrended_data = detrend_2D(sample_data)
    for channel in detrended_data:
        # 去趋势后，数据的线性拟合斜率应接近于0
        x = np.arange(len(channel))
        m = np.sum((x - np.mean(x)) * (channel - np.mean(channel))) / np.sum((x - np.mean(x)) ** 2)
        assert np.isclose(m, 0, atol=1e-6), "去趋势后，数据的线性拟合斜率应接近于0"


# 测试输入为全零数据时的行为
def test_detrend_2D_all_zeros():
    data = np.zeros((3, 10))
    detrended_data = detrend_2D(data)
    assert np.allclose(detrended_data, np.zeros((3, 10))), "全零数据去趋势后应仍为全零"


# 测试单通道数据
def test_detrend_2D_single_channel():
    data = np.random.rand(1, 10)
    detrended_data = detrend_2D(data)
    assert detrended_data.shape == data.shape, "单通道数据的形状应保持不变"
    assert np.isclose(np.mean(detrended_data), 0, atol=1e-6), "单通道数据去趋势后均值应接近于0"