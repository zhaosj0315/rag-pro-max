
def disable_query_rewrite():
    """禁用查询改写，直接返回原查询"""
    return lambda query: query

# 替换查询改写函数
query_rewrite = disable_query_rewrite()
