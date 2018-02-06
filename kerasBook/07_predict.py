import numpy as np
from keras.regularizers import l2
from keras.datasets import mnist
from keras.layers import Activation, Dense, Dropout
from keras.models import Sequential
from keras.optimizers import Adam
from keras.utils import np_utils

np.random.seed(1976)

# Network and training
EPOCHS = 30
BATCH = 128
VERBOSE = 1
N_CLASSES = 10
OPTIMIZER = Adam()
N_HIDDEN = 128
VALIDATION_SPLIT = 0.2
DROPOUT = 0.3
RESHAPED = 28 * 28 # 28x28 -> 784 (MNIST img size)

# Data -- shuffled and split between train and test
(X_train, y_train), (X_test, y_test) = mnist.load_data()

X_train = X_train.reshape(-1, RESHAPED).astype('float32')
X_test  = X_test.reshape(-1,  RESHAPED).astype('float32')

# Normalize
X_train /= 255
X_test /= 255
print('X train:', X_train.shape)
print('X test:',  X_test.shape)

# Convert y class vectors to matrices
Y_train = np_utils.to_categorical(y_train, N_CLASSES)
Y_test  = np_utils.to_categorical(y_test, N_CLASSES)
print('recoding y:', y_train[0], ' -> ', Y_train[0]) #5 -> [0 0 0 0 0 1 0 0 0 0]


# Model
model = Sequential()
model.add(Dense(N_HIDDEN, input_shape=(RESHAPED,), kernel_regularizer=l2(0.01)))
model.add(Activation('relu'))
model.add(Dropout(DROPOUT))
model.add(Dense(N_HIDDEN, kernel_regularizer=l2(0.01)))
model.add(Activation('relu'))
model.add(Dropout(DROPOUT))
model.add(Dense(N_CLASSES, kernel_regularizer=l2(0.01)))
model.add(Activation('softmax'))
print(model.summary())

model.compile(
    loss='categorical_crossentropy', optimizer=OPTIMIZER, metrics=['accuracy'])

history = model.fit(X_train,
                    Y_train,
                    batch_size=BATCH,
                    epochs=EPOCHS,
                    verbose=VERBOSE,
                    validation_split=VALIDATION_SPLIT)
score = model.evaluate(X_test, Y_test, verbose=VERBOSE)
print('Test score:', score[0], '\nTest accuracy:', score[1])


# Predict
predictions = model.predict(X_test)
print('predictions:\n', predictions)

pred_probs  = model.predict_proba(X_test)
print('prediction probabilities:\n', pred_probs)

pred_classes = model.predict_classes(X_test)
print('prediction classes:\n', pred_classes)
