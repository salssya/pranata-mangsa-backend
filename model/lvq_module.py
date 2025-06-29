# lvq_module.py
import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin

class LVQClassifier(BaseEstimator, ClassifierMixin):
    def __init__(self, learning_rate=0.001, decay_rate=0.1, min_learning_rate=0.0, epochs=50):
        self.learning_rate = learning_rate
        self.decay_rate = decay_rate
        self.min_learning_rate = min_learning_rate
        self.epochs = epochs

    def fit(self, X, y):
        self.classes_ = np.unique(y)
        n_classes = len(self.classes_)
        n_features = X.shape[1]
        self.weights_ = np.zeros((n_classes, n_features))

        for i, cls in enumerate(self.classes_):
            self.weights_[i] = X[y == cls].mean(axis=0)

        lr = self.learning_rate
        for epoch in range(self.epochs):
            for i in range(len(X)):
                x = X[i]
                label = y[i]
                idx = self._winner(x)
                target_class = self.classes_[idx]

                if target_class == label:
                    self.weights_[idx] += lr * (x - self.weights_[idx])
                else:
                    self.weights_[idx] -= lr * (x - self.weights_[idx])
            lr = max(lr - self.decay_rate, self.min_learning_rate)

        return self

    def _winner(self, x):
        distances = np.linalg.norm(self.weights_ - x, axis=1)
        return np.argmin(distances)

    def predict(self, X):
        return np.array([self.classes_[self._winner(x)] for x in X])
