import dataclasses
import datetime
import decimal
from enum import Enum, Flag, IntFlag, auto

import pydantic
import pytest
from returns.result import Failure, Success

from codeflash.verification.comparator import comparator
from codeflash.verification.equivalence import compare_test_results
from codeflash.verification.test_results import (
    FunctionTestInvocation,
    InvocationId,
    TestResults,
    TestType,
)


def test_basic_python_objects():
    a = 5
    b = 5
    c = 6
    d = None
    assert comparator(a, b)
    assert not comparator(a, c)
    assert not comparator(a, d)

    a = 5.0
    b = 5.0
    c = 6.0
    d = None
    e = None
    assert comparator(a, b)
    assert not comparator(a, c)
    assert not comparator(a, d)
    assert not comparator(d, a)
    assert comparator(d, e)

    a = "Hello"
    b = "Hello"
    c = "World"
    assert comparator(a, b)
    assert not comparator(a, c)

    a = [1, 2, 3]
    b = [1, 2, 3]
    c = [1, 2, 4]
    assert comparator(a, b)
    assert not comparator(a, c)

    a = {"a": 1, "b": 2}
    b = {"a": 1, "b": 2}
    c = {"a": 1, "b": 3}
    d = {"c": 1, "b": 2}
    e = {"a": 1, "b": 2, "c": 3}
    assert comparator(a, b)
    assert not comparator(a, c)
    assert not comparator(a, d)
    assert not comparator(a, e)

    a = (1, 2, "str")
    b = (1, 2, "str")
    c = (1, 2, "str2")
    d = [1, 2, "str"]
    assert comparator(a, b)
    assert not comparator(a, c)
    assert not comparator(a, d)

    a = {1, 2, 3}
    b = {2, 3, 1}
    c = {1, 2, 4}
    d = {1, 2, 3, 4}
    assert comparator(a, b)
    assert not comparator(a, c)
    assert not comparator(a, d)

    a = (65).to_bytes(1, byteorder="big")
    b = (65).to_bytes(1, byteorder="big")
    c = (66).to_bytes(1, byteorder="big")
    assert comparator(a, b)
    assert not comparator(a, c)
    a = (65).to_bytes(2, byteorder="little")
    b = (65).to_bytes(2, byteorder="big")
    assert not comparator(a, b)

    a = bytearray([65, 64, 63])
    b = bytearray([65, 64, 63])
    c = bytearray([65, 64, 62])
    assert comparator(a, b)
    assert not comparator(a, c)

    memoryview_a = memoryview(bytearray([65, 64, 63]))
    memoryview_b = memoryview(bytearray([65, 64, 63]))
    memoryview_c = memoryview(bytearray([65, 64, 62]))
    assert comparator(memoryview_a, memoryview_b)
    assert not comparator(memoryview_a, memoryview_c)

    a = frozenset([1, 2, 3])
    b = frozenset([2, 3, 1])
    c = frozenset([1, 2, 4])
    d = frozenset([1, 2, 3, 4])
    assert comparator(a, b)
    assert not comparator(a, c)
    assert not comparator(a, d)

    a = map
    b = pow
    c = pow
    d = abs
    assert comparator(b, c)
    assert not comparator(a, b)
    assert not comparator(c, d)

    a = object()
    b = object()
    c = abs
    assert comparator(a, b)
    assert not comparator(a, c)

    a = type([])
    b = type([])
    c = type({})
    assert comparator(a, b)
    assert not comparator(a, c)


