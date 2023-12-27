from __future__ import print_function          # PY3
""" test_dummy shows the most useful options within the nose test framework

requires Python V2.6 or higher
"""
# from io import StringIO  to use in Python 3 when strings are unicode
from io import StringIO
from contextlib import contextmanager
import time,sys
from adapya.base.dump import dump
from difflib import context_diff

# from nose.tools import assert_raises, raises, timed, assert_almost_equal
import pytest

# used in test_stdout()
stdout_expected="""
1.line
2.line somewhat looooonger
3.line is the last
""".strip()

#def setup():
def setup_module():
    print('-- setup() called in %s --' % __name__)

#def teardown():
def teardown_module():
    print('-- teardown() called %s --' % __name__)

def test_to_succeed():
    print('-- starting test_to_succeed() --')
    assert 'c' == 'c', 'test will succeed'
    print('-- ending after success --')

def test_to_fail():
    print('-- starting test_to_fail() --')
    assert 'b' == 'c', 'test will fail'
    print('-- ending not printed after failure --')

def test_to_raise():
    print('-- starting test_to_raise() --')

    #nose assert_raises(ZeroDivisionError,int.__div__,10,0)
    #nose assert_raises(ValueError,int,'this is no number')
    with pytest.raises(ZeroDivisionError):
        10/0
    with pytest.raises(ValueError):
        int('this is no number')

    print('-- ending after successful raise --')

def test_to_raise_none_of_2():
    print('-- starting test_to_raise_none_of_2() --')

    # assert_raises(ZeroDivisionError,int.__div__,10,2)
    with pytest.raises(ZeroDivisionError):
        10/2

    print('-- ending not printed after no raise occurred --')
    with pytest.raises(ValueError):
        int('100')

def print3lines(out=sys.stdout):
    """ called in test_stdout() """
    print('1.line', file=out)
    print('2.line somewhat longer', file=out)
    print('3.line is the last', file=out)

def test_stdout():
    print('-- starting test_stdout() --')

    out = StringIO()
    print3lines(out=out)
    output = out.getvalue().strip()

    assert output == stdout_expected

    print('-- ending test_stdout() --')


def print3lines2():
    """ called in test_stdout() """
    print('1.line')
    print('2.line somewhat longer')
    print('3.line is the last')


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err

def test_stdout_ctx():
    print('-- starting test_stdout_ctx() with context manager --')

    with captured_output() as (out, err):
        #note: cannot use print3lines since it uses sys.stdout as default from definition time
        print3lines2()

    # This can go inside or outside the `with` block
    output = out.getvalue().strip()

    print('output:\n', output)
    dump(output)
    print('output expected:\n', stdout_expected)
    dump(stdout_expected)

    for line in context_diff(output.split('\n'),stdout_expected.split('\n'),'output','expected'):
        print(line)

    assert output == stdout_expected

    print('-- ending test_stdout_ctx() --')


def test_almost_equal():
    #nose assert_almost_equal(9999.12345678, 9999.2, 0)
    #nose assert_almost_equal(0.12345678, 0.12345671, 6)
    9999.12345678 == pytest.approx(9999.2), 'Value almost equal'
    0.12345678 == pytest.approx(0.12345671)

    print('-- next fails even though number same on the 7 digits behind')
    print('   -> set it to 6 to make it succeed')
    # assert_almost_equal(9999.12345678, 9999.12345671, 7)
    9999.12345678 == pytest.approx(9999.12345671, rel=1e-7)

#@timed(.1)
#@pytest.mark.timeout(.1, 'slow', method='thread')
#def test_that_exceeds_time_limit():
#    time.sleep(.2)
# pytest: prints warning

#@pytest.raises(TypeError)
#def test_raises_type_error():
#    raise TypeError("This test passes")

#@pytest.raises(Exception)
#def test_that_fails_by_passing():
#    pass
#pytest: TypeError 'RaisesContext' object is not callable

#def test_with_iteration():
#    """ Generate test cases with i ranging from 0 to 4
#        and call the 'checkeven' procedure
#    """
#    print('-- starting test_with_iteration() --')
#    for i in range(5):
#        yield checkeven, i


@pytest.mark.parametrize('i', [(i) for i in range(5)] )
def test_checkeven(i):
    print('-- checkeven(%d) --' % i)

    assert i%2 == 0, 'number i=%d is not even' % i
