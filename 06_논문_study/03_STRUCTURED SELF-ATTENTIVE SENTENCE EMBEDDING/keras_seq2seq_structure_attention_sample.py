# -*- coding: utf-8 -*-
"""keras-seq2seq-structure-attention-sample.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1-F6y1-hx33oO87_eJodyPR0USlfNLBwM
"""

# https://github.com/chaitjo/structured-self-attention/blob/master/model.py

import numpy as np
from keras.models import Sequential
from keras.layers import Activation, TimeDistributed, Dense, RepeatVector, LSTM
from keras.utils import np_utils
from keras.callbacks import TensorBoard
import os

# brew install graphviz
# pip3 install graphviz
# pip3 install pydot-ng
from keras.utils.vis_utils import plot_model

digit = "0123456789"
alpha = "abcdefghij"

char_set = list(set(digit + alpha))  # id -> char
char_dic = {w: i for i, w in enumerate(char_set)}

data_dim = len(char_set)  # one hot encoding size
seq_length = time_steps = 7
num_classes = len(char_set)

# Build training date set
dataX = []
dataY = []

for i in range(1): #1000
    rand_pick = np.random.choice(10, 7)
    x = [char_dic[digit[c]] for c in rand_pick]
    y = [char_dic[alpha[c]] for c in rand_pick]
    
    dataX.append(x)
    dataY.append(y)
    
print(dataX)
print(dataY)
print(np.array(dataX).shape)
print(np.array(dataY).shape)

# One-hot encoding
dataX = np_utils.to_categorical(dataX, num_classes=num_classes)
# reshape X to be [samples, time steps, features]
dataX = np.reshape(dataX, (-1, seq_length, data_dim))
#dataX = np.reshape(dataX, (seq_length, data_dim))

# One-hot encoding
dataY = np_utils.to_categorical(dataY, num_classes=num_classes)
# time steps
dataY = np.reshape(dataY, (-1, seq_length, data_dim)) #reshape to batch size
#dataY = np.reshape(dataY, (seq_length, data_dim))

print(dataX)
print(dataX.shape)
print(dataY)
print(dataY.shape)

print('Build model...')
TensorBoard(log_dir='./logs', histogram_freq=1,
            write_graph=True, write_images=False)

from keras.models import Model
from keras.layers import *
from keras.activations import *
from keras.regularizers import *
from keras.initializers import *


def build_structured_self_attention_embedder(word_window_size, vocabulary_size, word_embedding_size,
                                             hidden_state_size, num_layers, attention_filters1, attention_filters2,
                                             dropout, recurrent_dropout, regularization_lambda):
    # Input for text sequence
    sequence_input = Input(shape=(word_window_size, ), name="sequence_input_placeholder") #shape=(word_window_size, )
    print("sequence_input.shape: ", sequence_input.shape)

    # Word embeddings lookup for words in sequence
    sequence_word_embeddings = Embedding(input_dim=vocabulary_size + 1,  # vocabulary_size + 1 ??
                                         output_dim=word_embedding_size,
                                         embeddings_initializer='glorot_uniform',
                                         embeddings_regularizer=l2(regularization_lambda),
                                         #input_length=20,
                                         #trainable=False,
                                         #mask_zero=True, 
                                         name="sequence_word_embeddings")(sequence_input)
    print("sequence_word_embeddings: ", sequence_word_embeddings)

    # Obtain hidden state of Bidirectional LSTM at each word embedding
    hidden_states = sequence_word_embeddings
    print("hidden_states: ", hidden_states)
    print("num_layers: ", num_layers)
    
    for layer in range(num_layers):
        hidden_states = Bidirectional(LSTM(units=hidden_state_size,
                                           #input_shape=(word_window_size, ),
                                           #batch_input_shape = (None, word_window_size, ),
                                           dropout=dropout,
                                           recurrent_dropout=recurrent_dropout,
                                           kernel_initializer='glorot_uniform',
                                           recurrent_initializer='glorot_uniform',
                                           bias_initializer='zeros',
                                           kernel_regularizer=l2(regularization_lambda),
                                           recurrent_regularizer=l2(regularization_lambda),
                                           bias_regularizer=l2(regularization_lambda),
                                           activity_regularizer=l2(regularization_lambda),
                                           implementation=1,
                                           return_sequences=True,
                                           return_state=False,
                                           unroll=True),
                                      merge_mode='mul', name="lstm_outputs_{}".format(layer))(hidden_states) #merge_mode = 'concat'
        
    print("hidden_states: ", hidden_states)

    # Attention mechanism
    attention = Conv1D(filters=attention_filters1, kernel_size=1, activation='tanh', padding='same', use_bias=True,
                       kernel_initializer='glorot_uniform', bias_initializer='zeros',
                       kernel_regularizer=l2(regularization_lambda),
                       bias_regularizer=l2(regularization_lambda), activity_regularizer=l2(regularization_lambda),
                       name="attention_layer1")(hidden_states)
    attention = Conv1D(filters=attention_filters2, kernel_size=1, activation='linear', padding='same', use_bias=True,
                       kernel_initializer='glorot_uniform', bias_initializer='zeros',
                       kernel_regularizer=l2(regularization_lambda),
                       bias_regularizer=l2(regularization_lambda), activity_regularizer=l2(regularization_lambda),
                       name="attention_layer2")(attention)
    attention = Lambda(lambda x: softmax(x, axis=1), name="attention_vector")(attention)

    # Apply attention weights
    weighted_sequence_embedding = Dot(axes=[1, 1], normalize=False, name="weighted_sequence_embedding")(
        [attention, hidden_states])
    print("attention:" , attention)
    print("hidden_states:" , hidden_states)
    print("weighted_sequence_embedding:", weighted_sequence_embedding)
    
    # Add and normalize to obtain final sequence embedding
    sequence_embedding = Lambda(lambda x: K.l2_normalize(K.sum(x, axis=1)))(weighted_sequence_embedding)
    print("sequence_embedding:",sequence_embedding)
    
    print("sequence_input:", sequence_input)
    print("sequence_embedding:", sequence_embedding)
    # Build model
    model = Model(inputs=sequence_input, outputs=sequence_embedding, name="sequence_embedder")
    #model = Model(inputs=sequence_word_embeddings, outputs=sequence_embedding, name="sequence_embedder")
    model.summary()
    return model

