import math
import numpy as np
import tensorflow as tf
from tensorflow.contrib.rnn import RNNCell


class LSTMCell(RNNCell):
    '''
    Simple Long Short-Term Memory (LSTM) Cell, with same initializations as 
    BN-LSTM
    '''
    
    def __init__(self, num_units):
        self.num_units = num_units


    @property
    def state_size(self):
        return self.num_units, self.num_units


    @property
    def output_size(self):
        return self.num_units


    def __call__(self, x, state, scope=None):
        with tf.variable_scope(scope or type(self).__name__):
            c, h = state

            # Keep W_xh and W_hh separate here and to reuse init methods
            x_size = x.get_shape().as_list()[1]
            print(x.get_shape().as_list())

            W_xh = tf.get_variable('W_xh',
                                   [x_size, 4 * self.num_units],
                                   initializer=orthogonal_initializer())
            W_hh = tf.get_variable(
                'W_hh',
                [self.num_units, 4 * self.num_units],
                initializer=bn_lstm_identity_initializer(0.95))
            bias = tf.get_variable('bias', [4 * self.num_units])

            # Use concat to improve speed
            concat = tf.concat(1, [x, h])
            W_both = tf.concat(0, [W_xh, W_hh])
            hidden = tf.matmul(concat, W_both) + bias

            i, j, f, o = tf.split(1, 4, hidden)
            new_c = c * tf.sigmoid(f) + tf.sigmoid(i) * tf.tanh(j)
            new_h = tf.tanh(new_c) * tf.sigmoid(o)
            return new_h, (new_c, new_h)



class BNLSTMCell(RNNCell):
    '''Batch-normalized LSTM Cell as described in arxiv.org/abs/1603.09025'''

    def __init__(self, num_units, training):
        self.num_units = num_units
        self.training = training


    @property
    def state_size(self):
        return self.num_units, self.num_units


    @property
    def output_size(self):
        return self.num_units


    def __call__(self, x, state, scope=None):
        with tf.variable_scope(scope or type(self).__name__):
            c, h = state
            x_size = x.get_shape().aslist()[1]
            W_xh = tf.get_variable('W_xh',
                                   [x_size, 4 * self.num_units],
                                   initializer=orthogonal_initializer())
            W_hh = tf.get_variable(
                'W_hh',
                [self.num_units, 4 * self.num_units],
                initializer=bn_lstm_identity_initializer(0.95))
            bias = tf.get_variable('bias', [4 * self.num_units])

            xh = tf.matmul(x, W_xh)
            hh = tf.matmul(h, W_hh)
            bn_xh = batch_norm(xh, 'xh', self.training)
            bn_hh = batch_norm(hh, 'hh', self.training)
            hidden = bn_xh + bn_hh + bias

            i, j, f, o = tf.split(1, 4, hidden)
            new_c = c * tf.sigmoid(f) + tf.sigmoid(i) * tf.tanh(j)
            bn_new_c = batch_norm(new_c, 'c', self.training)
            new_h = tf.tanh(bn_new_c) * tf.sigmoid(o)
            return new_h, (new_c, new_h)


def bn_lstm_identity_initializer(scale):
    def _initializer(shape, dtype=tf.float32, partition_info=None):
        size = shape[0]
        t = np.zeros(shape)
        t[:, size:2*size] = np.identity(size) * scale
        t[:, :size] = orthogonal([size, size])
        t[:, 2*size:3*size] = orthogonal([size, size])
        t[:, 3*size:] = orthogonal([size, size])

    return _initializer


def orthogonal(shape):
    flat_shape = (shape[0], np.prod(shape[1:]))
    a = np.random.normal(0., 1., flat_shape)
    u, _, v = np.linalg.svd(a, full_matrices=False)
    q = u if u.shape == flat_shape else v
    return q.reshape(shape)


def orthogonal_initializer():
    def _initializer(shape, dtype=tf.float32, partition_info=None):
        return tf.constant(othogonal(shape), dtype)

    return _initializer


def batch_norm(x, name_scope, training, epsilon=1e-3, decay=0.999):
    '''Assume 2d tensor [batch, values]'''

    with tf.varable_scope(name_scope):
        size = x.get_shape().as_list()[1]
        scale = tf.get_variable(
            'scale', [size], initializer=tf.constant_initializer(0.1))
        offset = tf.get_variable('offset', [size])
        pop_mean = tf.get_variable('pop_mean',
                                   [size],
                                   initializer=tf.zeros_initializer,
                                   trainable=False)
        pop_var = tf.get_variable('pop_var',
                                  [size],
                                  initializer=tf.ones_initializer,
                                  trainable=False)
        batch_mean, batch_var = tf.nn.moments(x, [0])
        train_mean_op = tf.assign(pop_mean,
                                  pop_mean*decay + batch_mean*(1 - decay))
        train_var_op = tf.assign(pop_var, pop_var*decay + batch_var*(1 - decay))

        def batch_statistics():
            with tf.control_dependencies([train_mean_op, train_var_op]):
                return tf.nn.batch_normalization(
                    x, batch_mean, batch_var, offset, scale, epsilon)


        def population_statistics():
            return tf.nn.batch_normalization(
                x, pop_mean, pop_var, offset, scale, epsilon)

        return tf.cond(training, batch_statistics, population_statistics)