def test_standard_python_library_objects():
    a = datetime.datetime(2020, 2, 2, 2, 2, 2)
    b = datetime.datetime(2020, 2, 2, 2, 2, 2)
    c = datetime.datetime(2020, 2, 2, 2, 2, 3)
    assert comparator(a, b)
    assert not comparator(a, c)

    a = datetime.date(2020, 2, 2)
    b = datetime.date(2020, 2, 2)
    c = datetime.date(2020, 2, 3)
    assert comparator(a, b)
    assert not comparator(a, c)

    a = datetime.timedelta(days=1)
    b = datetime.timedelta(days=1)
    c = datetime.timedelta(days=2)
    assert comparator(a, b)
    assert not comparator(a, c)

    a = datetime.time(2, 2, 2)
    b = datetime.time(2, 2, 2)
    c = datetime.time(2, 2, 3)
    assert comparator(a, b)
    assert not comparator(a, c)

    a = datetime.timezone.utc
    b = datetime.timezone.utc
    c = datetime.timezone(datetime.timedelta(hours=1))
    assert comparator(a, b)
    assert not comparator(a, c)

    a = decimal.Decimal(3.14)
    b = decimal.Decimal(3.14)
    c = decimal.Decimal(3.15)
    assert comparator(a, b)
    assert not comparator(a, c)

    class Color(Flag):
        RED = auto()
        GREEN = auto()
        BLUE = auto()

    class Color2(Enum):
        RED = auto()
        GREEN = auto()
        BLUE = auto()

    a = Color.RED
    b = Color.RED
    c = Color.GREEN
    assert comparator(a, b)
    assert not comparator(a, c)

    a = Color2.RED
    b = Color2.RED
    c = Color2.GREEN
    assert comparator(a, b)
    assert not comparator(a, c)

    class Color4(IntFlag):
        RED = auto()
        GREEN = auto()
        BLUE = auto()

    a = Color4.RED
    b = Color4.RED
    c = Color4.GREEN
    assert comparator(a, b)
    assert not comparator(a, c)


def test_numpy():
    try:
        import numpy as np
    except ImportError:
        pytest.skip()
    a = np.array([1, 2, 3])
    b = np.array([1, 2, 3])
    c = np.array([1, 2, 4])
    assert comparator(a, b)
    assert not comparator(a, c)

    d = np.array([[1, 2], [3, 4]])
    e = np.array([[1, 2], [3, 4]])
    f = np.array([[1, 2], [3, 5]])
    assert comparator(d, e)
    assert not comparator(d, f)
    assert not comparator(a, d)

    g = np.array([1.0, 2.0, 3.0])
    assert not comparator(a, g)

    h = np.float32(1.0)
    i = np.float32(1.0)
    assert comparator(h, i)

    j = np.float64(1.0)
    k = np.float64(1.0)
    assert not comparator(h, j)
    print(comparator(j, k))
    assert comparator(j, k)

    l = np.int32(1)
    m = np.int32(1)
    assert comparator(l, m)
    assert not comparator(l, h)
    assert not comparator(l, j)

    n = np.int64(1)
    o = np.int64(1)
    assert not comparator(n, l)
    assert comparator(n, o)

    p = np.uint32(1)
    q = np.uint32(1)
    assert comparator(p, q)
    assert not comparator(p, l)

    r = np.uint64(1)
    s = np.uint64(1)
    assert not comparator(r, p)
    assert comparator(r, s)

    t = np.bool_(True)
    u = np.bool_(True)
    assert comparator(t, u)
    assert not comparator(t, r)

    v = np.complex64(1.0 + 1.0j)
    w = np.complex64(1.0 + 1.0j)
    assert comparator(v, w)
    assert not comparator(v, t)

    x = np.complex128(1.0 + 1.0j)
    y = np.complex128(1.0 + 1.0j)
    assert not comparator(x, v)
    assert comparator(x, y)

    # Create numpy array with mixed type object
    z = np.array([1, 2, "str"], dtype=np.object_)
    aa = np.array([1, 2, "str"], dtype=np.object_)
    ab = np.array([1, 2, "str2"], dtype=np.object_)
    assert comparator(z, aa)
    assert not comparator(z, ab)

    ac = np.array([1, 2, "str2"])
    ad = np.array([1, 2, "str2"])
    assert comparator(ac, ad)

    # Test for numpy array with nan and inf
    ae = np.array([1, 2, np.nan])
    af = np.array([1, 2, np.nan])
    ag = np.array([1, 2, np.inf])
    ah = np.array([1, 2, np.inf])
    ai = np.inf
    aj = np.inf
    ak = np.nan
    al = np.nan
    assert comparator(ae, af)
    assert comparator(ag, ah)
    assert not comparator(ae, ag)
    assert not comparator(af, ah)
    assert comparator(ai, aj)
    assert comparator(ak, al)
    assert not comparator(ai, ak)


