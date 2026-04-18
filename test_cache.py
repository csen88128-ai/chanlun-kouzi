#!/usr/bin/env python3
"""
测试缓存机制
"""
import sys
import time
sys.path.insert(0, '/workspace/projects')
sys.path.insert(0, '/workspace/projects/src')

from multi_agents.cache import DataCache


def test_cache_basic():
    """测试缓存基本功能"""
    print("=" * 60)
    print("测试缓存基本功能")
    print("=" * 60)

    cache = DataCache(default_ttl_minutes=5)

    # 1. 测试get/set
    print("\n[1] 测试get/set")
    cache.set("key1", "value1")
    result = cache.get("key1")
    assert result == "value1", f"期望 value1，得到 {result}"
    print(f"  ✓ get/set功能正常")

    # 2. 测试不存在的键
    print("\n[2] 测试不存在的键")
    result = cache.get("nonexistent")
    assert result is None, f"期望 None，得到 {result}"
    print(f"  ✓ 不存在的键返回None")

    # 3. 测试缓存命中/未命中统计
    print("\n[3] 测试缓存统计")
    cache.clear()
    cache.set("key1", "value1")

    cache.get("key1")  # 命中
    cache.get("key1")  # 命中
    cache.get("key2")  # 未命中

    assert cache.hits == 2, f"期望 hits=2，得到 {cache.hits}"
    assert cache.misses == 1, f"期望 misses=1，得到 {cache.misses}"
    print(f"  ✓ 命中: {cache.hits}, 未命中: {cache.misses}")

    # 4. 测试TTL过期
    print("\n[4] 测试TTL过期")
    cache.set("key_expire", "value", ttl_minutes=0.01)  # 0.6秒过期
    time.sleep(1)  # 等待过期

    result = cache.get("key_expire")
    assert result is None, f"期望 None（已过期），得到 {result}"
    print(f"  ✓ 缓存过期后返回None")

    # 5. 测试delete
    print("\n[5] 测试delete")
    cache.set("key_delete", "value")
    cache.delete("key_delete")
    result = cache.get("key_delete")
    assert result is None, f"期望 None（已删除），得到 {result}"
    print(f"  ✓ delete功能正常")

    # 6. 测试clear
    print("\n[6] 测试clear")
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.clear()

    assert cache.hits == 0 and cache.misses == 0
    print(f"  ✓ clear功能正常（hits={cache.hits}, misses={cache.misses}）")

    print("\n✓ 缓存基本功能测试通过！")
    return True


def test_cache_performance():
    """测试缓存性能提升"""
    print("\n" + "=" * 60)
    print("测试缓存性能提升")
    print("=" * 60)

    cache = DataCache(default_ttl_minutes=5)

    # 模拟数据获取函数（耗时操作）
    def expensive_operation(key: str) -> str:
        """模拟耗时操作"""
        time.sleep(1)  # 模拟耗时1秒
        return f"data_{key}"

    # 1. 第一次调用（缓存未命中）
    print("\n[1] 第一次调用（缓存未命中）")
    start_time = time.time()
    key = "test_key"
    result = cache.get(key)
    if result is None:
        result = expensive_operation(key)
        cache.set(key, result)
    first_call_time = time.time() - start_time
    print(f"  ✓ 耗时: {first_call_time:.2f}秒（未命中缓存）")

    # 2. 第二次调用（缓存命中）
    print("\n[2] 第二次调用（缓存命中）")
    start_time = time.time()
    result = cache.get(key)
    if result is None:
        result = expensive_operation(key)
        cache.set(key, result)
    second_call_time = time.time() - start_time
    print(f"  ✓ 耗时: {second_call_time:.2f}秒（命中缓存）")

    # 3. 计算性能提升
    print("\n[3] 性能对比")
    time_saved = first_call_time - second_call_time
    speedup = first_call_time / second_call_time if second_call_time > 0 else 0

    print(f"  - 第一次调用: {first_call_time:.4f}秒")
    print(f"  - 第二次调用: {second_call_time:.4f}秒")
    print(f"  - 节省时间: {time_saved:.4f}秒")
    print(f"  - 性能提升: {speedup:.1f}x")

    assert second_call_time < first_call_time, "缓存应该提升性能"
    print(f"\n✓ 缓存性能提升测试通过！")

    return {
        "first_call_time": first_call_time,
        "second_call_time": second_call_time,
        "time_saved": time_saved,
        "speedup": speedup
    }


