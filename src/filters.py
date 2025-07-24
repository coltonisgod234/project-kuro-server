def parse_in_param(param):
    # e.g. "a,b,c" -> ['a', 'b', 'c']
    return [x.strip() for x in param.split(',')] if param else []

OPS = {
    # number
    "eq": lambda col, val: col == val,
    "ne": lambda col, val: col != val,
    "lt": lambda col, val: col < val,
    "lte": lambda col, val: col <= val,
    "gt": lambda col, val: col > val,
    "gte": lambda col, val: col >= val,

    # string
    "in": lambda col, val: col.in_(parse_in_param(val)),
    "ni": lambda col, val: ~col.in_(parse_in_param(val)),
    "re": lambda col, val: col.regexp_match(val),
    "like": lambda col, val: col.like(val)
}

STRING_OPS_SUBSET = [
    "re",
    "in",
    "ni",
    "like"
]

STIRNG_OPS = {k: v for k, v in OPS.items() if k in STRING_OPS_SUBSET}

def comparision(query, col, val, op):
    query = query.filter(
        OPS[op](col, val)
    )
    return query

def comparisons(prefix, query, data, col, cst=int, ops=OPS):
    for op in ops.keys():
        try:
            d = data[f"{prefix}_{op}"]
            if cst: d = cst(d)
            if d: query = comparision(query, col, d, op)
        except (ValueError, TypeError, KeyError):
            continue
    return query
