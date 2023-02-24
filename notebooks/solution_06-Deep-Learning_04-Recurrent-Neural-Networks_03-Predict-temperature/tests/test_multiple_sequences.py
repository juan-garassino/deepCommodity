from nbresult import ChallengeResultTestCase

N_TRAIN = 6666
N_TEST = 3333

INPUT_LENGTH = 8 * 14   # records every 3 hours x 8 = 24 hours
                        # two weeks
N_FEATURES = 19

OUTPUT_LENGTH = 1  # predicting the weather in the next 3 hours (next timestep)
N_TARGETS = 1  # predicting only the temperature


class TestMultipleSequences(ChallengeResultTestCase):

    def test_variable_x_train_shape(self):
        self.assertEqual(self.result.x_train_shape,
                         (N_TRAIN, INPUT_LENGTH, N_FEATURES))

    def test_variable_y_train_shape(self):
        self.assertEqual(self.result.y_train_shape,
                         (N_TRAIN, OUTPUT_LENGTH, N_TARGETS))

    def test_variable_x_test_i_shape(self):
        self.assertEqual(self.result.x_test_shape,
                         (N_TEST, INPUT_LENGTH, N_FEATURES))

    def test_variable_y_test_i_shape(self):
        self.assertEqual(self.result.y_test_shape,
                         (N_TEST, OUTPUT_LENGTH, N_TARGETS))
