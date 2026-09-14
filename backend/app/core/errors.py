class AppError(Exception):
    code = "INTERNAL_ERROR"
    safe_message = "服务暂时不可用，请稍后重试。"
    status_code = 500
    retryable = True

    def __init__(self, detail: str | None = None):
        super().__init__(detail or self.safe_message)
        self.detail = detail


class SpaceNotFoundError(AppError):
    code = "SPACE_NOT_FOUND"
    safe_message = "没有找到这个学习主题。"
    status_code = 404
    retryable = False


class AnalysisInProgressError(AppError):
    code = "ANALYSIS_IN_PROGRESS"
    safe_message = "这个主题正在分析，请不要重复提交。"
    status_code = 409


class AnalysisNotReadyError(AppError):
    code = "ANALYSIS_NOT_READY"
    safe_message = "请先完成主题分析。"
    status_code = 409
    retryable = False


class QuizNotFoundError(AppError):
    code = "QUIZ_NOT_FOUND"
    safe_message = "没有找到这道测验。"
    status_code = 404
    retryable = False


class ContentUnavailableError(AppError):
    code = "CONTENT_UNAVAILABLE"
    safe_message = "暂时没有找到足够的学习来源。"
    status_code = 503


class ContentProviderError(AppError):
    code = "CONTENT_PROVIDER_ERROR"
    safe_message = "内容服务暂时不可用。"
    status_code = 503


class LLMTimeoutError(AppError):
    code = "LLM_TIMEOUT"
    safe_message = "AI 分析超时，请重新尝试。"
    status_code = 504


class LLMInvalidOutputError(AppError):
    code = "LLM_INVALID_JSON"
    safe_message = "AI 返回格式异常，请重新尝试。"
    status_code = 502


class LLMProviderError(AppError):
    code = "LLM_PROVIDER_ERROR"
    safe_message = "AI 服务暂时不可用。"
    status_code = 502


class RepositoryError(AppError):
    code = "DATABASE_ERROR"
    safe_message = "保存结果失败，请稍后重试。"
    status_code = 503


def safe_message_for(exc: Exception) -> str:
    if isinstance(exc, AppError):
        return exc.safe_message
    return AppError.safe_message