def test_scipy():
    try:
        import scipy as sp
    except ImportError:
        pytest.skip()
    a = sp.sparse.csr_matrix([[1, 0, 0], [0, 0, 3], [4, 0, 5]])
    b = sp.sparse.csr_matrix([[1, 0, 0], [0, 0, 3], [4, 0, 5]])
    c = sp.sparse.csr_matrix([[1, 0, 0], [0, 0, 3], [4, 0, 6]])
    ca = sp.sparse.csr_matrix([[1, 0, 0, 0], [0, 0, 3, 0], [4, 0, 6, 0]])
    assert comparator(a, b)
    assert not comparator(a, c)
    assert not comparator(c, ca)

    d = sp.sparse.csc_matrix([[1, 0, 0], [0, 0, 3], [4, 0, 5]])
    e = sp.sparse.csc_matrix([[1, 0, 0], [0, 0, 3], [4, 0, 5]])
    f = sp.sparse.csc_matrix([[1, 0, 0], [0, 0, 3], [4, 0, 6]])
    fa = sp.sparse.csc_matrix([[1, 0, 0, 0], [0, 0, 3, 0], [4, 0, 6, 0]])
    assert comparator(d, e)
    assert not comparator(d, f)
    assert not comparator(a, d)
    assert not comparator(c, f)
    assert not comparator(f, fa)

    g = sp.sparse.lil_matrix([[1, 0, 0], [0, 0, 3], [4, 0, 5]])
    h = sp.sparse.lil_matrix([[1, 0, 0], [0, 0, 3], [4, 0, 5]])
    i = sp.sparse.lil_matrix([[1, 0, 0], [0, 0, 3], [4, 0, 6]])
    assert comparator(g, h)
    assert not comparator(g, i)
    assert not comparator(a, g)

    j = sp.sparse.dok_matrix([[1, 0, 0], [0, 0, 3], [4, 0, 5]])
    k = sp.sparse.dok_matrix([[1, 0, 0], [0, 0, 3], [4, 0, 5]])
    l = sp.sparse.dok_matrix([[1, 0, 0], [0, 0, 3], [4, 0, 6]])
    assert comparator(j, k)
    assert not comparator(j, l)
    assert not comparator(a, j)

    m = sp.sparse.dia_matrix([[1, 0, 0], [0, 0, 3], [4, 0, 5]])
    n = sp.sparse.dia_matrix([[1, 0, 0], [0, 0, 3], [4, 0, 5]])
    o = sp.sparse.dia_matrix([[1, 0, 0], [0, 0, 3], [4, 0, 6]])
    assert comparator(m, n)
    assert not comparator(m, o)
    assert not comparator(a, m)

    p = sp.sparse.coo_matrix([[1, 0, 0], [0, 0, 3], [4, 0, 5]])
    q = sp.sparse.coo_matrix([[1, 0, 0], [0, 0, 3], [4, 0, 5]])
    r = sp.sparse.coo_matrix([[1, 0, 0], [0, 0, 3], [4, 0, 6]])
    assert comparator(p, q)
    assert not comparator(p, r)
    assert not comparator(a, p)

    s = sp.sparse.bsr_matrix([[1, 0, 0], [0, 0, 3], [4, 0, 5]])
    t = sp.sparse.bsr_matrix([[1, 0, 0], [0, 0, 3], [4, 0, 5]])
    u = sp.sparse.bsr_matrix([[1, 0, 0], [0, 0, 3], [4, 0, 6]])
    assert comparator(s, t)
    assert not comparator(s, u)
    assert not comparator(a, s)

    try:
        import numpy as np

        row = np.array([0, 3, 1, 0])
        col = np.array([0, 3, 1, 2])
        data = np.array([4, 5, 7, 9])
        v = sp.sparse.coo_array((data, (row, col)), shape=(4, 4)).toarray()
        w = sp.sparse.coo_array((data, (row, col)), shape=(4, 4)).toarray()
        assert comparator(v, w)
    except ImportError:
        print("Should run tests with numpy installed to test more thoroughly")