def test_cache_hit_rate():
    """测试缓存命中率"""
    print("\n" + "=" * 60)
    print("测试缓存命中率")
    print("=" * 60)

    cache = DataCache(default_ttl_minutes=5)

    # 模拟多次访问
    keys = ["key1", "key2", "key3", "key1", "key2", "key1", "key4", "key1", "key2", "key1"]

    # 首次加载（全部未命中）
    print("\n[1] 首次加载")
    for key in keys:
        if cache.get(key) is None:
            cache.set(key, f"value_{key}")

    initial_misses = cache.misses
    print(f"  ✓ 初始化缓存，未命中: {initial_misses}次")

    # 再次访问（部分命中）
    print("\n[2] 再次访问")
    cache.clear()
    cache.misses = 0
    cache.hits = 0

    # 预先加载部分数据
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")

    # 访问
    for key in keys:
        cache.get(key)

    total_requests = cache.hits + cache.misses
    hit_rate = (cache.hits / total_requests * 100) if total_requests > 0 else 0

    print(f"  ✓ 总请求: {total_requests}")
    print(f"  ✓ 命中: {cache.hits}")
    print(f"  ✓ 未命中: {cache.misses}")
    print(f"  ✓ 命中率: {hit_rate:.1f}%")

    # 保存报告
    report = {
        "total_requests": total_requests,
        "hits": cache.hits,
        "misses": cache.misses,
        "hit_rate": hit_rate
    }

    print(f"\n✓ 缓存命中率测试通过！")

    return report


def test_cache_with_json():
    """测试缓存JSON数据"""
    print("\n" + "=" * 60)
    print("测试缓存JSON数据")
    print("=" * 60)

    cache = DataCache(default_ttl_minutes=5)

    # 1. 缓存简单JSON
    print("\n[1] 缓存简单JSON")
    simple_data = {"status": "success", "price": 77149.39}
    cache.set("simple", simple_data)
    result = cache.get("simple")
    assert result == simple_data
    print(f"  ✓ 简单JSON缓存成功")

    # 2. 缓存复杂JSON
    print("\n[2] 缓存复杂JSON")
    complex_data = {
        "status": "success",
        "fractals": {"total_count": 30, "top_count": 14},
        "bis": {"total_count": 14, "up_count": 6},
        "segments": [{"direction": "up", "price": 72000}, {"direction": "down", "price": 68000}]
    }
    cache.set("complex", complex_data)
    result = cache.get("complex")
    assert result == complex_data
    print(f"  ✓ 复杂JSON缓存成功")

    # 3. 缓存列表
    print("\n[3] 缓存列表")
    list_data = [{"id": 1, "name": "item1"}, {"id": 2, "name": "item2"}]
    cache.set("list", list_data)
    result = cache.get("list")
    assert result == list_data
    print(f"  ✓ 列表缓存成功")

    print(f"\n✓ JSON缓存测试通过！")

    return True


def run_all_cache_tests():
    """运行所有缓存测试"""
    print("=" * 60)
    print("缓存机制完整测试")
    print("=" * 60)

    results = {}

    try:
        # 1. 基本功能测试
        results['basic'] = test_cache_basic()

        # 2. 性能测试
        results['performance'] = test_cache_performance()

        # 3. 命中率测试
        results['hit_rate'] = test_cache_hit_rate()

        # 4. JSON测试
        results['json'] = test_cache_with_json()

        # 总结
        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)

        print(f"\n测试结果:")
        print(f"  ✓ 基本功能: 通过")
        print(f"  ✓ 性能提升: 通过 (加速 {results['performance']['speedup']:.1f}x)")
        print(f"  ✓ 命中率: 通过 ({results['hit_rate']['hit_rate']:.1f}%)")
        print(f"  ✓ JSON缓存: 通过")

        # 保存完整报告
        import json
        report_file = "/workspace/projects/data/cache_test_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n完整报告已保存到: {report_file}")

        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_cache_tests()

    if success:
        print("\n✓ 所有缓存测试通过！")
    else:
        print("\n✗ 缓存测试失败！")

    sys.exit(0 if success else 1)
