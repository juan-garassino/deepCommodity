from nbresult import ChallengeResultTestCase

INPUT_LENGTH = 8 * 14   # records every 3 hours x 8 = 24 hours
                        # two weeks
N_FEATURES = 19

OUTPUT_LENGTH = 1 # predicting the weather in the next 3 hours (next timestep)
N_TARGETS = 1 # predicting only the temperature


class TestSequence(ChallengeResultTestCase):

    def test_variable_x_train_i_shape(self):
        self.assertEqual(self.result.x_train_i_shape, (INPUT_LENGTH, N_FEATURES))

    def test_variable_y_train_i_shape(self):
        self.assertEqual(self.result.y_train_i_shape,
                         (OUTPUT_LENGTH, N_TARGETS))

    def test_variable_x_test_i_shape(self):
        self.assertEqual(self.result.x_test_i_shape, (INPUT_LENGTH, N_FEATURES))

    def test_variable_y_test_i_shape(self):
        self.assertEqual(self.result.y_test_i_shape,
                         (OUTPUT_LENGTH, N_TARGETS))