def test_pandas():
    try:
        import pandas as pd
    except ImportError:
        pytest.skip()
    a = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    b = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    c = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 7]})
    ca = pd.DataFrame({"a": [1, 2, 3, 4], "b": [4, 5, 6, 7]})
    assert comparator(a, b)
    assert not comparator(a, c)
    assert not comparator(c, ca)

    ak = pd.DataFrame(
        {
            "a": [datetime.datetime(2020, 2, 2, 2, 2, 2), datetime.datetime(2020, 2, 2, 2, 2, 2)],
            "b": [4, 5],
        },
    )
    al = pd.DataFrame(
        {
            "a": [datetime.datetime(2020, 2, 2, 2, 2, 2), datetime.datetime(2020, 2, 2, 2, 2, 2)],
            "b": [4, 5],
        },
    )
    am = pd.DataFrame(
        {
            "a": [datetime.datetime(2020, 2, 2, 2, 2, 2), datetime.datetime(2020, 2, 2, 2, 2, 3)],
            "b": [4, 5],
        },
    )
    assert comparator(ak, al)
    assert not comparator(ak, am)

    d = pd.Series([1, 2, 3])
    e = pd.Series([1, 2, 3])
    f = pd.Series([1, 2, 4])
    assert comparator(d, e)
    assert not comparator(d, f)

    g = pd.Index([1, 2, 3])
    h = pd.Index([1, 2, 3])
    i = pd.Index([1, 2, 4])
    assert comparator(g, h)
    assert not comparator(g, i)

    j = pd.MultiIndex.from_tuples([(1, 2), (3, 4)])
    k = pd.MultiIndex.from_tuples([(1, 2), (3, 4)])
    l = pd.MultiIndex.from_tuples([(1, 2), (3, 5)])
    assert comparator(j, k)
    assert not comparator(j, l)

    m = pd.Categorical([1, 2, 3])
    n = pd.Categorical([1, 2, 3])
    o = pd.Categorical([1, 2, 4])
    assert comparator(m, n)
    assert not comparator(m, o)

    p = pd.Interval(1, 2)
    q = pd.Interval(1, 2)
    r = pd.Interval(1, 3)
    assert comparator(p, q)
    assert not comparator(p, r)

    s = pd.IntervalIndex.from_tuples([(1, 2), (3, 4)])
    t = pd.IntervalIndex.from_tuples([(1, 2), (3, 4)])
    u = pd.IntervalIndex.from_tuples([(1, 2), (3, 5)])
    assert comparator(s, t)
    assert not comparator(s, u)

    v = pd.Period("2021-01")
    w = pd.Period("2021-01")
    x = pd.Period("2021-02")
    assert comparator(v, w)
    assert not comparator(v, x)

    y = pd.period_range(start="2021-01", periods=3, freq="M")
    z = pd.period_range(start="2021-01", periods=3, freq="M")
    aa = pd.period_range(start="2021-01", periods=4, freq="M")
    assert comparator(y, z)
    assert not comparator(y, aa)

    ab = pd.Timedelta("1 days")
    ac = pd.Timedelta("1 days")
    ad = pd.Timedelta("2 days")
    assert comparator(ab, ac)
    assert not comparator(ab, ad)

    ae = pd.TimedeltaIndex(["1 days", "2 days"])
    af = pd.TimedeltaIndex(["1 days", "2 days"])
    ag = pd.TimedeltaIndex(["1 days", "3 days"])
    assert comparator(ae, af)
    assert not comparator(ae, ag)

    ah = pd.Timestamp("2021-01-01")
    ai = pd.Timestamp("2021-01-01")
    aj = pd.Timestamp("2021-01-02")
    assert comparator(ah, ai)
    assert not comparator(ah, aj)

    # test cases for sparse pandas arrays
    an = pd.arrays.SparseArray([1, 2, 3])
    ao = pd.arrays.SparseArray([1, 2, 3])
    ap = pd.arrays.SparseArray([1, 2, 4])
    assert comparator(an, ao)
    assert not comparator(an, ap)


