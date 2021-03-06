import tensorflow as tf
from nolearn.lasagne import BatchIterator


class Trainer:
    def __init__(self, graph_model, epochs, batch_size, logdir, save_path, val_epoch=100, save_epoch=200):
        self.graph_model = graph_model
        self.epochs = epochs
        self.val_epoch = val_epoch
        self.save_epoch = save_epoch
        self.batch_size = batch_size
        self.logdir = logdir
        self.save_path = save_path
        self.session = None

    def eval(self, x, y, tf_x, tf_y, tf_train, tf_loss):
        loss = self.session.run([tf_loss], feed_dict={
            tf_x: x,
            tf_y: y,
            tf_train: False
        })
        return loss

    def train(self, data):
        print 'Start training ...'

        x_train = data['train']['x']
        y_train = data['train']['y']
        x_val = data['val']['x']
        y_val = data['val']['y']
        x_test = data['test']['x']
        y_test = data['test']['y']

        graph, init_graph = self.graph_model.get_graph()
        optimizer = self.graph_model.optimizer
        x_placeholder, y_placeholder, is_training_placeholder = self.graph_model.get_placeholders()

        print 'Running a session ...'
        tf_config = tf.ConfigProto(device_count={'GPU': 1})
        tf_config.gpu_options.allow_growth = True

        with tf.Session(graph=graph, config=tf_config) as self.session:

            self.session.run(init_graph)
            saver = tf.train.Saver()
            summary_op = tf.summary.merge_all()
            writer = tf.summary.FileWriter(logdir=self.logdir, graph=self.session.graph)

            for epoch in range(self.epochs):
                print '%s / %s th epoch, training ...' % (epoch, self.epochs)
                batch_iterator = BatchIterator(batch_size=self.batch_size, shuffle=True)
                for x_train_batch, y_train_batch in batch_iterator(x_train, y_train):
                    _, summary = self.session.run([optimizer, summary_op], feed_dict={
                        x_placeholder: x_train_batch,
                        y_placeholder: y_train_batch,
                        is_training_placeholder: True
                    })

                if epoch % self.val_epoch == 0:
                    print '[Validating Round]'

                    loss_train = self.eval(x=x_train,
                                           y=y_train,
                                           tf_x=x_placeholder,
                                           tf_y=y_placeholder,
                                           tf_train=is_training_placeholder,
                                           tf_loss=self.graph_model.loss)
                    loss_val = self.eval(x=x_val,
                                         y=y_val,
                                         tf_x=x_placeholder,
                                         tf_y=y_placeholder,
                                         tf_train=is_training_placeholder,
                                         tf_loss=self.graph_model.loss)

                    print '%s th epoch:\n' \
                          '   train loss: %s' \
                          '   val loss: %s' \
                          % (epoch, loss_train, loss_val)

                writer.add_summary(summary, epoch)

                if (epoch % self.save_epoch == 0) or (epoch == self.epochs - 1):
                    print '[Testing Round]'
                    snapshot_path = saver.save(sess=self.session, save_path="%s_%s_" % (self.save_path, epoch))
                    print 'Snapshot of %s th epoch is saved to %s' % (epoch, snapshot_path)

                    loss_test = self.eval(x=x_test,
                                          y=y_test,
                                          tf_x=x_placeholder,
                                          tf_y=y_placeholder,
                                          tf_train=is_training_placeholder,
                                          tf_loss=self.graph_model.loss)
                    print '%s th epoch:\n' \
                          '   test loss: %s' \
                          % (epoch, loss_test)
            save_path = saver.save(self.session, self.save_path)
            print 'Training ended and model file is in here: ', save_path