#lstm_en = LSTM(32, input_shape=(time_steps, data_dim), return_sequences=False);
# For the decoder's input, we repeat the encoded input for each time step
#model.add(RepeatVector(time_steps))


#attention_layer param
# word_window_size, vocabulary_size, word_embedding_size,
# hidden_state_size, num_layers, attention_filters1, attention_filters2,
# dropout, recurrent_dropout, regularization_lambda
#-hidden_state_size: LSTM unit 크기(넓이 폭) => LSTM output size
#-word_window_size : input shape(입력길이)
#-vocabulary_size : Embedding input dimension
#-word_embedding_size : Embedding output dim
#-num_layers : LSTM 반복수(깊이)
#seq2seq sample param
# data_dim = len(char_set)     > 20
# seq_length = time_steps = 7  > 7 
# num_classes = len(char_set)  > 20
attention_model  = build_structured_self_attention_embedder(
    data_dim, data_dim, data_dim,
    data_dim, 4, 64, 32,
    0.1, 0.1, 0.01
);
#model.add(attention_layer);

attention_model.compile(loss='categorical_crossentropy',
              optimizer='adam',
              metrics=['accuracy'])
print(dataX[0, :, :])
print(dataX[0, :, :].shape)
print(dataY[0, :, :])
print(dataY[0, :, :].shape)
attention_model.fit(dataX[0, :, :], dataY[0, :, :], epochs=10)

__file__ = 'seq2seq_sample'
# Store model graph in png
# (Error occurs on in python interactive shell)
plot_model(attention_model, to_file=os.path.basename(__file__) + '.png', show_shapes=True)

# Create test data set for fun
testX = []
testY = []
for i in range(1): #10
    rand_pick = np.random.choice(10, 7)
    x = [char_dic[digit[c]] for c in rand_pick]
    y = [alpha[c] for c in rand_pick]
    testX.append(x)
    testY.append(y)

print(testX)
print(testY)

# One-hot encoding
testX = np_utils.to_categorical(testX, num_classes=num_classes)
# reshape X to be [samples, time steps, features]
testX = np.reshape(testX, (-1, seq_length, data_dim))
print(testX.shape)

model = attention_model

print(testX[0, :, :])
print(testX[0, :, :].shape)      
predictions = model.predict(testX[0, :, :], verbose=0)
for i, prediction in enumerate(predictions):
    # print(prediction)
    x_index = np.argmax(testX[0, :, :], axis=0) #axis=1
    print("x_index: ", x_index)
    x_str = [char_set[j] for j in x_index]

    index = np.argmax(prediction, axis=0) #axis=1
    print("index: ", index)
    #result = [char_set[j] for j in index]

    #print(''.join(x_str), ' -> ', ''.join(result), " true: ", ''.join(testY[i]))

