import theano.tensor as T

from smartlearner.interfaces import Loss


class L2DistanceForSequences(Loss):
    def _get_updates(self):
        return {}  # There is no updates for L2Distance.

    def _compute_batch_losses(self, model_output):
        mask = self.dataset.symb_mask

        regression_outputs = model_output
        self.mean_sqr_error = T.mean(((regression_outputs - self.dataset.symb_targets)**2)*mask[:, :, None], axis=[1, 2])

        return self.mean_sqr_error


class L2DistanceWithBinaryCrossEntropy(Loss):
    def _get_updates(self):
        return {}  # There is no updates for L2Distance.

    def _compute_batch_losses(self, model_output):
        mask = self.dataset.symb_mask
        lengths = T.cast(T.sum(mask, axis=1), dtype="int32")  # Mask values are floats.
        idx_examples = T.arange(self.dataset.symb_targets.shape[0])
        # Create a mask that does not contain the last element of each sequence.
        smaller_mask = T.set_subtensor(mask[idx_examples, lengths-1], 0)

        # WARN: no sigmoid activation have been applied to `classif_outputs`.
        regression_outputs, classif_outputs = model_output
        self.mean_sqr_error = T.mean(((regression_outputs - self.dataset.symb_targets)**2)*mask[:, :, None], axis=[1, 2])

        # Compute cross-entropy for non-ending points.
        # Since target == 0, softplus(target * -classif_outputs + (1 - target) * classif_outputs)
        # can be simplified to softplus(classif_outputs)
        cross_entropy_not_ending = T.sum(T.nnet.softplus(classif_outputs)*smaller_mask[:, :, None], axis=[1, 2])

        # Compute cross-entropy for ending points.
        # Since target == 1, softplus(target * -classif_outputs + (1 - target) * classif_outputs)
        # can be simplified to softplus(-classif_outputs)
        # We also add an scaling factor because there is only one ending point per sequence whereas
        # there multiple non-ending points.
        cross_entropy_ending = (lengths-1) * T.nnet.softplus(-classif_outputs[idx_examples, lengths-1, 0])

        self.cross_entropy = (cross_entropy_not_ending + cross_entropy_ending) / lengths

        return self.mean_sqr_error + self.cross_entropy