def test_pyrsistent():
    try:
        from pyrsistent import PBag, PClass, PRecord, field, pdeque, pmap, pset, pvector
    except ImportError:
        pytest.skip()

    a = pmap({"a": 1, "b": 2})
    b = pmap({"a": 1, "b": 2})
    c = pmap({"a": 1, "b": 3})
    assert comparator(a, b)
    assert not comparator(a, c)

    d = pvector([1, 2, 3])
    e = pvector([1, 2, 3])
    f = pvector([1, 2, 4])
    assert comparator(d, e)
    assert not comparator(d, f)

    g = pset([1, 2, 3])
    h = pset([2, 3, 1])
    i = pset([1, 2, 4])
    assert comparator(g, h)
    assert not comparator(g, i)

    class TestRecord(PRecord):
        a = field()
        b = field()

    j = TestRecord()
    k = TestRecord()
    l = TestRecord(a=2, b=3)
    assert comparator(j, k)
    assert not comparator(j, l)

    class TestClass(PClass):
        a = field()
        b = field()

    m = TestClass()
    n = TestClass()
    o = TestClass(a=1, b=3)
    assert comparator(m, n)
    assert not comparator(m, o)

    p = pdeque([1, 2, 3], 3)
    q = pdeque([1, 2, 3], 3)
    r = pdeque([1, 2, 4], 3)
    assert comparator(p, q)
    assert not comparator(p, r)

    s = PBag([1, 2, 3])
    t = PBag([1, 2, 3])
    u = PBag([1, 2, 4])
    assert comparator(s, t)
    assert not comparator(s, u)

    v = pvector([1, 2, 3])
    w = pvector([1, 2, 3])
    x = pvector([1, 2, 4])
    assert comparator(v, w)
    assert not comparator(v, x)


def test_returns():
    a = Success(5)
    b = Success(5)
    c = Success(6)
    d = Failure(5)
    e = Success((5, 5))
    f = Success((5, 6))
    assert comparator(a, b)
    assert not comparator(a, c)
    assert not comparator(a, d)
    assert not comparator(a, e)
    assert not comparator(e, f)

    g = Success((5, 5))
    h = Success((5, 5))
    i = Success((5, 6))
    assert comparator(g, h)
    assert not comparator(g, i)


def test_custom_object():
    class TestClass:
        def __init__(self, value):
            self.value = value

        def __eq__(self, other):
            return self.value == other.value

    a = TestClass(5)
    b = TestClass(5)
    c = TestClass(6)
    assert comparator(a, b)
    assert not comparator(a, c)

    class TestClass2:
        def __init__(self, value1, value2=6):
            self.value1 = value1
            self.value2 = value2

    a = TestClass(5)
    b = TestClass2(5, 6)
    c = TestClass2(5, 7)
    d = TestClass2(5, 6)
    assert not comparator(a, b)
    assert not comparator(b, c)
    assert comparator(b, d)

    class TestClass3(TestClass):
        def print(self):
            print(self.value)

    a = TestClass2(5)
    b = TestClass3(5)
    c = TestClass3(5)
    assert not comparator(a, b)
    assert comparator(b, c)

    @dataclasses.dataclass
    class InventoryItem:
        """Class for keeping track of an item in inventory."""

        name: str
        unit_price: float
        quantity_on_hand: int = 0

        def total_cost(self) -> float:
            return self.unit_price * self.quantity_on_hand

    a = InventoryItem(name="widget", unit_price=3.0, quantity_on_hand=10)
    b = InventoryItem(name="widget", unit_price=3.0, quantity_on_hand=10)
    c = InventoryItem(name="widget", unit_price=3.0, quantity_on_hand=11)

    assert comparator(a, b)
    assert not comparator(a, c)

    @pydantic.dataclasses.dataclass
    class InventoryItemPydantic:
        """Class for keeping track of an item in inventory."""

        name: str
        unit_price: float
        quantity_on_hand: int = 0

        def total_cost(self) -> float:
            return self.unit_price * self.quantity_on_hand

    a = InventoryItemPydantic(name="widget", unit_price=3.0, quantity_on_hand=10)
    b = InventoryItemPydantic(name="widget", unit_price=3.0, quantity_on_hand=10)
    c = InventoryItemPydantic(name="widget", unit_price=3.0, quantity_on_hand=11)
    assert comparator(a, b)
    assert not comparator(a, c)

    class InventoryItemBasePydantic(pydantic.BaseModel):
        name: str
        unit_price: float
        quantity_on_hand: int = 0

        def total_cost(self) -> float:
            return self.unit_price * self.quantity_on_hand

    a = InventoryItemBasePydantic(name="widget", unit_price=3.0, quantity_on_hand=10)
    b = InventoryItemBasePydantic(name="widget", unit_price=3.0, quantity_on_hand=10)
    c = InventoryItemBasePydantic(name="widget", unit_price=3.0, quantity_on_hand=11)
    assert comparator(a, b)
    assert not comparator(a, c)

    class A:
        items = [1, 2, 3]
        val = 5

    class B:
        items = [1, 2, 4]
        val = 5

    assert comparator(A, A)
    assert not comparator(A, B)

    class C:
        items = [1, 2, 3]
        val = 5

        def __init__(self):
            self.itemm2 = [1, 2, 3]
            self.val2 = 5

    class D:
        items = [1, 2, 3]
        val = 5

        def __init__(self):
            self.itemm2 = [1, 2, 4]
            self.val2 = 5

    assert comparator(C, C)
    assert not comparator(C, D)

    E = C
    assert comparator(C, E)


