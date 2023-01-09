import torch

from loss import create_criterion
from tqdm import tqdm
from transformers import (
    Trainer,
)


class CustomTrainer(Trainer):
    """Custom Loss를 적용하기 위한 Trainer"""

    def __init__(self, loss_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loss_name = loss_name

    def compute_loss(self, model, inputs, return_outputs=False):

        if "labels" in inputs and self.loss_name != "default":
            custom_loss = create_criterion(self.loss_name)
            labels = inputs.pop("labels")
        else:
            labels = None

        outputs = model(**inputs)

        if labels is not None:
            loss = custom_loss(outputs[0], labels)
        else:
            # We don't use .loss here since the model may return tuples instead of ModelOutput.
            loss = outputs["loss"] if isinstance(outputs, dict) else outputs[0]
        return (loss, outputs) if return_outputs else loss


class MultiLabelTrainer(Trainer):
    def __init__(self, loss_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loss_name = loss_name

    def compute_loss(self, model, inputs, return_outputs=False):
        if "labels" in inputs and self.loss_name != "default":
            type_loss = create_criterion(self.loss_name)
            polarity_loss = create_criterion(self.loss_name)
            tense_loss = create_criterion(self.loss_name)
            certainty_loss = create_criterion(self.loss_name)
            labels = inputs.pop("labels")
        else:
            labels = None

        type_logit, polarity_logit, tense_logit, certainty_logit = model(**inputs)

        loss = (
            type_loss(type_logit, labels[::, 0])
            + polarity_loss(polarity_logit, labels[::, 1])
            + tense_loss(tense_logit, labels[::, 2])
            + certainty_loss(certainty_logit, labels[::, 3])
        )
        outputs = (
            torch.argmax(type_logit, dim=1),
            torch.argmax(polarity_logit, dim=1),
            torch.argmax(tense_logit, dim=1),
            torch.argmax(certainty_logit, dim=1),
        )
        return (loss, outputs) if return_outputs else loss
