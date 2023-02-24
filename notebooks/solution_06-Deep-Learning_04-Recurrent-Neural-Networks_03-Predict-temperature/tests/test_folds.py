from nbresult import ChallengeResultTestCase

FOLD_LENGTH = 8*365*3
N_FEATURES = 19

class TestFolds(ChallengeResultTestCase):

    def test_variable_number_of_folds(self):
        self.assertEqual(self.result.number_of_folds, 21)

    def test_variable_fold_shape(self):
        self.assertEqual(self.result.fold_shape, (FOLD_LENGTH, N_FEATURES))
