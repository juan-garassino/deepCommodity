from nbresult import ChallengeResultTestCase

class TestHoldout(ChallengeResultTestCase):

    def test_variable_train_index_start(self):
        self.assertEqual(self.result.train_index_start, 0)


    def test_variable_train_index_stop(self):
        self.assertEqual(self.result.train_index_stop, 5782)

    def test_variable_test_index_start(self):
        self.assertEqual(self.result.test_index_start, 5670)

    def test_variable_test_index_stop(self):
        self.assertEqual(self.result.test_index_stop, 8760)