def test_compare_results_fn():
    original_results = TestResults(
        test_results=[
            FunctionTestInvocation(
                id=InvocationId(
                    test_module_path="test_module_path",
                    test_class_name="test_class_name",
                    test_function_name="test_function_name",
                    function_getting_tested="function_getting_tested",
                    iteration_id="0",
                ),
                file_name="file_name",
                did_pass=True,
                runtime=5,
                test_framework="unittest",
                test_type=TestType.EXISTING_UNIT_TEST,
                return_value=5,
                timed_out=False,
                loop_index=1,
            ),
        ],
    )

    new_results_1 = TestResults(
        test_results=[
            FunctionTestInvocation(
                id=InvocationId(
                    test_module_path="test_module_path",
                    test_class_name="test_class_name",
                    test_function_name="test_function_name",
                    function_getting_tested="function_getting_tested",
                    iteration_id="0",
                ),
                file_name="file_name",
                did_pass=True,
                runtime=10,
                test_framework="unittest",
                test_type=TestType.EXISTING_UNIT_TEST,
                return_value=5,
                timed_out=False,
                loop_index=1,
            ),
        ],
    )

    assert compare_test_results(original_results, new_results_1)

    new_results_2 = TestResults(
        test_results=[
            FunctionTestInvocation(
                id=InvocationId(
                    test_module_path="test_module_path",
                    test_class_name="test_class_name",
                    test_function_name="test_function_name",
                    function_getting_tested="function_getting_tested",
                    iteration_id="0",
                ),
                file_name="file_name",
                did_pass=True,
                runtime=10,
                test_framework="unittest",
                test_type=TestType.EXISTING_UNIT_TEST,
                return_value=[5],
                timed_out=False,
                loop_index=1,
            ),
        ],
    )

    assert not compare_test_results(original_results, new_results_2)

    new_results_3 = TestResults(
        test_results=[
            FunctionTestInvocation(
                id=InvocationId(
                    test_module_path="test_module_path",
                    test_class_name="test_class_name",
                    test_function_name="test_function_name",
                    function_getting_tested="function_getting_tested",
                    iteration_id="0",
                ),
                file_name="file_name",
                did_pass=True,
                runtime=10,
                test_framework="unittest",
                test_type=TestType.EXISTING_UNIT_TEST,
                return_value=5,
                timed_out=False,
                loop_index=1,
            ),
            FunctionTestInvocation(
                id=InvocationId(
                    test_module_path="test_module_path",
                    test_class_name="test_class_name",
                    test_function_name="test_function_name",
                    function_getting_tested="function_getting_tested",
                    iteration_id="2",
                ),
                file_name="file_name",
                did_pass=True,
                runtime=10,
                test_framework="unittest",
                test_type=TestType.EXISTING_UNIT_TEST,
                return_value=5,
                timed_out=False,
                loop_index=1,
            ),
        ],
    )

    assert compare_test_results(original_results, new_results_3)

    assert not compare_test_results(TestResults(), TestResults())
