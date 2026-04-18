"""
异常处理和重试机制模块
"""
import time
import logging
from functools import wraps
from typing import Callable, Type, Tuple, Any, Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RetryException(Exception):
    """重试异常基类"""
    pass


class MaxRetriesExceededError(RetryException):
    """超过最大重试次数异常"""
    pass


def retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None
):
    """
    重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 初始延迟（秒）
        backoff_factor: 退避因子，每次重试延迟乘以这个因子
        exceptions: 需要重试的异常类型
        on_retry: 每次重试时的回调函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    # 如果达到最大重试次数
                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} 超过最大重试次数 ({max_retries})"
                        )
                        raise MaxRetriesExceededError(
                            f"{func.__name__} 在 {max_retries} 次重试后仍然失败"
                        ) from e

                    # 计算延迟
                    current_delay = delay * (backoff_factor ** attempt)
                    logger.warning(
                        f"{func.__name__} 第 {attempt + 1}/{max_retries} 次尝试失败: {e}. "
                        f"{current_delay:.2f}秒后重试..."
                    )

                    # 调用回调
                    if on_retry:
                        try:
                            on_retry(attempt + 1, e)
                        except Exception as callback_error:
                            logger.error(f"重试回调失败: {callback_error}")

                    # 等待
                    time.sleep(current_delay)

            # 不应该到达这里
            raise last_exception

        return wrapper
    return decorator


def safe_execute(
    func: Callable,
    default_value: Any = None,
    log_error: bool = True,
    reraise: bool = False
):
    """
    安全执行装饰器，捕获所有异常

    Args:
        func: 要执行的函数
        default_value: 异常时返回的默认值
        log_error: 是否记录错误
        reraise: 是否重新抛出异常
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if log_error:
                logger.error(f"{func.__name__} 执行失败: {e}", exc_info=True)
            if reraise:
                raise
            return default_value
    return wrapper


def timeout(seconds: float, timeout_message: Optional[str] = None):
    """
    超时装饰器

    Args:
        seconds: 超时时间（秒）
        timeout_message: 超时时的消息
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            import signal

            def _timeout_handler(signum, frame):
                raise TimeoutError(
                    timeout_message or f"{func.__name__} 执行超时（{seconds}秒）"
                )

            # 设置超时
            old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(int(seconds))

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # 取消超时
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)

        return wrapper
    return decorator


class ErrorHandler:
    """错误处理器"""

    @staticmethod
    def handle_network_error(e: Exception) -> str:
        """处理网络错误"""
        logger.error(f"网络错误: {e}")
        return {"error": "network_error", "message": str(e)}

    @staticmethod
    def handle_data_error(e: Exception) -> str:
        """处理数据错误"""
        logger.error(f"数据错误: {e}")
        return {"error": "data_error", "message": str(e)}

    @staticmethod
    def handle_api_error(e: Exception) -> str:
        """处理API错误"""
        logger.error(f"API错误: {e}")
        return {"error": "api_error", "message": str(e)}

    @staticmethod
    def handle_unknown_error(e: Exception) -> str:
        """处理未知错误"""
        logger.error(f"未知错误: {e}", exc_info=True)
        return {"error": "unknown_error", "message": str(e)}


# 便捷装饰器
def safe_with_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    default_value: Any = None,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    组合装饰器：先重试，失败后返回默认值

    Args:
        max_retries: 最大重试次数
        delay: 初始延迟
        default_value: 默认值
        exceptions: 需要重试的异常类型
    """
    def decorator(func: Callable) -> Callable:
        # 先应用重试
        retry_wrapper = retry(
            max_retries=max_retries,
            delay=delay,
            exceptions=exceptions
        )(func)

        # 再应用安全执行
        safe_wrapper = safe_execute(
            retry_wrapper,
            default_value=default_value,
            log_error=True,
            reraise=False
        )

        return safe_wrapper
    return decorator
