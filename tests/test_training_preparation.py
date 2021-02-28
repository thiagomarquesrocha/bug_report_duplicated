import numpy as np
import pytest
from jobs.data_pipeline import DataPipeline
from deep_learning.training.training_preparation import TrainingPreparation

class TestTrainingPreparation:

    @pytest.fixture
    def eclipse_test_dataset(self):
        dataset = 'eclipse_test'
        domain = 'eclipse_test'
        COLAB = ''
        PREPROCESSING = 'bert'
        pipeline = DataPipeline(dataset, domain, COLAB, PREPROCESSING)
        pipeline.run()
        return pipeline

    def test_prepare_training_data_then_successful(self, eclipse_test_dataset):
        DOMAIN = 'eclipse_test'
        PREPROCESSING = 'bert'
        DIR = eclipse_test_dataset.DIR_OUTPUT
        TOKEN_END = 102
        MAX_SEQUENCE_LENGTH_T = 10
        MAX_SEQUENCE_LENGTH_D = 100
        train_preparation = TrainingPreparation(DIR, DOMAIN, 
                                        PREPROCESSING,
                                        MAX_SEQUENCE_LENGTH_T, 
                                        MAX_SEQUENCE_LENGTH_D,
                                        TOKEN_END)
        train_preparation.run()
        data = train_preparation.get_data()
        bug_id = np.random.choice(data.bug_ids, 1)[0]
        assert bug_id in data.bug_set 
        bug = data.bug_set[bug_id]
        assert 'bug_severity' in bug
        assert 'bug_status' in bug
        assert 'component' in bug
        assert 'creation_ts' in bug
        assert 'delta_ts' in bug
        assert 'description' in bug
        assert 'description_segment' in bug
        assert 'description_token' in bug
        assert 'dup_id' in bug
        assert 'issue_id' in bug
        assert 'priority' in bug
        assert 'product' in bug
        assert 'resolution' in bug
        assert 'textual_token' in bug
        assert 'title' in bug
        assert 'title_segment' in bug
        assert 'title_token' in bug
        assert 'version' in bug

    def test_prepare_training_data_then_successful(self, eclipse_test_dataset):
        DOMAIN = 'eclipse_test'
        PREPROCESSING = 'bert'
        DIR = eclipse_test_dataset.DIR_OUTPUT
        TOKEN_END = 102
        MAX_SEQUENCE_LENGTH_T = 10
        MAX_SEQUENCE_LENGTH_D = 100
        train_preparation = TrainingPreparation(DIR, DOMAIN, 
                                        PREPROCESSING,
                                        MAX_SEQUENCE_LENGTH_T, 
                                        MAX_SEQUENCE_LENGTH_D,
                                        TOKEN_END)
        train_preparation.run()
        data = train_preparation.get_data()
        bug_id = np.random.choice(data.bug_ids, 1)[0]
        assert bug_id in data.bug_set 
        bug = data.bug_set[bug_id]
        assert 'bug_severity' in bug
        assert 'bug_status' in bug
        assert 'component' in bug
        assert 'creation_ts' in bug
        assert 'delta_ts' in bug
        assert 'description' in bug
        assert 'description_segment' in bug
        assert 'description_token' in bug
        assert 'dup_id' in bug
        assert 'issue_id' in bug
        assert 'priority' in bug
        assert 'product' in bug
        assert 'resolution' in bug
        assert 'textual_token' in bug
        assert 'title' in bug
        assert 'title_segment' in bug
        assert 'title_token' in bug
        assert 'version' in bug