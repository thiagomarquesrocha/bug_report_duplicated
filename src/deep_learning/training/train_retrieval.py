from src.deep_learning.model.siameseTAT_model import SiameseTA, SiameseTAT
from src.deep_learning.model.siameseQAT_model import SiameseQA, SiameseQAT
from src.deep_learning.training.training_preparation import TrainingPreparation
from src.deep_learning.model.compile_model import compile_model, get_bug_encoder
from src.evaluation.retrieval import Retrieval
import math
import logging
import mlflow

logger = logging.getLogger('TrainRetrieval')

class TrainRetrieval():

    def __init__(self, MODEL_NAME, DIR, DOMAIN, PREPROCESSING, 
                MAX_SEQUENCE_LENGTH_T=10, MAX_SEQUENCE_LENGTH_D=100,
                TOPIC_LENGTH=30, BERT_LAYERS = 8, EPOCHS=10, 
                BATCH_SIZE=64, BATCH_SIZE_TEST=128):
        self.MODEL_NAME = MODEL_NAME
        self.EPOCHS = EPOCHS
        self.BATCH_SIZE = BATCH_SIZE
        # Test batch is composed by an anchor, pos and neg
        self.BATCH_SIZE_TEST = BATCH_SIZE_TEST
        self.DOMAIN = DOMAIN # eclipse, netbeans, openoffice
        self.PREPROCESSING = PREPROCESSING # bert, baseline or fake
        self.DIR = DIR
        self.TOKEN_END = 102 # TODO: Read from BERT pretrained
        self.TOPIC_LENGTH = TOPIC_LENGTH
        self.MAX_SEQUENCE_LENGTH_T = MAX_SEQUENCE_LENGTH_T
        self.MAX_SEQUENCE_LENGTH_D = MAX_SEQUENCE_LENGTH_D
        self.BERT_LAYERS = BERT_LAYERS # MAX 12 layers

    def build(self):
        self.prepare_data()
        self.prepare_validation_data()
        self.create_model(self.MODEL_NAME)
        return self

    def run(self):
        self.build()
        self.train_model()
        return self

    def create_model(self, model):
        logger.debug("Creating {} model...".format(model))
        if model == 'SiameseTA':
            self.model = SiameseTA(model_name=model, 
                        title_size=self.MAX_SEQUENCE_LENGTH_T, 
                        desc_size=self.MAX_SEQUENCE_LENGTH_D, 
                        categorical_size=self.MAX_LENGTH_CATEGORICAL,
                        number_of_BERT_layers=self.BERT_LAYERS)
        elif model == 'SiameseTAT':
            self.model = SiameseTAT(model_name=model, 
                        title_size=self.MAX_SEQUENCE_LENGTH_T, 
                        desc_size=self.MAX_SEQUENCE_LENGTH_D, 
                        categorical_size=self.MAX_LENGTH_CATEGORICAL,
                        topic_size=self.TOPIC_LENGTH,
                        number_of_BERT_layers=self.BERT_LAYERS)
        elif model == 'SiameseQA-A' or model == 'SiameseQA-W':
            self.model = SiameseQA(model_name=model,
                                    title_size=self.MAX_SEQUENCE_LENGTH_T, 
                                    desc_size=self.MAX_SEQUENCE_LENGTH_D, 
                                    categorical_size=self.MAX_LENGTH_CATEGORICAL,
                                    number_of_BERT_layers=self.BERT_LAYERS,
                                    trainable=model == 'SiameseQA-W')
        elif model == 'SiameseQAT-A' or model == 'SiameseQAT-W':
            self.model = SiameseQAT(model_name=model,
                                    title_size=self.MAX_SEQUENCE_LENGTH_T, 
                                    desc_size=self.MAX_SEQUENCE_LENGTH_D, 
                                    categorical_size=self.MAX_LENGTH_CATEGORICAL,
                                    topic_size=self.TOPIC_LENGTH,
                                    number_of_BERT_layers=self.BERT_LAYERS,
                                    trainable=model == 'SiameseQAT-W')
        
        # Save loss to compile and recovery bug encoder
        self.loss = self.model.get_loss()
        # Compile model
        self.model = compile_model(self.model)

    def get_model(self):
        return self.model

    def get_bug_encoder(self):
        return get_bug_encoder(self.model, self.loss)

    def train_model(self):
        logger.debug("Starting training!")
        total_data = len(self.train_preparation.get_data().train_data)
        number_of_batches = math.ceil(total_data / self.BATCH_SIZE)
        epochs = number_of_batches * self.EPOCHS
        epoch_index = 1
        logger.debug("Train size: {}".format(total_data))
        logger.debug("Epochs to train: {}".format(self.EPOCHS))
        for epoch in range(epochs):
            # Read batch to train
            _, _, train_sim, train_sample = self.generate_batch_data(self.BATCH_SIZE, 'train')

            # Train model
            h = self.model.train_on_batch(x=train_sample, y=train_sim)
            h_validation = self.model.test_on_batch(x=self.validation_sample, y=self.valid_sim)

            # Evaluate every epoch
            if epoch % number_of_batches == 0: # epoch done
                logger.debug(self.get_epoch_result(epoch_index, h=h, h_validation=h_validation))
                epoch_index += 1

        logger.debug("Train finished!")

    def get_epoch_result(self, epoch, **kwargs):
        step = epoch - 1
        if self.MODEL_NAME == 'SiameseTA' or self.MODEL_NAME == 'SiameseTAT':
            h = kwargs.get('h')
            h_validation = kwargs.get('h_validation')
            mlflow.log_metric("train_loss", h, step=step)
            mlflow.log_metric("test_loss", h_validation, step=step)
            return "Epoch: {} - Loss: {:.2f}, Loss_test: {:.2f}".format(epoch, h, h_validation)
        if self.MODEL_NAME == 'SiameseQA-A' or self.MODEL_NAME == 'SiameseQA-W' or self.MODEL_NAME == 'SiameseQAT-A' or self.MODEL_NAME == 'SiameseQAT-W':
            h = kwargs.get('h')
            h_validation = kwargs.get('h_validation')
            train_tl_w = h[1]
            train_tl_w_centroid = h[2]
            train_tl = h[3]
            train_tl_centroid = h[4]
            validation_tl_w = h_validation[1]
            validation_tl_w_centroid = h_validation[2]
            validation_tl = h_validation[3]
            validation_tl_centroid = h_validation[4]
            mlflow.log_metric("train_loss", h[0], step=step)
            mlflow.log_metric("test_loss", h_validation[0], step=step)
            mlflow.log_metric("train_triplet_loss_w", train_tl_w, step=step)
            mlflow.log_metric("train_triplet_loss", train_tl, step=step)
            mlflow.log_metric("train_triplet_loss_centroid", train_tl_centroid, step=step)
            mlflow.log_metric("train_triplet_loss_centroid_w", train_tl_w_centroid, step=step)
            mlflow.log_metric("test_triplet_loss_w", validation_tl_w, step=step)
            mlflow.log_metric("test_triplet_loss", validation_tl, step=step)
            mlflow.log_metric("test_triplet_loss_centroid", validation_tl_centroid, step=step)
            mlflow.log_metric("test_triplet_loss_centroid_w", validation_tl_w_centroid, step=step)
            return ("Epoch: {} " + 
              "Train - Loss: {:.2f}, " +
              "TL_w: {:.2f}, TL_centroid_w: {:.2f}, " + 
              "TL: {:.2f}, TL_centroid: {:.2f}\n" +
              "Validation - Loss_test: {:.2f}, " +
              "TL_w: {:.2f}, TL_centroid_w: {:.2f}, " + 
              "TL: {:.2f}, TL_centroid: {:.2f}").format(epoch, h[0], 
                                                train_tl_w, train_tl_w_centroid, 
                                                train_tl, train_tl_centroid,
                                                h_validation[0], validation_tl_w, validation_tl_w_centroid, 
                                                validation_tl, validation_tl_centroid,)
        return "Epoch: {}".format(epoch)
    
    def prepare_data(self):
        # These models do not use topic feature
        if self.MODEL_NAME == 'SiameseTA' or self.MODEL_NAME == 'SiameseQA-A' or self.MODEL_NAME == 'SiameseQA-W':
            self.TOPIC_LENGTH = 0
        
        self.train_preparation = TrainingPreparation(self.DIR, self.DOMAIN, 
                                        self.PREPROCESSING,
                                        self.MAX_SEQUENCE_LENGTH_T, 
                                        self.MAX_SEQUENCE_LENGTH_D,
                                        self.TOKEN_END)
        self.train_preparation.run()
        self.MAX_LENGTH_CATEGORICAL = self.train_preparation.get_data().categorical_size

    def prepare_validation_data(self):
        _, _, self.valid_sim, self.validation_sample = self.generate_batch_data(self.BATCH_SIZE_TEST, 'test')

    def generate_batch_data(self, batch_size_test, mode='test'):
        data = self.train_preparation.get_data()
        categorical_size = data.categorical_size
        buckets = data.buckets
        issues_by_buckets = data.issues_by_buckets
        if mode == 'test':
            bug_ids = data.bug_test_ids
            set_data = data.test_data
            bug_set = data.bug_set
        else: # train
            bug_ids = data.bug_train_ids
            set_data = data.train_data
            bug_set = data.bug_set
        # we want a constant validation group to have a frame of reference for model performance
        batch_triplets_valid, valid_input_sample, _, _, _, valid_sim = self.train_preparation.batch_iterator(
                                                                            bug_set, buckets, 
                                                                            set_data,
                                                                            bug_ids,
                                                                            batch_size_test,
                                                                            issues_by_buckets)
        validation_sample = []
        # Add Categorical
        if self.MAX_LENGTH_CATEGORICAL > 0:
            validation_sample.append(valid_input_sample['info'])
        # Add Desc
        if self.MAX_SEQUENCE_LENGTH_D > 0:
            validation_sample.append(valid_input_sample['description']['segment'])
            validation_sample.append(valid_input_sample['description']['token'])
        # Add Title
        if self.MAX_SEQUENCE_LENGTH_T > 0:
            validation_sample.append(valid_input_sample['title']['segment'])    
            validation_sample.append(valid_input_sample['title']['token'])
        # Add Topic
        if self.TOPIC_LENGTH > 0:
            validation_sample.append(valid_input_sample['topics'])
        
        # Add Label
        validation_sample.append(valid_sim)
            
        return batch_triplets_valid, valid_input_sample, valid_sim, validation_sample