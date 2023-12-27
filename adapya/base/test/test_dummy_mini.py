def test_to_succeed():
    assert 'c' == 'c', 'test will succeed'

def test_to_fail():
    assert 'b' == 'c', 'test will fail'

def test_with_iteration():
    """ Generate test cases with i ranging from 0 to 4
        and call the 'checkeven' procedure
    """
    for i in range(5):
        yield checkeven, i

def checkeven(i):
    assert i%2 == 0, 'number i=%d is not even' % i
